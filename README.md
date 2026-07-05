# ML Model Monitoring Pipeline

A serverless, event-driven pipeline on AWS that monitors ML model predictions in real time, detects confidence drift, and fires automated alerts when model performance degrades.

Built for CSCI 5411 Advanced Cloud Architecting — Summer 2026.

---

## Architecture Overview

```
ML Model → API Gateway (x-api-key) → Lambda (Ingestor) → DynamoDB (ml-predictions)
                                                  ↓
                                        Kinesis Data Stream → Lambda (Kinesis Processor) → DynamoDB

ML Engineer → API Gateway → Lambda (Ground Truth)   → DynamoDB (ml-ground-truth)
ML Engineer → API Gateway → Lambda (Model Config)   → DynamoDB (ml-model-config)

EventBridge (5 min)  → Lambda (Drift Detector)      → CloudWatch + SNS → Step Functions (Drift Responder)
EventBridge (15 min) → Lambda (Anomaly Detector)    → CloudWatch + SNS
EventBridge (15 min) → Lambda (Accuracy Publisher)  → CloudWatch
EventBridge (daily)  → Lambda (Report Generator)    → S3
```

**AWS Services Used:**
- API Gateway — HTTP entry point for prediction ingestion, ground truth, and model config
- Lambda — nine serverless functions (ingestor, ground truth, model config, drift detector, anomaly detector, accuracy publisher, kinesis processor, report generator, drift responder)
- DynamoDB — stores every prediction, ground-truth label, and per-model threshold config
- Kinesis Data Streams — decouples the synchronous ingest path from async batch processing
- Step Functions — orchestrates the automated drift-response workflow
- S3 — stores daily JSON summary reports
- SNS — sends email alerts when drift or anomalies are detected
- CloudWatch — dashboards and alarms for real-time metric visualization
- EventBridge — triggers scheduled Lambda functions automatically
- CloudFormation — Infrastructure as Code for the entire stack (deployed via the SAM CLI)
- IAM — least-privilege role for Lambda execution

---

## Prerequisites

- AWS CLI configured with valid credentials
- AWS SAM CLI (`pip install aws-sam-cli`)
- Python 3.11+
- Git
- Environment variables / parameters: `AlertEmail` (SNS alert recipient), `LabRoleArn` (IAM execution role)

---

## Deployment

### One-command deploy

```bash
sam build --template-file infrastructure/template.yaml
sam deploy --guided \
  --stack-name ml-monitoring-pipeline \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AlertEmail=your@email.com \
  --region us-east-1
```

### Launch the dashboard

```bash
streamlit run dashboard.py
```

### Get your API endpoint

```bash
aws cloudformation describe-stacks \
  --stack-name ml-monitoring-pipeline \
  --query 'Stacks[0].Outputs' \
  --output table
```

---

## Testing

### Send a prediction

```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/predictions \
  -H "Content-Type: application/json" \
  -d '{"model_id": "spam-detector-v1", "prediction": "spam", "confidence": 0.92}'
```

### Simulate drift (low confidence)

```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/predictions \
  -H "Content-Type: application/json" \
  -d '{"model_id": "spam-detector-v1", "prediction": "spam", "confidence": 0.61}'
```

### Submit a ground-truth label

```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/ground-truth \
  -H "Content-Type: application/json" \
  -d '{"prediction_id": "<id from the predictions response>", "model_id": "spam-detector-v1", "actual_label": "spam"}'
```

### Read or update a per-model threshold config

```bash
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/models/spam-detector-v1/config

curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/models/spam-detector-v1/config \
  -H "Content-Type: application/json" \
  -d '{"confidence_threshold": 0.75, "psi_threshold": 0.2}'
```

### Run unit tests

```bash
python -m pytest tests/ -v
```

---

## CI/CD

Every push to `main` automatically deploys via GitHub Actions.

Add these secrets to your GitHub repository (Settings → Secrets → Actions):
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`

---

## Cleanup

```bash
aws cloudformation delete-stack --stack-name ml-monitoring-pipeline
```
