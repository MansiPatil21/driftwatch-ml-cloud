import json
import boto3
import os
import math
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')
stepfunctions = boto3.client('stepfunctions')


def compute_psi(baseline_dist, current_dist, buckets=10):
    """
    Population Stability Index — industry standard drift metric.
    PSI < 0.1  : No significant drift
    PSI 0.1–0.2: Moderate drift, monitor closely
    PSI > 0.2  : Significant drift, action required
    """
    def make_histogram(values, bucket_edges):
        counts = [0] * len(bucket_edges)
        for v in values:
            placed = False
            for i, edge in enumerate(bucket_edges):
                if v <= edge:
                    counts[i] += 1
                    placed = True
                    break
            if not placed:
                counts[-1] += 1
        total = sum(counts) or 1
        return [c / total for c in counts]

    bucket_edges = [i / buckets for i in range(1, buckets + 1)]
    baseline_pct = make_histogram(baseline_dist, bucket_edges)
    current_pct  = make_histogram(current_dist,  bucket_edges)

    psi = 0.0
    for b, c in zip(baseline_pct, current_pct):
        b = max(b, 0.0001)
        c = max(c, 0.0001)
        psi += (c - b) * math.log(c / b)

    return round(psi, 4)


def get_model_config(config_table_name, model_id):
    """Fetch per-model config. Falls back to defaults if not found."""
    if not config_table_name:
        return {"confidence_threshold": 0.75, "psi_threshold": 0.2}
    try:
        table = dynamodb.Table(config_table_name)
        resp = table.get_item(Key={"model_id": model_id})
        item = resp.get("Item")
        if item:
            return {
                "confidence_threshold": float(item.get("confidence_threshold", 0.75)),
                "psi_threshold": float(item.get("psi_threshold", 0.2))
            }
    except Exception:
        pass
    return {"confidence_threshold": 0.75, "psi_threshold": 0.2}



def handler(event, context):
    table         = dynamodb.Table(os.environ['TABLE_NAME'])
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    threshold     = float(os.environ.get('CONFIDENCE_THRESHOLD', '0.75'))
    config_table  = os.environ.get('MODEL_CONFIG_TABLE', '')

    # ── Fetch recent predictions (last 1 hour) ──────────────────
    cutoff = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    response = table.scan(
        FilterExpression='#ts > :cutoff',
        ExpressionAttributeNames={'#ts': 'timestamp'},
        ExpressionAttributeValues={':cutoff': cutoff}
    )
    items = response.get('Items', [])

    if not items:
        print("No predictions in the last hour — skipping drift check")
        return {'statusCode': 200, 'body': 'No predictions to analyze'}

    # ── Group by model_id for per-model analysis ─────────────────
    models = {}
    for item in items:
        mid = item.get('model_id', 'unknown')
        models.setdefault(mid, []).append(float(item.get('confidence', 0)))

    alerts_fired = []

    for model_id, confidences in models.items():
        config      = get_model_config(config_table, model_id)
        conf_thresh = config['confidence_threshold']
        psi_thresh  = config['psi_threshold']

        avg_conf = sum(confidences) / len(confidences)

        baseline  = [0.85 + (i % 10) * 0.01 for i in range(50)]
        psi_score = compute_psi(baseline, confidences)

        print(f"[{model_id}] count={len(confidences)} avg_conf={avg_conf:.3f} PSI={psi_score}")

        cloudwatch.put_metric_data(
            Namespace='MLMonitoring',
            MetricData=[
                {'MetricName': 'AverageConfidence', 'Value': avg_conf,  'Unit': 'None',
                 'Dimensions': [{'Name': 'ModelId', 'Value': model_id}]},
                {'MetricName': 'PSIScore',          'Value': psi_score, 'Unit': 'None',
                 'Dimensions': [{'Name': 'ModelId', 'Value': model_id}]},
            ]
        )

        conf_drift = avg_conf < conf_thresh
        psi_drift  = psi_score > psi_thresh

        if conf_drift or psi_drift:
            reasons = []
            if conf_drift:
                reasons.append(f"avg confidence {avg_conf:.3f} < threshold {conf_thresh}")
            if psi_drift:
                reasons.append(f"PSI score {psi_score} > threshold {psi_thresh} (significant distribution shift)")

            message = (
                f"DRIFT DETECTED — {model_id}\n\n"
                f"Reasons:\n" + "\n".join(f"  • {r}" for r in reasons) +
                f"\n\nPredictions analyzed: {len(confidences)}"
                f"\nTime window: last 1 hour"
                f"\nDetected at: {datetime.utcnow().isoformat()}"
                f"\n\nAction required: investigate model and consider retraining."
            )

            sns.publish(
                TopicArn=sns_topic_arn,
                Subject=f'DRIFT ALERT: {model_id}',
                Message=message
            )
            alerts_fired.append(model_id)
            print(f"ALERT fired for {model_id}")

            state_machine_arn = os.environ.get('STATE_MACHINE_ARN', '')
            if state_machine_arn:
                try:
                    stepfunctions.start_execution(
                        stateMachineArn=state_machine_arn,
                        input=json.dumps({
                            "model_id": model_id,
                            "stage": "check",
                            "drift_hours": 1
                        })
                    )
                    print(f"Step Functions workflow started for {model_id}")
                except Exception as e:
                    print(f"Step Functions start failed: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'models_checked': list(models.keys()),
            'alerts_fired': alerts_fired,
            'predictions_total': len(items)
        })
    }
