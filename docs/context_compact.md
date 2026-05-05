# Context Compact - 账本管理系统 v0.9

更新时间: 2026-05-05

## 项目目标
- 完成账单 CSV 的导入、清洗、去重、按月归档、主表汇总。
- 提供可视化分析与消费洞察，支持管理员/编辑者上传与访客查看。
- 在移动端和桌面端保持可用且简洁的分析体验。

## 当前版本状态
- 版本: v0.9.1（认证简化 + Bug 修复）
- 线上地址: https://my-account.streamlit.app/
- 主入口: app.py（薄入口）
- UI 层: src/ui_app.py
- 分析模块: src/analytics.py
- 数据流水线: src/data_pipeline.py
- 数据契约: src/data_contract.py
- SQLite 存储: src/sqlite_store.py
- 认证模块: src/auth.py
- 配置中心: src/config.py

## v0.9.1 核心更新
1. 认证简化：内置 admin/parent 两个默认账号，无需配置 `LEDGER_USERS_JSON` 即可登录。
2. 移除公开只读模式：必须登录才能访问，不再匿名暴露数据。
3. CSV 编码修复：`pd.read_csv` 统一指定 `utf-8-sig` 编码，防止 Windows 乱码。
4. UI 全面去 Emoji 化：登录页、侧边栏、指标卡、按钮、提示消息全部使用纯文本。
5. 清理未使用导入和死代码。

## v0.9 关键基线
1. 4月数据导入（42条，合计147条/5个月），收入分类别名映射（”收红包”→”红包”）。
2. 深空科技主题 UI 刷新：色彩系统重构、CSS 收敛、卡片/按钮/标签页样式统一。
3. 权限模型：admin/viewer 二角色（内置），可通过 `LEDGER_USERS_JSON` 扩展。

## 数据现状
- 主表: data/processed/ledger_master.csv + .sqlite3
- 主表记录数: 147
- 覆盖月份: 2026-01 ~ 2026-05
- 原始资料基线: data/origin/2026-05-05.csv, data/origin/项目需求.md
- 月份分布:
  - 2026-01: 35
  - 2026-02: 25
  - 2026-03: 39
  - 2026-04: 42
  - 2026-05: 6（进行中）
- 归档文件: data/archive/2026-{01..05}.csv

## 功能结构
- 登录与权限:
  - admin: 上传/导入 + 全量查看
  - editor: 上传/导入 + 分析查看
  - viewer: 只读查看
- 主界面板块:
  - 财务概览（5指标 + 健康指数 + 消费效率 + 智能洞察）
  - 分析中心（趋势与同比 / 结构透视 / 消费节律 / 异常检测）
  - 明细分析（支出分析 / 消费习惯 / 详细账目 / 预算建议）

## 已知限制
- SQLite 写入以单进程顺序更新为前提，暂未做并发锁优化。
- 内置默认账号（admin/parent）密码为简单密码，部署后建议通过 `LEDGER_USERS_JSON` 覆盖。

## 建议下一步
1. 增加最小自动化回归测试（认证、导入、月度分析）。
2. 补充 SQLite 到 CSV 的回放/迁移脚本。
3. 继续拆分 `src/ui_app.py` 页面模块，降低单文件复杂度。

## 迭代发布工作流（强制）
1. 完成功能或修复后，先执行基础校验（语法/关键数据检查）。
2. 校验通过后，执行 commit 并 push 到远程主分支。
3. 若线上连接 Streamlit Cloud，push 后检查自动部署状态。
4. README 仅保留对外发布信息，不暴露内部调试细节。
5. 根目录保持精简，原始 CSV 与需求文档统一放在 data/origin/。

## iteration-workflow Skill
- 项目级 skill：.github/skills/iteration-workflow/SKILL.md
- 标准流程：分析 → 实现 → 校验 → 文档/记忆 → commit + push
