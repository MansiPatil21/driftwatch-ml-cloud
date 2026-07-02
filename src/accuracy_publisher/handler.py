import json
import boto3
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')


def handler(event, context):
    table_name = os.environ.get('GROUND_TRUTH_TABLE', 'ml-ground-truth')
    table = dynamodb.Table(table_name)

    # Scan all ground truth records
    response = table.scan()
    items = response.get('Items', [])

    # Handle DynamoDB pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    if not items:
        print("No ground truth records found — skipping")
        return {'statusCode': 200, 'body': json.dumps({'message': 'No data'})}

    # Group by model_id and compute accuracy per model
    models = {}
    for item in items:
        mid = item.get('model_id', 'unknown')
        models.setdefault(mid, {'correct': 0, 'total': 0})
        models[mid]['total'] += 1
        if item.get('correct') is True:
            models[mid]['correct'] += 1

    metrics = []
    results = {}
    for model_id, counts in models.items():
        accuracy = counts['correct'] / counts['total'] if counts['total'] > 0 else 0.0
        accuracy = round(accuracy, 4)
        results[model_id] = {'accuracy': accuracy, **counts}
        print(f"[{model_id}] accuracy={accuracy:.1%}  correct={counts['correct']}/{counts['total']}")

        metrics.append({
            'MetricName': 'ModelAccuracy',
            'Value': accuracy,
            'Unit': 'None',
            'Dimensions': [{'Name': 'ModelId', 'Value': model_id}]
        })

    # Publish all model accuracies in one call
    cloudwatch.put_metric_data(Namespace='MLMonitoring', MetricData=metrics)
    print(f"Published ModelAccuracy for {list(results.keys())}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'models': results,
            'total_records': len(items)
        })
    }
