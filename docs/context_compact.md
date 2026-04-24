# Context Compact - 账本管理系统 v0.8

更新时间: 2026-04-25

## 项目目标
- 完成账单 CSV 的导入、清洗、去重、按月归档、主表汇总。
- 提供可视化分析与消费洞察，支持管理员/编辑者上传与访客查看。
- 在移动端和桌面端保持可用且简洁的分析体验。

## 当前版本状态
- 版本: v0.8（安全与体验优化版）
- 线上地址: https://my-account.streamlit.app/
- 主入口: app.py（薄入口）
- UI 层: src/ui_app.py
- 分析模块: src/analytics.py
- 数据流水线: src/data_pipeline.py
- 数据契约: src/data_contract.py
- SQLite 存储: src/sqlite_store.py
- 认证模块: src/auth.py

## v0.8 核心更新
1. 认证安全重构：移除硬编码默认账号回退，统一改为 `LEDGER_USERS_JSON` 配置。
2. 登录页改造：新增认证状态提示和配置模板提示，不再展示固定演示口令。
3. 权限模型一致化：文档与 UI 均同步三角色（admin/editor/viewer）。
4. UI 升级：深空主题上增加更简洁的 Hero 面板与轻量科技感背景。
5. 版本统一：配置、UI、README、迭代记录同步到 v0.8。
6. 维护补丁（2026-04-25）：无 `LEDGER_USERS_JSON` 时自动进入只读访客模式，避免云端不可访问。

## v0.7 关键基线
1. 主数据层切换到 SQLite，CSV 保留为归档与外部镜像。
2. 数据契约集中到 `src/data_contract.py`。
3. 入口文件瘦身为 `app.py` 启动器，UI 逻辑迁入 `src/ui_app.py`。

## 数据现状
- 主表: data/processed/ledger_master.csv
- 主表记录数: 99
- 覆盖月份: 2026-01, 2026-02, 2026-03
- 原始资料基线: data/origin/2026-04.csv, data/origin/项目需求.md
- 月份分布:
  - 2026-01: 35
  - 2026-02: 25
  - 2026-03: 39
- 归档文件:
  - data/archive/2026-01.csv
  - data/archive/2026-02.csv
  - data/archive/2026-03.csv
- SQLite 说明:
  - 当前工作区可无 `ledger_master.sqlite3` 快照文件，应用会在读取路径中按需从 CSV 自举。

## 功能结构
- 登录与权限:
  - admin: 上传/导入 + 全量查看
  - editor: 上传/导入 + 分析查看（不含管理权限）
  - viewer: 只读查看
- 主界面板块:
  - 财务概览与评分
  - 四维分析中心（趋势/结构/节律/异常）
  - 详细分析（支出/习惯/账目/预算）

## 已知限制
- 认证依赖 `LEDGER_USERS_JSON`；未配置时应用自动降级到只读访客模式。
- SQLite 写入仍以单进程顺序更新为前提，暂未做并发锁优化。
- 只读模式下无法上传数据；如需上传与账号登录，需配置 Secrets 并重启部署。

## 建议下一步
1. 增加最小自动化回归测试（认证、导入、月度分析）。
2. 补充 SQLite 到 CSV 的回放/迁移脚本。
3. 继续拆分 `src/ui_app.py` 页面模块，降低单文件复杂度。

## 迭代发布工作流（强制）
1. 完成功能或修复后，先执行基础校验（语法/关键数据检查）。
2. 校验通过后，执行 commit 并 push 到远程主分支。
3. 若线上连接 Streamlit Cloud，push 后检查自动部署状态；失败则手动 Redeploy。
4. README 仅保留对外发布信息，不暴露内部调试细节与演示凭证。
5. 根目录保持精简，原始 CSV 与需求文档统一放在 data/origin/。

## iteration-workflow Skill
- 已创建项目级 skill：.github/skills/iteration-workflow/SKILL.md
- 用途：迭代时先分析代码，再实现、校验、更新文档/记忆，最后 commit + push
- 触发方式：在 Copilot 对话中直接要求“使用 iteration-workflow skill 处理当前项目迭代”
