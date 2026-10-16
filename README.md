# Ledger Atlas

个人生活账本。把每月的 CSV / Excel 原始记录整理成清楚的收支、分类与生活节奏，方便自己与家人阅读。

当前版本 **3.2**：React + TypeScript + Vite + shadcn/ui 前端，FastAPI 数据服务。保留暖纸色、陶土色与青灰色的文档式布局，加入原生滚动纸页展开、可反复触发的弹簧倾斜与磁吸操作；桌面侧栏、手机底部导航。Streamlit 和上一版原生 JavaScript 前端已移除，旧实现只保留在 Git 历史。

## 已实现

- **月度总览**：收入、支出、结余、日均支出、月度 / 年度图表、分类占比、预算和近期账单。
- **消费分析**：分类排行、星期分布、消费日历、二级分类。点击分类或日期可直接查看对应明细。
- **账单明细**：搜索、分类 / 收支 / 日期 / 二级分类筛选、排序、分页、详情抽屉、CSV 导出；筛选与月份保留在 URL。
- **数据管理**：原始文件、完整性信息、SHA-256；导入先校验预览，再确认更新。按字符串 ID 合并，更正日期也能更新同一记录。
- **真实交互**：服务端保存预算、错误重试、空状态、键盘选择与弹窗焦点管理、图表数据表、月报 CSV / 打印 PDF。
- **月度手记与月结**：共享保存每月说明，打印月报包含手记；自动判断 / 仍在记录 / 已完成月结实际参与日均与可比区间计算。
- **导入差异**：预览分别统计新增、内容变更、保持不变，并显示最多 20 条变更记录的字段前后值。
- **动态阅读**：ScrollTimeline 驱动纸页展开和回收；纸卡弹簧 3D 倾斜、暖光与边线反馈、磁吸手记操作、账单行轻抬、链接下划线、列表错峰入场与加载扫光。右上角可减少动态效果，也自动尊重系统设置。

仓库当前数据为 387 条唯一记录、2026 年 1–10 月。十月只收录至 9 日，因此按九月 1–9 日比较，不与九月整月直接计算环比。

## 本地运行

环境：Python 3.11+、Node.js 22.12+（建议 24）、npm，以及运行浏览器验收所需的 Chrome。

Windows 一键安装、构建、整理数据并启动：

```powershell
.\scripts\run_app.ps1
```

或者手动运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm ci --prefix frontend
npm run build --prefix frontend
.\.venv\Scripts\python.exe scripts\rebuild_atlas.py
.\.venv\Scripts\python.exe server.py
```

打开 [本地账本](http://localhost:8000)。FastAPI 同时提供编译后的页面与 API，只需要一个服务端口。`server.py` 监听 `0.0.0.0:8000`，同一局域网的家人可通过电脑的局域网 IP 访问。

开发时保持 Python 服务运行，另开终端执行 `npm run dev --prefix frontend`，访问 `http://127.0.0.1:5173`；Vite 将 `/api` 代理到端口 8000。

## 数据与部署

原始来源放在 `data/origin/`；支持 CSV、XLSX、XLS。界面上传限制 10 MB；必需列为 `ID、时间、分类、类型、金额`。更正文件使用相同 ID 重新导入。系统保留来源文件，生成 CSV、SQLite、月度归档与数据清单。预算、月度手记和月结状态保存在 `data/settings.json`，不提交 Git。

推荐 NAS / 小型服务器单实例部署，或使用仓库的多阶段 `Dockerfile`。容器不包含个人数据，需要把数据目录挂载到 `/app/data`，并给予容器用户 UID 10001 写权限。

```sh
docker build -t ledger-atlas .
docker run --rm -p 8000:8000 -v /absolute/ledger-data:/app/data -e LEDGER_ADMIN_TOKEN=your-token ledger-atlas
```

`LEDGER_ADMIN_TOKEN` 保护导入、预算和月度手记修改；它不是阅读权限认证。若需公网家庭共享，应在反向代理层加访问认证及 HTTPS。当前没有发布到公网。GitHub 用于代码托管和 CI；GitHub Pages 不能单独承载此应用的数据写入与上传。

## 验证

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts\validate_atlas.py
npm run format:check --prefix frontend
npm run build --prefix frontend
# 保持 http://127.0.0.1:8000 运行
npm run qa:chrome --prefix frontend
npm run qa:motion --prefix frontend
npm run qa:reduced --prefix frontend
```

浏览器脚本通过真实 Chrome DevTools MCP 驱动 Chrome，覆盖响应式布局、图表、无障碍和主要交互；`qa:motion` 验证真实鼠标反复悬停、最终形变、滚动回放和新增业务，`qa:reduced` 启动真正启用系统减少动态效果的 Chrome 实例。3.2 的截图、原始 MCP 记录与 JSON 结果保存在本地 `output/qa-v3.2/`，不提交含个人账单的截图。预算与手记验收会暂时保存测试值并还原原值；导入浏览器验收只做预览，实际写入测试使用临时账本。

## 文档

- [总体规划](docs/总体规划.md)：产品范围、已交付阶段、下一阶段及验收标准。
- [设计系统](docs/设计系统.md)：视觉、组件与交互规范。
- [动效与月度手记规划](docs/动效与月度手记规划.md)：3.1 创意方向、交互规则及验收条件。
- [交互动效规划](docs/交互动效规划-3.2.md)：3.2 持续交互、滚动编排与文案清理；[本轮验收](docs/验收记录-3.2.md)。
- [架构说明](docs/架构说明.md)：数据契约、API、持久化与部署边界。
- [验收记录](docs/验收记录.md)：实际执行结果与视觉迭代证据。
- [开发上下文](docs/context_compact.md)：后续维护入口；[迭代日志](docs/迭代日志.md) 记录版本变化。
