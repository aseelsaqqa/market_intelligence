
import os
import pandas as pd
import torch
from transformers import pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(
    BASE_DIR, "data", "competitor_reviews_cleaned.csv"
)

MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

_sentiment_model = None


def load_sentiment_model():
    """Load the sentiment model once and reuse it."""
    global _sentiment_model

    if _sentiment_model is None:
        _sentiment_model = pipeline(
            task="text-classification",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
            device=-1
        )

    return _sentiment_model


def analyze_reviews(reviews):
    """Analyze a list of review texts and return sentiment results."""
    model = load_sentiment_model()

    results = model(
        [str(review) for review in reviews],
        truncation=True,
        max_length=512,
        batch_size=8
    )

    output = []

    for result in results:
        label = result["label"].lower()

        if "positive" in label or label == "label_2":
            sentiment = "Positive"
        elif "negative" in label or label == "label_0":
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        output.append({
            "sentiment": sentiment,
            "confidence": round(float(result["score"]), 3)
        })

    return output


def analyze_cleaned_reviews():
    """Analyze the cleaned review dataset."""
    df = pd.read_csv(DATA_FILE)

    df = df.dropna(subset=["review_clean"]).copy()
    df["review_clean"] = df["review_clean"].astype(str).str.strip()
    df = df[df["review_clean"] != ""]

    if df.empty:
        raise ValueError("No valid reviews found.")

    results = analyze_reviews(df["review_clean"].tolist())

    df["ai_sentiment"] = [item["sentiment"] for item in results]
    df["ai_confidence"] = [item["confidence"] for item in results]

    return df


if __name__ == "__main__":
    print("Testing AI sentiment analysis...", flush=True)

    df = pd.read_csv(DATA_FILE)
    df = df.dropna(subset=["review_clean"]).copy()
    df["review_clean"] = df["review_clean"].astype(str).str.strip()
    df = df[df["review_clean"] != ""]

    if df.empty:
        raise ValueError("No valid reviews found.")

    sample = df.head(5).copy()
    results = analyze_reviews(sample["review_clean"].tolist())

    for (_, row), result in zip(sample.iterrows(), results):
        print("\nApp:", row["app_id"])
        print("Rating:", row["rating"])
        print("Review:", row["review_clean"])
        print("AI sentiment:", result["sentiment"])
        print("Confidence:", result["confidence"])

    print("\nAI test completed successfully!")
