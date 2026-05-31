from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict

import pandas as pd

from .data_pipeline import import_csv_bytes, import_csv_file, load_master, rebuild_from_origin
from .data_quality import dataset_profile, quality_warnings, storage_profile
from .data_contract import SQLITE_DB_SUFFIX, SQLITE_TABLE_NAME


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ORIGIN_DIR = DATA_DIR / "origin"
ARCHIVE_DIR = DATA_DIR / "archive"
PROCESSED_DIR = DATA_DIR / "processed"
MASTER_FILE = PROCESSED_DIR / "ledger_master.csv"
DB_FILE = MASTER_FILE.with_suffix(SQLITE_DB_SUFFIX)


def sqlite_row_count() -> int | None:
    if not DB_FILE.exists():
        return None
    with sqlite3.connect(DB_FILE) as conn:
        return int(pd.read_sql_query(f'select count(*) as n from "{SQLITE_TABLE_NAME}"', conn).iloc[0]["n"])


def load_ledger() -> pd.DataFrame:
    return load_master(MASTER_FILE)


def import_upload(content: bytes, source_name: str) -> Dict[str, object]:
    return import_csv_bytes(content, ARCHIVE_DIR, MASTER_FILE, source_name)


def import_local_file(file_path: Path) -> Dict[str, object]:
    return import_csv_file(file_path, ARCHIVE_DIR, MASTER_FILE)


def rebuild_all_data() -> Dict[str, object]:
    return rebuild_from_origin(ORIGIN_DIR, ARCHIVE_DIR, MASTER_FILE)


def data_status(df: pd.DataFrame) -> Dict[str, object]:
    profile = dataset_profile(df)
    storage = storage_profile(MASTER_FILE, sqlite_row_count())
    warnings = quality_warnings(profile, storage)
    return {
        "profile": profile,
        "storage": storage,
        "warnings": warnings,
    }
