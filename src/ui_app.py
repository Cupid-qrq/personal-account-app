"""
账本管理系统 v0.9 - 智能财务分析平台

核心特性:
  RBAC 权限系统 (3角色7权限)
  24+ 高级分析函数 (年度对比、健康评分、异常检测、AI洞察)
  深空科技主题 / 玻璃态卡片 / 响应式布局
  实时财务洞察与可执行建议
  SQLite 主数据层 / CSV 归档镜像
"""

from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from src.analytics import (
    anomaly_detection,
    consumption_habit,
    expense_by_category,
    expense_health_index,
    filter_month,
    generate_budget_suggestion,
    generate_smart_insights,
    month_over_month,
    monthly_category_share,
    monthly_rhythm_heatmap,
    monthly_trend,
    monthly_overview,
    prepare_detail_table,
    spending_efficiency_score,
)
from src.auth import (
    authenticate_user,
    can_upload,
    get_user_permissions,
    is_auth_configured,
)
from src.data_pipeline import (
    discover_root_csv_files,
    import_csv_bytes,
    import_csv_file,
    load_master,
)
from src.config import APP_NAME, APP_VERSION, COLORS, FEATURES

st.set_page_config(
    page_title=f"{APP_NAME} {APP_VERSION} | SQLite 财务平台",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

VERSION_TAG = APP_VERSION

st.markdown(f"""
<style>
    #MainMenu {{ visibility: hidden; }}
    [data-testid="stToolbar"] {{ display: none !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}

    .stApp {{
        background:
            radial-gradient(ellipse at 15% 0%, rgba(41, 152, 255, 0.10), transparent 42%),
            radial-gradient(ellipse at 85% 5%, rgba(167, 139, 250, 0.08), transparent 40%),
            linear-gradient(180deg, {COLORS['bg_primary']} 0%, {COLORS['bg_secondary']} 100%);
        background-attachment: fixed;
        color: {COLORS['text_primary']};
    }}

    [data-testid="stMainBlockContainer"] {{
        background-color: transparent;
        max-width: 1200px;
        padding-top: 1rem;
    }}

    .hero-shell {{
        border: 1px solid {COLORS['border_normal']};
        border-radius: 14px;
        padding: 20px 28px;
        margin: 0 0 20px 0;
        background: linear-gradient(105deg, rgba(13, 26, 43, 0.85) 0%, rgba(9, 18, 30, 0.70) 100%);
        backdrop-filter: blur(10px);
        box-shadow: {COLORS['shadow_soft']};
    }}

    .hero-title {{
        font-size: 1.6rem;
        font-weight: 700;
        line-height: 1.2;
        letter-spacing: 0.2px;
        color: {COLORS['text_primary']};
        margin: 0;
    }}

    .hero-sub {{
        margin-top: 6px;
        color: {COLORS['text_secondary']};
        font-size: 0.88rem;
        line-height: 1.5;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent;
        border-bottom: 1px solid {COLORS['border_light']};
        gap: 0;
    }}

    .stTabs [data-baseweb="tab"] {{
        color: {COLORS['text_secondary']};
        font-size: 0.88rem;
        padding: 8px 16px;
        border-radius: 8px 8px 0 0;
        margin-right: 2px;
        transition: all 0.2s ease;
    }}

    .stTabs [aria-selected="true"] {{
        color: {COLORS['accent_blue']};
        background: rgba(41, 152, 255, 0.08);
        border-bottom: 2px solid {COLORS['accent_blue']};
    }}

    .stButton > button {{
        background: linear-gradient(135deg, {COLORS['accent_blue']}, {COLORS['accent_purple']});
        color: #fff;
        border: none;
        border-radius: 8px;
        transition: all 0.25s ease;
        font-weight: 600;
        font-size: 0.85rem;
    }}

    .stButton > button:hover {{
        background: linear-gradient(135deg, #3aadff, #b99eff);
        box-shadow: 0 0 18px rgba(41, 152, 255, 0.35);
        transform: translateY(-1px);
    }}

    .stButton > button:disabled {{
        opacity: 0.45;
        transform: none;
        box-shadow: none;
    }}

    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {{
        background-color: rgba(13, 26, 43, 0.55);
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 8px;
        font-size: 0.9rem;
    }}

    [data-testid="stMetric"] {{
        background: rgba(13, 26, 43, 0.45);
        border: 1px solid {COLORS['border_light']};
        border-radius: 12px;
        padding: 14px 16px;
        transition: all 0.25s ease;
    }}

    [data-testid="stMetric"]:hover {{
        background: rgba(13, 26, 43, 0.7);
        border-color: {COLORS['accent_blue']};
        box-shadow: 0 4px 20px rgba(41, 152, 255, 0.12);
    }}

    h2, h3, h4 {{
        color: {COLORS['text_primary']};
    }}

    [data-testid="stSidebar"] {{
        background: rgba(6, 13, 23, 0.85);
        border-right: 1px solid {COLORS['border_light']};
        backdrop-filter: blur(8px);
    }}

    [data-testid="stSidebar"] .stMarkdown {{
        color: {COLORS['text_secondary']};
    }}

    hr {{
        border-color: {COLORS['border_light']};
        margin: 0.8rem 0;
    }}

    .stAlert {{
        border-radius: 10px;
        font-size: 0.88rem;
    }}
</style>
""", unsafe_allow_html=True)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = PROJECT_ROOT / "data" / "archive"
MASTER_FILE = PROJECT_ROOT / "data" / "processed" / "ledger_master.csv"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.user_perms = []
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "configured"

AUTH_READY = is_auth_configured()


def login_page():
    """现代化登录页面"""
    col1, col2, col3 = st.columns([1, 1.25, 1])

    with col2:
        st.markdown(f"""
        <div class="hero-shell" style="text-align: center;">
            <div style="font-size: 36px; margin: 0 0 8px 0;">&nbsp;</div>
            <h1 class="hero-title">{APP_NAME}</h1>
            <div class="hero-sub">{VERSION_TAG} &middot; 智能财务分析平台</div>
            <div class="hero-sub">企业级权限管理 &middot; 多维数据洞察 &middot; 实时异常检测</div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("用户名", placeholder="输入用户名", key="login_user")
        password = st.text_input("密码", type="password", placeholder="输入密码", key="login_pass")

        if st.button("登录", use_container_width=True, key="do_login"):
            if not username or not password:
                st.error("用户名和密码不能为空")
            else:
                success, user_name, role = authenticate_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_role = role
                    st.session_state.user_perms = get_user_permissions(username)
                    st.session_state.auth_mode = "configured"
                    st.success(f"欢迎, {user_name}!")
                    st.rerun()
                else:
                    st.error("用户名或密码错误")


if not st.session_state.logged_in:
    login_page()
    st.stop()

with st.sidebar:
    st.markdown("### 账户信息")
    role_name_map = {
        "admin": "管理员",
        "editor": "编辑者",
        "viewer": "访客",
    }

    col_user1, col_user2 = st.columns(2)
    with col_user1:
        st.write(f"**{st.session_state.username}**")
    with col_user2:
        role_text = role_name_map.get(st.session_state.user_role, st.session_state.user_role)
        st.write(f"__{role_text}__")

    if st.button("登出", use_container_width=True, key="do_logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_role = None
        st.session_state.user_perms = []
        st.session_state.auth_mode = "configured"
        st.rerun()

    st.markdown("---")

    if can_upload(st.session_state.user_role):
        st.markdown("### 数据导入")

        upload_choice = st.radio("选择方式", ["单文件上传", "批量扫描"], key="upload_mode")

        if upload_choice == "单文件上传":
            uploaded_file = st.file_uploader("选择 CSV 文件", type=["csv"], key="file_upload")
            if st.button("导入", use_container_width=True, key="do_upload"):
                if uploaded_file:
                    try:
                        result = import_csv_bytes(
                            uploaded_file.getvalue(),
                            ARCHIVE_DIR,
                            MASTER_FILE,
                            uploaded_file.name,
                        )
                        st.success(
                            f"导入成功！\n"
                            f"新增 {result['imported_rows']} 条记录\n"
                            f"月份: {', '.join(result['months_saved']) if result['months_saved'] else '无'}"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"导入失败: {str(e)[:80]}")

        else:
            if st.button("批量扫描导入", use_container_width=True, key="do_batch"):
                try:
                    files = discover_root_csv_files(PROJECT_ROOT)
                    if files:
                        for f in files:
                            import_csv_file(f, ARCHIVE_DIR, MASTER_FILE)
                        st.success(f"批量导入完成 ({len(files)} 个文件)")
                        st.rerun()
                    else:
                        st.warning("未发现 CSV 文件")
                except Exception as e:
                    st.error(f"批量导入失败: {str(e)[:80]}")
    else:
        st.info("当前角色为只读模式，无上传权限。")

    st.markdown("---")
    st.markdown("### 链接")
    col_link1, col_link2 = st.columns(2)
    with col_link1:
        st.link_button("Star", "https://github.com/Cupid-qrq/personal-account-app/stargazers")
    with col_link2:
        st.link_button("GitHub", "https://github.com/Cupid-qrq/personal-account-app")

try:
    master_df = load_master(MASTER_FILE)
except Exception as e:
    st.error(f"数据加载失败: {str(e)[:100]}")
    st.stop()

if master_df.empty:
    st.warning("暂无数据，请上传账单文件开始使用")
    st.stop()

st.markdown(f"""
<div class="hero-shell">
    <p class="hero-title">财务分析驾驶舱</p>
    <p class="hero-sub">{VERSION_TAG} &middot; 智能消费洞察 &middot; 企业级分析</p>
</div>
""", unsafe_allow_html=True)

months = sorted(master_df["月份"].dropna().unique().tolist())
if not months:
    st.error("没有有效的月份数据")
    st.stop()

selected_month = st.selectbox("分析月份", months, index=len(months) - 1, key="month_sel")

month_df = filter_month(master_df, selected_month)
if month_df.empty:
    st.warning(f"{selected_month} 没有数据")
    st.stop()

st.markdown("---")
st.markdown("### 财务概览")

overview = monthly_overview(month_df)

cols = st.columns(5)
metrics = [
    ("收入", f"¥{overview['income']:.0f}", COLORS['accent_green']),
    ("支出", f"¥{overview['expense']:.0f}", COLORS['accent_red']),
    ("结余", f"¥{overview['balance']:.0f}", COLORS['accent_blue']),
    ("笔数", f"{overview['records']}", COLORS['accent_orange']),
    (f"{VERSION_TAG}", "已就绪", COLORS['accent_purple']),
]

for col, (label, value, _) in zip(cols, metrics):
    with col:
        st.metric(label, value)

st.markdown("---")

if FEATURES["expense_health_index"]:
    health = expense_health_index(master_df)
    efficiency = spending_efficiency_score(month_df)

    col_health, col_efficiency, col_insights = st.columns(3, gap="medium")

    with col_health:
        st.markdown("#### 财务健康指数")
        health_color = COLORS['accent_green'] if health["index"] >= 70 else COLORS['accent_yellow'] if health["index"] >= 50 else COLORS['accent_red']
        st.markdown(f"""
        <div style='text-align: center; padding: 20px; border-radius: 12px; 
                    background: rgba({int(health_color[1:3], 16)}, {int(health_color[3:5], 16)}, {int(health_color[5:7], 16)}, 0.15);
                    border: 1px solid {health_color}; margin-bottom: 12px;'>
            <div style='font-size: 48px; font-weight: bold; color: {health_color};'>{health["index"]}</div>
            <div style='font-size: 14px; color: {COLORS['text_secondary']};'>{health['grade']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**建议:**")
        for rec in health["recommendations"][:2]:
            st.caption(rec)

    with col_efficiency:
        st.markdown("#### 消费效率")
        st.markdown(f"""
        **评分**: {efficiency["score"]:.0f}/100  
        **等级**: {efficiency["level"]}
        """)

        cols_detail = st.columns(2)
        for i, (k, v) in enumerate(list(efficiency["details"].items())[:4]):
            with cols_detail[i % 2]:
                st.metric(k, f"{v:.1f}")

    with col_insights:
        st.markdown("#### 智能洞察")
        if FEATURES["smart_insights"]:
            insights = generate_smart_insights(master_df, selected_month)
            for insight in insights["insights"][:2]:
                st.info(insight)

st.markdown("---")
st.markdown("### 分析中心")

tab1, tab2, tab3, tab4 = st.tabs([
    "趋势与同比",
    "结构透视",
    "消费节律",
    "异常检测",
])

with tab1:
    st.markdown("#### 趋势分析")
    monthly_df = monthly_trend(master_df)
    mom_data = month_over_month(master_df, selected_month)

    col_trend, col_mom = st.columns([2, 1], gap="large")

    with col_trend:
        trend_long = monthly_df.melt(
            id_vars="月份",
            value_vars=["收入", "支出", "结余"],
            var_name="指标",
            value_name="金额",
        )
        try:
            fig = px.line(trend_long, x="月份", y="金额", color="指标", markers=True, line_shape="spline")
            fig.update_layout(
                height=350,
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0.05)",
                font=dict(color=COLORS['text_primary']),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.warning("趋势图渲染失败，已降级为表格展示。")
            st.dataframe(trend_long, use_container_width=True, hide_index=True)

    with col_mom:
        st.markdown("#### 环比变化")
        if mom_data["has_previous"]:
            st.metric("支出环比", f"¥{mom_data['expense_delta']:+.0f}", f"{mom_data['expense_delta_pct']:+.1f}%")
            st.metric("收入环比", f"¥{mom_data['income_delta']:+.0f}", f"{mom_data['income_delta_pct']:+.1f}%")
            st.metric("结余环比", f"¥{mom_data['balance_delta']:+.0f}", f"{mom_data['balance_delta_pct']:+.1f}%")
        else:
            st.info("首个月份，无上月数据")

with tab2:
    st.markdown("#### 分类结构")
    share_df = monthly_category_share(master_df)

    if not share_df.empty:
        col_stack, col_pie = st.columns(2)

        with col_stack:
            fig_area = px.area(share_df, x="月份", y="占比", color="分类", groupnorm="percent")
            fig_area.update_layout(
                height=300,
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0.05)",
                font=dict(color=COLORS['text_primary']),
            )
            st.plotly_chart(fig_area, use_container_width=True)

        with col_pie:
            month_cat_df = monthly_category_share(master_df)
            current_month_cat = month_cat_df[month_cat_df["月份"] == selected_month]
            if not current_month_cat.empty:
                fig_pie = px.pie(current_month_cat, names="分类", values="金额", hole=0.4)
                fig_pie.update_layout(
                    height=300,
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=COLORS['text_primary']),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.markdown("#### 周期热力分析")
    rhythm_df = monthly_rhythm_heatmap(master_df, selected_month)

    if not rhythm_df.empty:
        pivot = rhythm_df.pivot(index="周序", columns="周几", values="金额").fillna(0.0)
        weekday_order = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        pivot = pivot.reindex(columns=weekday_order, fill_value=0.0)

        fig_heat = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=weekday_order,
                y=[f"第{int(i)}周" for i in pivot.index],
                colorscale="Viridis",
                hovertemplate="%{y} %{x}<br>¥%{z:.2f}<extra></extra>",
            )
        )
        fig_heat.update_layout(
            height=300,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLORS['text_primary']),
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("无足够数据生成热力图")

with tab4:
    st.markdown("#### 异常检测")

    if FEATURES["anomaly_detection"]:
        anomalies = anomaly_detection(month_df)

        col_high, col_rare = st.columns(2)

        with col_high:
            st.markdown("**大额异常**")
            if anomalies["high_amount_anomalies"]:
                for anom in anomalies["high_amount_anomalies"][:5]:
                    anom_date = anom.get("日期") or anom.get("时间") or "未知日期"
                    anom_cat = anom.get("分类", "未分类")
                    anom_amount = float(anom.get("金额", 0.0))
                    st.warning(f"{anom_date} | {anom_cat} | **¥{anom_amount:.0f}**")
            else:
                st.success("无异常")

        with col_rare:
            st.markdown("**低频分类**")
            if anomalies["rare_categories"]:
                for cat in anomalies["rare_categories"][:5]:
                    st.info(cat)
            else:
                st.success("分类多元充分")

st.markdown("---")
st.markdown("### 明细分析")

detail_tab1, detail_tab2, detail_tab3, detail_tab4 = st.tabs([
    "支出分析",
    "消费习惯",
    "详细账目",
    "预算建议",
])

with detail_tab1:
    cat_df = expense_by_category(month_df)
    if not cat_df.empty:
        col_cat1, col_cat2 = st.columns(2)

        with col_cat1:
            fig_pie = px.pie(cat_df, names="分类", values="金额", title="支出占比")
            fig_pie.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS['text_primary']))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_cat2:
            fig_bar = px.bar(cat_df, x="金额", y="分类", orientation="h", title="分类金额排行")
            fig_bar.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS['text_primary']), showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

with detail_tab2:
    habit = consumption_habit(month_df)
    st.markdown("#### 消费行为指标")

    cols = st.columns(4)
    cols[0].metric("总支出", f"¥{habit.get('total_expense', 0):.0f}")
    cols[1].metric("平均单笔", f"¥{habit.get('avg_per_transaction', 0):.0f}")
    cols[2].metric("日均消费", f"¥{habit.get('avg_daily_expense', 0):.0f}")
    cols[3].metric("消费天数", f"{habit.get('expense_days', 0)}")

    st.markdown(f"**最常支出分类**: {habit.get('most_freq_category', '无')} (共 {habit.get('most_freq_count', 0)} 次)")

with detail_tab3:
    detail_df = prepare_detail_table(month_df)
    if not detail_df.empty:
        display_df = detail_df.copy()
        display_df["金额"] = pd.to_numeric(display_df["金额"], errors="coerce").fillna(0.0)
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "金额": st.column_config.NumberColumn("金额", format="¥ %.2f"),
            },
        )

with detail_tab4:
    budget_df = generate_budget_suggestion(month_df)
    if not budget_df.empty:
        display_df = budget_df.copy()
        for col_name in ["本月支出", "建议下月预算"]:
            display_df[col_name] = pd.to_numeric(display_df[col_name], errors="coerce").fillna(0.0)
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "本月支出": st.column_config.NumberColumn("本月支出", format="¥ %.2f"),
                "建议下月预算": st.column_config.NumberColumn("建议下月预算", format="¥ %.2f"),
            },
        )

st.markdown("---")
st.markdown(f"""
<div style='text-align: center; opacity: 0.5; font-size: 11px; margin-top: 40px; color: {COLORS['text_subdue']};'>
    <p>{APP_NAME} {VERSION_TAG} &middot; SQLite 财务分析平台<br>
    {datetime.now().strftime('%Y-%m-%d %H:%M')} &middot;
    {st.session_state.username} &middot;
    {st.session_state.user_role}</p>
</div>
""", unsafe_allow_html=True)
