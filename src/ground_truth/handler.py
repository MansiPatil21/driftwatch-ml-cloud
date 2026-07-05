import json
import boto3
import os
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    """
    POST /ground-truth
    Body: { "prediction_id": "abc-123", "model_id": "spam-detector-v1", "actual_label": "spam" }

    Matches against the original prediction in DynamoDB and records the outcome.
    Aggregate accuracy is computed and published to CloudWatch separately by
    the scheduled ml-accuracy-publisher Lambda, not here.
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

    # Find the original prediction via the IdIndex GSI (avoids a full table scan)
    query_resp = predictions_table.query(
        IndexName='IdIndex',
        KeyConditionExpression=Key('id').eq(prediction_id)
    )
    matches = query_resp.get('Items', [])

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
