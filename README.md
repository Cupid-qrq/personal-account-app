# Personal Ledger Analytics

A Streamlit-based ledger system for CSV import, monthly analytics, and lightweight personal finance insights.

## Main Features

- CSV import with normalization and ID-based de-duplication
- SQLite-backed master data with CSV snapshot compatibility
- Role-based access (admin/editor/viewer)
- Secure login based on `LEDGER_USERS_JSON` (no built-in default credentials)
- Monthly dashboard for trend, structure, rhythm, and anomaly insights
- Clean dark-themed dashboard UI with glass-morphism cards (v0.9)

## Tech Stack

- Python 3.9+
- Streamlit
- Pandas
- Plotly
- SQLite

## Deployment

Streamlit Cloud (recommended):

Live URL: https://my-account.streamlit.app/

If `LEDGER_USERS_JSON` is missing, the app falls back to public read-only mode. Configure `LEDGER_USERS_JSON` in Streamlit app Secrets to enable authenticated upload/login.

1. Push repository to GitHub.
2. Create an app in Streamlit Cloud.
3. Configure `LEDGER_USERS_JSON` in app Secrets.
4. Set the main file path to app.py.
5. Deploy.

## Quick Start

```bash
git clone https://github.com/Cupid-qrq/personal-account-app.git
cd personal-account-app
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:LEDGER_USERS_JSON='{"admin":{"password":"ChangeMe_2026!","name":"Admin","role":"admin"}}'
streamlit run app.py
```

## License

MIT
