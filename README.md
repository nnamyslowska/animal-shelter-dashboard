# Animal Shelter Dashboard

**Student:** Natalia Namysłowska


## Project Description

This project analyses animal shelter intakes and outcomes using real data from the **Long Beach Animal Shelter**.
The aim is to explore patterns in how animals enter the shelter, what outcomes they experience, and how long they stay before leaving.

The analysis is presented as an interactive dashboard built with Streamlit.
The project combines data cleaning, exploratory data analysis, visualisation, and simple user action logging using SQLite.

The full project repository is available on GitHub:
👉 **[https://github.com/nnamyslowska/animal-shelter-dashboard](https://github.com/nnamyslowska/animal-shelter-dashboard)**


## Research Questions

The analysis focuses on the following research questions:

1. **What are the most common intake and outcome types?**
2. **Are some animals more likely to have positive outcomes than others?**
3. **How long do animals typically stay in the shelter?**

Each research question is explored in a separate tab of the dashboard using multiple visualisations.


## Dataset

**Source:** Long Beach Open Data Portal
**Dataset name:** *Animal Shelter Intakes and Outcomes*

**Original dataset link:**
[https://longbeach.opendatasoft.com/explore/dataset/animal-shelter-intakes-and-outcomes/information/](https://longbeach.opendatasoft.com/explore/dataset/animal-shelter-intakes-and-outcomes/information/)

The dataset contains records of animals taken into the shelter, including:

* animal type,
* sex,
* age at intake,
* intake type and reason,
* outcome type,
* intake and outcome dates.

The dataset was downloaded as a CSV file and kept in its original structure.


## Data Preparation

Before analysis, the dataset was cleaned and prepared using a custom data cleaning pipeline implemented in `cleaner.py`. The following steps were performed:

* **Column names were standardized**
  All column names were converted to lowercase, trimmed, and changed to snake_case for consistency.

* **Date columns were parsed**
  Date fields (`dob`, `intake_date`, `outcome_date`) were converted to datetime format. Invalid or incorrect dates were set to missing values.

* **Missing values were handled consistently**
  Selected text fields (such as animal name, secondary color, reason for intake, intake subtype, outcome subtype, jurisdiction, and crossing) were filled with `"Unknown"` where data was missing.

* **Text values were normalized**
  Text columns were cleaned by trimming spaces, fixing multiple spaces, and standardizing capitalization. Known typos were corrected.

* **Boolean fields were standardized**
  Intake and outcome status fields indicating whether an animal was dead or alive were converted into proper boolean values.

* **Age features were created**
  Age at intake was calculated in years based on date of birth and intake date.
  Animals were grouped into age categories:

  * Baby (under 1 year)
  * Young (1–3 years)
  * Adult (3–8 years)
  * Senior (over 8 years)
  * Unknown (missing or invalid age)

* **Sex information was simplified**
  The original sex field was split into:

  * `sex_base` (Male, Female, or Unknown)
  * `is_sterilized` (True, False, or missing if unknown)

* **Outcome groups were created**
  Outcome types were grouped into broader categories:

  * Positive (e.g. Adoption, Return To Owner)
  * Negative (e.g. Euthanasia, Died)
  * Other or Partner (e.g. Transfer, Rescue)
  * Admin or Unknown (e.g. Missing, Duplicate)
  * No Outcome Yet (animals still in the shelter)

* **Invalid values were removed or corrected**
  Unrealistic ages (negative or over 40 years) and negative stay durations were set to missing values to avoid incorrect analysis.

These steps ensure that the data is consistent and suitable for analysis.


## Technologies Used

* **Python**
* **Pandas** – data manipulation
* **Matplotlib** – visualisations
* **Streamlit** – interactive dashboard
* **SQLite** – user action logging


## How to Run the Project

1. Download the dataset from the link above.
2. Place the CSV file in the `data/` folder.
3. Install all required packages listed in `requirements.txt`.
4. From the main project directory, run:

```bash
streamlit run app/app.py
```

The dashboard will open in your web browser.


## Project Structure

The project is organised into clearly separated folders:

```
animal-shelter-dashboard/
│
├── app/
│   └── app.py
│
├── src/
│   ├── data_loader.py
│   ├── cleaner.py
│   ├── plots.py
│   ├── auth_db.py
│   └── config.py
│
├── data/
│   ├── animal-shelter-intakes-and-outcomes.csv
│   └── app.db
│
├── notebooks/
│   ├── inspect_data.py
│   └── test_cleaning.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

### Folder description

* **`app/`**
  Contains the main Streamlit application (`app.py`).
  This file defines the dashboard layout, tabs, filters, and connects all visualisations.

* **`src/`**
  Contains the core project logic, including:

  * data loading,
  * data cleaning and feature creation,
  * plotting functions,
  * authentication and logging logic.

* **`data/`**
  Stores the dataset used in the project and the SQLite database file used for logging user actions.

* **`notebooks/`**
  Contains helper scripts used during the development process, such as:

  * initial data inspection,
  * testing and validating data cleaning steps.
    These files document the analysis process but are not part of the final dashboard.

* **`requirements.txt`**
  Lists all Python dependencies required to run the project.


## Notes and Limitations

* Some intake reasons are missing or recorded as “Unknown”, which limits detailed analysis of intake causes.
* The dataset is observational, so results describe patterns but do not imply causation.
* Some animal categories have small sample sizes and should be interpreted with caution.