import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')


def handler(event, context):
    """
    Step Functions task handler — called at each stage of the drift response workflow.
    Receives the current state and decides what action to take.

    Step Functions passes: { "model_id": "...", "stage": "check|escalate|resolve", "drift_hours": N }
    """
    model_id    = event.get('model_id', 'unknown')
    stage       = event.get('stage', 'check')
    drift_hours = event.get('drift_hours', 1)
    sns_topic   = os.environ['SNS_TOPIC_ARN']

    print(f"[DriftResponder] model={model_id} stage={stage} drift_hours={drift_hours}")

    if stage == 'check':
        # Re-check current drift state before escalating
        still_drifting = _check_current_drift(model_id)
        return {
            'model_id':      model_id,
            'stage':         'escalate' if still_drifting else 'resolve',
            'drift_hours':   drift_hours + 1,
            'still_drifting': still_drifting,
            'checked_at':    datetime.utcnow().isoformat()
        }

    if stage == 'escalate':
        # Drift persisted — send escalation alert
        sns.publish(
            TopicArn=sns_topic,
            Subject=f'ESCALATION: {model_id} has been drifting for {drift_hours} hours',
            Message=(
                f"Model {model_id} has been continuously drifting for {drift_hours} hours.\n\n"
                f"Immediate action required:\n"
                f"  1. Review recent input data for distribution shifts\n"
                f"  2. Collect new labeled samples\n"
                f"  3. Evaluate model for retraining\n\n"
                f"Escalated at: {datetime.utcnow().isoformat()}"
            )
        )
        return {
            'model_id':    model_id,
            'stage':       'check',
            'drift_hours': drift_hours,
            'escalated':   True
        }

    if stage == 'resolve':
        # Drift resolved — send all-clear
        sns.publish(
            TopicArn=sns_topic,
            Subject=f'RESOLVED: {model_id} drift has cleared',
            Message=(
                f"Model {model_id} confidence has returned to healthy levels.\n"
                f"Drift duration: approximately {drift_hours} hours.\n"
                f"Resolved at: {datetime.utcnow().isoformat()}"
            )
        )
        return {
            'model_id': model_id,
            'resolved': True,
            'drift_hours': drift_hours
        }

    return {'model_id': model_id, 'stage': stage, 'error': 'Unknown stage'}


def _check_current_drift(model_id):
    """Quick confidence check to see if model is still drifting."""
    try:
        table_name = os.environ.get('TABLE_NAME', 'ml-predictions')
        table = dynamodb.Table(table_name)
        from datetime import timedelta
        cutoff = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        resp = table.scan(
            FilterExpression='model_id = :mid AND #ts > :cutoff',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':mid': model_id, ':cutoff': cutoff}
        )
        items = resp.get('Items', [])
        if not items:
            return False
        confidences = [float(i.get('confidence', 0)) for i in items]
        avg = sum(confidences) / len(confidences)
        return avg < 0.75
    except Exception as e:
        print(f"Check drift error: {e}")
        return True
