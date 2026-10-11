from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.ingest import rebuild


if __name__ == "__main__":
    result = rebuild()
    print(f"sources={len(result['source_files'])}")
    print(f"raw_rows={result['raw_rows']}")
    print(f"rows={result['rows']}")
    print(f"date_range={result['date_min']}..{result['date_max']}")
    print("months=" + ",".join(result["months"]))
    print("status=ok")

