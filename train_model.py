"""
Train a spam classifier on the SMS Spam Collection dataset.
Saves the model to models/spam_classifier.pkl
Run once: python3 train_model.py
"""

import pickle
import os
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

DATASET_URL = "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv"
MODEL_PATH  = "models/spam_classifier.pkl"


def download_dataset():
    print("Downloading SMS Spam Collection dataset...")
    import requests
    resp = requests.get(DATASET_URL, verify=False, timeout=15)
    rows = []
    for line in resp.text.strip().split("\n"):
        parts = line.split("\t", 1)
        if len(parts) == 2:
            rows.append((parts[0].strip(), parts[1].strip()))
    labels   = [r[0] for r in rows]
    messages = [r[1] for r in rows]
    print(f"  Loaded {len(messages)} messages ({labels.count('spam')} spam, {labels.count('ham')} ham)")
    return messages, labels


def train():
    messages, labels = download_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        messages, labels, test_size=0.2, random_state=42, stratify=labels
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            strip_accents="unicode",
            analyzer="word",
            ngram_range=(1, 2),
            max_features=10_000,
            sublinear_tf=True,
        )),
        ("clf", MultinomialNB(alpha=0.1)),
    ])

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc   = accuracy_score(y_test, preds)
    print(f"\nTest accuracy: {acc:.1%}")
    print(classification_report(y_test, preds))

    os.makedirs("models", exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"Model saved to {MODEL_PATH}")
    return model


if __name__ == "__main__":
    train()
