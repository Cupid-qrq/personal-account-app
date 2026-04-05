"""账本系统统一数据契约。"""

from __future__ import annotations

RAW_COLUMNS = [
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

DERIVED_COLUMNS = ["日期", "月份", "年份"]

REQUIRED_COLUMNS = RAW_COLUMNS
CANONICAL_COLUMNS = RAW_COLUMNS + DERIVED_COLUMNS

SQLITE_TABLE_NAME = "ledger_records"
SQLITE_DB_SUFFIX = ".sqlite3"
CSV_ENCODING = "utf-8-sig"

NUMERIC_COLUMNS = ["金额", "手续费", "优惠券"]
