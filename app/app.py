import sys
from pathlib import Path

import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from data_loader import ShelterDataLoader
from cleaner import ShelterDataCleaner
from auth_db import init_db, add_user, create_user, check_login, log_action
from plots import plot_bar_counts, plot_hist , plot_line, plot_box, plot_scatter, plot_stacked_bar, plot_heatmap, plot_violin_by_group
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

    import sqlite3
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

    # filters (simple, class-level)
    animal_types = sorted(df["animal_type"].dropna().unique().tolist()) if "animal_type" in df.columns else []
    outcome_groups = sorted(df["outcome_group"].dropna().unique().tolist()) if "outcome_group" in df.columns else []

    with st.sidebar:
        st.subheader("Filters")
        animal_type = st.selectbox("Animal type", ["All"] + animal_types)
        outcome_group = st.selectbox("Outcome group", ["All"] + outcome_groups)

    # log filter changes (simple behavior tracking)
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
            """
        )

        st.subheader("What the dataset contains")

        st.write(
            """
            Each row represents one animal intake case.
            The dataset includes information such as:
            - animal type (for example: dog, cat, bird),
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
            - dates were converted to proper date format,
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
            2. Are some animals more likely to be adopted than others?
            3. How long do animals typically stay in the shelter?
            """
        )

        st.write(
            """
            The following tabs present visual analyses that address each research question.
            """
        )

# ------------------------------- RQ1 -----------------------------------------------
    with tab_rq1:
        st.header("RQ1: What are the most common intake and outcome types?")

        st.info(
            """
            - Stray is the most common intake type by a large margin.
            - Rescue and adoption are the most common outcome types.
            - Many intake records have an unknown intake reason, so reasons must be interpreted with care.
            - Monthly intakes change over time and show repeating peaks and drops.
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
                This bar chart shows the most common outcomes.
                It helps us see what happens to animals after intake.
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
                This chart shows why animals are brought to the shelter.
                It helps us understand the main drivers of intake.
                """
            )

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
                This line chart shows how intakes change over time.          
                """
            )

        st.divider()

        col_s1, col_s2 = st.columns([2, 1])

        with col_s1:
            # Sex distribution (Male / Female / Unknown)
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
                This chart shows the most common primary colors recorded for animals in the dataset.
                Colors are taken from the primary_color field and represent the main coat color category.
                It provides a basic description of the animal population entering the shelter.
                """
            )

        st.success(
            """
            RQ1 Conclusions
            The shelter mainly receives stray animals. This is the dominant intake type.
            The most common outcomes are rescue and adoption, which suggests many animals find homes.
            Intake reasons are often missing or recorded as Unknown, so detailed reason analysis is limited.
            Intake volume changes across months and shows a repeating pattern, which may indicate seasonality.
            """
        )

# ------------------------------- RQ2 -----------------------------------------------
    with tab_rq2:
        st.header("RQ2: Adoption likelihood")

        st.info(
            """
            This section explores whether some animals are more likely to have positive outcomes than others.
            In this project, a "positive outcome" is defined using the outcome_group variable (Positive vs other groups).
            """
        )

        # Safety checks (class-level)
        required_cols = {"outcome_group", "animal_type", "age_group"}
        missing = [c for c in required_cols if c not in filtered.columns]
        if missing:
            st.warning(f"Missing required column(s) for RQ2: {', '.join(missing)}")
        else:
            df_rq2 = filtered.copy()

            # Define adopted/positive as a simple boolean
            df_rq2["is_positive_outcome"] = df_rq2["outcome_group"] == "Positive"

            # -----------------------------
            # Plot 1: Positive outcome rate by animal type
            # -----------------------------
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
                    # Convert to percent for readability
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
                    Cats and small mammals have moderate positive outcome rates.
                    Reptiles and animals grouped as “Other” have the lowest positive outcome rates.
                    This suggests that adoption likelihood differs across animal types.
                    """
                )

            st.divider()

            # -----------------------------
            # Plot 2: Positive outcome rate by age group
            # -----------------------------
            col3, col4 = st.columns([2, 1])

            with col3:
                adoption_by_age = (
                    df_rq2.dropna(subset=["age_group", "is_positive_outcome"])
                    .groupby("age_group")["is_positive_outcome"]
                    .mean()
                )

                # Optional: keep a logical order if your labels allow it
                # If your age_group is already ordered categories, this will keep it.
                # Otherwise it will still plot in groupby order.
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
                    Senior, Young, and Adult animals have relatively high positive outcome rates.
                    Baby animals have a lower positive outcome rate compared to older age groups.
                    The Unknown age group has the lowest positive outcome rate.
                    """
                )

            st.divider()

            # -----------------------------
            # Plot 3: Outcome-group distribution by age group (stacked bar)
            # -----------------------------
            col5, col6 = st.columns([2, 1])

            with col5:
                def normalize_age_group(v):
                    # Case 1: real tuple like ("Adult", "Adult")
                    if isinstance(v, tuple) and len(v) > 0:
                        return str(v[0])

                    # Case 2: string like "(Adult, Adult)"
                    s = str(v).strip()
                    if s.startswith("(") and s.endswith(")") and "," in s:
                        # remove parentheses and take the first item before the comma
                        inner = s[1:-1]
                        first = inner.split(",")[0].strip().strip("'").strip('"')
                        return first

                    # Case 3: normal label
                    return s

                df_rq2["age_group_clean"] = df_rq2["age_group"].apply(normalize_age_group)

                dist = pd.crosstab(
                    index=df_rq2["age_group_clean"],
                    columns=df_rq2["outcome_group"],
                    normalize="index"
                )

                # Optional: keep a clean order on x-axis
                age_order = ["Baby", "Young", "Adult", "Senior", "Unknown"]
                dist = dist.reindex([a for a in age_order if a in dist.index])

                # Make sure all expected outcome groups exist as columns (keeps legend consistent)
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
                    Positive outcomes make up a larger share for some age groups than others.
                    Negative and partner-related outcomes are more common in certain age groups.
                    """
                )

            st.divider()

            colh1, colh2 = st.columns([2, 1])

            with colh1:
                # Build a matrix of positive outcome rates (0..1)
                heat_df = pd.crosstab(
                    index=df_rq2["age_group_clean"],
                    columns=df_rq2["animal_type"],
                    values=df_rq2["is_positive_outcome"],
                    aggfunc="mean"
                )

                # Order age groups for readability
                age_order = ["Baby", "Young", "Adult", "Senior", "Unknown"]
                heat_df = heat_df.reindex([a for a in age_order if a in heat_df.index])

                # Missing combinations -> NaN (no data). Keep them as NaN so they show as blank/neutral.
                # (Plot function will handle NaN safely.)
                fig_hm = plot_heatmap(
                    heat_df,
                    title="Positive outcome rate by age group and animal type",
                    xlabel="Animal type",
                    ylabel="Age group",
                    figsize=(7, 4),
                    cmap="RdBu_r"   # classic red-white-blue heatmap
                )
                st.pyplot(fig_hm, use_container_width=True)

            with colh2:
                st.subheader("What this chart shows")
                st.write(
                    """
                    This heatmap shows the positive outcome rate for each combination of age group and animal type.
                    Each cell represents a percentage (from 0 to 1). Warmer colors indicate higher rates and cooler colors indicate lower rates.
                    """
                )

            st.success(
                """
                RQ2 Conclusions
                Positive outcome rates differ across animal types and age groups.
                Some animal types have higher positive outcome rates than others.
                Age group also matters, as the outcome distribution changes across age categories.
                Overall, these results suggest that both animal type and age are related to adoption likelihood.
                """
            )

# ------------------------------- RQ3 -----------------------------------------------
    with tab_rq3:
        st.header("RQ3: How long do animals typically stay in the shelter?")

        st.info(
            """
            This section describes the length of stay in the shelter.
            It shows the overall distribution and how stay length differs by outcome group.
            """
        )

        if "intake_duration" not in filtered.columns:
            st.warning("Column intake_duration not found in the dataset.")
        else:
            stay = filtered["intake_duration"].dropna()
            stay = stay[(stay >= 0) & (stay <= 365)]  # cap at 1 year for readability

            # --- Row 1: Histogram + explanation ---
            col1, col2 = st.columns([2, 1])

            with col1:
                fig1 = plot_hist(
                    stay,
                    title="Length of stay distribution (0–365 days)",
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

            # --- Row 2: Boxplot by outcome group + explanation ---
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
                    Negative outcomes are associated with very short stays in the shelter.
                    Positive outcomes tend to have longer and more variable stays.
                    Partner and administrative outcomes show mixed patterns of stay length.
                    \n Outcome groups used in this chart:
                    \n- Positive - Adoption, Return To Owner, Community Cat, Return To Wild Habitat, Homefirst, Foster To Adopt  
                    \n- Negative - Euthanasia, Died, Disposal  
                    \n- Other or Partner - Transfer, Rescue, Transport, Shelter, Neuter, Return  
                    \n- Admin or Unknown - Missing, Duplicate  
                    \n- No Outcome Yet - Still at the shelter
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
                        This scatter plot shows the relationship between age at intake and length of stay.
                        Most animals stay for a short time regardless of age.
                        Longer stays appear across different ages, and there is no clear linear relationship between age and length of stay.
                        """
                    )

        st.divider()

        # Use the same filtered data, cap length of stay for readability
        violin_df = filtered.copy()
        violin_df = violin_df[
            (violin_df["intake_duration"].between(0, 365)) &
            (violin_df["age_group"].notna())
        ].copy()

        # If age_group values are messy, reuse your cleaning (if you already made age_group_clean in RQ2)
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
                Age groups are defined based on age at intake: Baby (under 1 year), Young (1–3 years), Adult (3–8 years), Senior (over 8 years), and Unknown.

                \nAcross all age groups, the vast majority of animals stay in the shelter for less than 20 days.
                All age groups show a similar pattern, with short stays being the most common.
                Longer stays occur in every age group but are much less frequent.
                """
            )

        st.success(
            """
            Most animals leave the shelter within a short period after intake.
            The length of stay distribution is highly right-skewed, meaning that only a small number of animals remain in the shelter for a long time.
            Length of stay differs clearly by outcome group: negative outcomes are associated with very short stays, while positive outcomes tend to involve longer and more variable stays.
            Animal age does not show a strong relationship with length of stay, as both short and long stays occur across different age groups.
            """
        )

    with tab_logs:
        log_action(username, "open_tab", "Logs")
        logs_tab(username)


if __name__ == "__main__":
    main()
