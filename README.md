# 💳 个人账本分析系统

**版本**: v0.4修复版 | **状态**: ✅ 生产就绪  
**在线体验**: https://personal-account-app.streamlit.app/  
**GitHub**: https://github.com/Cupid-qrq/personal-account-app

---

## 🎯 核心功能

| 功能 | 说明 |
|------|------|
| 📤 **数据导入** | 支持 CSV 单个/批量导入，自动清洗去重 |
| 🔐 **多用户认证** | 管理员(上传) vs 访客(查看)，权限隔离 |
| 📊 **智能分析** | 支出分类、趋势预测、消费效率评分 |
| ⚠️ **风险预警** | 异常消费检测、波动监测、智能建议 |
| 📱 **移动适配** | 深色主题、响应式布局、全屏优化 |
| 🚀 **云部署** | Streamlit Cloud 一键部署 |

---

## 📋 版本迭代

```
v0.4 (修复版) ✅ 完全重写 app.py, 解决 DuplicateElementId bug, 登录流程优化
v0.4         认证系统 + 移动端优化 + UI 清理
v0.3         科技感 UI + 深度分析 + 部署方案
v0.2         专业界面 + 交互式仪表板  
v0.1         基础 CSV 导入 + 分析
```

---

##  🔐 身份认证

### 演示账号

| 账户 | 密码 | 权限 |
|------|------|------|
| `cupid` | `demonCupid2026` | 🔑 管理员 (可上传) |
| `dad` | `dad2026` | 👁️ 访客 (仅查看) |
| `mom` | `mom2026` | 👁️ 访客 (仅查看) |

### 权限说明

- **管理员 (cupid)**:
  - ✅ 上传/导入 CSV 文件
  - ✅ 查看所有分析数据
  - ✅ 访问数据管理面板

- **访客 (dad/mom)**:
  - ✅ 查看分析报告
  - ✅ 浏览数据可视化
  - ❌ 无法上传文件

---

## 📊 分析特性

### 🎯 支出分析
- 分类占比饼图（可交互）
- 次分类排行柱图
- 每日支出趋势线图
- 选中分类查看详情

### 🧠 消费洞察
- 效率评分 (0-100分) 
  - 储蓄率 40%
  - 消费均衡度 20%
  - 分类多样性 20%
  - 数据完整度 20%
- 消费习惯分析 (日均、平均单笔等)
- 个性化改进建议

### ⚠️ 风险预警
- 日均消费分析
- 消费波动度监测
- 异常支出自动检测
- 消费预警列表

### 📋 详细账目
- 分类汇总表
- 高额支出 Top 10
- 下月预算建议
- 原始交易明细

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
├── app.py                      # 主应用 (v0.4修复版)
│
├── src/
│   ├── auth.py                 # 多用户认证模块
│   ├── data_pipeline.py        # CSV 导入/清洗/归档
│   ├── analytics.py            # 12+ 分析函数
│   └── config.py               # 分类规则配置
│
├── data/
│   ├── archive/                # 月度归档 CSV
│   │   ├── 2026-03.csv
│   │   └── 2026-04.csv
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

## 📊 CSV 格式说明

### 必需字段

| 字段 | 格式 | 示例 |
|------|------|------|
| 日期 | YYYY-MM-DD | 2026-04-15 |
| 分类 | 文本 | 食品、交通、娱乐 |
| 二级分类 | 文本 | 早餐、出租车、电影 |
| 金额 | 正数 | 50.00 |
| 备注 | 文本 (可选) | 便利店 |

### 示例行

```csv
日期,分类,二级分类,金额,备注
2026-04-15,食品,早餐,15.50,便利店
2026-04-16,交通,地铁,2.50,上班
2026-04-17,娱乐,电影,68.00,新片
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

| 层级 | 技术 | 备注 |
|------|------|------|
| **前端** | Streamlit 1.50+ | 纯 Python, 无前端代码 |
| **数据** | Pandas 2.0+ | CSV 导入、清洗、聚合 |
| **图表** | Plotly 6.0+ | 交互式可视化 |
| **认证** | Session-based | 自定义模块 (无第三方) |
| **存储** | CSV + 本地文件 | 无数据库依赖 |
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

| 问题 | 状态 | 说明 |
|------|------|------|
| 重复按钮 key 导致崩溃 | ✅ 已修复 v0.4 | 换用 selectbox |
| 登录输入框显示不全 | ✅ 已修复 v0.4 | 重新构建登录页 |
| 移动端图表交互 | ⏳ 受限 | Plotly 自身限制 |
| 会话超时 | ⏳ 未实现 | 永久保活 |
| 多用户独立数据 | ⏳ 未实现 | 全局视图 |
| 硬编码密码 | ⏳ 待优化 | 可升级为 .env + 数据库 |

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
- 请用 `cupid` 账户登录 (管理员)
- 或联系管理员添加权限

### Q: CSV 导入失败
**A**: 检查文件格式
- 必需列: 日期, 分类, 二级分类, 金额
- 日期格式: YYYY-MM-DD
- 金额必须是数字

---

## 📞 支持与反馈

- 🐛 **报告问题**: [GitHub Issues](https://github.com/Cupid-qrq/personal-account-app/issues)
- 📝 **功能建议**: [GitHub Discussions](https://github.com/Cupid-qrq/personal-account-app/discussions)
- ⭐ **Star 支持**: 如有帮助，请 Star 一下 ~

---

## 📄 许可证

MIT License © 2026 Cupid-qrq

---

## 🔄 更新日志

**v0.4修复版** (2026-04-XX)
- ✅ 完全重写 app.py 解决 DuplicateElementId bug
- ✅ 登录页面简化，输入框正常显示
- ✅ 用 selectbox 替代循环按钮，避免 key 冲突
- ✅ 简化 CSS，删除重复定义
- ✅ 增强错误处理
- ✅ 测试通过: Streamlit 正常启动

**v0.4** (2026-04)
- 多用户认证系统
- 移动端完整适配
- UI 清理 (隐藏 Share/Deploy 按钮)
- 深色主题强制锁定

**v0.3** (2026-04)
- 科技感 UI 升级
- 消费效率评分
- 风险预警模块
- 5 种部署方案

---

**最后更新**: 2026-04-01 | v0.4修复版 ✅ 生产就绪
