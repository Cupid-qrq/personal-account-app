$ErrorActionPreference = 'Stop'

if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\rebuild_atlas.py
python server.py
