from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .data_contract import CANONICAL_COLUMNS, NUMERIC_COLUMNS, SQLITE_TABLE_NAME


def _empty_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=CANONICAL_COLUMNS)


def _normalize_for_sqlite(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    if frame.empty:
        return _empty_frame()

    if "时间" in frame.columns:
        frame["时间"] = pd.to_datetime(frame["时间"], errors="coerce")
        frame = frame[frame["时间"].notna()].copy()
        frame["时间"] = frame["时间"].dt.strftime("%Y-%m-%d %H:%M:%S")

    for col in NUMERIC_COLUMNS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)

    if "年份" in frame.columns:
        frame["年份"] = pd.to_numeric(frame["年份"], errors="coerce").astype("Int64")

    for col in CANONICAL_COLUMNS:
        if col not in frame.columns:
            frame[col] = ""

    return frame[CANONICAL_COLUMNS].copy()


def _restore_from_sqlite(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    if frame.empty:
        return _empty_frame()

    if "时间" in frame.columns:
        frame["时间"] = pd.to_datetime(frame["时间"], errors="coerce")

    for col in NUMERIC_COLUMNS:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)

    if "年份" in frame.columns:
        frame["年份"] = pd.to_numeric(frame["年份"], errors="coerce").astype("Int64")

    return frame


def _read_sqlite_table(db_file: Path) -> pd.DataFrame:
    if not db_file.exists():
        return _empty_frame()

    with sqlite3.connect(db_file) as conn:
        try:
            frame = pd.read_sql_query(f'SELECT * FROM "{SQLITE_TABLE_NAME}"', conn)
        except Exception:
            return _empty_frame()

    return _restore_from_sqlite(frame)


def load_records(db_file: Path) -> pd.DataFrame:
    """从 SQLite 读取主表数据。"""
    frame = _read_sqlite_table(db_file)
    if frame.empty:
        return _empty_frame()

    if "时间" in frame.columns:
        frame = frame.sort_values("时间", na_position="last")
    return frame.reset_index(drop=True)


def save_records(db_file: Path, df_new: pd.DataFrame) -> pd.DataFrame:
    """写入 SQLite 主表，并返回合并后的标准化结果。"""
    db_file.parent.mkdir(parents=True, exist_ok=True)

    existing = load_records(db_file)
    merged = pd.concat([existing, df_new.copy()], ignore_index=True, sort=False)

    if "ID" in merged.columns:
        merged = merged.drop_duplicates(subset=["ID"], keep="last")

    if "时间" in merged.columns:
        merged["时间"] = pd.to_datetime(merged["时间"], errors="coerce")
        merged = merged.sort_values("时间", na_position="last")

    for col in CANONICAL_COLUMNS:
        if col not in merged.columns:
            merged[col] = ""

    merged = merged[CANONICAL_COLUMNS].copy().reset_index(drop=True)

    sqlite_frame = _normalize_for_sqlite(merged)
    with sqlite3.connect(db_file) as conn:
        sqlite_frame.to_sql(SQLITE_TABLE_NAME, conn, if_exists="replace", index=False)

    return merged


def bootstrap_from_csv(csv_file: Path, db_file: Path) -> pd.DataFrame:
    """用 CSV 快照初始化 SQLite 主表。"""
    if not csv_file.exists():
        return _empty_frame()

    frame = pd.read_csv(csv_file)
    return save_records(db_file, frame)


def export_snapshot(df: pd.DataFrame, csv_file: Path) -> None:
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    frame = df.copy()
    if "时间" in frame.columns:
        frame["时间"] = pd.to_datetime(frame["时间"], errors="coerce")
    frame.to_csv(csv_file, index=False, encoding="utf-8-sig")
