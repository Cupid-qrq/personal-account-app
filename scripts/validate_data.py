from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics import (
    anomaly_detection,
    expense_health_index,
    generate_smart_insights,
    month_over_month,
    monthly_overview,
    monthly_trend,
)
from src.data_pipeline import load_master


MASTER_FILE = PROJECT_ROOT / "data" / "processed" / "ledger_master.csv"
DB_FILE = MASTER_FILE.with_suffix(".sqlite3")


def main() -> None:
    master = load_master(MASTER_FILE)
    if master.empty:
        raise SystemExit("master data is empty")

    csv_rows = len(pd.read_csv(MASTER_FILE, encoding="utf-8-sig"))
    sqlite_rows = None
    if DB_FILE.exists():
        with sqlite3.connect(DB_FILE) as conn:
            sqlite_rows = int(pd.read_sql_query("select count(*) as n from ledger_records", conn).iloc[0]["n"])

    duplicate_ids = int(master["ID"].duplicated().sum()) if "ID" in master.columns else 0
    blank_ids = int((master["ID"].fillna("").astype(str).str.strip() == "").sum()) if "ID" in master.columns else 0
    if duplicate_ids or blank_ids:
        raise SystemExit(f"invalid IDs: duplicate={duplicate_ids}, blank={blank_ids}")

    if sqlite_rows is not None and sqlite_rows != csv_rows:
        raise SystemExit(f"row mismatch: sqlite={sqlite_rows}, csv={csv_rows}")

    months = sorted(master["月份"].dropna().unique().tolist())
    latest_month = months[-1]
    month_df = master[master["月份"] == latest_month]

    print(f"rows={len(master)}")
    print("months=" + ",".join(months))
    print(master["月份"].value_counts().sort_index().to_string())
    print(f"latest_month={latest_month}")
    print(f"latest_overview={monthly_overview(month_df)}")
    print(f"trend_rows={len(monthly_trend(master))}")
    print(f"mom={month_over_month(master, latest_month)}")
    print(f"health_index={expense_health_index(master)['index']}")
    print(f"anomalies={anomaly_detection(month_df).get('anomaly_count', 0)}")
    print(f"insights={len(generate_smart_insights(master, latest_month)['insights'])}")
    print("status=ok")


if __name__ == "__main__":
    main()
