from __future__ import annotations

import hashlib
import json
import sqlite3
import warnings
from contextlib import closing
from io import BytesIO
from pathlib import Path

import pandas as pd

from .config import (
    ATLAS_ARCHIVE_DIR,
    ATLAS_PROCESSED_DIR,
    CANONICAL_COLUMNS,
    COLUMN_ALIASES,
    DB_FILE,
    MANIFEST_FILE,
    NUMERIC_COLUMNS,
    ORIGIN_DIR,
    RAW_COLUMNS,
    EXPENSE_CATEGORY_MAP,
    INCOME_ALIASES,
    INCOME_CATEGORIES,
)

DEFAULT_CURRENCY = "CNY"
DEFAULT_EXPENSE_PRIMARY = "其它"
DEFAULT_EXPENSE_SECONDARY = "未分类"


def _read_bytes(content: bytes, suffix: str) -> pd.DataFrame:
    suffix = suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Workbook contains no default style")
            return pd.read_excel(BytesIO(content), dtype={"ID": str})
    for encoding in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            return pd.read_csv(BytesIO(content), encoding=encoding, dtype={"ID": str})
        except UnicodeDecodeError:
            continue
    raise ValueError("无法识别 CSV 编码，请使用 UTF-8 或 GBK。")


def _rename_columns(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = {col: COLUMN_ALIASES.get(str(col).strip(), str(col).strip()) for col in frame.columns}
    return frame.rename(columns=renamed)


def normalize_records(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize CSV/XLSX exports into the stable Atlas contract."""
    frame = _rename_columns(frame.copy())
    for col in RAW_COLUMNS:
        if col not in frame.columns:
            frame[col] = ""
    frame = frame[RAW_COLUMNS].copy()
    for col in RAW_COLUMNS:
        if col not in {"金额", "手续费", "优惠券", "时间"}:
            frame[col] = frame[col].fillna("").astype(str).str.strip()

    frame["时间"] = pd.to_datetime(frame["时间"], errors="coerce")
    frame = frame[frame["时间"].notna()].copy()
    frame["金额"] = pd.to_numeric(frame["金额"], errors="coerce").fillna(0.0).abs()
    for col in ["手续费", "优惠券"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)
    frame["类型"] = frame["类型"].replace({"收入": "收入", "支出": "支出", "转账": "支出"})
    income_mask = frame["分类"].isin(INCOME_CATEGORIES + list(INCOME_ALIASES)) | (frame["类型"] == "收入")
    frame.loc[~frame["类型"].isin(["收入", "支出"]) & income_mask, "类型"] = "收入"
    frame.loc[~frame["类型"].isin(["收入", "支出"]) & ~income_mask, "类型"] = "支出"

    frame.loc[frame["类型"] == "收入", "分类"] = frame.loc[frame["类型"] == "收入", "分类"].replace(INCOME_ALIASES)
    frame.loc[(frame["类型"] == "收入") & ~frame["分类"].isin(INCOME_CATEGORIES), "分类"] = "其它"
    frame.loc[frame["类型"] == "收入", "二级分类"] = ""

    expense = frame["类型"] == "支出"
    frame.loc[expense & ~frame["分类"].isin(EXPENSE_CATEGORY_MAP), "分类"] = DEFAULT_EXPENSE_PRIMARY
    for primary, secondaries in EXPENSE_CATEGORY_MAP.items():
        mask = expense & (frame["分类"] == primary)
        frame.loc[mask & ~frame["二级分类"].isin(secondaries), "二级分类"] = DEFAULT_EXPENSE_SECONDARY

    frame["币种"] = frame["币种"].replace("", DEFAULT_CURRENCY).fillna(DEFAULT_CURRENCY)
    frame = frame[frame["ID"].astype(str).str.strip().ne("")].copy()
    frame["日期"] = frame["时间"].dt.strftime("%Y-%m-%d")
    frame["月份"] = frame["时间"].dt.to_period("M").astype(str)
    frame["年份"] = frame["时间"].dt.year.astype(int)
    # A correction may move a transaction to an earlier date. Last source row wins.
    frame = frame.drop_duplicates("ID", keep="last").sort_values("时间", kind="stable")
    return frame[CANONICAL_COLUMNS].reset_index(drop=True)


def _source_files(origin_dir: Path = ORIGIN_DIR) -> list[Path]:
    if not origin_dir.exists():
        return []
    files = [p for p in origin_dir.iterdir()
             if p.is_file() and p.suffix.lower() in {".csv", ".xlsx", ".xls"} and not p.name.startswith("~")]
    # Manual exports are chronological by filename; confirmed uploads take precedence.
    return sorted(files, key=lambda p: (p.name.startswith("upload_"), p.name))


def _read_source(path: Path) -> pd.DataFrame:
    return normalize_records(_read_bytes(path.read_bytes(), path.suffix))


def _write_sqlite(frame: pd.DataFrame, db_file: Path) -> None:
    db_file.parent.mkdir(parents=True, exist_ok=True)
    sqlite_frame = frame.copy()
    sqlite_frame["时间"] = pd.to_datetime(sqlite_frame["时间"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    for col in NUMERIC_COLUMNS:
        sqlite_frame[col] = pd.to_numeric(sqlite_frame[col], errors="coerce").fillna(0.0)
    with closing(sqlite3.connect(db_file)) as conn:
        sqlite_frame.to_sql("ledger_records", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_month ON ledger_records(月份)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ledger_type ON ledger_records(类型)")
        conn.commit()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rebuild(origin_dir: Path | None = None) -> dict[str, object]:
    files = _source_files(origin_dir or ORIGIN_DIR)
    frames: list[pd.DataFrame] = []
    raw_rows = 0
    for path in files:
        raw = _read_bytes(path.read_bytes(), path.suffix)
        raw_rows += len(raw)
        cleaned = normalize_records(raw)
        if not cleaned.empty:
            frames.append(cleaned)
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=CANONICAL_COLUMNS)
    if not combined.empty:
        combined = combined.drop_duplicates("ID", keep="last").sort_values("时间", kind="stable").reset_index(drop=True)

    ATLAS_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ATLAS_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    combined.to_csv(ATLAS_PROCESSED_DIR / "ledger_atlas.csv", index=False, encoding="utf-8-sig")
    for month, group in (combined.groupby("月份") if not combined.empty else []):
        group.to_csv(ATLAS_ARCHIVE_DIR / f"{month}.csv", index=False, encoding="utf-8-sig")
    _write_sqlite(combined, DB_FILE)
    master_path = ATLAS_PROCESSED_DIR / "ledger_atlas.csv"
    dates = pd.to_datetime(combined["时间"], errors="coerce") if not combined.empty else pd.Series(dtype="datetime64[ns]")
    manifest = {
        "version": "atlas-2",
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "source_files": [{"name": p.name, "bytes": p.stat().st_size, "sha256": _sha256(p)} for p in files],
        "raw_rows": raw_rows,
        "rows": int(len(combined)),
        "columns": CANONICAL_COLUMNS,
        "date_min": dates.min().isoformat() if dates.notna().any() else None,
        "date_max": dates.max().isoformat() if dates.notna().any() else None,
        "months": sorted(combined["月份"].dropna().unique().tolist()) if not combined.empty else [],
        "month_counts": {str(k): int(v) for k, v in combined["月份"].value_counts().sort_index().items()} if not combined.empty else {},
        "types": {str(k): int(v) for k, v in combined["类型"].value_counts().items()} if not combined.empty else {},
        "master_sha256": _sha256(master_path),
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def load_master() -> pd.DataFrame:
    path = ATLAS_PROCESSED_DIR / "ledger_atlas.csv"
    if not path.exists():
        rebuild()
    frame = pd.read_csv(path, encoding="utf-8-sig", dtype={"ID": str})
    frame["时间"] = pd.to_datetime(frame["时间"], errors="coerce")
    for col in NUMERIC_COLUMNS:
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)
    for col in frame.columns:
        if col not in NUMERIC_COLUMNS and col not in {"年份"}:
            frame[col] = frame[col].fillna("")
    return frame


