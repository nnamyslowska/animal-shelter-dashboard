import sys
from pathlib import Path

import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "src"))

from data_loader import ShelterDataLoader
from cleaner import ShelterDataCleaner
from auth_db import init_db, add_user, create_user, check_login, log_action
from plots import plot_bar_counts, plot_hist , plot_line, plot_box, plot_scatter

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
    st.caption("Login or create an account")

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

            st.divider()
            st.caption("Demo (for testing)")
            if st.button("Create demo user (admin/admin)"):
                add_user("admin", "admin")
                log_action("admin", "demo_user_created", "admin/admin created or overwritten")
                st.success("Demo user created: admin / admin")

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
    st.write("This tab shows that the app writes user actions to SQLite.")

    # Simple select, same level as class
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

    tab_about, tab_rq1, tab_rq2, tab_rq3, tab_rq4, tab_logs = st.tabs([
        "About the data",
        "RQ1: Intake & outcomes",
        "RQ2: Adoption likelihood",
        "RQ3: Intake reasons & outcomes",
        "RQ4: Length of stay",
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
            3. Do intake reasons influence outcomes?
            4. How long do animals typically stay in the shelter?
            """
        )

        st.write(
            """
            The following tabs present visual analyses that address each research question.
            """
        )

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

        st.success(
            """
            RQ1 Conclusions
            The shelter mainly receives stray animals. This is the dominant intake type.
            The most common outcomes are rescue and adoption, which suggests many animals find homes.
            Intake reasons are often missing or recorded as Unknown, so detailed reason analysis is limited.
            Intake volume changes across months and shows a repeating pattern, which may indicate seasonality.
            """
        )








    with tab_rq4:
        st.header("RQ4: How long do animals typically stay in the shelter?")

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
                        title="Age vs length of stay (sample, capped)",
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
