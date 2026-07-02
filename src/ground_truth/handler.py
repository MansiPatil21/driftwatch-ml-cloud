import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')


def handler(event, context):
    """
    POST /ground-truth
    Body: { "prediction_id": "abc-123", "model_id": "spam-detector-v1", "actual_label": "spam" }

    Matches against the original prediction in DynamoDB and calculates real accuracy.
    Publishes accuracy metrics to CloudWatch.
    """
    predictions_table   = dynamodb.Table(os.environ['TABLE_NAME'])
    ground_truth_table  = dynamodb.Table(os.environ['GROUND_TRUTH_TABLE'])

    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return _response(400, {'error': 'Invalid JSON'})

    prediction_id = body.get('prediction_id')
    model_id      = body.get('model_id')
    actual_label  = body.get('actual_label')

    if not all([prediction_id, model_id, actual_label]):
        return _response(400, {'error': 'prediction_id, model_id, and actual_label are required'})

    # Find the original prediction by scanning for matching id
    scan_resp = predictions_table.scan(
        FilterExpression='#id = :pid',
        ExpressionAttributeNames={'#id': 'id'},
        ExpressionAttributeValues={':pid': prediction_id}
    )
    matches = scan_resp.get('Items', [])

    if not matches:
        return _response(404, {'error': f'Prediction {prediction_id} not found'})

    original = matches[0]
    predicted_label = original.get('prediction', '')
    is_correct = predicted_label == actual_label

    # Store ground truth record
    ground_truth_table.put_item(Item={
        'prediction_id': prediction_id,
        'model_id':      model_id,
        'predicted':     predicted_label,
        'actual':        actual_label,
        'correct':       is_correct,
        'timestamp':     datetime.utcnow().isoformat()
    })

    # Calculate rolling accuracy for this model from recent ground truth records
    gt_scan = ground_truth_table.scan(
        FilterExpression='model_id = :mid',
        ExpressionAttributeValues={':mid': model_id}
    )
    all_records = gt_scan.get('Items', [])
    if all_records:
        accuracy = sum(1 for r in all_records if r.get('correct')) / len(all_records)

        cloudwatch.put_metric_data(
            Namespace='MLMonitoring',
            MetricData=[{
                'MetricName': 'ModelAccuracy',
                'Value': accuracy,
                'Unit': 'None',
                'Dimensions': [{'Name': 'ModelId', 'Value': model_id}]
            }]
        )
        print(f"[{model_id}] accuracy={accuracy:.3f} from {len(all_records)} ground truth records")

    return _response(200, {
        'message': 'Ground truth recorded',
        'prediction_id': prediction_id,
        'model_id': model_id,
        'predicted': predicted_label,
        'actual': actual_label,
        'correct': is_correct
    })


def _response(status, body):
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body)
    }
