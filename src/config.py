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

from .data_contract import REQUIRED_COLUMNS

# ===== 分类系统 =====
EXPENSE_CATEGORY_MAP = {
    "餐饮": ["零食", "外卖", "校园卡", "饮品", "聚餐"],
    "购物": ["日用品", "网购"],
    "日常": ["交通", "话费网费", "学习", "娱乐", "运动", "洗澡"],
    "其它": ["医疗", "未分类"],
}

INCOME_CATEGORIES = ["生活费", "红包", "其它"]

INCOME_CATEGORY_ALIASES = {
    "收红包": "红包",
}

DEFAULT_CURRENCY = "CNY"
DEFAULT_EXPENSE_PRIMARY = "其它"
DEFAULT_EXPENSE_SECONDARY = "未分类"
DEFAULT_INCOME_PRIMARY = "其它"

# ===== 应用元数据 =====
APP_NAME = "账本管理系统"
APP_VERSION = "v0.9"
APP_TITLE = f"{APP_NAME} | {APP_VERSION} - 智能财务分析"
APP_DESCRIPTION = "企业级个人财务管理与AI洞察平台"

# ===== 颜色系统 (深空科技主题 v0.9) =====
COLORS = {
    # 背景
    "bg_primary": "#060d17",
    "bg_secondary": "#0b1522",
    "card_bg": "#0d1a2b",
    "card_overlay": "#09121e",

    # 文字
    "text_primary": "#e2edff",
    "text_secondary": "#8da4be",
    "text_subdue": "#5e7488",

    # 强调色
    "accent_blue": "#2998ff",
    "accent_orange": "#f09b4a",
    "accent_green": "#3ecf8e",
    "accent_red": "#f25c5c",
    "accent_yellow": "#e5b73c",
    "accent_purple": "#a78bfa",

    # 边框与阴影
    "border_light": "rgba(100, 180, 255, 0.12)",
    "border_normal": "rgba(100, 180, 255, 0.22)",
    "shadow_soft": "0 4px 16px rgba(0, 0, 0, 0.3)",
    "shadow_hard": "0 8px 32px rgba(0, 0, 0, 0.5)",
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
