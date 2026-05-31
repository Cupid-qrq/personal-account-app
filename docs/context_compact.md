# Context Compact - 账本管理系统 v1.0

更新时间: 2026-05-31

## 项目目标
- 将个人账单 CSV 转化为可审计、可重建、可分析的 SQLite 主数据资产。
- 在 Streamlit Cloud 上提供现代化财务工作台，兼顾视觉质感、信息密度和家庭成员可访问性。
- 支持日常上传、origin 全量重建、月度归档、数据质量检查和多维分析。

## 当前版本状态
- 版本: v1.0（全面 UI / 数据 / 架构重构）
- 线上地址: https://my-account.streamlit.app/
- 主入口: app.py（薄入口）
- 页面编排: src/ui_app.py
- UI 主题: src/styles.py
- UI 组件: src/ui_components.py
- 数据服务门面: src/data_service.py
- 数据流水线: src/data_pipeline.py
- 数据质量: src/data_quality.py
- 数据契约: src/data_contract.py
- SQLite 存储: src/sqlite_store.py
- 分析模块: src/analytics.py
- 认证模块: src/auth.py
- 架构说明: docs/架构说明.md

## v1.0 核心更新
1. UI 全面重写为 Notebook / Claude 风格浅色工作台，页面拆为总览、结构、预算与异常、节律、数据室。
2. 新增 `src/styles.py` 和 `src/ui_components.py`，将视觉系统和 UI 组件从主页面拆出。
3. 新增 `src/data_service.py`，集中暴露 UI 所需路径、导入、重建和数据状态接口。
4. 新增 `src/data_quality.py`，提供主表 profile、CSV/SQLite 一致性和质量告警。
5. `src/data_pipeline.py` 新增 `rebuild_from_origin()`，支持从 `data/origin` 全量重建 SQLite、CSV 快照和月度归档。
6. `src/sqlite_store.py` 新增 `replace_records()`，支持完整替换主表。
7. `src/analytics.py` 新增现金流、分类动量、预算压力、星期画像、日度累计、二级分类穿透和自动摘要。
8. 新增 `scripts/rebuild_data.py` 和升级 `scripts/validate_data.py`，形成数据重建和验证闭环。
9. README、部署指南、迭代日志、项目 workflow 和架构说明同步 v1.0。

## 数据现状
- 主表: data/processed/ledger_master.csv + ledger_master.sqlite3
- 主表记录数: 184
- 覆盖月份: 2026-01 ~ 2026-05
- origin 源文件: 3 个 CSV
- 月份分布:
  - 2026-01: 35
  - 2026-02: 25
  - 2026-03: 39
  - 2026-04: 42
  - 2026-05: 43

## 操作命令
```bash
python scripts\rebuild_data.py
python scripts\validate_data.py
streamlit run app.py
```

## 已知限制
- SQLite 写入仍以单进程顺序更新为前提，暂未做并发锁或服务端事务队列。
- 内置默认账号仅适合初始部署，线上应通过 `LEDGER_USERS_JSON` 覆盖。
- 当前分析为规则和统计模型，未接入外部 LLM。

## 下一步建议
1. 为 `data_pipeline` 和 `analytics` 增加 pytest 自动化测试。
2. 增加可下载 Excel/PDF 月报。
3. 根据更多月份数据补充同比、季度、年度和滚动预算模型。
4. 视并发访问情况评估 PostgreSQL 或托管数据层。
