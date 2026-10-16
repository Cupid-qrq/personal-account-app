"""Atomic local settings store; monthly budgets and reviews are shared across browsers."""
import json
import threading
from .config import SETTINGS_FILE

_settings_lock = threading.RLock()

def get_budget(month: str) -> float | None:
    with _settings_lock:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8")) if SETTINGS_FILE.exists() else {}
        return data.get("budgets", {}).get(month)

def set_budget(month: str, amount: float | None) -> None:
    _update("budgets", month, amount)


def get_reviews() -> dict:
    with _settings_lock:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8")) if SETTINGS_FILE.exists() else {}
        return data.get("reviews", {})


def set_review(month: str, note: str, status: str) -> dict:
    from datetime import datetime, timezone
    review = {"note": note.strip(), "status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    _update("reviews", month, review)
    return review


def _update(section: str, key: str, value) -> None:
    with _settings_lock:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8")) if SETTINGS_FILE.exists() else {}
        data.setdefault(section, {})[key] = value
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = SETTINGS_FILE.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(SETTINGS_FILE)
