import sys
import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from config import RAW_DATA_FILE

# inspect the raw data
def main() -> None:
    df = pd.read_csv(RAW_DATA_FILE)

    print("================= INSPECTING DATA ======================")

    print("First 5 rows of the dataset:")
    print(df.head())

    print("\nDataset info:")
    print(df.info())

    print("\nColumn names:")
    print(list(df.columns))

    print("\nData types:")
    print(df.dtypes)

    print("\n================= MISSING VALUES ======================")

    missing_counts = df.isna().sum()
    missing_percentage = (missing_counts / len(df) * 100).round(2)

    missing_report = (
        pd.DataFrame({"missing_count": missing_counts, "missing_percentage": missing_percentage})
        .sort_values("missing_percentage", ascending=False)
    )

    print(missing_report.head(25))
    print("\nColumns with missing values:\n")
    print(missing_report[missing_report["missing_count"] > 0])

    print(f"\nDuplicate rows: {df.duplicated().sum():,}")

    # Columns important for analysis
    key_cols = [
        "Animal Type",
        "Sex",
        "Intake Condition",
        "Intake Type",
        "Reason for Intake",
        "Outcome Type",
        "Outcome Subtype",
        "intake_is_dead",
        "outcome_is_current",
        "was_outcome_alive",
    ]

    for col in key_cols:
        if col in df.columns:
            print(f"\n--- {col} ---")
            print(df[col].value_counts(dropna=False).head(15))

if __name__ == "__main__":
    main()