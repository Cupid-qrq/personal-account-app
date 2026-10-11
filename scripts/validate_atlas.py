from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.analytics import summary
from backend.config import CANONICAL_COLUMNS
from backend.ingest import load_master


if __name__ == "__main__":
    frame = load_master()
    missing = [col for col in CANONICAL_COLUMNS if col not in frame.columns]
    duplicate_ids = int(frame["ID"].duplicated().sum()) if "ID" in frame else -1
    if frame.empty or missing or duplicate_ids:
        raise SystemExit(f"invalid dataset: rows={len(frame)} missing={missing} duplicate_ids={duplicate_ids}")
    latest = sorted(frame["月份"].dropna().astype(str).unique())[-1]
    view = summary(frame, latest)
    print(f"rows={len(frame)}")
    print(f"latest_month={latest}")
    print(f"months={len(view['months'])}")
    print(f"categories={len(view['categories'])}")
    print(f"recent={len(view['recent'])}")
    print("status=ok")

