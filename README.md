# Personal Ledger Analytics

A Streamlit-based ledger system for CSV import, monthly analytics, and lightweight personal finance insights.

## Main Features

- CSV import with normalization and ID-based de-duplication
- SQLite-backed master data with CSV snapshot compatibility
- Built-in login with default accounts (admin / parent)
- Monthly dashboard for trend, structure, rhythm, and anomaly insights
- Clean dark-themed dashboard UI (v0.9.1)

## Tech Stack

- Python 3.9+
- Streamlit
- Pandas
- Plotly
- SQLite

## Deployment

Streamlit Cloud (recommended):

Live URL: https://my-account.streamlit.app/

Two default accounts are built in: `admin` (full access) and `parent` (view-only). Set `LEDGER_USERS_JSON` in Streamlit Secrets to override default accounts or passwords.

1. Push repository to GitHub.
2. Create an app in Streamlit Cloud.
3. Optionally configure `LEDGER_USERS_JSON` in Secrets to change passwords.
4. Set the main file path to app.py.
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
