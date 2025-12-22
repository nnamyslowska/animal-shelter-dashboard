import pandas as pd
import numpy as np


class ShelterDataCleaner:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()    

    # Changing column names to snake_case
    def clean_column_names(self) -> None:
        self.df.columns = (
            self.df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

    # date columns to datetime
    def parse_dates(self) -> None:
        date_cols = ["dob", "intake_date", "outcome_date"]

        for col in date_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(self.df[col], errors="coerce") # coerce invalid dates to NaT (Not a Time)

    # filling missing values
    def fill_missing_values(self) -> None:
        fill_cols = [
            "animal_name",
            "secondary_color",
            "reason_for_intake",
            "intake_subtype",
            "outcome_subtype",
            "jurisdiction",
            "crossing",
        ]

        for col in fill_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna("Unknown")


    # normalizing text columns
    def normalize_text_columns(self) -> None:
        text_cols = [
            "animal_type",
            "sex",
            "intake_condition",
            "intake_type",
            "intake_subtype",
            "reason_for_intake",
            "outcome_type",
            "outcome_subtype",
            "jurisdiction",
        ]

        for col in text_cols:
            if col in self.df.columns:
                s = self.df[col].astype("string")  # keeps missing as NA
                s = (
                    s.str.strip()
                        .str.replace(r"\s+", " ", regex=True)
                        .str.title()
                )
                self.df[col] = s

        # Fixing typos
        if "intake_condition" in self.df.columns:
            self.df["intake_condition"] = self.df["intake_condition"].replace({"Ill Moderatete": "Ill Moderate"})

    # convert intake_is_dead to boolean, if alive on intake then False, if dead on intake then True
    def fix_intake_is_dead(self) -> None:
        if "intake_is_dead" in self.df.columns:
            self.df["intake_is_dead"] = (
                self.df["intake_is_dead"]
                .astype("string")
                .map({"Alive on Intake": False, "Dead on Intake": True})
                .astype("boolean")
            )


    # convert was_outcome_alive to boolean
    def fix_was_outcome_alive(self) -> None:
        if "was_outcome_alive" in self.df.columns:
            self.df["was_outcome_alive"] = (
                self.df["was_outcome_alive"]
                .astype("Int64")  # allows missing if ever present
                .fillna(0)
                .astype(int)
                .astype(bool)
            )

    # creating age features
    def create_age_features(self) -> None:
        if "dob" not in self.df.columns or "intake_date" not in self.df.columns:
            self.df["age_at_intake_years"] = np.nan
            self.df["age_group"] = "Unknown"
            return

        # Age in years
        self.df["age_at_intake_years"] = (
            (self.df["intake_date"] - self.df["dob"])
            .dt.days / 365.25
        )

        def age_group(age):
            if pd.isna(age):
                return "Unknown"
            elif age < 1:
                return "Baby"
            elif age < 3:
                return "Young"
            elif age < 8:
                return "Adult"
            else:
                return "Senior"

        self.df["age_group"] = self.df["age_at_intake_years"].apply(age_group)
        self.df["age_group"] = self.df["age_group"].astype("string")

    # splitting sex into base and sterilization status
    def create_sex_features(self) -> None:
        if "sex" not in self.df.columns:
            self.df["sex_base"] = "Unknown"
            self.df["is_sterilized"] = pd.Series(pd.NA, index=self.df.index, dtype="boolean")
            return

        sex = self.df["sex"].astype("string")

        self.df["sex_base"] = sex.replace({
            "Neutered": "Male",
            "Spayed": "Female",
        }).where(
            sex.isin(["Male", "Female", "Unknown", "Neutered", "Spayed"]),
            other="Unknown"
        )

        is_ster = pd.Series(pd.NA, index=self.df.index, dtype="boolean")
        is_ster = is_ster.mask(sex.isin(["Neutered", "Spayed"]), True)
        is_ster = is_ster.mask(sex.isin(["Male", "Female"]), False) # we assume unsterilized if not specified

        self.df["is_sterilized"] = is_ster


    # outcome grouping: No_Outcome_Yet, Positive, Negative, Other_or_Partner, Admin_or_Unknown
    def create_outcome_group(self) -> None:
        if "outcome_is_current" in self.df.columns:
            current_mask = self.df["outcome_is_current"] == True
        else:
            current_mask = pd.Series(False, index=self.df.index)

        outcome_type = (
            self.df["outcome_type"]
            if "outcome_type" in self.df.columns
            else pd.Series(pd.NA, index=self.df.index, dtype="string")
        )

        positive = {
            "Adoption", "Return To Owner", "Community Cat",
            "Return To Wild Habitat", "Homefirst", "Foster To Adopt"
        }
        negative = {"Euthanasia", "Died", "Disposal"}
        partner = {"Transfer", "Rescue", "Transport", "Shelter, Neuter, Return"}
        admin = {"Missing", "Duplicate"}

        group = pd.Series("Admin_or_Unknown", index=self.df.index, dtype="string")

        group = group.mask(current_mask | outcome_type.isna(), "No_Outcome_Yet")
        group = group.mask(outcome_type.isin(positive), "Positive")
        group = group.mask(outcome_type.isin(negative), "Negative")
        group = group.mask(outcome_type.isin(partner), "Other_or_Partner") # 
        group = group.mask(outcome_type.isin(admin), "Admin_or_Unknown") # whether missing or duplicate

        self.df["outcome_group"] = group


    # Validation
    def validate_fields(self) -> None:
        # Age at intake cannot be negative or unrealistically high
        if "age_at_intake_years" in self.df.columns:
            invalid_age = (self.df["age_at_intake_years"] < 0) | (self.df["age_at_intake_years"] > 40)
            self.df.loc[invalid_age, "age_at_intake_years"] = np.nan
            self.df.loc[invalid_age, "age_group"] = "Unknown"

        # Intake duration cannot be negative
        if "intake_duration" in self.df.columns:
            invalid_duration = self.df["intake_duration"] < 0
            self.df.loc[invalid_duration, "intake_duration"] = np.nan

    # Finalizing the cleaning process and returning cleaned DataFrame
    def finalize(self) -> pd.DataFrame:
        """Run all cleaning steps in order and return cleaned DataFrame."""
        self.clean_column_names()
        self.parse_dates()
        self.fill_missing_values()
        self.normalize_text_columns()

        self.fix_intake_is_dead()
        self.fix_was_outcome_alive()

        self.create_age_features()
        self.create_sex_features()
        self.create_outcome_group()

        self.validate_fields()

        return self.df


