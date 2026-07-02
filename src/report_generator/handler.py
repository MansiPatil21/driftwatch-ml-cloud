import json
import boto3
import os
from datetime import datetime, timedelta
from collections import Counter

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')


def handler(event, context):
    table = dynamodb.Table(os.environ['TABLE_NAME'])
    bucket_name = os.environ['BUCKET_NAME']

    # Query last 24 hours of predictions
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    response = table.scan(
        FilterExpression='#ts > :cutoff',
        ExpressionAttributeNames={'#ts': 'timestamp'},
        ExpressionAttributeValues={':cutoff': cutoff}
    )

    items = response.get('Items', [])
    confidences = [float(item.get('confidence', 0)) for item in items]
    predictions = [item.get('prediction', '') for item in items]
    prediction_counts = dict(Counter(predictions))

    report = {
        'date': datetime.utcnow().strftime('%Y-%m-%d'),
        'generated_at': datetime.utcnow().isoformat(),
        'total_predictions': len(items),
        'avg_confidence': round(sum(confidences) / len(confidences), 3) if confidences else 0,
        'min_confidence': round(min(confidences), 3) if confidences else 0,
        'max_confidence': round(max(confidences), 3) if confidences else 0,
        'prediction_distribution': prediction_counts
    }

    print(f"Daily report: {report['total_predictions']} predictions, avg confidence {report['avg_confidence']}")

    # Save report to S3
    key = f"reports/{report['date']}/daily-report.json"
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(report, indent=2),
        ContentType='application/json'
    )

    print(f"Report saved to s3://{bucket_name}/{key}")

    return {
        'statusCode': 200,
        'body': json.dumps(report)
    }
