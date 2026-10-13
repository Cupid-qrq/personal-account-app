"""Small, atomic local settings store; budgets are shared across browsers."""
import json
import threading
from .config import SETTINGS_FILE

_settings_lock = threading.RLock()

def get_budget(month: str) -> float | None:
    with _settings_lock:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8")) if SETTINGS_FILE.exists() else {}
        return data.get("budgets", {}).get(month)

def set_budget(month: str, amount: float | None) -> None:
    with _settings_lock:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8")) if SETTINGS_FILE.exists() else {}
        data.setdefault("budgets", {})[month] = amount
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = SETTINGS_FILE.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(SETTINGS_FILE)
