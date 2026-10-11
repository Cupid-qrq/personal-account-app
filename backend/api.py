from __future__ import annotations

import os
import threading
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .analytics import patterns, summary
from .config import APP_NAME, APP_VERSION, ADMIN_TOKEN, FRONTEND_DIR, ORIGIN_DIR
from .ingest import load_master, rebuild


app = FastAPI(title=APP_NAME, version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_lock = threading.RLock()
_frame = None
_stamp: float | None = None


def _data():
    global _frame, _stamp
    path = ORIGIN_DIR.parent / "processed_atlas" / "ledger_atlas.csv"
    stamp = path.stat().st_mtime if path.exists() else None
    with _lock:
        if _frame is None or stamp != _stamp:
            _frame = load_master()
            _stamp = stamp
        return _frame


def _require_admin(token: str | None) -> None:
    if ADMIN_TOKEN and token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="需要有效的管理令牌。")


@app.get("/api/health")
def health() -> dict[str, object]:
    frame = _data()
    return {"ok": True, "app": APP_NAME, "version": APP_VERSION, "rows": int(len(frame))}


@app.get("/api/summary")
def get_summary(month: str | None = None) -> dict[str, object]:
    return summary(_data(), month)


@app.get("/api/patterns")
def get_patterns(month: str | None = None) -> dict[str, object]:
    return patterns(_data(), month)


@app.get("/api/transactions")
def transactions(month: str | None = None) -> dict[str, object]:
    frame = _data()
    months = sorted(frame["月份"].dropna().astype(str).unique())
    selected = month if month in months else (months[-1] if months else None)
    view = frame[frame["月份"].astype(str) == selected].sort_values("时间", ascending=False) if selected else frame.iloc[0:0]
    rows = []
    for _, row in view.iterrows():
        rows.append({
            "id": str(row.get("ID", "")),
            "date": row["时间"].strftime("%Y-%m-%d %H:%M") if hasattr(row["时间"], "strftime") else str(row["时间"]),
            "category": str(row.get("分类", "")),
            "subcategory": "未分类" if not row.get("二级分类") else str(row.get("二级分类")),
            "type": str(row.get("类型", "支出")),
            "amount": round(float(row.get("金额", 0) or 0), 2),
            "note": "无备注" if not row.get("备注") else str(row.get("备注")),
        })
    return {"month": selected, "rows": rows}


@app.get("/api/data-room")
def data_room() -> dict[str, object]:
    frame = _data()
    path = ORIGIN_DIR.parent / "processed_atlas" / "dataset_manifest.json"
    manifest = {}
    if path.exists():
        import json
        manifest = json.loads(path.read_text(encoding="utf-8"))
    return {
        "manifest": manifest,
        "null_counts": {str(k): int(v) for k, v in frame.isna().sum().sort_values(ascending=False).head(8).items()},
        "duplicate_ids": int(frame["ID"].duplicated().sum()) if "ID" in frame else 0,
        "columns": list(frame.columns),
    }


@app.post("/api/import")
async def import_file(file: UploadFile = File(...), x_admin_token: str | None = Header(default=None)) -> dict[str, object]:
    _require_admin(x_admin_token)
    suffix = Path(file.filename or "upload.csv").suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(status_code=400, detail="仅支持 CSV、XLSX 或 XLS 文件。")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空。")
    ORIGIN_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
    target = ORIGIN_DIR / safe_name
    target.write_bytes(content)
    manifest = rebuild()
    global _stamp
    _stamp = None
    return {"ok": True, "stored_as": safe_name, "manifest": manifest}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

