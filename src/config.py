"""
v0.6 中央配置管理

包含：数据模式、分类、颜色系统、功能开关、权限配置
"""

import os

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*args, **kwargs):
        return False

# 加载环境变量
load_dotenv()

# ===== 数据列定义 =====
REQUIRED_COLUMNS = [
    "ID",
    "时间",
    "分类",
    "二级分类",
    "类型",
    "金额",
    "币种",
    "账户1",
    "账户2",
    "备注",
    "已报销",
    "手续费",
    "优惠券",
    "记账者",
    "账单标记",
    "标签",
    "账单图片",
    "关联账单",
]

# ===== 分类系统 =====
EXPENSE_CATEGORY_MAP = {
    "餐饮": ["零食", "外卖", "校园卡", "饮品", "聚餐"],
    "购物": ["日用品", "网购"],
    "日常": ["交通", "话费网费", "学习", "娱乐", "运动", "洗澡"],
    "其它": ["医疗", "未分类"],
}

INCOME_CATEGORIES = ["生活费", "红包", "其它"]

DEFAULT_CURRENCY = "CNY"
DEFAULT_EXPENSE_PRIMARY = "其它"
DEFAULT_EXPENSE_SECONDARY = "未分类"
DEFAULT_INCOME_PRIMARY = "其它"

# ===== v0.6 新增：应用元数据 =====
APP_NAME = "账本管理系统"
APP_VERSION = "v0.6"
APP_TITLE = f"{APP_NAME} | {APP_VERSION} - 智能财务分析"
APP_DESCRIPTION = "企业级个人财务管理与AI洞察平台"

# ===== v0.6 新增：颜色系统 (深空主题) =====
COLORS = {
    # 背景
    "bg_primary": "#0a141f",         # 深空背景
    "bg_secondary": "#0f1828",       # 次级背景
    "card_bg": "#0f1a2e",            # 卡片背景
    "card_overlay": "#06111d",       # 卡片叠层
    
    # 文字
    "text_primary": "#d8ecff",       # 主文字
    "text_secondary": "#9bb0c8",     # 次级文字
    "text_subdue": "#7a8e9f",        # 淡化文字
    
    # 强调色
    "accent_blue": "#3ab9ff",        # 主强调 - 蓝色
    "accent_orange": "#ffb057",      # 次强调 - 橙色
    "accent_green": "#4caf50",       # 成功色 - 绿色
    "accent_red": "#ff6464",         # 错误/警告色
    "accent_yellow": "#ffc107",      # 信息色 - 黄色
    "accent_purple": "#b57edc",      # 特殊色 - 紫色
    
    # 边框与阴影
    "border_light": "rgba(123, 210, 255, 0.2)",
    "border_normal": "rgba(58, 185, 255, 0.4)",
    "shadow_soft": "0 8px 22px rgba(5, 14, 30, 0.35)",
    "shadow_hard": "0 18px 32px rgba(18, 34, 69, 0.55)",
}

# ===== v0.6 新增：功能开关 =====
FEATURES = {
    "smart_insights": True,          # 🧠 AI 智能洞察
    "year_over_year": True,          # 📊 年度对比分析
    "budget_forecast": True,         # 📈 预算预测
    "anomaly_detection": True,       # 🚨 异常检测
    "expense_health_index": True,    # ❤️ 财务健康指数
    "export_pdf": False,             # PDF 导出 (需要 reportlab)
    "export_excel": False,           # Excel 导出 (需要 openpyxl)
    "realtime_dashboard": False,     # 实时更新 (v0.7 计划)
    "rbac_enabled": True,            # 角色权限控制
    "audit_logging": True,           # 审计日志记录
}

# ===== v0.6 新增：性能配置 =====
CACHE_EXPIRY_MINUTES = 5
MAX_DISPLAY_ROWS = 1000
CHUNK_SIZE = 10000
ANOMALY_SENSITIVITY = 1.5   # IQR 倍数，用于离群值检测
FORECAST_HORIZON = 3        # 预测未来 N 个月

# ===== v0.6 新增：模型与AI配置 =====
AI_INSIGHTS_MODEL = "rule_based"  # rule_based, gpt, claude (后续扩展)
INSIGHT_GENERATION_ENABLED = True

# ===== 文件路径 =====
PROJECT_ROOT = os.getenv("PROJECT_ROOT", ".")
ARCHIVE_DIR = f"{PROJECT_ROOT}/data/archive"
MASTER_FILE = f"{PROJECT_ROOT}/data/processed/ledger_master.csv"
AUDIT_LOG_FILE = f"{PROJECT_ROOT}/logs/audit.log"

# ===== Streamlit 配置 =====
STREAMLIT_THEME = {
    "primaryColor": COLORS["accent_blue"],
    "backgroundColor": COLORS["bg_primary"],
    "secondaryBackgroundColor": COLORS["card_bg"],
    "textColor": COLORS["text_primary"],
    "font": "sans serif"
}
