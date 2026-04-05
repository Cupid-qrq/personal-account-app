# Personal Ledger Analytics

A Streamlit-based ledger system for CSV import, monthly analytics, and lightweight personal finance insights.

## Main Features

- CSV import with normalization and ID-based de-duplication
- SQLite-backed master data with CSV snapshot compatibility
- Role-based access (admin upload, viewer read-only)
- Monthly dashboard for trend, structure, rhythm, and anomaly insights

## Tech Stack

- Python 3.9+
- Streamlit
- Pandas
- Plotly
- SQLite

## Deployment

Streamlit Cloud (recommended):

1. Push repository to GitHub.
2. Create an app in Streamlit Cloud.
3. Set the main file path to app.py.
4. Deploy.

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
