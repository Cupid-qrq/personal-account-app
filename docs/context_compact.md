# Context Compact - Ledger Atlas

更新时间: 2026-10-11

## 当前状态

- 项目已从 Streamlit v1.1 迁移到 FastAPI + 静态 HTML/CSS/JS 的 Ledger Atlas 2.0 alpha。
- 新入口：`app.py` 暴露 `backend.api:app`，`server.py` 本地运行。
- 新数据输出：`data/processed_atlas/ledger_atlas.csv`、`ledger_atlas.sqlite3`、`dataset_manifest.json`；月度镜像在 `data/archive_atlas/`。
- 新源格式：`data/origin/` 中的 CSV/XLSX/XLS；最新 Excel 387 条，2026-01 至 2026-10，覆盖旧主表的 184 条并新增 203 条。
- 旧 `src/`、Streamlit 配置、旧生成产物和旧脚本已从工作树删除；历史版本仍在 Git 提交中可追溯。

## 验证命令

```powershell
python scripts\rebuild_atlas.py
python scripts\validate_atlas.py
python -m py_compile app.py server.py backend\*.py scripts\rebuild_atlas.py scripts\validate_atlas.py
```

## 重要边界

- `ID` 是幂等主键，导入和重建都按 ID 去重。
- `账本` 是最新 Excel 的源字段，已纳入新契约。
- `LEDGER_ADMIN_TOKEN` 为空时导入接口适合本地环境；公共部署前必须配置。
- GitHub Pages 只能部署只读静态前端，写入与上传仍需 FastAPI 服务。
