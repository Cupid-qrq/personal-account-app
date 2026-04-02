from __future__ import annotations

from typing import Dict, List

import pandas as pd


def filter_month(df: pd.DataFrame, month: str) -> pd.DataFrame:
    if df.empty:
        return df
    return df[df["月份"] == month].copy()


def monthly_overview(df: pd.DataFrame) -> Dict[str, float]:
    if df.empty:
        return {"income": 0.0, "expense": 0.0, "balance": 0.0, "records": 0}

    income = float(df.loc[df["类型"] == "收入", "金额"].sum())
    expense = float(df.loc[df["类型"] == "支出", "金额"].sum())
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "balance": round(income - expense, 2),
        "records": int(len(df)),
    }


def expense_by_category(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["分类", "金额"])

    out = (
        df[df["类型"] == "支出"]
        .groupby("分类", as_index=False)["金额"]
        .sum()
        .sort_values("金额", ascending=False)
    )
    return out


def expense_by_subcategory(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["二级分类", "金额"])

    out = (
        df[df["类型"] == "支出"]
        .groupby("二级分类", as_index=False)["金额"]
        .sum()
        .sort_values("金额", ascending=False)
    )
    return out


def subcategory_by_parent(df: pd.DataFrame, parent_category: str) -> pd.DataFrame:
    """获取某个一级分类下的所有二级分类及金额"""
    if df.empty:
        return pd.DataFrame(columns=["二级分类", "金额"])

    filtered = df[(df["类型"] == "支出") & (df["分类"] == parent_category)]
    if filtered.empty:
        return pd.DataFrame(columns=["二级分类", "金额"])

    out = (
        filtered
        .groupby("二级分类", as_index=False)["金额"]
        .sum()
        .sort_values("金额", ascending=False)
    )
    return out


def daily_expense_trend(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["日期", "金额"])

    daily = (
        df[df["类型"] == "支出"]
        .groupby("日期", as_index=False)["金额"]
        .sum()
    )
    daily["日期"] = pd.to_datetime(daily["日期"], errors="coerce")
    return daily.sort_values("日期")


def top_expenses(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["日期", "分类", "二级分类", "金额", "备注"])

    df_copy = df[df["类型"] == "支出"].copy()
    df_copy["日期"] = pd.to_datetime(df_copy["时间"]).dt.date.astype(str)
    
    cols = ["日期", "分类", "二级分类", "金额", "备注"]
    out = df_copy[cols].sort_values("金额", ascending=False).head(n)
    return out.reset_index(drop=True)


def generate_budget_suggestion(df: pd.DataFrame) -> pd.DataFrame:
    cat_df = expense_by_category(df)
    if cat_df.empty:
        return pd.DataFrame(columns=["分类", "本月支出", "建议下月预算"])

    cat_df = cat_df.rename(columns={"金额": "本月支出"})
    cat_df["建议下月预算"] = (cat_df["本月支出"] * 0.95).round(2)
    return cat_df


def prepare_detail_table(df: pd.DataFrame) -> pd.DataFrame:
    """准备原始明细表，隐藏不需要的字段"""
    if df.empty:
        return pd.DataFrame()

    df_copy = df[df["类型"] == "支出"].copy()
    df_copy["日期"] = pd.to_datetime(df_copy["时间"]).dt.date.astype(str)
    
    # 只保留需要显示的列
    keep_cols = ["日期", "分类", "二级分类", "金额", "备注", "记账者"]
    display_df = df_copy[keep_cols].sort_values("日期", ascending=False).reset_index(drop=True)
    
    return display_df


def consumption_alerts(df: pd.DataFrame) -> Dict[str, object]:
    """消费预警与异常检测"""
    if df.empty:
        return {"daily_avg": 0.0, "highest_day": "无", "highest_day_amount": 0.0, "alerts": []}
    
    expense_df = df[df["类型"] == "支出"].copy()
    if expense_df.empty:
        return {
            "daily_avg": 0.0,
            "daily_std": 0.0,
            "highest_day": "无",
            "highest_day_amount": 0.0,
            "alerts": []
        }

    expense_df["日期"] = pd.to_datetime(expense_df["时间"]).dt.date.astype(str)
    
    daily_totals = expense_df.groupby("日期")["金额"].sum()
    
    daily_avg = float(daily_totals.mean())
    daily_std = float(daily_totals.std()) if len(daily_totals) > 1 else 0.0
    
    highest_day = daily_totals.idxmax() if not daily_totals.empty else "无"
    highest_day_amount = float(daily_totals.max()) if not daily_totals.empty else 0.0
    
    # 预警阈值：平均值 + 1 个标准差
    threshold = daily_avg + daily_std
    
    alerts = []
    for day, amount in daily_totals.items():
        if amount > threshold:
            alerts.append({
                "日期": day,
                "金额": amount,
                "偏差": round(amount - daily_avg, 2),
                "类型": "⚠️ 超支"
            })
    
    return {
        "daily_avg": round(daily_avg, 2),
        "daily_std": round(daily_std, 2),
        "highest_day": highest_day,
        "highest_day_amount": round(highest_day_amount, 2),
        "alerts": sorted(alerts, key=lambda x: x["金额"], reverse=True)
    }


def consumption_habit(df: pd.DataFrame) -> Dict[str, object]:
    """消费习惯分析"""
    if df.empty:
        return {}
    
    expense_df = df[df["类型"] == "支出"].copy()
    expense_df["时间"] = pd.to_datetime(expense_df["时间"])
    
    total_expense = float(expense_df["金额"].sum())
    expense_days = len(expense_df["时间"].dt.date.unique())
    
    # 按周几统计
    expense_df["weekday"] = expense_df["时间"].dt.day_name()
    weekday_expense = expense_df.groupby("weekday", as_index=False)["金额"].sum()
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    
    # 消费频率最高的分类
    category_freq = expense_df["分类"].value_counts()
    most_freq_category = category_freq.index[0] if len(category_freq) > 0 else "无"
    
    # 平均单笔支出
    avg_per_transaction = round(total_expense / len(expense_df), 2) if len(expense_df) > 0 else 0.0
    
    return {
        "total_expense": round(total_expense, 2),
        "expense_days": expense_days,
        "avg_daily_expense": round(total_expense / expense_days, 2) if expense_days > 0 else 0.0,
        "avg_per_transaction": avg_per_transaction,
        "most_freq_category": most_freq_category,
        "most_freq_count": int(category_freq[most_freq_category]) if len(category_freq) > 0 else 0,
    }


def spending_efficiency_score(df: pd.DataFrame) -> Dict[str, object]:
    """消费效率评分（0-100）"""
    if df.empty:
        return {"score": 0, "level": "数据不足", "tips": []}
    
    expense_df = df[df["类型"] == "支出"].copy()
    income_df = df[df["类型"] == "收入"].copy()
    
    total_income = float(income_df["金额"].sum()) if not income_df.empty else 100.0
    total_expense = float(expense_df["金额"].sum())
    
    # 储蓄率 (40%)
    savings_rate = (total_income - total_expense) / total_income if total_income > 0 else 0
    savings_score = min(100, max(0, savings_rate * 100 * 0.4))
    
    # 消费均衡度：标准差越小越好 (20%)
    expense_df["日期"] = pd.to_datetime(expense_df["时间"]).dt.date.astype(str)
    daily_totals = expense_df.groupby("日期")["金额"].sum()
    
    if len(daily_totals) > 1:
        daily_avg = daily_totals.mean()
        daily_std = daily_totals.std()
        cv = daily_std / daily_avg if daily_avg > 0 else 1.0
        balance_score = max(0, 20 * (1 - cv))
    else:
        balance_score = 20
    
    # 分类多样性评分 (20%)
    category_count = expense_df["分类"].nunique()
    diversity_score = min(20, category_count * 5)
    
    # 消费数据量 (20%)
    transaction_count = len(expense_df)
    volume_score = min(20, transaction_count / 5)
    
    total_score = round(savings_score + balance_score + diversity_score + volume_score, 1)
    
    if total_score >= 80:
        level = "⭐⭐⭐⭐⭐ 优秀"
        tips = ["清晰的消费计划", "良好的消费习惯", "建议保持当前节奏", "考虑增加投资比例"]
    elif total_score >= 60:
        level = "⭐⭐⭐⭐ 良好"
        tips = ["消费基本均衡", "建议减少某些类别支出", "可以尝试记录更多细节", "定期复盘支出"]
    elif total_score >= 40:
        level = "⭐⭐⭐ 中等"
        tips = ["消费波动较大", "建议制定月度预算", "关注高频支出类别", "优化支出结构"]
    else:
        level = "⭐⭐ 需要改进"
        tips = ["消费缺乏规划", "建议建立预算体系", "减少不必要支出", "定期审视消费模式"]
    
    return {
        "score": total_score,
        "level": level,
        "tips": tips,
        "details": {
            "储蓄率评分": round(savings_score, 1),
            "消费均衡度": round(balance_score, 1),
            "分类多样性": round(diversity_score, 1),
            "数据完整度": round(volume_score, 1),
        }
    }


def category_trend(df: pd.DataFrame) -> pd.DataFrame:
    """分类消费趋势（按周或日）"""
    if df.empty:
        return pd.DataFrame()
    
    expense_df = df[df["类型"] == "支出"].copy()
    expense_df["日期"] = pd.to_datetime(expense_df["时间"]).dt.date.astype(str)
    expense_df["周"] = pd.to_datetime(expense_df["时间"]).dt.isocalendar().week
    
    # 按日期和分类分组
    trend = expense_df.groupby(["日期", "分类"], as_index=False)["金额"].sum()
    return trend.sort_values("日期")


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """按月汇总收入/支出/结余与储蓄率。"""
    if df.empty:
        return pd.DataFrame(columns=["月份", "收入", "支出", "结余", "储蓄率"])

    work = df.copy()
    if "月份" not in work.columns:
        work["月份"] = pd.to_datetime(work["时间"], errors="coerce").dt.to_period("M").astype(str)

    grouped = (
        work.groupby(["月份", "类型"], as_index=False)["金额"]
        .sum()
    )

    pivot = grouped.pivot(index="月份", columns="类型", values="金额").fillna(0.0)
    income = pivot["收入"] if "收入" in pivot.columns else pd.Series(0.0, index=pivot.index)
    expense = pivot["支出"] if "支出" in pivot.columns else pd.Series(0.0, index=pivot.index)
    out = pd.DataFrame({
        "月份": pivot.index.astype(str),
        "收入": income.values,
        "支出": expense.values,
    })
    out["结余"] = out["收入"] - out["支出"]
    out["储蓄率"] = out.apply(
        lambda r: round((r["结余"] / r["收入"] * 100), 2) if r["收入"] > 0 else 0.0,
        axis=1,
    )
    out = out.sort_values("月份").reset_index(drop=True)
    return out


def month_over_month(df: pd.DataFrame, selected_month: str) -> Dict[str, object]:
    """返回所选月份与上月的环比信息。"""
    trend = monthly_trend(df)
    if trend.empty or selected_month not in set(trend["月份"]):
        return {
            "has_previous": False,
            "current_month": selected_month,
            "previous_month": None,
            "expense_delta": 0.0,
            "expense_delta_pct": 0.0,
            "income_delta": 0.0,
            "income_delta_pct": 0.0,
            "balance_delta": 0.0,
            "balance_delta_pct": 0.0,
        }

    idx = trend.index[trend["月份"] == selected_month][0]
    current = trend.loc[idx]
    if idx == 0:
        return {
            "has_previous": False,
            "current_month": selected_month,
            "previous_month": None,
            "expense_delta": 0.0,
            "expense_delta_pct": 0.0,
            "income_delta": 0.0,
            "income_delta_pct": 0.0,
            "balance_delta": 0.0,
            "balance_delta_pct": 0.0,
        }

    previous = trend.loc[idx - 1]

    def _pct(cur: float, prev: float) -> float:
        if prev == 0:
            return 0.0
        return round((cur - prev) / prev * 100, 2)

    return {
        "has_previous": True,
        "current_month": selected_month,
        "previous_month": previous["月份"],
        "expense_delta": round(float(current["支出"] - previous["支出"]), 2),
        "expense_delta_pct": _pct(float(current["支出"]), float(previous["支出"])),
        "income_delta": round(float(current["收入"] - previous["收入"]), 2),
        "income_delta_pct": _pct(float(current["收入"]), float(previous["收入"])),
        "balance_delta": round(float(current["结余"] - previous["结余"]), 2),
        "balance_delta_pct": _pct(float(current["结余"]), float(previous["结余"])),
    }


def monthly_category_share(df: pd.DataFrame) -> pd.DataFrame:
    """按月输出各分类支出金额及占比。"""
    if df.empty:
        return pd.DataFrame(columns=["月份", "分类", "金额", "占比"])

    work = df[df["类型"] == "支出"].copy()
    if work.empty:
        return pd.DataFrame(columns=["月份", "分类", "金额", "占比"])

    if "月份" not in work.columns:
        work["月份"] = pd.to_datetime(work["时间"], errors="coerce").dt.to_period("M").astype(str)

    cat = work.groupby(["月份", "分类"], as_index=False)["金额"].sum()
    month_total = work.groupby("月份", as_index=False)["金额"].sum().rename(columns={"金额": "月支出"})
    out = cat.merge(month_total, on="月份", how="left")
    out["占比"] = out.apply(
        lambda r: round(r["金额"] / r["月支出"] * 100, 2) if r["月支出"] > 0 else 0.0,
        axis=1,
    )
    out = out.drop(columns=["月支出"]).sort_values(["月份", "金额"], ascending=[True, False])
    return out.reset_index(drop=True)


def monthly_rhythm_heatmap(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """输出某月周序号 x 周几的支出热力数据。"""
    if df.empty:
        return pd.DataFrame(columns=["周序", "周几", "金额"])

    work = df[(df["类型"] == "支出") & (df["月份"] == month)].copy()
    if work.empty:
        return pd.DataFrame(columns=["周序", "周几", "金额"])

    dt = pd.to_datetime(work["时间"], errors="coerce")
    work = work[dt.notna()].copy()
    dt = pd.to_datetime(work["时间"], errors="coerce")

    work["日"] = dt.dt.day
    work["周序"] = ((work["日"] - 1) // 7 + 1).astype(int)
    work["周几"] = dt.dt.weekday.astype(int)

    grouped = work.groupby(["周序", "周几"], as_index=False)["金额"].sum()
    weekday_map = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
    grouped["周几"] = grouped["周几"].map(weekday_map)
    return grouped.sort_values(["周序", "周几"]).reset_index(drop=True)


def monthly_insight_digest(df: pd.DataFrame, selected_month: str) -> Dict[str, object]:
    """生成月度洞察摘要，用于卡片和文案。"""
    trend = monthly_trend(df)
    if trend.empty or selected_month not in set(trend["月份"]):
        return {
            "expense_rank": 0,
            "month_count": 0,
            "savings_rank": 0,
            "top_category": "无",
            "top_category_ratio": 0.0,
            "volatility": 0.0,
            "insights": ["当前月份数据不足，无法生成洞察"],
        }

    selected = trend[trend["月份"] == selected_month].iloc[0]
    trend_expense_desc = trend.sort_values("支出", ascending=False).reset_index(drop=True)
    trend_saving_desc = trend.sort_values("储蓄率", ascending=False).reset_index(drop=True)

    expense_rank = int(trend_expense_desc.index[trend_expense_desc["月份"] == selected_month][0] + 1)
    savings_rank = int(trend_saving_desc.index[trend_saving_desc["月份"] == selected_month][0] + 1)
    month_count = int(len(trend))

    month_df = filter_month(df, selected_month)
    cat_df = expense_by_category(month_df)
    if cat_df.empty:
        top_category = "无"
        top_ratio = 0.0
    else:
        top_category = str(cat_df.iloc[0]["分类"])
        total_expense = float(cat_df["金额"].sum())
        top_ratio = round(float(cat_df.iloc[0]["金额"]) / total_expense * 100, 2) if total_expense > 0 else 0.0

    daily = daily_expense_trend(month_df)
    if daily.empty or float(daily["金额"].mean()) == 0:
        volatility = 0.0
    else:
        volatility = round(float(daily["金额"].std(ddof=0) / daily["金额"].mean() * 100), 2)

    insights: List[str] = []
    insights.append(f"本月支出在全部 {month_count} 个月中排名第 {expense_rank}。")
    insights.append(f"本月储蓄率排名第 {savings_rank}，当月结余 ¥{float(selected['结余']):.0f}。")
    insights.append(f"支出集中在 {top_category}，占当月支出 {top_ratio:.1f}%。")
    if volatility > 60:
        insights.append("日度消费波动较大，建议设置周预算并分散大额消费。")
    else:
        insights.append("日度消费波动相对稳定，可继续保持当前节奏。")

    return {
        "expense_rank": expense_rank,
        "month_count": month_count,
        "savings_rank": savings_rank,
        "top_category": top_category,
        "top_category_ratio": top_ratio,
        "volatility": volatility,
        "insights": insights,
    }
