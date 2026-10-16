from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from typing import Literal

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from .analytics import patterns, summary
from .config import APP_NAME, APP_VERSION, ADMIN_TOKEN, FRONTEND_DIR, ORIGIN_DIR
from .ingest import load_master, rebuild
from .imports import MAX_UPLOAD_BYTES, preview_import
from .preferences import get_budget, set_budget, get_reviews, set_review


app = FastAPI(title=APP_NAME, version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PUT"],
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
    return {"ok": True, "app": APP_NAME, "version": APP_VERSION, "rows": int(len(frame)), "auth_required": bool(ADMIN_TOKEN)}


@app.get("/api/summary")
def get_summary(month: str | None = None) -> dict[str, object]:
    result = summary(_data(), month, get_reviews())
    result["budget"] = get_budget(result["month"]) if result["month"] else None
    return result


@app.get("/api/patterns")
def get_patterns(month: str | None = None) -> dict[str, object]:
    return patterns(_data(), month, get_reviews())


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
            "account": str(row.get("账户1", "")),
            "book": str(row.get("账本", "")),
            "currency": str(row.get("币种", "CNY")),
            "tags": str(row.get("标签", "")),
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


async def _upload_bytes(file: UploadFile) -> tuple[bytes, str]:
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    return content, Path(file.filename or "").suffix.lower()


@app.post("/api/import/preview")
async def preview_file(file: UploadFile = File(...), x_admin_token: str | None = Header(default=None)) -> dict:
    _require_admin(x_admin_token)
    content, suffix = await _upload_bytes(file)
    try:
        return await run_in_threadpool(preview_import, content, suffix, _data())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _commit_import(content: bytes, suffix: str) -> dict:
    global _stamp
    with _lock:
        preview = preview_import(content, suffix, _data())
        if not preview["valid"]:
            raise ValueError("账单含无效行，请修正预览中的问题后重新导入。")
        ORIGIN_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid4().hex[:8]}{suffix}"
        target = ORIGIN_DIR / safe_name
        target.write_bytes(content)
        try:
            manifest = rebuild()
        except Exception:
            target.unlink(missing_ok=True)
            rebuild()
            raise
        _stamp = None
        return {"ok": True, "stored_as": safe_name, "manifest": manifest, "new_rows": preview["new_rows"]}


@app.post("/api/import")
async def import_file(file: UploadFile = File(...), x_admin_token: str | None = Header(default=None)) -> dict:
    _require_admin(x_admin_token)
    content, suffix = await _upload_bytes(file)
    try:
        return await run_in_threadpool(_commit_import, content, suffix)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class BudgetInput(BaseModel):
    amount: float | None = Field(default=None, ge=0.01, le=10000000, allow_inf_nan=False)


class ReviewInput(BaseModel):
    note: str = Field(default="", max_length=800)
    status: Literal["auto", "in_progress", "closed"] = "auto"


@app.put("/api/reviews/{month}")
def update_review(month: str, body: ReviewInput, x_admin_token: str | None = Header(default=None)) -> dict:
    _require_admin(x_admin_token)
    if month not in set(_data()["月份"].astype(str)):
        raise HTTPException(status_code=404, detail="该月份没有账单，请先导入记录。")
    return set_review(month, body.note, body.status)


@app.put("/api/budgets/{month}")
def update_budget(month: str, body: BudgetInput, x_admin_token: str | None = Header(default=None)) -> dict:
    _require_admin(x_admin_token)
    import re
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise HTTPException(status_code=400, detail="月份格式应为 YYYY-MM。")
    set_budget(month, round(body.amount, 2) if body.amount is not None else None)
    return {"month": month, "budget": get_budget(month)}


@app.get("/")
def index() -> FileResponse:
    if not (FRONTEND_DIR / "index.html").exists():
        raise HTTPException(status_code=503, detail="前端尚未构建，请在 frontend 目录运行 npm ci 和 npm run build。")
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets", check_dir=False), name="assets")

