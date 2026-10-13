# Ledger Atlas · 开发上下文

更新：2026-10-13。

- 当前版本 3.0；React + TypeScript + Vite + 真正的 shadcn/ui / Radix，后端 FastAPI。不得使用已删除的 Streamlit 或原生 `frontend/app.js` 启动说明。
- 生产：`npm ci --prefix frontend` → `npm run build --prefix frontend` → `python server.py`，8000 同源服务。开发 Vite 在 5173 代理 API。
- 数据 `data/origin`，387 条唯一记录，2026-01 至 2026-10。最新 Excel 保留 `账本` 字段。原始数据未因 UI 验收改写。
- ID 是字符串合并键。最新上传内容优先，即使修正日期变早。不要先按交易时间排序再去重。
- 本次重建恢复了 126 条「账本」字段，原值被旧版去重逻辑选成了旧 CSV 的空值；金额、日期、分类和 ID 不变。
- 十月截至 9 日：支出 744、收入 3100、结余 2356；日均 82.67；上一自然月 1–9 日支出 461，同期增加 61.4%。不与九月整月比较。
- 预算写入 `data/settings.json`；导入预览不写入，确认会重建。当前单进程，读取权限与公网部署尚未实现。
- 全局 frontend-design、web-design-guidelines、react-best-practices 技能，以及项目 `.agents/skills/ui-ux-pro-max` 已安装使用；本地技能与 QA 产物被 Git 忽略但保留。
- 后续入口：[总体规划](总体规划.md)、[架构说明](架构说明.md)、[验收记录](验收记录.md)。原始 MCP 调用和截图在 `output/qa/`，不要把早期失败截图当最终结果。
- 验证：`python -m unittest discover -s tests -v`、`python scripts/validate_atlas.py`、前端 format:check / build、运行服务器后 `npm run qa:chrome --prefix frontend`。
- 用户要求实际打开页面、审查桌面手机画面并迭代；不能把代码生成或构建成功称为视觉验收。
