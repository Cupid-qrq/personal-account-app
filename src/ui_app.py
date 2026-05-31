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
    account_flow,
    budget_pressure,
    cashflow_statement,
    category_month_matrix,
    category_momentum,
    category_treemap_data,
    daily_cumulative_expense,
    executive_kpis,
    expense_by_category,
    generate_budget_suggestion,
    insight_brief,
    mining_summary,
    monthly_scorecard,
    monthly_category_share,
    monthly_overview,
    pareto_by_category,
    record_density_calendar,
    subcategory_pressure,
    top_transactions,
    transaction_distribution,
    weekday_profile,
)
from src.auth import authenticate_user, can_upload, get_user_permissions
from src.charting import PALETTE, add_reference_band, apply_chart_theme
from src.config import APP_NAME, APP_VERSION
from src.data_pipeline import discover_origin_csv_files
from src.data_service import ORIGIN_DIR, data_status, import_local_file, import_upload, load_ledger, rebuild_all_data
from src.styles import apply_v1_theme
from src.ui_components import chips, dataframe_money, health_bar, hero, insight_card, metric_card, money, note, pct, plain_grade, rank_list, section


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


def _show_chart(fig: go.Figure, height: int = 340, showlegend: bool = True) -> None:
    st.plotly_chart(apply_chart_theme(fig, height=height, showlegend=showlegend), width="stretch")


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
        fig.update_layout(barmode="group")
        _show_chart(fig, height=380)

    with c2:
        section("本月判断", "自动摘要本月财务状态，帮助快速定位需要关注的部分。")
        for item in insight_brief(master_df, selected_month):
            note(item)
        st.markdown("#### 健康指数")
        health_bar(kpis["health_index"])
        st.caption(f"{kpis['health_index']} / 100 · {plain_grade(kpis['health_grade'])}")

    section("月度 Scorecard", "以表格形式同时看收入、支出、结余、储蓄率、环比和累计结余。")
    scorecard = monthly_scorecard(master_df)
    dataframe_money(scorecard, ["收入", "支出", "结余", "累计结余", "结余环比"])


def _render_structure(master_df: pd.DataFrame, selected_month: str) -> None:
    month_df = master_df[master_df["月份"] == selected_month]
    category = expense_by_category(month_df)
    momentum = category_momentum(master_df, selected_month)
    subcat = subcategory_pressure(master_df, selected_month)
    treemap = category_treemap_data(master_df, selected_month)

    c1, c2 = st.columns([0.95, 1.2], gap="large")
    with c1:
        section("分类结构", "观察本月支出构成和集中度。")
        if not category.empty:
            fig = px.pie(category, names="分类", values="金额", hole=0.58, color_discrete_sequence=PALETTE)
            fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="rgba(255,255,255,0.75)", width=2)))
            _show_chart(fig, height=360)
    with c2:
        section("分类动量", "对比上月支出，识别本月增长或收缩的支出类别。")
        dataframe_money(momentum, ["本月支出", "上月支出", "变化"])

    section("二级分类穿透", "从一级分类进入更细颗粒度的消费结构。")
    dataframe_money(subcat, ["金额", "均笔"])

    section("分类空间图", "用 treemap 展示一级与二级分类的面积关系，比传统饼图更适合观察长尾。")
    if not treemap.empty:
        fig = px.treemap(
            treemap,
            path=["分类", "二级分类"],
            values="金额",
            color="金额",
            color_continuous_scale=["#f1e6d6", "#b66d38", "#315f72"],
        )
        fig.update_layout(coloraxis_showscale=False)
        _show_chart(fig, height=420, showlegend=False)


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


def _render_mining(master_df: pd.DataFrame, selected_month: str) -> None:
    top = top_transactions(master_df, selected_month, 10)
    pareto = pareto_by_category(master_df, selected_month)
    distribution = transaction_distribution(master_df, selected_month)
    flow = account_flow(master_df, selected_month)
    matrix = category_month_matrix(master_df)

    section("数据挖掘摘要", "聚合 TopK、Pareto、金额分布和账户流，定位本月最值得关注的消费行为。")
    summary = mining_summary(master_df, selected_month)
    cols = st.columns(max(1, min(3, len(summary))))
    for col, item in zip(cols, summary):
        with col:
            insight_card("Mining Signal", item, "blue")

    c1, c2 = st.columns([1.1, 0.9], gap="large")
    with c1:
        section("TopK 消费记录", "按金额排序的本月最大支出，保留备注、账户和记账者。")
        if top.empty:
            st.info("本月暂无支出记录。")
        else:
            rank_items = [
                (
                    f"{row['分类']} / {row['二级分类']}",
                    money(row["金额"]),
                    f"{row['日期']} · {row.get('备注', '') or '无备注'}",
                )
                for _, row in top.head(6).iterrows()
            ]
            rank_list(rank_items)
    with c2:
        section("金额区间分布", "观察消费是由小额高频驱动，还是由大额低频驱动。")
        if not distribution.empty:
            fig = px.bar(
                distribution,
                x="金额区间",
                y="笔数",
                color="金额",
                text="笔数",
                color_continuous_scale=["#f1e6d6", "#b66d38", "#315f72"],
            )
            fig.update_layout(coloraxis_showscale=False)
            _show_chart(fig, height=360, showlegend=False)

    c3, c4 = st.columns([1, 1], gap="large")
    with c3:
        section("Pareto 贡献", "用累计占比识别真正决定本月支出的少数类别。")
        if not pareto.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=pareto["分类"], y=pareto["金额"], name="金额", marker_color="#b66d38"))
            fig.add_trace(
                go.Scatter(
                    x=pareto["分类"],
                    y=pareto["累计占比"],
                    name="累计占比",
                    yaxis="y2",
                    mode="lines+markers",
                    line=dict(color="#315f72", width=3),
                )
            )
            fig.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 105], ticksuffix="%"))
            add_reference_band(fig, 0, pareto["金额"].max() * 0.8 if len(pareto) else 1)
            _show_chart(fig, height=360)
    with c4:
        section("账户流向", "按账户和收支类型聚合，帮助识别资金来源与支出账户。")
        if not flow.empty:
            fig = px.bar(flow, x="账户", y="金额", color="类型", barmode="group", text="笔数", color_discrete_sequence=PALETTE)
            _show_chart(fig, height=360)

    section("跨月分类矩阵", "每个分类在不同月份的金额分布，适合看长期结构变化。")
    if not matrix.empty:
        heat = matrix.set_index("分类")
        fig = go.Figure(
            data=go.Heatmap(
                z=heat.values,
                x=heat.columns,
                y=heat.index,
                colorscale=[[0, "#f6efe3"], [0.5, "#d6a06a"], [1, "#315f72"]],
                hovertemplate="%{y} · %{x}<br>¥%{z:.0f}<extra></extra>",
            )
        )
        _show_chart(fig, height=360, showlegend=False)


def _render_rhythm(master_df: pd.DataFrame, selected_month: str) -> None:
    daily = daily_cumulative_expense(master_df, selected_month)
    weekday = weekday_profile(master_df, selected_month)
    share = monthly_category_share(master_df)
    calendar = record_density_calendar(master_df, selected_month)

    c1, c2 = st.columns([1.25, 0.9], gap="large")
    with c1:
        section("日度累计", "看本月消费是集中爆发，还是稳定推进。")
        if not daily.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=daily["日期"], y=daily["金额"], name="日支出", marker_color="#d6a06a"))
            fig.add_trace(go.Scatter(x=daily["日期"], y=daily["累计支出"], name="累计支出", mode="lines+markers", line=dict(color="#20201d", width=3)))
            _show_chart(fig, height=360)
    with c2:
        section("星期画像", "识别不同星期的支出密度。")
        if not weekday.empty:
            fig = px.bar(weekday, x="周几", y="金额", text="笔数", color="金额", color_continuous_scale=["#e9dfcf", "#b66d38", "#315f72"])
            fig.update_layout(coloraxis_showscale=False)
            _show_chart(fig, height=360, showlegend=False)

    section("跨月分类占比", "分类结构随月份变化，用于观察长期消费重心是否迁移。")
    if not share.empty:
        fig = px.area(share, x="月份", y="占比", color="分类", groupnorm="percent", color_discrete_sequence=PALETTE)
        _show_chart(fig, height=360)

    section("日历密度", "按周序与星期映射每天支出，呈现本月消费集中日。")
    if not calendar.empty:
        pivot = calendar.pivot(index="周序", columns="周几", values="金额").fillna(0)
        pivot = pivot.reindex(columns=list(range(7)), fill_value=0)
        labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        fig = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=labels,
                y=[f"第{int(i)}周" for i in pivot.index],
                colorscale=[[0, "#f6efe3"], [0.4, "#d6a06a"], [1, "#315f72"]],
                hovertemplate="%{y} %{x}<br>¥%{z:.0f}<extra></extra>",
            )
        )
        _show_chart(fig, height=320, showlegend=False)


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

    tab_overview, tab_structure, tab_mining, tab_pressure, tab_rhythm, tab_data = st.tabs(
        ["总览", "结构", "挖掘", "预算与异常", "节律", "数据室"]
    )

    with tab_overview:
        _render_overview(master_df, selected_month)
    with tab_structure:
        _render_structure(master_df, selected_month)
    with tab_mining:
        _render_mining(master_df, selected_month)
    with tab_pressure:
        _render_pressure(master_df, selected_month)
    with tab_rhythm:
        _render_rhythm(master_df, selected_month)
    with tab_data:
        _render_data_room(master_df, selected_month)

    st.markdown('<div class="v1-rule"></div>', unsafe_allow_html=True)
    st.caption(f"{APP_NAME} {APP_VERSION} · {datetime.now().strftime('%Y-%m-%d %H:%M')} · {st.session_state.username}")


main()
