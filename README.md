# Personal Ledger Analytics

v0.5 Final

A Streamlit-based personal ledger system for importing CSV bills, cleaning and archiving records, and generating monthly financial insights with interactive visualizations.

## Highlights

- CSV import with automatic normalization and de-duplication
- SQLite-backed master table with CSV snapshot compatibility
- Role-based access (admin upload, viewer read-only)
- Monthly dashboard with trend, structure, rhythm, and insight panels
- Risk alerts for unusual spending patterns
- Responsive UI for desktop and mobile
- Streamlit Cloud ready deployment

## Core Capabilities

1. Data Pipeline
- Import single CSV or batch scan root CSV files
- Normalize schema and amount/type fields with a shared data contract
- Archive by month: data/archive/YYYY-MM.csv
- Persist master data in SQLite and export CSV snapshots for compatibility

2. Analytics
- Monthly income/expense/balance overview
- Category and subcategory spend distribution
- Month-over-month change metrics
- Monthly structure share analysis
- Weekly rhythm heatmap within month
- Insight digest with ranking, concentration, and volatility

3. Access Control
- Session-based login
- Admin: upload/import + full analysis
- Viewer: analysis only

## Tech Stack

- Python 3.9+
- Streamlit
- Pandas
- Plotly

## Quick Start

```bash
git clone https://github.com/Cupid-qrq/personal-account-app.git
cd personal-account-app
python -m venv .venv
# Windows
.venv\Scripts\Activate.ps1
# Linux / macOS
# source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open: http://localhost:8501

## Project Structure

```text
personal-account-app/
├── app.py
├── src/
│   ├── data_contract.py
│   ├── auth.py
│   ├── config.py
│   ├── data_pipeline.py
│   ├── analytics.py
│   ├── sqlite_store.py
│   └── ui_app.py
├── data/
│   ├── archive/
│   └── processed/
├── docs/
├── scripts/
└── requirements.txt
```

## Deployment

Use Streamlit Cloud:

1. Push repository to GitHub
2. Create app in Streamlit Cloud
3. Set main file path to app.py
4. Deploy

## Data Notes

- Monthly archives are generated automatically after import
- Master table is SQLite-backed and ID-based deduplicated
- CSV snapshots remain in `data/processed/ledger_master.csv` for compatibility
- Input encoding fallback: UTF-8-SIG / UTF-8 / GBK

## License

MIT License
