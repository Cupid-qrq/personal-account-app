"""
账本管理系统 v1.0 - Streamlit 财务分析工作台。

v1.0 目标：
  - Notebook / Claude 风格的现代信息工作台
  - SQLite 主库 + CSV 快照 + origin 全量重建
  - 多维现金流、分类动量、预算压力、节律和数据质量分析
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import (
    anomaly_table,
    budget_pressure,
    cashflow_statement,
    category_momentum,
    daily_cumulative_expense,
    executive_kpis,
    expense_by_category,
    generate_budget_suggestion,
    insight_brief,
    monthly_category_share,
    monthly_overview,
    subcategory_pressure,
    weekday_profile,
)
from src.auth import authenticate_user, can_upload, get_user_permissions
from src.config import APP_NAME, APP_VERSION
from src.data_pipeline import discover_origin_csv_files
from src.data_service import ORIGIN_DIR, data_status, import_local_file, import_upload, load_ledger, rebuild_all_data
from src.styles import apply_v1_theme
from src.ui_components import chips, dataframe_money, health_bar, hero, metric_card, money, note, pct, plain_grade, section


st.set_page_config(
    page_title=f"{APP_NAME} {APP_VERSION}",
    page_icon="◧",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_v1_theme()


def _file_stamp() -> tuple[float, float]:
    from src.data_service import DB_FILE, MASTER_FILE

    master_stamp = MASTER_FILE.stat().st_mtime if MASTER_FILE.exists() else 0
    db_stamp = DB_FILE.stat().st_mtime if DB_FILE.exists() else 0
    return master_stamp, db_stamp


@st.cache_data(show_spinner=False)
def _load_cached(_stamp: tuple[float, float]) -> pd.DataFrame:
    return load_ledger()


def _plot_layout(height: int = 330) -> dict:
    return {
        "height": height,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(255,255,255,0.36)",
        "font": {"family": "IBM Plex Sans, Microsoft YaHei, sans-serif", "color": "#161513"},
        "margin": {"l": 10, "r": 10, "t": 30, "b": 20},
        "legend": {"orientation": "h", "y": 1.08, "x": 0},
    }


def _login_page() -> None:
    left, center, right = st.columns([0.8, 1.1, 0.8])
    with center:
        st.markdown(
            """
<div class="v1-card">
  <div class="v1-kicker">Ledger Access</div>
  <h1 class="v1-title" style="font-size:3.4rem;">账本工作台</h1>
  <p class="v1-subtitle">登录后查看现金流、预算压力、分类结构和数据质量。默认账号仅用于初始部署，线上建议用 Secrets 覆盖。</p>
</div>
            """,
            unsafe_allow_html=True,
        )
        username = st.text_input("用户名", placeholder="admin / parent", key="login_user")
        password = st.text_input("密码", type="password", placeholder="输入密码", key="login_pass")
        if st.button("登录", key="do_login", width="stretch"):
            if not username or not password:
                st.error("用户名和密码不能为空")
                return
            success, user_name, role = authenticate_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_role = role
                st.session_state.user_perms = get_user_permissions(username)
                st.success(f"欢迎, {user_name}")
                st.rerun()
            st.error("用户名或密码错误")


def _format_import_result(result: dict) -> str:
    months = ", ".join(result.get("months_saved", [])) if result.get("months_saved") else "无"
    return (
        f"扫描 {result.get('raw_rows', 0)} 条，规范化 {result.get('normalized_rows', 0)} 条；"
        f"新增 {result.get('new_rows', 0)} 条，覆盖 {result.get('updated_rows', 0)} 条；"
        f"主表共 {result.get('master_rows', 0)} 条；月份：{months}"
    )


def _init_session() -> None:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_role = None
        st.session_state.user_perms = []


def _render_sidebar(master_df: pd.DataFrame) -> None:
    status = data_status(master_df)
    profile = status["profile"]
    storage = status["storage"]

    with st.sidebar:
        st.markdown("### 账户")
        role_name = {"admin": "管理员", "editor": "编辑者", "viewer": "访客"}.get(
            st.session_state.user_role,
            st.session_state.user_role,
        )
        st.write(f"**{st.session_state.username}**")
        st.caption(f"{role_name} · {APP_VERSION}")
        if st.button("登出", key="do_logout", width="stretch"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_role = None
            st.session_state.user_perms = []
            st.rerun()

        st.markdown("---")
        st.markdown("### 数据控制台")
        st.caption(f"主表 {profile['rows']} 条 · CSV {storage.get('csv_rows')} · SQLite {storage.get('sqlite_rows')}")

        if status["warnings"]:
            for warning in status["warnings"]:
                st.warning(warning)
        else:
            st.success("数据一致性正常")

        if can_upload(st.session_state.user_role):
            uploaded_file = st.file_uploader("上传账单 CSV", type=["csv"], key="file_upload")
            if st.button("导入上传文件", key="do_upload", width="stretch"):
                if not uploaded_file:
                    st.warning("请先选择 CSV 文件")
                else:
                    try:
                        result = import_upload(uploaded_file.getvalue(), uploaded_file.name)
                        st.cache_data.clear()
                        st.success(_format_import_result(result))
                        st.rerun()
                    except Exception as exc:
                        st.error(f"导入失败: {str(exc)[:120]}")

            origin_files = discover_origin_csv_files(ORIGIN_DIR)
            if origin_files:
                selected_file = st.selectbox("导入 origin 文件", origin_files, format_func=lambda p: p.name)
                if st.button("导入选中文件", key="import_origin", width="stretch"):
                    result = import_local_file(selected_file)
                    st.cache_data.clear()
                    st.success(_format_import_result(result))
                    st.rerun()

            if st.button("从 data/origin 全量重建", key="rebuild_all", width="stretch"):
                result = rebuild_all_data()
                st.cache_data.clear()
                st.success(
                    f"重建完成：{len(result['source_files'])} 个源文件，"
                    f"主表 {result['master_rows']} 条，月份 {', '.join(result['months_saved'])}"
                )
                st.rerun()
        else:
            st.info("当前角色为只读模式。")

        st.markdown("---")
        st.markdown("### 快捷链接")
        st.link_button("线上应用", "https://my-account.streamlit.app/", width="stretch")
        st.link_button("GitHub", "https://github.com/Cupid-qrq/personal-account-app", width="stretch")


def _render_kpis(kpis: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Income", money(kpis["income"]), f"本月收入 · 储蓄率 {kpis['savings_rate']:.1f}%")
    with c2:
        metric_card("Expense", money(kpis["expense"]), f"环比 {pct(kpis['expense_delta_pct'])} · 排名 {kpis['expense_rank']}/{kpis['month_count']}")
    with c3:
        metric_card("Balance", money(kpis["balance"]), f"结余变化 {money(kpis['expense_delta'] * -1)}")
    with c4:
        metric_card("Records", f"{kpis['records']}", f"健康指数 {kpis['health_index']} · {plain_grade(kpis['health_grade'])}")


def _render_overview(master_df: pd.DataFrame, selected_month: str) -> None:
    kpis = executive_kpis(master_df, selected_month)
    _render_kpis(kpis)

    c1, c2 = st.columns([1.35, 0.9], gap="large")
    with c1:
        section("现金流曲线", "收入、支出、结余和累计结余，用于观察资金节奏和月度趋势。")
        cashflow = cashflow_statement(master_df)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cashflow["月份"], y=cashflow["收入"], name="收入", marker_color="#60735f"))
        fig.add_trace(go.Bar(x=cashflow["月份"], y=cashflow["支出"], name="支出", marker_color="#b66d38"))
        fig.add_trace(go.Scatter(x=cashflow["月份"], y=cashflow["累计结余"], name="累计结余", mode="lines+markers", line=dict(color="#315f72", width=3)))
        fig.update_layout(**_plot_layout(380), barmode="group")
        st.plotly_chart(fig, width="stretch")

    with c2:
        section("本月判断", "自动摘要本月财务状态，帮助快速定位需要关注的部分。")
        for item in insight_brief(master_df, selected_month):
            note(item)
        st.markdown("#### 健康指数")
        health_bar(kpis["health_index"])
        st.caption(f"{kpis['health_index']} / 100 · {plain_grade(kpis['health_grade'])}")


def _render_structure(master_df: pd.DataFrame, selected_month: str) -> None:
    month_df = master_df[master_df["月份"] == selected_month]
    category = expense_by_category(month_df)
    momentum = category_momentum(master_df, selected_month)
    subcat = subcategory_pressure(master_df, selected_month)

    c1, c2 = st.columns([0.95, 1.2], gap="large")
    with c1:
        section("分类结构", "观察本月支出构成和集中度。")
        if not category.empty:
            fig = px.pie(category, names="分类", values="金额", hole=0.58, color_discrete_sequence=["#b66d38", "#60735f", "#315f72", "#8f6f4f"])
            fig.update_layout(**_plot_layout(360), showlegend=True)
            st.plotly_chart(fig, width="stretch")
    with c2:
        section("分类动量", "对比上月支出，识别本月增长或收缩的支出类别。")
        dataframe_money(momentum, ["本月支出", "上月支出", "变化"])

    section("二级分类穿透", "从一级分类进入更细颗粒度的消费结构。")
    dataframe_money(subcat, ["金额", "均笔"])


def _render_pressure(master_df: pd.DataFrame, selected_month: str) -> None:
    pressure = budget_pressure(master_df, selected_month)
    anomalies = anomaly_table(master_df, selected_month)
    budget = generate_budget_suggestion(master_df[master_df["月份"] == selected_month])

    c1, c2 = st.columns([1.1, 0.9], gap="large")
    with c1:
        section("预算压力", "用历史月均估计建议预算，标记接近上限或超预算的类别。")
        dataframe_money(pressure, ["本月支出", "历史月均", "建议预算"])
    with c2:
        section("预算建议", "面向下一月的基础预算草案。")
        dataframe_money(budget, ["本月支出", "建议下月预算"])

    section("异常交易", "基于 IQR 的大额异常检测，适合快速排查明显偏离项。")
    if anomalies.empty:
        st.success("本月没有检测到大额异常。")
    else:
        dataframe_money(anomalies, ["金额"])


def _render_rhythm(master_df: pd.DataFrame, selected_month: str) -> None:
    daily = daily_cumulative_expense(master_df, selected_month)
    weekday = weekday_profile(master_df, selected_month)
    share = monthly_category_share(master_df)

    c1, c2 = st.columns([1.25, 0.9], gap="large")
    with c1:
        section("日度累计", "看本月消费是集中爆发，还是稳定推进。")
        if not daily.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=daily["日期"], y=daily["金额"], name="日支出", marker_color="#d6a06a"))
            fig.add_trace(go.Scatter(x=daily["日期"], y=daily["累计支出"], name="累计支出", mode="lines+markers", line=dict(color="#20201d", width=3)))
            fig.update_layout(**_plot_layout(360))
            st.plotly_chart(fig, width="stretch")
    with c2:
        section("星期画像", "识别不同星期的支出密度。")
        if not weekday.empty:
            fig = px.bar(weekday, x="周几", y="金额", text="笔数", color="金额", color_continuous_scale=["#e9dfcf", "#b66d38", "#315f72"])
            fig.update_layout(**_plot_layout(360), showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, width="stretch")

    section("跨月分类占比", "分类结构随月份变化，用于观察长期消费重心是否迁移。")
    if not share.empty:
        fig = px.area(share, x="月份", y="占比", color="分类", groupnorm="percent", color_discrete_sequence=["#b66d38", "#60735f", "#315f72", "#8f6f4f"])
        fig.update_layout(**_plot_layout(360))
        st.plotly_chart(fig, width="stretch")


def _render_data_room(master_df: pd.DataFrame, selected_month: str) -> None:
    status = data_status(master_df)
    profile = status["profile"]
    storage = status["storage"]
    month_df = master_df[master_df["月份"] == selected_month].copy()
    month_df["金额"] = pd.to_numeric(month_df["金额"], errors="coerce").fillna(0.0)

    section("数据资产", "查看主库规模、月份覆盖、存储一致性和明细。")
    chips(
        [
            f"主表 {profile['rows']} 条",
            f"月份 {len(profile['months'])} 个",
            f"CSV {storage.get('csv_rows')}",
            f"SQLite {storage.get('sqlite_rows')}",
            "一致" if storage.get("in_sync") else "需修复",
        ]
    )
    if status["warnings"]:
        for warning in status["warnings"]:
            st.warning(warning)
    else:
        st.success("数据质量检查通过。")

    section("本月明细", "保留关键字段，便于快速追踪来源账单。")
    keep = ["时间", "分类", "二级分类", "类型", "金额", "备注", "记账者"]
    dataframe_money(month_df[keep].sort_values("时间", ascending=False), ["金额"])


def main() -> None:
    _init_session()
    if not st.session_state.logged_in:
        _login_page()
        st.stop()

    master_df = _load_cached(_file_stamp())
    if master_df.empty:
        st.warning("暂无数据，请上传账单文件开始使用。")
        st.stop()

    _render_sidebar(master_df)

    months = sorted(master_df["月份"].dropna().unique().tolist())
    default_month = months[-1]

    hero(
        "账本智能工作台",
        "把账单从原始 CSV 到 SQLite 主库、月度归档、现金流分析、预算压力和异常检测串成一个可审计的个人财务系统。",
        [f"{APP_VERSION}", f"{len(master_df)} 条记录", f"{months[0]} 至 {months[-1]}", "SQLite 主库", "CSV 快照"],
    )

    selected_month = st.selectbox("分析月份", months, index=months.index(default_month), key="month_sel")
    selected_overview = monthly_overview(master_df[master_df["月份"] == selected_month])
    st.caption(
        f"{selected_month} · 收入 {money(selected_overview['income'])} · "
        f"支出 {money(selected_overview['expense'])} · 结余 {money(selected_overview['balance'])}"
    )

    tab_overview, tab_structure, tab_pressure, tab_rhythm, tab_data = st.tabs(
        ["总览", "结构", "预算与异常", "节律", "数据室"]
    )

    with tab_overview:
        _render_overview(master_df, selected_month)
    with tab_structure:
        _render_structure(master_df, selected_month)
    with tab_pressure:
        _render_pressure(master_df, selected_month)
    with tab_rhythm:
        _render_rhythm(master_df, selected_month)
    with tab_data:
        _render_data_room(master_df, selected_month)

    st.markdown('<div class="v1-rule"></div>', unsafe_allow_html=True)
    st.caption(f"{APP_NAME} {APP_VERSION} · {datetime.now().strftime('%Y-%m-%d %H:%M')} · {st.session_state.username}")


main()
