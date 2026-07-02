import json
import boto3
import os
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    table = dynamodb.Table(os.environ['TABLE_NAME'])

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
        'id': str(uuid.uuid4())
    }

    table.put_item(Item=item)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Prediction logged', 'id': item['id']})
    }
