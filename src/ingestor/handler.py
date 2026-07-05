import json
import boto3
import os
import time
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
kinesis = boto3.client('kinesis')

PREDICTION_RETENTION_DAYS = 90


def handler(event, context):
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    stream_name = os.environ.get('KINESIS_STREAM_NAME')

    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON body'})
        }

    model_id = body.get('model_id')
    confidence = body.get('confidence')
    prediction = body.get('prediction')

    if not model_id or confidence is None or not prediction:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'model_id, prediction, and confidence are required'})
        }

    item = {
        'model_id': model_id,
        'timestamp': datetime.utcnow().isoformat(),
        'prediction': prediction,
        'confidence': str(confidence),
        'id': str(uuid.uuid4()),
        'ttl': int(time.time()) + PREDICTION_RETENTION_DAYS * 86400
    }

    table.put_item(Item=item)

    if stream_name:
        try:
            kinesis.put_record(
                StreamName=stream_name,
                Data=json.dumps(item).encode('utf-8'),
                PartitionKey=model_id
            )
        except Exception as e:
            print(f"Kinesis put_record failed (non-fatal): {e}")

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Prediction logged', 'id': item['id']})
    }
