import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="FairAI | Responsible AI Fairness Checker",
    page_icon="⚖️",
    layout="wide",
)

st.markdown("""
<style>
    .main {background-color: #f7f9fc;}
    [data-testid="stMetric"] {
        background: white; padding: 16px; border-radius: 12px;
        border: 1px solid #e5eaf2;
    }
    .hero {
        padding: 24px; border-radius: 16px; color: white;
        background: linear-gradient(120deg, #14213d, #2457a7);
        margin-bottom: 18px;
    }
    .hero h1 { color: white; margin-bottom: 5px; }
    .hero p { color: #e8efff; margin-bottom: 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>⚖️ FairAI</h1>
  <p>Responsible AI Bias & Fairness Checker</p>
  <p>Explore hiring outcomes, measure group-level differences, and document limitations.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Project guide")
    st.write("1. Load the demo or upload a CSV.")
    st.write("2. Choose a group attribute.")
    st.write("3. Choose the outcome column and positive outcome.")
    st.write("4. Review rates, charts, and limitations.")
    st.divider()
    st.caption("Educational tool — not a legal finding or a hiring recommendation.")

@st.cache_data
def load_demo():
    return pd.read_csv("sample_hiring_data.csv")

uploaded = st.file_uploader("Upload a CSV dataset", type=["csv"])
if uploaded is not None:
    try:
        raw_df = pd.read_csv(uploaded)
        data_source = "Uploaded CSV"
    except Exception as exc:
        st.error(f"Could not read this CSV: {exc}")
        st.stop()
else:
    try:
        raw_df = load_demo()
        data_source = "Built-in synthetic demo dataset"
    except FileNotFoundError:
        st.error("sample_hiring_data.csv is missing. Add it to the same folder as app.py.")
        st.stop()

if raw_df.empty:
    st.warning("The dataset has no rows.")
    st.stop()

st.subheader("1. Explore the dataset")
st.caption(f"Data source: {data_source} · {len(raw_df):,} rows · {len(raw_df.columns)} columns")
st.dataframe(raw_df.head(20), use_container_width=True)
with st.expander("Dataset summary"):
    st.write(raw_df.describe(include="all").transpose())

columns = list(raw_df.columns)
if len(columns) < 2:
    st.error("Please upload a dataset with at least two columns.")
    st.stop()

default_group = columns.index("Gender") if "Gender" in columns else 0
default_outcome = columns.index("Hired") if "Hired" in columns else min(1, len(columns)-1)

st.subheader("2. Configure the fairness analysis")
left, right = st.columns(2)
with left:
    group_col = st.selectbox("Group attribute to compare", columns, index=default_group)
with right:
    outcome_col = st.selectbox("Outcome column", columns, index=default_outcome)

working = raw_df[[group_col, outcome_col]].copy()
working.columns = ["group", "outcome"]
working = working.dropna()
if working.empty:
    st.error("The selected columns contain no complete rows.")
    st.stop()

outcome_values = list(pd.unique(working["outcome"]))
if len(outcome_values) < 2:
    st.error("The outcome column needs at least two distinct values.")
    st.stop()

preferred = next((v for v in outcome_values if str(v).strip().lower() in
                  {"yes", "hired", "selected", "approved", "1", "true", "positive"}), outcome_values[-1])
positive_outcome = st.selectbox(
    "Which outcome counts as positive? (e.g., Hired or Yes)",
    outcome_values,
    index=outcome_values.index(preferred),
)
working["positive"] = working["outcome"].astype(str) == str(positive_outcome)

summary = (
    working.groupby("group", dropna=False)
    .agg(applicants=("positive", "size"), positive_outcomes=("positive", "sum"),
         selection_rate=("positive", "mean"))
    .reset_index()
)
summary["selection_rate_pct"] = summary["selection_rate"] * 100
summary["not_selected"] = summary["applicants"] - summary["positive_outcomes"]
summary = summary.sort_values("selection_rate", ascending=False).reset_index(drop=True)

st.subheader("3. Fairness metrics")
total = int(summary["applicants"].sum())
overall_rate = float(working["positive"].mean())
highest_rate = float(summary["selection_rate"].max())
lowest_rate = float(summary["selection_rate"].min())
rate_difference_pp = (highest_rate - lowest_rate) * 100
ratio = (lowest_rate / highest_rate) if highest_rate > 0 else None

m1, m2, m3, m4 = st.columns(4)
m1.metric("Rows analyzed", f"{total:,}")
m2.metric("Overall positive rate", f"{overall_rate:.1%}")
m3.metric("Rate difference", f"{rate_difference_pp:.1f} pp")
m4.metric("Lowest / highest rate", f"{ratio:.2f}" if ratio is not None else "N/A")

st.caption(
    "Rate difference is the highest group selection rate minus the lowest, in percentage points. "
    "The ratio is the lowest group rate divided by the highest group rate. These are descriptive "
    "comparisons; the ratio is not a universal pass/fail rule."
)
display = summary[["group", "applicants", "positive_outcomes", "not_selected", "selection_rate_pct"]].copy()
display["selection_rate_pct"] = display["selection_rate_pct"].map(lambda x: f"{x:.1f}%")
display = display.rename(columns={
    "group": "Group", "applicants": "Applicants",
    "positive_outcomes": "Positive outcomes", "not_selected": "Other outcomes",
    "selection_rate_pct": "Positive outcome rate"
})
st.dataframe(display, use_container_width=True, hide_index=True)

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    fig = px.bar(
        summary, x="group", y="selection_rate_pct",
        labels={"group": group_col, "selection_rate_pct": "Positive outcome rate (%)"},
        title="Positive outcome rate by group",
        text=summary["selection_rate_pct"].map(lambda x: f"{x:.1f}%"),
    )
    fig.update_layout(yaxis_range=[0, max(100, float(summary["selection_rate_pct"].max()) + 10)])
    st.plotly_chart(fig, use_container_width=True)
with chart_col2:
    counts = summary[["group", "applicants", "positive_outcomes", "not_selected"]].melt(
        id_vars="group", var_name="Measure", value_name="Count"
    )
    fig2 = px.bar(
        counts, x="group", y="Count", color="Measure", barmode="group",
        labels={"group": group_col}, title="Applicant and outcome counts",
    )
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("4. Interpretation and responsible-use notes")
if len(summary) < 2:
    st.warning("Only one group remains after removing missing values. Select another attribute with at least two groups.")
elif ratio is not None:
    if ratio < 0.8:
        st.warning(
            "The lowest group selection rate is substantially lower than the highest in this dataset. "
            "Treat this as a signal for further review, not proof of bias or unlawful discrimination."
        )
    elif ratio < 0.9:
        st.info(
            "There is a moderate difference between the lowest and highest group selection rates. "
            "Review sample sizes, job-related criteria, and the full selection process."
        )
    else:
        st.success(
            "The observed group selection rates are relatively close under this descriptive metric. "
            "This does not prove that the process is fair or free from bias."
        )

st.markdown("**Recommended review checklist**")
checks = [
    "Check sample sizes; small groups can produce unstable rates.",
    "Confirm that the dataset represents the relevant applicant pool and time period.",
    "Audit job-related criteria and each stage of the hiring process.",
    "Check data quality, missing values, category definitions, and outcome coding.",
    "Review results with qualified people and affected stakeholders before taking action.",
    "Do not use this dashboard alone to rank, reject, or select individual candidates.",
]
for item in checks:
    st.write(f"☐ {item}")

limitations = st.text_area(
    "Add context or limitations for your analysis (optional)",
    placeholder="Example: Synthetic dataset; does not include qualifications, experience, role type, or interview stage.",
)

def build_report():
    lines = [
        "FAIRAI — RESPONSIBLE AI FAIRNESS CHECKER",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Data source: {data_source}",
        f"Rows analyzed: {total}",
        f"Group attribute: {group_col}",
        f"Outcome column: {outcome_col}",
        f"Positive outcome: {positive_outcome}",
        f"Overall positive outcome rate: {overall_rate:.1%}",
        f"Highest-to-lowest rate difference: {rate_difference_pp:.2f} percentage points",
        f"Lowest/highest selection-rate ratio: {ratio:.3f}" if ratio is not None else "Lowest/highest selection-rate ratio: N/A",
        "",
        "GROUP METRICS",
        summary[["group", "applicants", "positive_outcomes", "not_selected", "selection_rate_pct"]].to_string(index=False),
        "",
        "INTERPRETATION LIMITATIONS",
        "These statistics describe observed differences and do not establish cause, intent, or unlawful discrimination.",
        "A ratio threshold is a screening heuristic, not a universal legal or ethical determination.",
        "Results depend on data quality, group sizes, context, job-related criteria, and omitted variables.",
        "Do not use this report as the sole basis for decisions about individuals.",
        "",
        "USER NOTES",
        limitations.strip() or "No additional context provided.",
        "",
        "RECOMMENDED NEXT STEPS",
        *[f"- {item}" for item in checks],
    ]
    return "\n".join(lines)

report_text = build_report()
st.download_button(
    "Download analysis report (.txt)",
    data=report_text.encode("utf-8"),
    file_name="fairai_analysis_report.txt",
    mime="text/plain",
)
st.download_button(
    "Download group metrics (.csv)",
    data=summary.to_csv(index=False).encode("utf-8"),
    file_name="fairai_group_metrics.csv",
    mime="text/csv",
)

st.divider()
st.caption(
    "FairAI is an educational portfolio project, not a certified audit, legal opinion, "
    "or substitute for expert review. Synthetic data is provided for demonstration."
)
