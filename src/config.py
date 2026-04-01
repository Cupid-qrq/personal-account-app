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
