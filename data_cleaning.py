
import os
import re
import html
import unicodedata
import pandas as pd


DATA_DIR = "data"
INPUT_FILE = os.path.join(DATA_DIR, "competitor_reviews.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "competitor_reviews_cleaned.csv")


def clean_review_text(value):
    """Clean review text while preserving its original meaning."""

    if pd.isna(value):
        return ""

    text = str(value)

    # Normalize Unicode characters
    text = unicodedata.normalize("NFKC", text)

    # Decode HTML entities, if present
    text = html.unescape(text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove invisible control characters
    text = "".join(
        char for char in text
        if unicodedata.category(char) != "Cc" or char in "\n\t"
    )

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_reviews():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Reviews file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    required_columns = {"app_id", "rating", "review"}

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    original_count = len(df)

    # Preserve the original review text
    df["review_original"] = df["review"]

    # Clean review text
    df["review_clean"] = df["review"].apply(clean_review_text)

    # Convert ratings to numeric values
    df["rating"] = pd.to_numeric(
        df["rating"], errors="coerce"
    )

    # Remove records missing essential information
    df = df.dropna(subset=["app_id", "rating"])

    # Keep only valid ratings from 1 to 5
    df = df[df["rating"].between(1, 5)]

    # Remove empty reviews
    df = df[df["review_clean"].str.len() > 0].copy()

    # Remove exact duplicate records while keeping distinct reviews
    duplicate_columns = [
        col for col in ["app_id", "rating", "review_clean", "date"]
        if col in df.columns
    ]

    before_deduplication = len(df)

    df = df.drop_duplicates(
        subset=duplicate_columns,
        keep="first"
    ).copy()

    duplicates_removed = before_deduplication - len(df)

    # Save cleaned data separately
    os.makedirs(DATA_DIR, exist_ok=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n=== Review Data Cleaning Report ===")
    print(f"Original rows: {original_count}")
    print(f"Cleaned rows: {len(df)}")
    print(f"Rows removed: {original_count - len(df)}")
    print(f"Duplicate rows removed: {duplicates_removed}")
    print(f"Unique apps: {df['app_id'].nunique()}")
    print(f"Empty cleaned reviews: {(df['review_clean'] == '').sum()}")
    print(f"Saved cleaned data to: {OUTPUT_FILE}")

    print("\n=== Sample Cleaned Reviews ===")

    for _, row in df.head(5).iterrows():
        print(f"\nApp ID: {row['app_id']}")
        print(f"Rating: {row['rating']}")
        print(f"Original: {row['review_original']}")
        print(f"Cleaned:  {row['review_clean']}")


def verify_cleaned_data():
    df = pd.read_csv(OUTPUT_FILE)

    print("\n=== Cleaned Data Verification ===")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("\nMissing values:")
    print(df[["app_id", "rating", "review_clean"]].isna().sum())

    print("\nRatings distribution:")
    print(df["rating"].value_counts().sort_index())

    print("\nReviews per app:")
    print(df.groupby("app_id").size())


if __name__ == "__main__":
    clean_reviews()
    verify_cleaned_data()