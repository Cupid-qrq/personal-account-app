# 💳 个人账本分析系统

**版本**: v0.5 交互增强版
---

## 🎯 核心功能

| 功能             | 说明                                 |
| ---------------- | ------------------------------------ |
| 📤 **数据导入**   | 支持 CSV 单个/批量导入，自动清洗去重 |
| 🔐 **多用户认证** | 管理员(上传) vs 访客(查看)，权限隔离 |
| 📊 **智能分析**   | 支出分类、趋势预测、消费效率评分     |
| 📆 **月度对比**   | 多月收入/支出/结余趋势与环比分析     |
| 🧩 **月度洞察中心** | 趋势/结构/节律/洞察四维分析          |
| ⚠️ **风险预警**   | 异常消费检测、波动监测、智能建议     |
| 📱 **移动适配**   | 深色主题、响应式布局、全屏优化       |
| 🚀 **云部署**     | Streamlit Cloud 一键部署             |

---

## 📋 版本迭代

```
v0.5+        交互视觉升级 + 月度洞察中心 + 3D可视化探索
v0.5         修复金额重复显示 + 月度对比分析 + 导入归档强化
v0.4 (修复版) ✅ 完全重写 app.py, 解决 DuplicateElementId bug, 登录流程优化
v0.4         认证系统 + 移动端优化 + UI 清理
v0.3         科技感 UI + 深度分析 + 部署方案
v0.2         专业界面 + 交互式仪表板  
v0.1         基础 CSV 导入 + 分析
```

---

##  🔐 身份认证

### 权限说明

- **管理员**:
  - ✅ 上传/导入 CSV 文件
  - ✅ 查看所有分析数据
  - ✅ 访问数据管理面板

- **访客**:
  - ✅ 查看分析报告
  - ✅ 浏览数据可视化
  - ❌ 无法上传文件

---

## ✨ 交互与可视化升级

- 动态渐变背景与浮动光斑，提升页面层次感
- 3D 质感指标卡（悬停立体倾斜反馈）
- 月度结构 3D 散点图（分类-月份-金额）
- 月度消费节律热力图（周序 × 周几）
- 洞察摘要卡片（排名、波动、集中度）

---

## 📆 月度洞察中心

- **趋势总览**：收入/支出/结余多月轨迹 + 环比指标
- **结构透视**：分类占比变化 + 3D 金额结构
- **消费节律**：按周与周几识别支出高峰
- **智能洞察**：自动提炼当月最关键结论

---


## 🛠️ 快速开始

### 环境要求
- Python 3.9+
- Streamlit 1.50+  
- Pandas 2.0+
- Plotly 6.0+

### 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/Cupid-qrq/personal-account-app.git
cd personal-account-app

# 2. 虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\Activate.ps1  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
streamlit run app.py
```

### 访问地址
```
本地: http://localhost:8501
```

---

## 📁 项目结构

```
personal-account-app/
├── app.py                      # 主应用 (v0.5)
│
├── src/
│   ├── auth.py                 # 多用户认证模块
│   ├── data_pipeline.py        # CSV 导入/清洗/归档
│   ├── analytics.py            # 12+ 分析函数
│   └── config.py               # 分类规则配置
│
├── data/
│   ├── archive/                # 月度归档 CSV
│   │   ├── 2026-01.csv
│   │   ├── 2026-02.csv
│   │   ├── 2026-03.csv
│   └── processed/
│       └── ledger_master.csv   # 主数据集 (已去重)
│
├── .streamlit/
│   └── config.toml             # Streamlit 配置 (深色主题)
│
├── docs/
│   ├── 迭代日志.md              # 版本历史
│   ├── context_compact.md      # 上下文压缩
│   └── 部署指南.md              # 5 种部署方案
│
├── scripts/
│   └── run_app.ps1             # Windows 启动脚本
│
├── .venv/                       # 虚拟环境
├── requirements.txt             # Python 依赖
└── README.md                    # 本文件
```



---

## 🚀 部署方案

### 推荐: Streamlit Cloud (免费)

```bash
# 1. GitHub 仓库已准备 (主分支)
# 2. 访问 https://streamlit.io/cloud
# 3. 点击 "Deploy an app"
# 4. 授权 GitHub + 选择仓库
# 5. 输入 Main file path: app.py
# 6. 自动部署完成! 🎉
```

### 其他方案
- **Docker + 云服务器** - 完全控制, ¥20-100/月
- **本地 NAS** - 家庭内网, 免费
- **GitHub Pages** - 静态导出 (功能受限)

详见 `docs/部署指南.md`

---

## 🔧 技术栈

| 层级     | 技术            | 备注                    |
| -------- | --------------- | ----------------------- |
| **前端** | Streamlit 1.50+ | 纯 Python, 无前端代码   |
| **数据** | Pandas 2.0+     | CSV 导入、清洗、聚合    |
| **图表** | Plotly 6.0+     | 交互式可视化            |
| **认证** | Session-based   | 自定义模块 (无第三方)   |
| **存储** | CSV + 本地文件  | 无数据库依赖            |
| **部署** | Streamlit Cloud | GitHub webhook 自动部署 |

---

## ⚙️ 配置说明

### `.streamlit/config.toml`

```toml
[theme]
base = "dark"                       # 深色主题锁定
primaryColor = "#68d3ff"            # 蓝色主题
backgroundColor = "#0f0f1e"         # 深黑背景
secondaryBackgroundColor = "#1a1a3e"
textColor = "#e0e0e0"
font = "sans serif"

[client]
showErrorDetails = false            # 隐藏错误细节 (安全)

[logger]
level = "error"                     # 日志级别
```

---

## 🐛 已知问题 & 限制

| 项目           | 现状       | 后续优化方向         |
| -------------- | ---------- | -------------------- |
| 移动端图表交互 | 部分受限   | 继续优化图表触摸体验 |
| 会话超时       | 尚未实现   | 增加自动超时登出     |
| 数据导出       | 功能较基础 | 增加 Excel/PDF 报告  |
| 凭证管理       | 待加强     | 使用环境变量与密钥库 |

---

## 🛠️ 故障排查

### Q: 打开应用后显示"暂无数据"
**A**: 需要上传 CSV 文件
- 点击左侧 "📤 数据导入"
- 选择 CSV 文件并点击 "✅ 导入"

### Q: 手机访问显示布局混乱
**A**: 清空缓存并刷新
```
iOS Safari: 设置 > Safari > 清除历史和网站数据
Android Chrome: 设置 > 隐私权 > 清除浏览数据
```

### Q: 登录后无上传按钮
**A**: 您的账户是访客角色
- 请使用管理员账号登录
- 或联系管理员添加权限

### Q: CSV 导入失败
**A**: 检查文件格式
- 必需列: 日期, 分类, 二级分类, 金额
- 日期格式: YYYY-MM-DD
- 金额必须是数字

---



## 📄 许可证

MIT License © 2026 Cupid-qrq

---

## 🔄 更新日志

详细迭代记录请查看 `docs/迭代日志.md`。

