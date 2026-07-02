# ML Model Monitoring Pipeline

A serverless, event-driven pipeline on AWS that monitors ML model predictions in real time, detects confidence drift, and fires automated alerts when model performance degrades.

Built for CSCI 5411 Advanced Cloud Architecting — Summer 2026.

---

## Architecture Overview

```
ML Model → API Gateway → Lambda (Ingestor) → DynamoDB
                                                  ↓
                              EventBridge → Lambda (Drift Detector) → CloudWatch + SNS
                              EventBridge → Lambda (Anomaly Detector) → CloudWatch + SNS
                              EventBridge → Lambda (Report Generator) → S3
```

**AWS Services Used:**
- API Gateway — HTTP entry point for prediction ingestion
- Lambda — four serverless functions (ingestor, drift detector, anomaly detector, report generator)
- DynamoDB — stores every prediction with model ID, confidence score, and timestamp
- S3 — stores daily JSON summary reports
- SNS — sends email alerts when drift or anomalies are detected
- CloudWatch — dashboards and alarms for real-time metric visualization
- EventBridge — triggers scheduled Lambda functions automatically
- CloudFormation — Infrastructure as Code for the entire stack
- IAM — least-privilege role for Lambda execution

---

## Prerequisites

- AWS CLI configured with valid credentials
- Python 3.11+
- Git

---

## Deployment

### One-command deploy

```bash
aws cloudformation deploy \
  --template-file infrastructure/template.yaml \
  --stack-name ml-monitoring-pipeline \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides AlertEmail=your@email.com \
  --region us-east-1
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
