import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
    """
    GET  /models/{model_id}/config  — fetch config for a model
    POST /models/{model_id}/config  — create or update config for a model
    """
    table = dynamodb.Table(os.environ['MODEL_CONFIG_TABLE'])
    method = event.get('httpMethod', 'GET')
    path_params = event.get('pathParameters') or {}
    model_id = path_params.get('model_id', '')

    if not model_id:
        return _response(400, {'error': 'model_id is required in path'})

    if method == 'GET':
        resp = table.get_item(Key={'model_id': model_id})
        item = resp.get('Item')
        if not item:
            return _response(404, {'error': f'No config found for model {model_id}'})
        return _response(200, item)

    if method == 'POST':
        body = json.loads(event.get('body') or '{}')
        item = {
            'model_id': model_id,
            'confidence_threshold': str(body.get('confidence_threshold', 0.75)),
            'psi_threshold':        str(body.get('psi_threshold', 0.2)),
            'owner_email':          body.get('owner_email', ''),
            'description':          body.get('description', ''),
        }
        table.put_item(Item=item)
        return _response(200, {'message': f'Config saved for {model_id}', 'config': item})

    return _response(405, {'error': f'Method {method} not allowed'})


def _response(status, body):
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body)
    }
