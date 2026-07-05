import json
import boto3
import os
import time
import uuid
import base64
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

PREDICTION_RETENTION_DAYS = 90


def handler(event, context):
    """
    Processes batches of predictions from Kinesis Data Streams.
    Triggered automatically when records accumulate in the stream.
    More cost-efficient than per-prediction Lambda invocations at high volume.
    """
    table = dynamodb.Table(os.environ['TABLE_NAME'])

    processed = 0
    failed = 0
    items_to_write = []

    for record in event.get('Records', []):
        try:
            # Kinesis records are base64-encoded
            raw = base64.b64decode(record['kinesis']['data']).decode('utf-8')
            body = json.loads(raw)

            item = {
                'model_id':   body.get('model_id', 'unknown'),
                'timestamp':  body.get('timestamp', datetime.utcnow().isoformat()),
                'prediction': body.get('prediction', ''),
                'confidence': str(body.get('confidence', 0)),
                'id':         str(uuid.uuid4()),
                'source':     'kinesis',
                'ttl':        int(time.time()) + PREDICTION_RETENTION_DAYS * 86400
            }
            items_to_write.append(item)
            processed += 1

        except Exception as e:
            print(f"Failed to process record: {e}")
            failed += 1

    # Batch write to DynamoDB (up to 25 items per batch)
    with table.batch_writer() as batch:
        for item in items_to_write:
            batch.put_item(Item=item)

    print(f"Kinesis batch: {processed} processed, {failed} failed")

    cloudwatch.put_metric_data(
        Namespace='MLMonitoring',
        MetricData=[
            {'MetricName': 'KinesisProcessed', 'Value': processed, 'Unit': 'Count'},
            {'MetricName': 'KinesisFailed',    'Value': failed,    'Unit': 'Count'},
        ]
    )

    return {'statusCode': 200, 'processed': processed, 'failed': failed}
