# Context Compact - 账本管理系统

更新时间：2026-04-01 v0.3（科技感升级版）

## 核心目标

- 对月度账单 CSV 进行导入、清洗、归档与高级可视化分析。
- 提供科技感强、交互丰富、数据洞察深度的财务分析体验。
- 支持多种部署方式，方便家人体验使用。

## 已实现能力（v0.3）

### 前端设计
- 深色主题（黑紫系）+ 毛玻璃容器卡片（Glass Morphism）
- 渐变蓝紫配色系统 + Hover 上浮动画
- 大幅饼图：占屏幕 2/3 宽度、清晰标签显示
- 4 个分析标签页：支出分析 | 消费洞察 | 风险预警 | 详细账目
- 分类快捷按钮：一键钻取分类明细

### 数据分析深化
- **消费效率评分**（0-100）：储蓄率40% + 消费均衡度20% + 分类多样性20% + 数据完整度20%
- **风险预警**：日均消费分析、日消费波动度、异常支出检测（阈值 = 日均 + 1σ）
- **消费习惯**：总支出、日均消费、平均单笔、消费天数、最高频分类
- **智能建议**：基于评分的个性化改进建议（4-5条）
- **预算建议**：基于本月支出的下月预算提议

### 核心分析函数
- `monthly_overview(df)` - 收支结余指标
- `expense_by_category(df)` - 一级分类汇总
- `expense_by_subcategory(df)` - 二级分类汇总  
- `subcategory_by_parent(df, cat)` - 分类钻取
- `consumption_alerts(df)` - 异常检测预警【v0.3新增】
- `consumption_habit(df)` - 消费习惯分析【v0.3新增】
- `spending_efficiency_score(df)` - 综合评分【v0.3新增】
- `category_trend(df)` - 分类趋势【v0.3新增】
- `daily_expense_trend(df)` - 日趋势
- `top_expenses(df)` - 高额排序
- `generate_budget_suggestion(df)` - 预算建议
- `prepare_detail_table(df)` - 明细格式化

### 部署方案（v0.3新增）
1. **Streamlit Cloud**（推荐）- 官方一键部署，免费，全球 CDN
2. **Docker + 云服务器** - 完全控制，稳定 24/7，¥20-100/月
3. **本地 NAS** - 家庭内网方案，完全免费
4. **Heroku** - 快速原型（当前已收费）
5. **GitHub Pages** - 静态导出（功能受限）

### 技术栈
- 核心：Python 3.13 + Streamlit 1.56
- 数据：Pandas 2.2+ + Plotly 6.6
- 样式：HTML/CSS 深色毛玻璃设计
- 部署：支持 Docker、Heroku、Streamlit Cloud

## 关键设计决策

- **深色主题**：减少眼疲劳，更科技感
- **毛玻璃卡片**：现代 UI 审美
- **表单化标签页**：清晰信息分层
- **数据驱动评分**：量化消费健康度
- **预警阈值**：标准差法则实现智能异常检测
- **Session State**：记录用户交互状态
- **多部署方案**：满足不同场景需求

## 目录结构
```
账本管理系统/
├── app.py                      # 主应用（v0.3 深色+标签页）
├── src/
│   ├── config.py              # 分类和字段规则
│   ├── data_pipeline.py       # 导入清洗归档
│   └── analytics.py           # 分析模块（v0.3 新增4个函数）
├── data/
│   ├── archive/               # 按月归档
│   └── processed/             # 去重主表
├── docs/
│   ├── context_compact.md     # 本文件
│   ├── 迭代日志.md            # 版本历史
│   ├── 部署指南.md            # 5种部署方案【v0.3新增】
│   └── README.md              # 项目说明
└── scripts/
    └── run_app.ps1            # 启动脚本
```

## 后续优先级

1. **UI 动画** - Lottie 动画、更多过渡效果
2. **年度分析** - 同比环比、年度趋势、月度对比
3. **高级预警** - 异常支出智能分类、重复消费检验
4. **多维筛选** - 标签筛选、账户筛选、记账者筛选、日期范围
5. **数据导出** - PDF 报表、Excel 下载、邮件订阅
6. **后端升级** - SQLite / PostgreSQL、多用户支持
7. **APP 适配** - 响应式前端、移动端 APP
