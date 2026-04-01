from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Dict, List

import pandas as pd

from .config import (
    DEFAULT_CURRENCY,
    DEFAULT_EXPENSE_PRIMARY,
    DEFAULT_EXPENSE_SECONDARY,
    DEFAULT_INCOME_PRIMARY,
    EXPENSE_CATEGORY_MAP,
    INCOME_CATEGORIES,
    REQUIRED_COLUMNS,
)


def _read_csv_with_fallback(content: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return pd.read_csv(BytesIO(content), encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 编码无法识别，请使用 UTF-8 或 GBK")


def _ensure_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[REQUIRED_COLUMNS].copy()


def _normalize_type_and_amount(df: pd.DataFrame) -> pd.DataFrame:
    df["金额"] = pd.to_numeric(df["金额"], errors="coerce").fillna(0.0).abs()
    df["类型"] = df["类型"].astype(str).str.strip()

    income_mask = df["分类"].astype(str).isin(INCOME_CATEGORIES)
    unknown_type = ~df["类型"].isin(["收入", "支出"])
    df.loc[unknown_type & income_mask, "类型"] = "收入"
    df.loc[unknown_type & ~income_mask, "类型"] = "支出"

    df.loc[df["类型"] == "收入", "金额"] = df.loc[df["类型"] == "收入", "金额"].abs()
    df.loc[df["类型"] == "支出", "金额"] = df.loc[df["类型"] == "支出", "金额"].abs()

    return df


def _normalize_category(df: pd.DataFrame) -> pd.DataFrame:
    df["分类"] = df["分类"].astype(str).str.strip()
    df["二级分类"] = df["二级分类"].fillna("").astype(str).str.strip()

    expense_mask = df["类型"] == "支出"
    income_mask = df["类型"] == "收入"

    valid_expense_primary = set(EXPENSE_CATEGORY_MAP.keys())
    df.loc[expense_mask & ~df["分类"].isin(valid_expense_primary), "分类"] = DEFAULT_EXPENSE_PRIMARY

    for primary, secondaries in EXPENSE_CATEGORY_MAP.items():
        mask = expense_mask & (df["分类"] == primary)
        valid_secondary = set(secondaries)
        df.loc[mask & ~df["二级分类"].isin(valid_secondary), "二级分类"] = DEFAULT_EXPENSE_SECONDARY

    df.loc[income_mask & ~df["分类"].isin(INCOME_CATEGORIES), "分类"] = DEFAULT_INCOME_PRIMARY
    df.loc[income_mask, "二级分类"] = ""

    return df


def normalize_records(df: pd.DataFrame) -> pd.DataFrame:
    df = _ensure_required_columns(df)
    df = df.copy()

    for col in REQUIRED_COLUMNS:
        if col not in ["金额", "时间"]:
            df[col] = df[col].fillna("").astype(str).str.strip()

    df["时间"] = pd.to_datetime(df["时间"], errors="coerce")
    df = df[df["时间"].notna()].copy()

    df = _normalize_type_and_amount(df)
    df = _normalize_category(df)

    df["币种"] = df["币种"].replace("", DEFAULT_CURRENCY).fillna(DEFAULT_CURRENCY)

    df["日期"] = df["时间"].dt.date.astype(str)
    df["月份"] = df["时间"].dt.to_period("M").astype(str)
    df["年份"] = df["时间"].dt.year.astype(int)

    if "ID" in df.columns:
        df = df[df["ID"].astype(str).str.strip() != ""]

    df = df.sort_values("时间").drop_duplicates(subset=["ID"], keep="last")
    return df.reset_index(drop=True)


def _merge_with_existing_csv(file_path: Path, df_new: pd.DataFrame) -> pd.DataFrame:
    if file_path.exists():
        df_old = pd.read_csv(file_path)
        merged = pd.concat([df_old, df_new], ignore_index=True)
        merged = merged.drop_duplicates(subset=["ID"], keep="last")
        return merged
    return df_new


def save_month_archives(df: pd.DataFrame, archive_dir: Path) -> List[str]:
    archive_dir.mkdir(parents=True, exist_ok=True)
    months_saved: List[str] = []

    for month, group in df.groupby("月份"):
        target = archive_dir / f"{month}.csv"
        merged = _merge_with_existing_csv(target, group)
        merged = merged.sort_values("时间")
        merged.to_csv(target, index=False, encoding="utf-8-sig")
        months_saved.append(month)

    return sorted(months_saved)


def save_master(df: pd.DataFrame, master_file: Path) -> int:
    master_file.parent.mkdir(parents=True, exist_ok=True)
    merged = _merge_with_existing_csv(master_file, df)
    merged = merged.sort_values("时间")
    merged.to_csv(master_file, index=False, encoding="utf-8-sig")
    return len(merged)


def import_csv_file(file_path: Path, archive_dir: Path, master_file: Path) -> Dict[str, object]:
    content = file_path.read_bytes()
    raw_df = _read_csv_with_fallback(content)
    normalized = normalize_records(raw_df)
    months_saved = save_month_archives(normalized, archive_dir)
    total_rows = save_master(normalized, master_file)

    return {
        "source": str(file_path),
        "imported_rows": len(normalized),
        "months_saved": months_saved,
        "master_rows": total_rows,
    }


def import_csv_bytes(file_content: bytes, archive_dir: Path, master_file: Path, source_name: str = "upload") -> Dict[str, object]:
    raw_df = _read_csv_with_fallback(file_content)
    normalized = normalize_records(raw_df)
    months_saved = save_month_archives(normalized, archive_dir)
    total_rows = save_master(normalized, master_file)

    return {
        "source": source_name,
        "imported_rows": len(normalized),
        "months_saved": months_saved,
        "master_rows": total_rows,
    }


def discover_root_csv_files(project_root: Path) -> List[Path]:
    candidates = []
    for p in project_root.glob("*.csv"):
        if p.name.startswith("~"):
            continue
        candidates.append(p)
    return sorted(candidates)


def load_master(master_file: Path) -> pd.DataFrame:
    if not master_file.exists():
        columns = REQUIRED_COLUMNS + ["日期", "月份", "年份"]
        return pd.DataFrame(columns=columns)

    df = pd.read_csv(master_file)
    if "时间" in df.columns:
        df["时间"] = pd.to_datetime(df["时间"], errors="coerce")
    return df
