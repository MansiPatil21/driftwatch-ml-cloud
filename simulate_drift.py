"""
Drift Simulation Script — ML Model Monitoring Pipeline
Sends realistic predictions that gradually drift over time.
Watch your CloudWatch dashboard as confidence degrades live.
"""

import requests
import time
import random
import argparse
from datetime import datetime

API_URL = "https://pxwyjr8f53.execute-api.us-east-1.amazonaws.com/prod/predictions"

SCENARIOS = {
    "healthy": {
        "description": "Healthy model — high confidence, stable predictions",
        "confidence_range": (0.85, 0.98),
        "spam_ratio": 0.30,
        "count": 20
    },
    "gradual_drift": {
        "description": "Gradual drift — confidence slowly declining over time",
        "phases": [
            {"confidence_range": (0.85, 0.95), "label": "stable",       "count": 10},
            {"confidence_range": (0.75, 0.85), "label": "early drift",  "count": 10},
            {"confidence_range": (0.60, 0.75), "label": "mid drift",    "count": 10},
            {"confidence_range": (0.45, 0.60), "label": "severe drift", "count": 10},
        ],
        "spam_ratio": 0.30
    },
    "sudden_drift": {
        "description": "Sudden drift — model confidence collapses abruptly",
        "phases": [
            {"confidence_range": (0.88, 0.97), "label": "stable",   "count": 15},
            {"confidence_range": (0.40, 0.58), "label": "collapse",  "count": 15},
        ],
        "spam_ratio": 0.30
    },
    "recovery": {
        "description": "Drift then recovery — simulates model being retrained",
        "phases": [
            {"confidence_range": (0.88, 0.96), "label": "healthy",   "count": 10},
            {"confidence_range": (0.48, 0.65), "label": "drifting",  "count": 10},
            {"confidence_range": (0.87, 0.95), "label": "recovered", "count": 10},
        ],
        "spam_ratio": 0.30
    }
}


def send_prediction(model_id, confidence, prediction, api_key=None):
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key

    payload = {
        "model_id": model_id,
        "prediction": prediction,
        "confidence": round(confidence, 3)
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"  Error: {e}")
        return False


def run_scenario(scenario_name, model_id="spam-detector-v1", delay=0.3, api_key=None):
    if scenario_name not in SCENARIOS:
        print(f"Unknown scenario. Choose from: {list(SCENARIOS.keys())}")
        return

    scenario = SCENARIOS[scenario_name]
    print(f"\n{'='*60}")
    print(f"Scenario: {scenario['description']}")
    print(f"Model:    {model_id}")
    print(f"Time:     {datetime.utcnow().strftime('%H:%M:%S UTC')}")
    print(f"{'='*60}\n")

    spam_ratio = scenario.get("spam_ratio", 0.30)

    if scenario_name == "healthy":
        low, high = scenario["confidence_range"]
        for i in range(scenario["count"]):
            confidence = random.uniform(low, high)
            prediction = "spam" if random.random() < spam_ratio else "not_spam"
            success = send_prediction(model_id, confidence, prediction, api_key)
            status = "✓" if success else "✗"
            print(f"  {status} [{i+1:02d}] confidence={confidence:.3f}  label={prediction}")
            time.sleep(delay)

    else:
        for phase in scenario["phases"]:
            low, high = phase["confidence_range"]
            label = phase["label"]
            count = phase["count"]

            print(f"  Phase: {label.upper()} (confidence {low:.2f}–{high:.2f})")
            for i in range(count):
                confidence = random.uniform(low, high)
                prediction = "spam" if random.random() < spam_ratio else "not_spam"
                success = send_prediction(model_id, confidence, prediction, api_key)
                status = "✓" if success else "✗"
                print(f"    {status} [{i+1:02d}] confidence={confidence:.3f}  label={prediction}")
                time.sleep(delay)
            print()

    print(f"\nDone. Open your CloudWatch dashboard to see the metrics update.")
    print(f"Dashboard: https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=MLMonitoringDashboard\n")


def run_multi_model(delay=0.3):
    """Simulate multiple models drifting at different rates."""
    models = [
        ("spam-detector-v1",   (0.88, 0.96), "stable"),
        ("fraud-detector-v2",  (0.55, 0.70), "drifting"),
        ("recommender-v3",     (0.72, 0.83), "borderline"),
    ]

    print(f"\n{'='*60}")
    print("Multi-Model Simulation — 3 models, different health states")
    print(f"{'='*60}\n")

    for _ in range(15):
        for model_id, conf_range, state in models:
            confidence = random.uniform(*conf_range)
            prediction = random.choice(["spam", "not_spam"]) if "spam" in model_id else random.choice(["fraud", "legit"])
            success = send_prediction(model_id, confidence, prediction)
            status = "✓" if success else "✗"
            print(f"  {status} {model_id:25s}  confidence={confidence:.3f}  [{state}]")
        print()
        time.sleep(delay * 3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ML Drift Simulation Script")
    parser.add_argument("--scenario", default="gradual_drift",
                        choices=list(SCENARIOS.keys()) + ["multi_model"],
                        help="Simulation scenario to run")
    parser.add_argument("--model", default="spam-detector-v1", help="Model ID to simulate")
    parser.add_argument("--delay", type=float, default=0.3, help="Seconds between predictions")
    parser.add_argument("--api-key", default=None, help="API Gateway API key (if auth enabled)")
    args = parser.parse_args()

    if args.scenario == "multi_model":
        run_multi_model(delay=args.delay)
    else:
        run_scenario(args.scenario, model_id=args.model, delay=args.delay, api_key=args.api_key)
