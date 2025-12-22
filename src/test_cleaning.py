from data_loader import ShelterDataLoader
from cleaner import ShelterDataCleaner

import pandas as pd

pd.set_option("display.max_columns", None)

def main():
    # Raw data
    loader = ShelterDataLoader()
    raw_df = loader.load()

    print("\n================= RAW DATA ======================")
    print(raw_df.head(3))
    print(raw_df.dtypes)

    # Clean data
    cleaner = ShelterDataCleaner(raw_df)
    clean_df = cleaner.finalize()

    print("\n====================== CLEANED DATA ======================")
    print(clean_df.head(6))
    print(clean_df.dtypes)

    print("\n====================== ADDITIONAL CHECKS ======================")
    print("Original columns:", list(raw_df.columns)[:5])
    print("Cleaned columns:", list(clean_df.columns)[:5])

    print("\nMissing DOB count:", clean_df["dob"].isna().sum())
    print("Age group value counts:")
    print(clean_df["age_group"].value_counts(dropna=False))


if __name__ == "__main__":
    main()
