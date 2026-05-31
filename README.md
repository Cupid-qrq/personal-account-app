# Personal Ledger OS

A Streamlit-based personal finance workbench for CSV ingestion, SQLite-backed storage, monthly archiving, and multi-dimensional spending analysis.

## Main Features

- v1.1 Notebook/Claude-inspired Streamlit workbench with a clean editorial dashboard
- CSV import with normalization, ID de-duplication, precise import stats, and `data/origin` full rebuild
- SQLite master data with UTF-8 CSV snapshots and monthly archive mirrors
- Professional analysis views: cash flow, category momentum, TopK records, Pareto, account flow, budget pressure, anomalies, cadence, and data quality
- Built-in role-based login with `admin`, `editor`, and `viewer` capabilities

## Tech Stack

- Python 3.9+
- Streamlit
- Pandas
- Plotly
- SQLite

## Data Workflow

Authoritative raw exports live in `data/origin/`. The app writes normalized records to SQLite first, then exports `data/processed/ledger_master.csv` and monthly files under `data/archive/`.

```bash
python scripts\rebuild_data.py
python scripts\validate_data.py
```

## Deployment

Streamlit Cloud is the target deployment platform.

Live URL: https://my-account.streamlit.app/

Two default accounts are built in: `admin` (full access) and `parent` (view-only). Set `LEDGER_USERS_JSON` in Streamlit Secrets to override default accounts or passwords before sharing the app.

1. Push repository to GitHub.
2. Create an app in Streamlit Cloud.
3. Configure `LEDGER_USERS_JSON` in Secrets for production credentials.
4. Set the main file path to `app.py`.
5. Deploy.

## Quick Start

```bash
git clone https://github.com/Cupid-qrq/personal-account-app.git
cd personal-account-app
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## License

MIT
