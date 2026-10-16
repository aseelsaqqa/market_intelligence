
import os
import pandas as pd
from ai import analyze_reviews
from database import update_review_sentiments

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

APPS_FILE = os.path.join(DATA_DIR, "competitor_apps.csv")
REVIEWS_FILE = os.path.join(DATA_DIR, "competitor_reviews.csv")
CLEANED_FILE = os.path.join(DATA_DIR, "competitor_reviews_cleaned.csv")


def load_data():
    """Load the latest collected competitor data."""
    apps_df = pd.read_csv(APPS_FILE)
    reviews_df = pd.read_csv(REVIEWS_FILE)

    return apps_df, reviews_df


def run_analysis():
    """Analyze ratings and AI sentiment for selected competitor apps."""
    apps_df, reviews_df = load_data()

    if apps_df.empty:
        raise ValueError("No competitor app data was collected.")

    if reviews_df.empty:
        raise ValueError("No competitor reviews were collected.")

    if not {"app_id", "title"}.issubset(apps_df.columns):
        raise ValueError("App data is missing app_id or title.")

    if not {"app_id", "rating", "review"}.issubset(reviews_df.columns):
        raise ValueError("Review data is missing app_id, rating, or review.")

    apps_df["app_id"] = apps_df["app_id"].astype(str)
    reviews_df["app_id"] = reviews_df["app_id"].astype(str)

    selected_ids = apps_df["app_id"].unique()
    reviews_df = reviews_df[
        reviews_df["app_id"].isin(selected_ids)
    ].copy()

    reviews_df["rating"] = pd.to_numeric(
        reviews_df["rating"], errors="coerce"
    )
    reviews_df = reviews_df[
        reviews_df["rating"].between(1, 5)
    ].copy()

    if reviews_df.empty:
        raise ValueError("No valid reviews are available for analysis.")

    # Average rating and review count
    review_summary = (
        reviews_df.groupby("app_id")
        .agg(
            average_rating=("rating", "mean"),
            review_count=("rating", "count")
        )
        .reset_index()
    )

    review_summary = review_summary.merge(
        apps_df[["app_id", "title"]].drop_duplicates("app_id"),
        on="app_id",
        how="left"
    )

    review_summary["average_rating"] = (
        review_summary["average_rating"].round(2)
    )

    # Rating distribution
    rating_distribution = (
        reviews_df.groupby(["app_id", "rating"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=[1, 2, 3, 4, 5], fill_value=0)
    )

    title_lookup = (
        apps_df.drop_duplicates("app_id")
        .set_index("app_id")["title"]
    )

    rating_distribution.index = rating_distribution.index.map(
        title_lookup
    )
    rating_distribution.index.name = "title"

    # Clean reviews for AI sentiment analysis
    if os.path.exists(CLEANED_FILE):
        cleaned_df = pd.read_csv(CLEANED_FILE)
    else:
        cleaned_df = reviews_df.copy()
        cleaned_df["review_clean"] = (
            cleaned_df["review"].fillna("").astype(str).str.strip()
        )

    required_clean_columns = {"app_id", "review_clean"}
    if not required_clean_columns.issubset(cleaned_df.columns):
        raise ValueError(
            "Cleaned review data must contain app_id and review_clean."
        )

    cleaned_df["app_id"] = cleaned_df["app_id"].astype(str)
    cleaned_df["review_clean"] = (
        cleaned_df["review_clean"].fillna("").astype(str).str.strip()
    )

    print("CLEANED DATA COLUMNS:", cleaned_df.columns.tolist())
    cleaned_df = cleaned_df[
        cleaned_df["app_id"].isin(selected_ids)
        & (cleaned_df["review_clean"] != "")
    ].copy()

    if cleaned_df.empty:
        raise ValueError("No non-empty cleaned reviews are available.")

    # Run AI in batches to avoid sending all reviews at once
    batch_size = 32
    ai_results = []

    for start in range(0, len(cleaned_df), batch_size):
        batch = cleaned_df["review_clean"].iloc[
            start:start + batch_size
        ].tolist()
        ai_results.extend(analyze_reviews(batch))

    cleaned_df["ai_sentiment"] = [
        result["sentiment"] for result in ai_results
    ]
    cleaned_df["ai_confidence"] = [
        result["confidence"] for result in ai_results
    ]
    # Save sentiments to SQLite
    update_review_sentiments(cleaned_df.to_dict("records"))

    # Save detailed AI results
    cleaned_df.to_csv(
        os.path.join(DATA_DIR, "competitor_reviews_ai.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    # AI sentiment summary by app
    sentiment_summary = (
        cleaned_df.groupby(["app_id", "ai_sentiment"])
        .size()
        .unstack(fill_value=0)
        .reindex(
            columns=["Positive", "Neutral", "Negative"],
            fill_value=0
        )
    )

    sentiment_summary["Total"] = sentiment_summary.sum(axis=1)

    for sentiment in ["Positive", "Neutral", "Negative"]:
        sentiment_summary[f"{sentiment} %"] = (
            sentiment_summary[sentiment]
            / sentiment_summary["Total"] * 100
        ).round(1)

    sentiment_summary = sentiment_summary.reset_index()

    sentiment_summary["title"] = sentiment_summary["app_id"].map(
        title_lookup
    )

    sentiment_summary = sentiment_summary.dropna(subset=["title"])
    sentiment_summary = sentiment_summary.set_index("title")
    sentiment_summary.index.name = "title"

    # Save results used by the dashboard
    review_summary.to_csv(
        os.path.join(DATA_DIR, "review_summary.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    rating_distribution.to_csv(
        os.path.join(DATA_DIR, "rating_distribution.csv"),
        encoding="utf-8-sig"
    )

    sentiment_summary.to_csv(
        os.path.join(DATA_DIR, "sentiment_summary.csv"),
        encoding="utf-8-sig"
    )

    print("Analysis results saved successfully.")
    print("\nReview summary:")
    print(review_summary[
        ["title", "average_rating", "review_count"]
    ].to_string(index=False))

    print("\nAI sentiment summary:")
    print(sentiment_summary)

    return review_summary, rating_distribution, sentiment_summary


if __name__ == "__main__":
    run_analysis()
