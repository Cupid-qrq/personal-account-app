# Ledger Atlas

Ledger Atlas 是一个面向家庭共享的个人账本工作台。它把 CSV / XLSX 原始账单按 `ID` 去重、标准化后写入 SQLite 与 CSV 快照，再用独立的 Python API 和静态前端展示现金流、支出结构、消费节律、账单明细与数据质量。

## 当前版本

- **应用**：Ledger Atlas 2.0 alpha
- **数据**：`data/origin/` 下的 CSV / XLSX 均可作为累计源文件；当前最新源文件覆盖 2026-01 至 2026-10，共 387 条唯一记录。
- **入口**：`app.py` 暴露 ASGI 应用，`server.py` 提供本地启动命令。
- **前端**：`frontend/` 下的原生 HTML / CSS / JavaScript，无 Streamlit 页面状态依赖。
- **后端**：`backend/` 下的 FastAPI、数据导入、分析和质量接口。

## 能力

- 同一数据契约读取 CSV、XLSX 和 XLS，保留来源字段并补充日期、月份、年份。
- 可重复的全量重建：按 `ID` 去重，输出 `processed_atlas/ledger_atlas.csv`、SQLite、月度归档和数据清单哈希。
- 总览：收入、支出、结余、储蓄率、现金流轨迹、支出结构和本月信号。
- 模式：分类动量、二级分类穿透、星期画像和日度节奏。
- 明细：当前月份全部原始记录，可搜索分类、备注和日期。
- 数据室：数据契约、来源文件数量、覆盖月份、重复 ID 与主表哈希。
- 导入：页面支持 CSV/XLSX 文件导入；设置 `LEDGER_ADMIN_TOKEN` 后，导入接口要求 `X-Admin-Token`。

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\rebuild_atlas.py
python scripts\validate_atlas.py
python server.py
```

打开 <http://localhost:8000>。部署时可使用 `uvicorn app:app --host 0.0.0.0 --port 8000`。

## 部署建议

推荐把前端静态资源部署到 GitHub Pages 或 Cloudflare Pages，把 FastAPI 部署到一台轻量 Python 服务上；如果只需要家庭内网访问，直接在 NAS 或家庭电脑运行 `server.py` 即可。GitHub Pages 本身只适合只读静态导出，不能承载上传和 SQLite 写入。

## 数据与文档

- [项目审计](docs/项目审计.md)：旧系统架构、数据证据、风险和迁移边界。
- [总体规划](docs/总体规划.md)：新系统的产品、架构、开发阶段和验收标准。
- [架构说明](docs/架构说明.md)：当前 Atlas 运行时与数据流。
- [迭代日志](docs/迭代日志.md)：版本记录和验证结果。

旧 Streamlit 实现已从工作树删除，只保留在 Git 历史中；当前工作树唯一运行入口是 FastAPI。
