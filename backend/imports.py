"""Validate before writing any source or derived data."""
import hashlib
import math
import pandas as pd
from .ingest import _read_bytes, _rename_columns, normalize_records
from .config import RAW_COLUMNS

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _diff_value(value, field: str) -> str:
    if pd.isna(value) or value == "":
        return ""
    if field == "时间":
        return pd.Timestamp(value).strftime("%Y-%m-%d %H:%M:%S")
    if field in {"金额", "手续费", "优惠券"}:
        return f"{float(value):.2f}"
    return str(value).strip()


def _changes(cleaned: pd.DataFrame, existing: pd.DataFrame) -> tuple[int, list]:
    if existing.empty:
        return 0, []
    old = existing.set_index("ID")
    changes, count = [], 0
    for _, row in cleaned.iterrows():
        if row["ID"] not in old.index:
            continue
        before = old.loc[row["ID"]]
        fields = []
        for field in RAW_COLUMNS:
            if field == "ID":
                continue
            a, b = _diff_value(before.get(field, ""), field), _diff_value(row.get(field, ""), field)
            if a != b:
                fields.append({"field": field, "before": a, "after": b})
        if fields:
            count += 1
            if len(changes) < 20:
                changes.append({"id": str(row["ID"]), "fields": fields})
    return count, changes

def preview_import(content: bytes, suffix: str, existing: pd.DataFrame) -> dict:
    if suffix not in {".csv", ".xlsx", ".xls"}:
        raise ValueError("请选择 CSV、XLSX 或 XLS 账单。")
    if not content:
        raise ValueError("文件为空，请重新导出账单。")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("文件超过 10 MB，请分批导入。")
    try:
        raw = _rename_columns(_read_bytes(content, suffix))
    except Exception as exc:
        raise ValueError("无法读取文件，请检查格式或重新导出。") from exc
    missing = [col for col in ["ID", "时间", "分类", "类型", "金额"] if col not in raw.columns]
    if missing:
        raise ValueError("缺少必要列：" + "、".join(missing))
    if raw.empty:
        raise ValueError("文件没有账单记录。")
    issues = []
    for idx, row in raw.iterrows():
        reasons = []
        if pd.isna(row["ID"]) or not str(row["ID"]).strip(): reasons.append("ID 为空")
        if pd.isna(pd.to_datetime(row["时间"], errors="coerce")): reasons.append("时间无效")
        try:
            amount = float(row["金额"])
            if not math.isfinite(amount): raise ValueError()
        except (ValueError, TypeError): reasons.append("金额无效")
        if str(row["类型"]).strip() not in {"收入", "支出"}: reasons.append("收支类型仅支持收入/支出")
        if "币种" in raw and pd.notna(row.get("币种")) and str(row["币种"]).strip() not in {"", "CNY", "人民币", "RMB"}:
            reasons.append("当前仅支持人民币账单")
        if reasons: issues.append({"row": int(idx) + 2, "reason": "、".join(reasons)})
    cleaned = normalize_records(raw)
    ids = set(existing["ID"].astype(str)) if not existing.empty else set()
    incoming = set(cleaned["ID"].astype(str))
    updated_rows, changes = _changes(cleaned, existing) if not issues else (0, [])
    return {
        "valid": not issues,
        "raw_rows": len(raw), "unique_rows": len(cleaned),
        "new_rows": len(incoming - ids), "existing_rows": len(incoming & ids),
        "updated_rows": updated_rows, "unchanged_rows": len(incoming & ids) - updated_rows,
        "changes": changes, "changes_truncated": updated_rows > len(changes),
        "duplicate_rows": len(raw) - len(cleaned) if not issues else 0,
        "issues": issues[:20], "issue_count": len(issues),
        "months": sorted(cleaned["月份"].unique().tolist()),
        "sha256": hashlib.sha256(content).hexdigest(),
        "sample": [{"date": r["时间"].strftime("%Y-%m-%d"), "category": r["分类"], "type": r["类型"], "amount": float(r["金额"])} for _, r in cleaned.head(5).iterrows()],
    }
