import json
import boto3
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')


def handler(event, context):
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']

    # Query predictions from the last 15 minutes
    cutoff = (datetime.utcnow() - timedelta(minutes=15)).isoformat()
    response = table.scan(
        FilterExpression='#ts > :cutoff',
        ExpressionAttributeNames={'#ts': 'timestamp'},
        ExpressionAttributeValues={':cutoff': cutoff}
    )

    items = response.get('Items', [])
    volume = len(items)

    print(f"Prediction volume in last 15 minutes: {volume}")

    # Push volume metric to CloudWatch
    cloudwatch.put_metric_data(
        Namespace='MLMonitoring',
        MetricData=[{
            'MetricName': 'PredictionVolume',
            'Value': volume,
            'Unit': 'Count'
        }]
    )

    # Alert if no predictions received — model may be down
    if volume == 0:
        message = (
            f"ANOMALY DETECTED\n\n"
            f"No predictions received in the last 15 minutes.\n"
            f"The monitored model may be offline, unreachable, or experiencing errors.\n\n"
            f"Time: {datetime.utcnow().isoformat()}\n"
            f"Action required: check model health and API connectivity."
        )
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject='ANOMALY ALERT: No predictions received in 15 minutes',
            Message=message
        )
        print("ALERT sent — zero prediction volume detected")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'volume_last_15min': volume,
            'alert_fired': volume == 0
        })
    }
