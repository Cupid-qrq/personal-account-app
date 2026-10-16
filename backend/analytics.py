from __future__ import annotations

from typing import Any

import pandas as pd


WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _money(value: Any) -> float:
    return round(float(value or 0), 2)


def _text(value: Any, fallback: str = "") -> str:
    if value is None or pd.isna(value):
        return fallback
    text = str(value).strip()
    return text or fallback


def _month_frame(df: pd.DataFrame, month: str | None) -> pd.DataFrame:
    if month and month in set(df["月份"].astype(str)):
        return df[df["月份"].astype(str) == month].copy()
    latest = sorted(df["月份"].dropna().astype(str).unique())[-1] if not df.empty else None
    return df[df["月份"].astype(str) == latest].copy() if latest else df.iloc[0:0].copy()


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return round((current - previous) / abs(previous) * 100, 1)


def _trend(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    grouped = df.groupby(["月份", "类型"], as_index=False)["金额"].sum()
    pivot = grouped.pivot(index="月份", columns="类型", values="金额").fillna(0.0)
    rows: list[dict[str, Any]] = []
    running = 0.0
    for month in sorted(pivot.index.astype(str)):
        income = _money(pivot.loc[month].get("收入", 0.0))
        expense = _money(pivot.loc[month].get("支出", 0.0))
        running += income - expense
        rows.append({"month": month, "income": income, "expense": expense, "balance": _money(income - expense), "running_balance": _money(running)})
    return rows


def _category_rows(month_df: pd.DataFrame) -> list[dict[str, Any]]:
    exp = month_df[month_df["类型"] == "支出"]
    if exp.empty:
        return []
    grouped = exp.groupby("分类", as_index=False).agg(amount=("金额", "sum"), records=("ID", "count"))
    total = grouped["amount"].sum() or 1
    grouped["share"] = grouped["amount"] / total * 100
    grouped = grouped.sort_values("amount", ascending=False)
    return [{"name": str(row["分类"]), "amount": _money(row["amount"]), "records": int(row["records"]), "share": round(float(row["share"]), 1)} for _, row in grouped.iterrows()]


def _recent(month_df: pd.DataFrame, limit: int = 8) -> list[dict[str, Any]]:
    if month_df.empty:
        return []
    view = month_df.sort_values("时间", ascending=False).head(limit)
    rows = []
    for _, row in view.iterrows():
        rows.append({
            "id": str(row.get("ID", "")),
            "date": pd.to_datetime(row["时间"]).strftime("%Y-%m-%d %H:%M"),
            "category": str(row.get("分类", "其它")),
            "subcategory": _text(row.get("二级分类"), "未分类"),
            "type": str(row.get("类型", "支出")),
            "amount": _money(row.get("金额", 0)),
            "note": _text(row.get("备注"), "无备注"),
            "account": _text(row.get("账户1")),
            "book": _text(row.get("账本")),
            "currency": _text(row.get("币种"), "CNY"),
            "tags": _text(row.get("标签")),
        })
    return rows


def _daily(month_df: pd.DataFrame) -> list[dict[str, Any]]:
    exp = month_df[month_df["类型"] == "支出"].copy()
    if exp.empty:
        return []
    exp["date_key"] = pd.to_datetime(exp["时间"]).dt.strftime("%Y-%m-%d")
    grouped = exp.groupby("date_key", as_index=False)["金额"].sum().sort_values("date_key")
    running = 0.0
    rows = []
    for _, row in grouped.iterrows():
        running += float(row["金额"])
        rows.append({"date": row["date_key"], "amount": _money(row["金额"]), "cumulative": _money(running)})
    return rows


def _weekday(month_df: pd.DataFrame) -> list[dict[str, Any]]:
    exp = month_df[month_df["类型"] == "支出"].copy()
    if exp.empty:
        return []
    exp["weekday_index"] = pd.to_datetime(exp["时间"]).dt.dayofweek
    grouped = exp.groupby("weekday_index", as_index=False).agg(amount=("金额", "sum"), records=("ID", "count"))
    mapping = {int(r["weekday_index"]): r for _, r in grouped.iterrows()}
    return [{"name": WEEKDAYS[i], "amount": _money(mapping[i]["amount"]) if i in mapping else 0.0, "records": int(mapping[i]["records"]) if i in mapping else 0} for i in range(7)]


def _insights(month_df: pd.DataFrame, categories: list[dict[str, Any]]) -> list[dict[str, str]]:
    insights: list[dict[str, str]] = []
    if categories:
        lead = categories[0]
        insights.append({"tone": "signal", "title": f"{lead['name']} 是主要支出来源", "body": f"占本月支出的 {lead['share']:.1f}%，共 {lead['records']} 笔。"})
    exp = month_df[month_df["类型"] == "支出"]
    if not exp.empty:
        daily = exp.assign(day=pd.to_datetime(exp["时间"]).dt.strftime("%Y-%m-%d")).groupby("day")["金额"].sum()
        peak_day = str(daily.idxmax())
        peak_amount = _money(daily.max())
        insights.append({"tone": "amber", "title": f"最高消费日是 {peak_day}", "body": f"当天合计 ¥{peak_amount:,.0f}，建议结合明细回看。"})
    return insights[:3]


def summary(df: pd.DataFrame, month: str | None = None, reviews: dict | None = None) -> dict[str, Any]:
    if df.empty:
        return {"month": None, "months": [], "metrics": {"income": 0, "expense": 0, "balance": 0, "saving_rate": 0, "records": 0, "expense_change": None, "daily_average": 0}, "coverage": None, "comparison": None, "trend": [], "categories": [], "daily": [], "weekday": [], "recent": [], "insights": []}
    months = sorted(df["月份"].dropna().astype(str).unique())
    month = month if month in months else months[-1]
    month_df = _month_frame(df, month)
    income = _money(month_df.loc[month_df["类型"] == "收入", "金额"].sum())
    expense = _money(month_df.loc[month_df["类型"] == "支出", "金额"].sum())
    balance = _money(income - expense)
    saving_rate = round(balance / income * 100, 1) if income else 0.0
    trend = _trend(df)
    last_date = pd.to_datetime(month_df["时间"]).max()
    period = pd.Period(month, freq="M")
    reviews = reviews or {}
    review = reviews.get(month, {"note": "", "status": "auto", "updated_at": None})
    status = review.get("status", "auto")
    is_partial = (status == "in_progress" or (status == "auto" and month == months[-1])) and last_date.day < period.days_in_month
    observed_days = last_date.day if is_partial else period.days_in_month
    previous_month = str(period - 1)
    previous = df[df["月份"].astype(str) == previous_month]
    previous_last_day = pd.to_datetime(previous["时间"]).max().day if not previous.empty else 0
    if is_partial:
        previous = previous[pd.to_datetime(previous["时间"]).dt.day <= observed_days]
    previous_expense = _money(previous.loc[previous["类型"] == "支出", "金额"].sum())
    previous_complete = not previous.empty and not (
        reviews.get(previous_month, {}).get("status") == "in_progress"
        and previous_last_day < min(observed_days, (period - 1).days_in_month)
    )
    change = _pct_change(expense, previous_expense) if previous_complete and previous_expense > 0 else None
    categories = _category_rows(month_df)
    insights = _insights(month_df, categories)
    if change is not None:
        insights.insert(0, {"tone": "calm" if change <= 0 else "watch", "title": f"较上月{'同期' if is_partial else ''}{'减少' if change < 0 else '增加'} {abs(change):.1f}%", "body": f"比较范围：{previous_month} 1–{min(observed_days, (period - 1).days_in_month)} 日，支出 ¥{previous_expense:,.2f}。"})
    daily_map = {r["date"]: r["amount"] for r in _daily(month_df)}
    daily, running = [], 0.0
    for day in range(1, observed_days + 1):
        date = f"{month}-{day:02d}"
        amount = daily_map.get(date, 0.0)
        running += amount
        daily.append({"date": date, "amount": amount, "cumulative": _money(running)})
    return {
        "month": month,
        "review": review,
        "months": months,
        "metrics": {
            "income": income,
            "expense": expense,
            "balance": balance,
            "saving_rate": saving_rate,
            "records": int(len(month_df)),
            "expense_change": change,
            "daily_average": _money(expense / observed_days),
        },
        "coverage": {"last_date": last_date.strftime("%Y-%m-%d"), "is_partial": is_partial, "observed_days": observed_days, "month_days": period.days_in_month},
        "comparison": {"month": previous_month, "expense": previous_expense, "partial": is_partial, "available": previous_complete},
        "trend": trend,
        "categories": categories,
        "daily": daily,
        "weekday": _weekday(month_df),
        "recent": _recent(month_df),
        "insights": insights[:3],
    }


def patterns(df: pd.DataFrame, month: str | None = None, reviews: dict | None = None) -> dict[str, Any]:
    data = summary(df, month, reviews)
    categories = data["categories"]
    sub = _month_frame(df, data["month"])
    sub = sub[sub["类型"] == "支出"]
    sub_rows = []
    if not sub.empty:
        grouped = sub.groupby(["分类", "二级分类"], as_index=False).agg(amount=("金额", "sum"), records=("ID", "count"))
        for _, row in grouped.sort_values("amount", ascending=False).head(12).iterrows():
            sub_rows.append({"category": _text(row["分类"]), "subcategory": _text(row["二级分类"], "未分类"), "amount": _money(row["amount"]), "records": int(row["records"])})
    return {"month": data["month"], "categories": categories, "subcategories": sub_rows, "daily": data["daily"], "weekday": data["weekday"]}

