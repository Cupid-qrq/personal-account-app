# Ledger Atlas · 开发上下文

更新：2026-10-16。

- 当前版本 3.2；React + TypeScript + Vite + 真正的 shadcn/ui / Radix，后端 FastAPI。不得使用已删除的 Streamlit 或原生 `frontend/app.js` 启动说明。
- 用户认可现有颜色和布局，要求加强持续动效、删除装饰性格言。3.2 将纸卡的入场 / 滚动 / 指针形变分层，原生 ScrollTimeline 可停留倒放；新增弹簧倾斜、磁吸、局部暖光、边线反馈、轻抬、下划线、错峰与加载扫光。正文始终不透明，金额始终准确；系统和手动 reduced-motion 均可停止动效。
- 纸卡必须用真实鼠标反复进入验收，并覆盖关闭弹窗 / 换月 / 切页后的再次响应；不能仅验证 CSS 变量。手记弹窗关闭后明确恢复入口焦点，键盘可再次打开。
- 生产：`npm ci --prefix frontend` → `npm run build --prefix frontend` → `python server.py`，8000 同源服务。开发 Vite 在 5173 代理 API。
- 数据 `data/origin`，387 条唯一记录，2026-01 至 2026-10。最新 Excel 保留 `账本` 字段。原始数据未因 UI 验收改写。
- ID 是字符串合并键。最新上传内容优先，即使修正日期变早。不要先按交易时间排序再去重。
- 3.0 重建曾恢复 126 条「账本」字段，原值被旧版去重逻辑选成了旧 CSV 的空值；3.1 未重写原始来源或派生主表。
- 默认自动判断下，十月截至 9 日：支出 744、收入 3100、结余 2356；日均 82.67；上一自然月 1–9 日支出 461，同期增加 61.4%。用户确认月结后日均 / 环比按整月计算。
- 预算、月度手记和状态写入 `data/settings.json` 的独立区段，修改一项须保留其他项。手记最多 800 字符，打印模板包含手记。月结 auto / in_progress / closed 参与后端 summary 与 patterns，不只改徽标。
- 导入预览不写入，确认会重建。预览区分 new_rows / updated_rows / unchanged_rows，最多 20 条字段前后明细；不是可选字段 PATCH。批次撤销、版本原子切换仍未实现。
- 当前单进程；读取认证、公网部署、整数分金额模型与明确覆盖截止日尚未实现。写入端点含 reviews 沿用管理令牌。
- 全局 frontend-design、web-design-guidelines、react-best-practices 技能，以及项目 `.agents/skills/ui-ux-pro-max` 已安装使用；本地技能与 QA 产物被 Git 忽略但保留。
- 后续入口：[总体规划](总体规划.md)、[交互动效规划](交互动效规划-3.2.md)、[架构说明](架构说明.md)、[3.2 验收记录](验收记录-3.2.md)。3.2 MCP 调用和截图在 `output/qa-v3.2/`；此前版本证据留在原目录，不要混用。
- 验证：`python -m unittest discover -s tests -v`（20 项）、`python scripts/validate_atlas.py`、前端 format:check / build；运行服务器后执行 `qa:chrome`（40 项）、`qa:motion`（20 项）、`qa:reduced`（3 项），均使用 `npm run <命令> --prefix frontend`。截图等待只针对 DocumentTimeline，不能等待 ScrollTimeline.finished，否则会一直等待滚动到终点。
- 用户要求实际打开页面、审查桌面手机画面并迭代；不能把代码生成或构建成功称为视觉验收。
