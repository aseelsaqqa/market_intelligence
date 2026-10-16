
import os
import pandas as pd


def create_excel_report(
    review_summary_path,
    rating_distribution_path,
    sentiment_summary_path,
    output_path="data/competitor_intelligence_report.xlsx",
):
    """Create a multi-sheet Excel report from analysis CSV files."""

    files = {
        "Review Summary": review_summary_path,
        "Rating Distribution": rating_distribution_path,
        "Sentiment Summary": sentiment_summary_path,
    }

    for sheet_name, file_path in files.items():
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Required analysis file not found: {file_path}"
            )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, file_path in files.items():
            df = pd.read_csv(file_path)
            df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )

    return output_path
