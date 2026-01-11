import sys
from pathlib import Path
import sqlite3

import streamlit as st
import pandas as pd
from config import PROJECT_ROOT

sys.path.append(str(PROJECT_ROOT / "src"))

from data_loader import ShelterDataLoader
from cleaner import ShelterDataCleaner
from auth_db import init_db, add_user, create_user, check_login, log_action
from plots import plot_bar_counts, plot_hist , plot_line, plot_box, plot_scatter, plot_stacked_bar, plot_violin_by_group
st.set_page_config(page_title="Animal Shelter Dashboard", layout="wide")

@st.cache_data
def load_and_clean_data() -> pd.DataFrame:
    """
    Load raw CSV -> clean -> return cleaned dataframe.
    Cached to avoid re-cleaning on every widget interaction.
    """
    loader = ShelterDataLoader(PROJECT_ROOT / "data" / "animal-shelter-intakes-and-outcomes.csv")
    raw = loader.load()
    cleaner = ShelterDataCleaner(raw)
    return cleaner.finalize()


def login_screen() -> None:
    st.title("Animal Shelter Dashboard")

    left, center, right = st.columns([1, 2, 1])
    with center:
        tab_login, tab_register = st.tabs(["Login", "Register"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                submitted = st.form_submit_button("Login")

            if submitted:
                if check_login(username, password):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    log_action(username, "login_success", "User logged in")
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    log_action(username or "Unknown", "login_failed", "Invalid credentials")
                    st.error("Invalid username or password.")

        with tab_register:
            with st.form("register_form"):
                new_user = st.text_input("New username", key="reg_user")
                new_pass = st.text_input("New password", type="password", key="reg_pass")
                new_pass2 = st.text_input("Repeat password", type="password", key="reg_pass2")
                created = st.form_submit_button("Create account")

            if created:
                if not new_user or not new_pass:
                    st.error("Username and password cannot be empty.")
                elif new_pass != new_pass2:
                    st.error("Passwords do not match.")
                else:
                    ok = create_user(new_user, new_pass)
                    if ok:
                        log_action(new_user, "register_success", "User account created")
                        st.success("Account created. You can now log in.")
                    else:
                        st.error("That username already exists.")

def logs_tab(username: str) -> None:
    st.subheader("Logs (SQLite)")

    conn = sqlite3.connect(PROJECT_ROOT / "data" / "app.db")
    df_logs = pd.read_sql_query(
        "SELECT ts, username, action, details FROM logs ORDER BY id DESC LIMIT 50;",
        conn
    )
    conn.close()

    st.dataframe(df_logs, use_container_width=True)


# Main application
def main() -> None:
    # init SQLite tables (users + logs)
    init_db()

    # session state defaults
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""

    # login gate
    if not st.session_state["logged_in"]:
        login_screen()
        return

    username = st.session_state["username"]

    # sidebar actions
    with st.sidebar:
        st.write(f"Logged in as: **{username}**")
        if st.button("Logout"):
            log_action(username, "logout", "User logged out")
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.rerun()

    # load data
    df = load_and_clean_data()

    st.title("Animal Shelter Dashboard")

    # filters in sidebar
    animal_types = sorted(df["animal_type"].dropna().unique().tolist()) if "animal_type" in df.columns else []
    outcome_groups = sorted(df["outcome_group"].dropna().unique().tolist()) if "outcome_group" in df.columns else []

    with st.sidebar:
        st.subheader("Filters")
        animal_type = st.selectbox("Animal type", ["All"] + animal_types)
        outcome_group = st.selectbox("Outcome group", ["All"] + outcome_groups)

    # log filter changes 
    log_action(username, "filters", f"animal_type={animal_type}, outcome_group={outcome_group}")

    # apply filters
    filtered = df.copy()
    if animal_type != "All":
        filtered = filtered[filtered["animal_type"] == animal_type]
    if outcome_group != "All":
        filtered = filtered[filtered["outcome_group"] == outcome_group]

    tab_about, tab_rq1, tab_rq2, tab_rq3, tab_logs = st.tabs([
        "About the data",
        "RQ1: Intake & outcomes",
        "RQ2: Adoption likelihood",
        "RQ3: Length of stay",
        "Logs"
    ])

    with tab_about:
        st.header("About the dataset")

        st.write(
            """
            This project uses data from the Long Beach Animal Shelter.
            The dataset contains records of animals that were taken into the shelter
            and their outcomes after intake.

            The dataset is publicly available and can be accessed here:
            https://longbeach.opendatasoft.com/explore/dataset/animal-shelter-intakes-and-outcomes/information/
            """
        )

        st.subheader("What the dataset contains")

        st.write(
            """
            Each row represents one animal intake case.
            The dataset includes information such as:
            - animal type,
            - sex and sterilization status,
            - age at intake,
            - intake type and reason for intake,
            - outcome type (for example: adoption, transfer, euthanasia),
            - length of stay in the shelter.
            """
        )

        st.subheader("Data preparation")

        st.write(
            """
            Before analysis, the dataset was cleaned and prepared.
            The following steps were performed:
            - column names were standardized,
            - dates were converted to a consistent date format,
            - missing values were handled consistently,
            - new variables were created, such as age group and outcome group,
            - incorrect or unrealistic values were removed.
            """
        )

        st.subheader("Research questions")

        st.write(
            """
            The analysis focuses on the following research questions:
            """
        )

        st.markdown(
            """
            1. What are the most common intake and outcome types?
            2. Are some animals more likely to have positive outcomes than others?
            3. How long do animals typically stay in the shelter?
            """
        )

        st.subheader("Definitions used in the analysis")

        st.write(
            """
            Outcome groups are defined as follows:
            - Positive: Adoption, Return To Owner, Community Cat, Return To Wild Habitat, Homefirst, Foster To Adopt
            - Negative: Euthanasia, Died, Disposal
            - Other or Partner: Transfer, Rescue, Transport, Shelter, Neuter, Return
            - Admin or Unknown: Missing, Duplicate
            - No Outcome Yet: Animals that are still in the shelter
            """
        )

        st.write(
            """
            Age groups are defined based on age at intake:
            - Baby: under 1 year
            - Young: 1-3 years
            - Adult: 3-8 years
            - Senior: over 8 years
            - Unknown: age not recorded
            """
        )

# ------------------------------- RQ1 -----------------------------------------------
    with tab_rq1:
        st.header("RQ1: What are the most common intake and outcome types?")

        st.info(
            """
            - Stray animals are the most common intake type by a large margin.
            - Rescue and adoption are the most common outcomes, but euthanasia is also frequent.
            - Many intake records have an unknown intake reason, which limits detailed analysis.
            - Monthly intake counts show clear seasonal patterns over time.
            """
        )

        # Value counts for intake type, outcome type, reason for intake
        intake_counts = filtered["intake_type"].value_counts().head(10) if "intake_type" in filtered.columns else None
        outcome_counts = filtered["outcome_type"].value_counts().head(10) if "outcome_type" in filtered.columns else None
        reason_counts = filtered["reason_for_intake"].value_counts().head(10) if "reason_for_intake" in filtered.columns else None

        # Monthly intakes trend
        if "intake_date" in filtered.columns:
            monthly = (
                filtered.dropna(subset=["intake_date"])
                .assign(year_month=filtered["intake_date"].dt.to_period("M").astype(str))
                .groupby("year_month")
                .size()
                .reset_index(name="intakes")
                .sort_values("year_month")
            )
        else:
            monthly = None


        st.subheader("Animal types admitted to the shelter")

        col1b, col2b = st.columns([2, 1])

        with col1b:
            if "animal_type" not in filtered.columns:
                st.warning("Column animal_type not found.")
            else:
                animal_counts = (
                    filtered["animal_type"]
                    .fillna("Unknown")
                    .value_counts()
                )

                fig_animals = plot_bar_counts(
                    animal_counts,
                    title="Number of animals admitted by type",
                    xlabel="Animal type",
                    ylabel="Number of cases",
                    top_n=None,               # show all animal types
                    figsize=(6.5, 3.2),
                    cmap_name="viridis"
                )
                st.pyplot(fig_animals, use_container_width=True)

        with col2b:
            st.markdown("### What this chart shows")
            st.write(
                """
                This bar chart shows how many animals of each type were admitted to the shelter.
                Each bar represents the total number of intake cases for a given animal type.
                Dogs and cats make up the vast majority of admissions, while other animal types
                appear much less frequently.
                """
            )
        st.divider()

        col1, col2 = st.columns([2, 1])

        with col1:
            if intake_counts is None or intake_counts.empty:
                st.warning("Column intake_type not found or has no data.")
            else:
                fig1 = plot_bar_counts(
                    intake_counts,
                    title="Top intake types (Top 10)",
                    xlabel="Intake type",
                    top_n=None,             
                    figsize=(6.5, 3.2),
                    cmap_name="viridis"
                )
                st.pyplot(fig1, use_container_width=True)

        with col2:
            st.subheader("What this chart shows")
            st.write(
                """
                This bar chart shows which intake types happen most often.
                It helps us understand how animals enter the shelter.
                """
            )

        st.divider()

        col3, col4 = st.columns([2, 1])

        with col3:
            if outcome_counts is None or outcome_counts.empty:
                st.warning("Column outcome_type not found or has no data.")
            else:
                fig2 = plot_bar_counts(
                    outcome_counts,
                    title="Top outcome types (Top 10)",
                    xlabel="Outcome type",
                    top_n=None,
                    figsize=(6.5, 3.2),
                    cmap_name="viridis"
                )
                st.pyplot(fig2, use_container_width=True)

        with col4:
            st.subheader("What this chart shows")
            st.write(
                """
                This bar chart shows the most common outcomes after intake.
                Rescue and adoption are the most frequent outcomes.
                Euthanasia also appears as one of the more common outcome types.
                """
            )

        st.divider()

        col5, col6 = st.columns([2, 1])

        with col5:
            if reason_counts is None or reason_counts.empty:
                st.warning("Column reason_for_intake not found or has no data.")
            else:
                fig3 = plot_bar_counts(
                    reason_counts,
                    title="Top reasons for intake (Top 10)",
                    xlabel="Reason for intake",
                    top_n=None,
                    figsize=(6.5, 3.2),
                    cmap_name="viridis"
                )
                st.pyplot(fig3, use_container_width=True)

        with col6:
            st.subheader("What this chart shows")
            st.write(
                """
                This chart shows the most common recorded reasons for intake.
                A large share of records are labeled as Unknown as the vast majority of reason_for_intake values were missing.
                This means that detailed analysis of intake reasons is limited.
                """
            )

        st.divider()

        col7, col8 = st.columns([2, 1])

        with col7:
            if monthly is None or monthly.empty:
                st.warning("Column intake_date not found or has no data.")
            else:
                monthly_plot = monthly.copy()
                monthly_plot["year_month_dt"] = pd.to_datetime(monthly_plot["year_month"] + "-01")
                monthly_plot = monthly_plot[monthly_plot["year_month_dt"] >= pd.Timestamp("2017-01-01")]

                fig4 = plot_line(
                    df=monthly_plot,
                    x="year_month_dt",
                    y="intakes",
                    title="Monthly intakes trend",
                    xlabel="Month",
                    ylabel="Intakes",
                    date_format=True,
                    month_interval=6
                )
                st.pyplot(fig4, use_container_width=True)


        with col8:
            st.subheader("What this chart shows")
            st.write(
                """
                This line chart shows how monthly intake numbers change over time.
                Intake counts show clear repeating peaks and drops, which suggests seasonality.
                There is also a visible decrease in intakes around the period of the COVID-19 pandemic.
                These patterns may be influenced by changes in human behavior.
                """
            )

        st.divider()

        col_s1, col_s2 = st.columns([2, 1])

        with col_s1:
            # Sex distribution
            sex_counts = (
                filtered["sex_base"]
                .fillna("Unknown")
                .value_counts()
            )

            fig_sex = plot_bar_counts(
                sex_counts,
                title="Sex distribution of animals (Male / Female / Unknown)",
                xlabel="Sex (base)",
                ylabel="Number of cases",
                top_n=None,
                figsize=(6.5, 3.2),
                cmap_name="viridis"
            )
            st.pyplot(fig_sex, use_container_width=True)

        with col_s2:
            st.subheader("What this chart shows")
            st.write(
                """
                This chart shows the distribution of animals by sex.
                The original sex information was simplified into three categories: Male, Female, and Unknown.
                Slightly more male animals than female animals were admitted to the shelter.
                """
            )

        st.divider()

        col_col1, col_col2 = st.columns([2, 1])

        with col_col1:
            if "primary_color" not in filtered.columns:
                st.warning("Column primary_color not found.")
            else:
                color_counts = (
                    filtered["primary_color"]
                    .fillna("Unknown")
                    .value_counts()
                    .head(15)   # Top 15 most common colors
                )

                fig_colors = plot_bar_counts(
                    color_counts,
                    title="Most common primary colors (Top 15)",
                    xlabel="Primary color",
                    ylabel="Number of cases",
                    top_n=None,
                    figsize=(6.5, 3.2),
                    cmap_name="viridis"
                )
                st.pyplot(fig_colors, use_container_width=True)

        with col_col2:
            st.subheader("What this chart shows")
            st.write(
                """
                This chart shows the most common primary coat colors recorded for animals in the dataset.
                Black is the most frequently recorded primary color.
                This pattern is consistent with observations commonly reported by animal shelters.
                """
            )

        st.success(
            """
            RQ1 Conclusions

            \nThe shelter mainly receives stray animals, which is the dominant intake type.
            Rescue and adoption are the most common outcomes, indicating that many animals eventually leave the shelter through positive channels.
            However, euthanasia also represents a significant share of outcomes.

            \nIntake reasons are often missing or recorded as Unknown, which limits detailed analysis of why animals are brought to the shelter.
            Monthly intake patterns show clear seasonality, with repeating increases and decreases over time.
            A temporary decrease in intakes is visible during the COVID-19 period.

            \nSlightly more male animals than female animals are admitted.
            Black is the most common primary coat color among admitted animals, which aligns with common shelter population patterns.
            """
        )


# ------------------------------- RQ2 -----------------------------------------------
    with tab_rq2:
        st.header("RQ2: Are some animals more likely to have positive outcomes than others?")

        st.info(
            """
            This section explores whether some animals are more likely to have positive outcomes than others.
            In this project, a positive outcome is defined using the outcome_group variable.
            Positive outcomes are compared with other outcome groups.
            """
        )

        required_cols = {"outcome_group", "animal_type", "age_group"}
        missing = [c for c in required_cols if c not in filtered.columns]
        if missing:
            st.warning(f"Missing required column(s) for RQ2: {', '.join(missing)}")
        else:
            df_rq2 = filtered.copy()

            df_rq2["is_positive_outcome"] = df_rq2["outcome_group"] == "Positive"

            col1, col2 = st.columns([2, 1])

            with col1:
                adoption_by_type = (
                    df_rq2.dropna(subset=["animal_type", "is_positive_outcome"])
                    .groupby("animal_type")["is_positive_outcome"]
                    .mean()
                    .sort_values(ascending=False)
                )

                if adoption_by_type.empty:
                    st.warning("Not enough data to calculate adoption rate by animal type.")
                else:
                    adoption_by_type_pct = (adoption_by_type * 100).round(1)

                    fig1 = plot_bar_counts(
                        adoption_by_type_pct,
                        title="Positive outcome rate by animal type (%)",
                        xlabel="Animal type",
                        ylabel="Positive outcome rate (%)",
                        top_n=8,
                        figsize=(6.5, 3.2),
                        cmap_name="viridis"
                    )
                    st.pyplot(fig1, use_container_width=True)

            with col2:
                st.subheader("What this chart shows")
                st.write(
                    """
                    This chart shows the percentage of cases that ended with a positive outcome by animal type.
                    Dogs have the highest positive outcome rate.
                    Cats have a lower positive outcome rate than dogs.
                    Animals grouped as Reptile or Other have the lowest positive outcome rates.
                    This indicates that adoption likelihood differs across animal types.
                    """
                )

            st.divider()

            col3, col4 = st.columns([2, 1])

            with col3:
                adoption_by_age = (
                    df_rq2.dropna(subset=["age_group", "is_positive_outcome"])
                    .groupby("age_group")["is_positive_outcome"]
                    .mean()
                )

                if adoption_by_age.empty:
                    st.warning("Not enough data to calculate adoption rate by age group.")
                else:
                    adoption_by_age_pct = (adoption_by_age * 100).round(1)

                    fig2 = plot_bar_counts(
                        adoption_by_age_pct,
                        title="Positive outcome rate by age group (%)",
                        xlabel="Age group",
                        ylabel="Positive outcome rate (%)",
                        top_n=None,
                        figsize=(6.5, 3.2),
                        cmap_name="viridis"
                    )
                    st.pyplot(fig2, use_container_width=True)

            with col4:
                st.subheader("What this chart shows")
                st.write(
                    """
                    This chart shows how positive outcome rates differ across age groups.
                    Senior animals have the highest positive outcome rate overall.
                    Young and Adult animals also have relatively high positive outcome rates.
                    Baby animals have a lower positive outcome rate.
                    The Unknown age group has the lowest positive outcome rate.
                    """
                )

            st.divider()

            col5, col6 = st.columns([2, 1])

            with col5:
                def normalize_age_group(v):
                    if isinstance(v, tuple) and len(v) > 0:
                        return str(v[0])

                    s = str(v).strip()
                    if s.startswith("(") and s.endswith(")") and "," in s:
                        inner = s[1:-1]
                        first = inner.split(",")[0].strip().strip("'").strip('"')
                        return first

                    return s

                df_rq2["age_group_clean"] = df_rq2["age_group"].apply(normalize_age_group)

                dist = pd.crosstab(
                    index=df_rq2["age_group_clean"],
                    columns=df_rq2["outcome_group"],
                    normalize="index"
                )

                age_order = ["Baby", "Young", "Adult", "Senior", "Unknown"]
                dist = dist.reindex([a for a in age_order if a in dist.index])

                expected_cols = ["Admin_or_Unknown", "Negative", "No_Outcome_Yet", "Other_or_Partner", "Positive"]
                for c in expected_cols:
                    if c not in dist.columns:
                        dist[c] = 0.0
                dist = dist[expected_cols]

                if dist.empty:
                    st.warning("Not enough data to build outcome distribution by age group.")
                else:
                    fig3 = plot_stacked_bar(
                        df=dist,
                        title="Outcome group distribution by age group",
                        xlabel="Age group",
                        ylabel="Share of outcomes",
                        figsize=(6.5, 3.4),
                        cmap_name="viridis",
                        legend_title="Outcome group"
                    )
                    st.pyplot(fig3, use_container_width=True)


            with col6:
                st.subheader("What this chart shows")
                st.write(
                    """
                    This stacked bar chart shows the share of each outcome group within each age group.
                    Positive outcomes make up a large share for most age groups.
                    The Senior age group also shows a relatively high share of negative outcomes.
                    This suggests that age is related not only to adoption success but also to outcome type.
                    """
                )

            st.success(
                """
                RQ2 Conclusions

                \nPositive outcome rates differ across both animal types and age groups.
                Dogs have a higher positive outcome rate than cats.
                For both dogs and cats, young animals aged 1-3 years show relatively high chances of positive outcomes.

                \nOverall, senior animals have the highest positive outcome rate.
                However, for senior cats, a large share of outcomes is negative.
                This indicates that age and animal type interact in shaping adoption likelihood.

                \nThese results suggest that both animal type and age at intake are important factors related to adoption outcomes.
                """
            )


# ------------------------------- RQ3 -----------------------------------------------
    with tab_rq3:
        st.header("RQ3: How long do animals typically stay in the shelter?")

        st.info(
            """
            This section examines how long animals typically stay in the shelter.
            It shows the overall distribution of length of stay and how stay length differs by age group and outcome group.
            """
        )

        if "intake_duration" not in filtered.columns:
            st.warning("Column intake_duration not found in the dataset.")
        else:
            stay = filtered["intake_duration"].dropna()
            stay = stay[(stay >= 0) & (stay <= 365)]  # cap at 1 year for readability

            col1, col2 = st.columns([2, 1])

            with col1:
                fig1 = plot_hist(
                    stay,
                    title="Length of stay distribution (0-365 days)",
                    xlabel="Days in shelter",
                    bins=40,
                    figsize=(6.5, 3.2)
                )
                st.pyplot(fig1, use_container_width=True)

            with col2:
                st.subheader("What this chart shows")
                st.write(
                    """
                    This histogram shows how long animals stay in the shelter.
                    Most animals leave the shelter within the first few days or weeks.
                    The distribution is strongly right-skewed, which means that only a small number of animals stay for a very long time.
                    """
                )

            st.divider()

            col3, col4 = st.columns([2, 1])

            with col3:
                if "outcome_group" in filtered.columns:
                    fig2 = plot_box(
                        df=filtered[(filtered["intake_duration"] >= 0) & (filtered["intake_duration"] <= 365)],
                        value_col="intake_duration",
                        group_col="outcome_group",
                        title="Length of stay by outcome group (top groups)",
                        xlabel="Outcome group",
                        ylabel="Days in shelter",
                        top_n=5,
                        figsize=(7, 3.4),
                        y_max=120
                    )
                    st.pyplot(fig2, use_container_width=True)
                else:
                    st.warning("Column outcome_group not found, cannot plot boxplot by outcome.")

            with col4:
                st.subheader("What this chart shows")
                st.write(
                    """
                    This boxplot compares length of stay across outcome groups.
                    Animals with negative outcomes tend to have very short stays in the shelter.
                    Animals with positive outcomes usually stay longer and show more variation
                    in length of stay.
                    Other or partner-related outcomes show mixed patterns.
                    """
                )

            st.divider()

            if "age_at_intake_years" in filtered.columns:
                col5, col6 = st.columns([2, 1])

                with col5:
                    scatter_df = filtered.copy()
                    scatter_df = scatter_df[
                        (scatter_df["intake_duration"].between(0, 365)) &
                        (scatter_df["age_at_intake_years"].between(0, 20))
                    ].dropna(subset=["intake_duration", "age_at_intake_years"])

                    if len(scatter_df) > 8000:
                        scatter_df = scatter_df.sample(8000, random_state=42)

                    fig3 = plot_scatter(
                        scatter_df,
                        x="age_at_intake_years",
                        y="intake_duration",
                        title="Age vs length of stay",
                        xlabel="Age at intake (years)",
                        ylabel="Days in shelter",
                        figsize=(6.5, 3.2),
                        alpha=0.25
                    )
                    st.pyplot(fig3, use_container_width=True)

                with col6:
                    st.subheader("What this chart shows")
                    st.write(
                        """
                        This scatter plot shows the relationship between age at intake and length of stay in the shelter.
                        Each point represents one animal.
                        Younger animals show a wider range of stay lengths, including some very long stays.
                        As age increases, most animals tend to have shorter stays.
                        This suggests that age at intake is related to how long animals remain in the shelter.
                        """
                    )

        st.divider()

        violin_df = filtered.copy()
        violin_df = violin_df[
            (violin_df["intake_duration"].between(0, 365)) &
            (violin_df["age_group"].notna())
        ].copy()

        if "age_group_clean" in df_rq2.columns:
            violin_df["age_group_clean"] = df_rq2["age_group_clean"]
        else:
            violin_df["age_group_clean"] = violin_df["age_group"].astype(str)

        colv1, colv2 = st.columns([2, 1])

        with colv1:
            fig_v = plot_violin_by_group(
                df=violin_df,
                value_col="intake_duration",
                group_col="age_group_clean",
                title="Length of stay by age group",
                xlabel="Age group",
                ylabel="Days in shelter",
                order=["Baby", "Young", "Adult", "Senior", "Unknown"],
                y_max=120,              
                figsize=(6.5, 3.4),
                cmap_name="viridis"
            )
            st.pyplot(fig_v, use_container_width=True)

        with colv2:
            st.subheader("What this chart shows")
            st.write(
                """
                This violin plot shows how length of stay in the shelter is distributed within each age group.
                Across all age groups, the vast majority of animals stay in the shelter for less than 20 days.
                All age groups show a similar pattern, with short stays being the most common.
                Longer stays occur in every age group but are much less frequent.
                """
            )

        st.success(
            """
            RQ3 Conclusions

            \nMost animals stay in the shelter for a relatively short period of time, usually less than 50 days.
            Only a small number of animals experience very long stays.

            \nLength of stay differs by outcome group.
            Animals with negative outcomes tend to have very short stays, while animals with positive outcomes generally stay longer.

            \nAge at intake is also related to length of stay.
            Younger animals, especially those under one year of age, tend to remain in the shelter longer.
            One possible explanation is that very young animals may need additional care before they are ready for adoption.

            \nDifferences are also visible across animal types.
            Cats older than one year tend to stay longer than dogs, while very young cats tend to leave the shelter faster than very young dogs.
            """
        )


    with tab_logs:
        log_action(username, "open_tab", "Logs")
        logs_tab(username)


if __name__ == "__main__":
    main()
