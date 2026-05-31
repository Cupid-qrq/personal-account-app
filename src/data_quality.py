from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

from .data_contract import CANONICAL_COLUMNS


def dataset_profile(df: pd.DataFrame) -> Dict[str, object]:
    if df.empty:
        return {
            "rows": 0,
            "months": [],
            "date_min": None,
            "date_max": None,
            "duplicate_ids": 0,
            "blank_ids": 0,
            "missing_required_columns": CANONICAL_COLUMNS,
            "type_counts": {},
            "month_counts": {},
        }

    frame = df.copy()
    time = pd.to_datetime(frame.get("时间"), errors="coerce")
    ids = frame["ID"].fillna("").astype(str).str.strip() if "ID" in frame.columns else pd.Series(dtype=str)
    missing_cols = [col for col in CANONICAL_COLUMNS if col not in frame.columns]

    return {
        "rows": int(len(frame)),
        "months": sorted(frame["月份"].dropna().astype(str).unique().tolist()) if "月份" in frame.columns else [],
        "date_min": str(time.min()) if time.notna().any() else None,
        "date_max": str(time.max()) if time.notna().any() else None,
        "duplicate_ids": int(ids.duplicated().sum()) if not ids.empty else 0,
        "blank_ids": int((ids == "").sum()) if not ids.empty else 0,
        "missing_required_columns": missing_cols,
        "type_counts": frame["类型"].value_counts(dropna=False).to_dict() if "类型" in frame.columns else {},
        "month_counts": frame["月份"].value_counts().sort_index().to_dict() if "月份" in frame.columns else {},
    }


def storage_profile(master_file: Path, db_rows: int | None) -> Dict[str, object]:
    csv_rows = None
    if master_file.exists():
        csv_rows = int(len(pd.read_csv(master_file, encoding="utf-8-sig")))

    return {
        "csv_rows": csv_rows,
        "sqlite_rows": db_rows,
        "in_sync": db_rows is None or csv_rows == db_rows,
    }


def quality_warnings(profile: Dict[str, object], storage: Dict[str, object] | None = None) -> List[str]:
    warnings: List[str] = []

    if profile.get("duplicate_ids", 0):
        warnings.append(f"存在重复 ID: {profile['duplicate_ids']} 条")
    if profile.get("blank_ids", 0):
        warnings.append(f"存在空 ID: {profile['blank_ids']} 条")
    if profile.get("missing_required_columns"):
        warnings.append("主表缺少标准字段: " + ", ".join(profile["missing_required_columns"]))
    if storage and not storage.get("in_sync", True):
        warnings.append(f"CSV/SQLite 行数不一致: CSV={storage.get('csv_rows')} SQLite={storage.get('sqlite_rows')}")

    return warnings
