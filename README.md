# 账本管理系统 v0.1

第一版实现目标：
- 月度 CSV 导入与清洗
- 自动归档到按月文件
- 主数据集去重汇总
- 可视化分析与预算建议

## 项目结构

- app.py: Streamlit 应用入口
- src/config.py: 字段和分类规则
- src/data_pipeline.py: 导入、清洗、归档、主表更新
- src/analytics.py: 统计分析逻辑
- data/archive/: 按月份归档后的账单
- data/processed/ledger_master.csv: 去重后的总账单数据
- docs/context_compact.md: 当前阶段上下文压缩记录
- docs/迭代日志.md: 版本迭代日志
- scripts/run_app.ps1: Windows 启动脚本

## 环境准备

1. 安装 Python 3.10+
2. 在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 运行

```powershell
streamlit run app.py
```

或者执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_app.ps1
```

## 使用方式

1. 打开页面后，在左侧上传月度 CSV。
2. 或者点击“扫描并导入项目根目录 CSV”，自动导入根目录中的月度文件。
3. 选择月份查看：
- 收入、支出、结余、记录数
- 一级分类占比
- 二级分类分布
- 每日支出趋势
- 高额支出 Top10
- 下月预算建议

## 规则说明

- 若分类不在预设范围，支出自动归入“其它/未分类”。
- 收入分类仅保留“生活费/红包/其它”。
- 按 ID 去重，后导入的同 ID 记录会覆盖旧记录。

## 后续建议

- 增加年度趋势图和同比环比。
- 增加预算阈值预警和异常消费检测。
- 增加 SQLite 存储与多用户支持。
