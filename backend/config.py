from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ORIGIN_DIR = DATA_DIR / "origin"
ATLAS_PROCESSED_DIR = DATA_DIR / "processed_atlas"
ATLAS_ARCHIVE_DIR = DATA_DIR / "archive_atlas"
MASTER_FILE = ATLAS_PROCESSED_DIR / "ledger_atlas.csv"
DB_FILE = ATLAS_PROCESSED_DIR / "ledger_atlas.sqlite3"
MANIFEST_FILE = ATLAS_PROCESSED_DIR / "dataset_manifest.json"
FRONTEND_DIR = ROOT / "frontend"

APP_NAME = "Ledger Atlas"
APP_VERSION = "2.0.0-alpha"
ADMIN_TOKEN = os.getenv("LEDGER_ADMIN_TOKEN", "")

RAW_COLUMNS = [
    "ID", "时间", "账本", "分类", "二级分类", "类型", "金额", "币种",
    "账户1", "账户2", "备注", "已报销", "手续费", "优惠券", "记账者",
    "账单标记", "标签", "账单图片", "关联账单",
]
DERIVED_COLUMNS = ["日期", "月份", "年份"]
CANONICAL_COLUMNS = RAW_COLUMNS + DERIVED_COLUMNS
NUMERIC_COLUMNS = ["金额", "手续费", "优惠券"]

EXPENSE_CATEGORY_MAP = {
    "餐饮": ["零食", "外卖", "校园卡", "饮品", "聚餐"],
    "购物": ["日用品", "网购"],
    "日常": ["交通", "话费网费", "学习", "娱乐", "运动", "洗澡"],
    "其它": ["医疗", "未分类"],
}
INCOME_CATEGORIES = ["生活费", "红包", "其它"]
INCOME_ALIASES = {"收红包": "红包"}

COLUMN_ALIASES = {
    "账本名称": "账本",
    "时间": "时间",
    "日期时间": "时间",
    "金额(元)": "金额",
    "交易类型": "类型",
    "一级分类": "分类",
    "子分类": "二级分类",
}

