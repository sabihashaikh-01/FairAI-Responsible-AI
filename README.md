# FairAI — Responsible AI Bias & Fairness Checker

A beginner-friendly Streamlit app for exploring group-level differences in hiring outcomes.

## Features
- Upload a CSV or use the synthetic sample dataset.
- Select a group attribute, outcome column, and positive outcome.
- Calculate group-level positive outcome rates, percentage-point differences, and lowest/highest rate ratio.
- Visualize rates and counts.
- Download group metrics and a plain-text analysis report.
- Display limitations and responsible-use guidance.

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Install packages: `pip install -r requirements.txt`
4. Start the app: `streamlit run app.py`
5. Open the local URL printed in the terminal.

## Run in GitHub Codespaces
1. Create a GitHub repository named `FairAI-Responsible-AI`.
2. Upload `app.py`, `requirements.txt`, and `sample_hiring_data.csv`.
3. Open the repository in a Codespace.
4. In the terminal, run `pip install -r requirements.txt`.
5. Run `streamlit run app.py --server.address 0.0.0.0`.
6. Open port 8501 when Codespaces prompts you.

## Important interpretation notes
This app measures descriptive group-level differences. It cannot establish why differences exist and cannot prove discrimination. The 0.8 ratio is sometimes used as a screening heuristic in certain contexts, but it is not a universal legal or ethical pass/fail standard. Review sample sizes, job relevance, process stages, data quality, context, and applicable law with qualified reviewers. Do not use the tool alone to make decisions about individual candidates.

## Data
`sample_hiring_data.csv` is synthetic and generated for demonstration. It does not contain real applicant records.


