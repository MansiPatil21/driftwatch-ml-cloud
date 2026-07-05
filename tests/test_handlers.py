import json
import unittest
from unittest.mock import patch, MagicMock
import os

os.environ['TABLE_NAME'] = 'ml-predictions'
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789:ml-drift-alerts'
os.environ['CONFIDENCE_THRESHOLD'] = '0.75'
os.environ['BUCKET_NAME'] = 'ml-monitoring-reports-123456789'


class TestIngestor(unittest.TestCase):

    @patch('boto3.client')
    @patch('boto3.resource')
    def test_valid_prediction_returns_200(self, mock_boto, mock_client):
        mock_table = MagicMock()
        mock_boto.return_value.Table.return_value = mock_table

        from src.ingestor.handler import handler

        event = {
            'body': json.dumps({
                'model_id': 'spam-detector-v1',
                'prediction': 'spam',
                'confidence': 0.92
            })
        }

        response = handler(event, {})
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertIn('id', body)
        self.assertEqual(body['message'], 'Prediction logged')

    @patch('boto3.client')
    @patch('boto3.resource')
    def test_missing_fields_returns_400(self, mock_boto, mock_client):
        from src.ingestor.handler import handler

        event = {'body': json.dumps({'model_id': 'spam-detector-v1'})}
        response = handler(event, {})
        self.assertEqual(response['statusCode'], 400)


class TestDriftDetector(unittest.TestCase):

    @patch('boto3.client')
    @patch('boto3.resource')
    def test_no_predictions_returns_200(self, mock_resource, mock_client):
        mock_table = MagicMock()
        mock_table.scan.return_value = {'Items': []}
        mock_resource.return_value.Table.return_value = mock_table

        from src.drift_detector.handler import handler

        response = handler({}, {})
        self.assertEqual(response['statusCode'], 200)

    @patch('boto3.client')
    @patch('boto3.resource')
    def test_low_confidence_triggers_alert(self, mock_resource, mock_client):
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            'Items': [
                {'model_id': 'spam-detector', 'confidence': '0.60', 'timestamp': '2026-01-01T00:00:00'},
                {'model_id': 'spam-detector', 'confidence': '0.65', 'timestamp': '2026-01-01T00:01:00'},
            ]
        }
        mock_resource.return_value.Table.return_value = mock_table
        mock_sns = MagicMock()
        mock_cw = MagicMock()
        mock_client.side_effect = lambda service: mock_sns if service == 'sns' else mock_cw

        from src.drift_detector import handler as drift_module
        drift_module.sns = mock_sns
        drift_module.cloudwatch = mock_cw

        response = drift_module.handler({}, {})
        body = json.loads(response['body'])
        self.assertTrue(len(body['alerts_fired']) > 0)


if __name__ == '__main__':
    unittest.main()
