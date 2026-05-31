from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_pipeline import rebuild_from_origin


def main() -> None:
    result = rebuild_from_origin(
        PROJECT_ROOT / "data" / "origin",
        PROJECT_ROOT / "data" / "archive",
        PROJECT_ROOT / "data" / "processed" / "ledger_master.csv",
    )
    print(f"source_files={len(result['source_files'])}")
    print(f"raw_rows={result['raw_rows']}")
    print(f"normalized_rows={result['normalized_rows']}")
    print(f"master_rows={result['master_rows']}")
    print("months=" + ",".join(result["months_saved"]))


if __name__ == "__main__":
    main()
