"""个人账本分析系统 v0.6 交互增强版。"""

from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.analytics import (
    consumption_alerts,
    consumption_habit,
    daily_expense_trend,
    expense_by_category,
    expense_by_subcategory,
    filter_month,
    generate_budget_suggestion,
    month_over_month,
    monthly_category_share,
    monthly_insight_digest,
    monthly_rhythm_heatmap,
    monthly_trend,
    monthly_overview,
    prepare_detail_table,
    spending_efficiency_score,
    subcategory_by_parent,
    top_expenses,
)
from src.auth import authenticate_user, can_upload
from src.data_pipeline import (
    discover_root_csv_files,
    import_csv_bytes,
    import_csv_file,
    load_master,
)

# ============ Streamlit 配置 ============
st.set_page_config(
    page_title="个人账本 | v0.5",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ 全局样式 ============
st.markdown("""
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    .stApp {
        background:
            radial-gradient(circle at 8% 18%, rgba(58, 185, 255, 0.16), transparent 38%),
            radial-gradient(circle at 86% 20%, rgba(255, 171, 69, 0.14), transparent 35%),
            linear-gradient(135deg, #0b0f19 0%, #121a29 48%, #0f1828 100%);
        background-attachment: fixed;
    }

    .hero-wrap {
        position: relative;
        margin: 8px 0 14px 0;
        padding: 18px 20px;
        border-radius: 16px;
        border: 1px solid rgba(117, 210, 255, 0.26);
        background: linear-gradient(125deg, rgba(18, 30, 50, 0.75), rgba(26, 44, 74, 0.58));
        overflow: hidden;
        transform-style: preserve-3d;
        perspective: 900px;
    }

    .hero-wrap::before,
    .hero-wrap::after {
        content: "";
        position: absolute;
        border-radius: 50%;
        filter: blur(2px);
        animation: floatOrb 10s ease-in-out infinite;
    }

    .hero-wrap::before {
        width: 140px;
        height: 140px;
        right: -30px;
        top: -30px;
        background: rgba(115, 201, 255, 0.28);
    }

    .hero-wrap::after {
        width: 110px;
        height: 110px;
        left: -25px;
        bottom: -25px;
        background: rgba(255, 176, 87, 0.24);
        animation-delay: 2s;
    }

    .hero-title {
        position: relative;
        z-index: 2;
        font-size: 24px;
        font-weight: 800;
        color: #d8ecff;
        letter-spacing: 0.6px;
    }

    .hero-sub {
        position: relative;
        z-index: 2;
        margin-top: 6px;
        font-size: 13px;
        color: #9bc4e6;
    }

    .metric-card {
        background: linear-gradient(145deg, rgba(93, 189, 243, 0.13), rgba(79, 122, 255, 0.09));
        border: 1px solid rgba(114, 205, 255, 0.27);
        border-radius: 12px;
        padding: 14px;
        text-align: center;
        transform: perspective(800px) rotateX(0deg) rotateY(0deg);
        transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
        box-shadow: 0 8px 22px rgba(5, 14, 30, 0.35);
        animation: fadeInUp .45s ease both;
    }

    .metric-card:hover {
        transform: perspective(800px) rotateX(6deg) rotateY(-6deg) translateY(-3px);
        border-color: rgba(155, 228, 255, 0.48);
        box-shadow: 0 18px 32px rgba(18, 34, 69, 0.55);
    }

    .metric-value {
        font-size: 26px;
        font-weight: bold;
        color: #7fd9ff;
    }

    .metric-label {
        font-size: 11px;
        color: #9bb0c8;
        margin-bottom: 6px;
    }

    .info-chip {
        display: inline-block;
        margin-right: 8px;
        margin-top: 6px;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid rgba(123, 199, 255, 0.24);
        background: rgba(102, 171, 255, 0.12);
        color: #b9dcff;
        font-size: 11px;
    }

    .alert-card {
        background: rgba(255, 100, 100, 0.06);
        border-left: 4px solid #ff6464;
        border-radius: 8px;
        padding: 10px;
        margin: 6px 0;
        font-size: 12px;
    }

    @keyframes floatOrb {
        0% { transform: translateY(0px); }
        50% { transform: translateY(10px); }
        100% { transform: translateY(0px); }
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 768px) {
        .metric-value { font-size: 18px; }
        .metric-label { font-size: 10px; }
        .hero-title { font-size: 18px; }
        .hero-sub { font-size: 12px; }
    }
</style>
""", unsafe_allow_html=True)

# ============ 常量配置 ============
PROJECT_ROOT = Path(__file__).parent
ARCHIVE_DIR = PROJECT_ROOT / "data" / "archive"
MASTER_FILE = PROJECT_ROOT / "data" / "processed" / "ledger_master.csv"

# ============ 会话初始化 ============
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# ============ 登录页 ============
if not st.session_state.logged_in:
    # 居中布局
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("---")
        st.markdown("## 💳 账本系统")
        st.markdown("### 请登录")
        st.markdown("")
        
        # 输入框
        username = st.text_input("用户名", key="login_user", value="")
        password = st.text_input("密码", type="password", key="login_pass", value="")
        
        # 登录按钮
        if st.button("🔓 登录", use_container_width=True, key="do_login"):
            if not username or not password:
                st.error("❌ 用户名和密码不能为空")
            else:
                success, user_name, role = authenticate_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_role = role
                    st.success(f"✓ 欢迎, {user_name}!")
                    st.balloons()
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ 账户或密码错误")
        
        st.markdown("---")
        st.info("""
        **演示账号:**
        - cupid / demonCupid2026 (管理员)
        - dad / dad2026 (访客)
        - mom / mom2026 (访客)
        """)
    
    st.stop()

# ============ 已登录主应用 ============

# ===== 侧边栏 =====
with st.sidebar:
    st.markdown("### 👤 账户信息")
    st.write(f"**用户:** {st.session_state.username}")
    role_text = "🔑 管理员" if st.session_state.user_role == "admin" else "👁️ 访客"
    st.write(f"**角色:** {role_text}")
    
    # 登出按钮
    if st.button("🔐 登出", use_container_width=True, key="do_logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_role = None
        st.rerun()
    
    st.markdown("---")
    
    # 管理员面板
    if can_upload(st.session_state.user_role):
        st.markdown("### 📤 数据导入")
        
        upload_choice = st.radio("选择方式", ["单个上传", "批量扫描"], key="upload_mode")
        
        if upload_choice == "单个上传":
            uploaded_file = st.file_uploader("选择 CSV", type=["csv"], key="file_upload")
            if st.button("✅ 导入", use_container_width=True, key="do_upload"):
                if uploaded_file:
                    try:
                        result = import_csv_bytes(
                            uploaded_file.getvalue(),
                            ARCHIVE_DIR,
                            MASTER_FILE,
                            uploaded_file.name
                        )
                        st.success(
                            f"✓ 导入 {result['imported_rows']} 条\n"
                            f"月份: {', '.join(result['months_saved']) if result['months_saved'] else '无'}"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 导入失败: {str(e)[:100]}")
                else:
                    st.warning("⚠️ 请先选择文件")
        
        else:  # 批量扫描
            if st.button("🔄 扫描导入", use_container_width=True, key="do_batch"):
                try:
                    files = discover_root_csv_files(PROJECT_ROOT)
                    if files:
                        for f in files:
                            import_csv_file(f, ARCHIVE_DIR, MASTER_FILE)
                        st.success(f"✓ 导入 {len(files)} 个文件")
                        st.rerun()
                    else:
                        st.info("📭 未发现 CSV")
                except Exception as e:
                    st.error(f"❌ 批量导入失败: {str(e)[:100]}")
    else:
        st.info("💼 您是访客账户，仅可查看数据。")
    
    st.markdown("---")
    st.markdown("### 🔗 链接")
    col_link1, col_link2 = st.columns(2)
    with col_link1:
        st.link_button("⭐ GitHub", "https://github.com/Cupid-qrq/personal-account-app")
    with col_link2:
        st.markdown("[📖 README](https://github.com/Cupid-qrq/personal-account-app)")

# ===== 主页面 =====
try:
    master_df = load_master(MASTER_FILE)
except Exception as e:
    st.error(f"❌ 数据加载失败: {str(e)[:100]}")
    st.stop()

if master_df.empty:
    st.warning("⚠️ 暂无数据，请上传账单文件")
    st.stop()

# 页面标题
st.markdown("# 💳 财务分析系统")
st.markdown("*智能消费洞察 v0.5*")
st.markdown(
    """
    <div class="hero-wrap">
        <div class="hero-title">消费雷达与财务驾驶舱</div>
        <div class="hero-sub">从月度结构、节律与风险信号中挖掘真正可执行的消费洞察</div>
        <span class="info-chip">3D 卡片动效</span>
        <span class="info-chip">多维月度分析</span>
        <span class="info-chip">异常信号识别</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# 月份选择
months = sorted(master_df["月份"].dropna().unique().tolist())
if not months:
    st.warning("⚠️ 没有有效的月份数据")
    st.stop()

selected_month = st.selectbox("📅 选择月份", months, index=len(months)-1, key="month_sel")

# 数据过滤
month_df = filter_month(master_df, selected_month)
if month_df.empty:
    st.warning(f"⚠️ {selected_month} 没有数据")
    st.stop()

overview = monthly_overview(month_df)

# ===== 概览指标 =====
st.markdown("---")
st.markdown("### 📊 财务概览")

cols = st.columns(4)
metrics_data = [
    ("💰 收入", f"¥{overview['income']:.0f}"),
    ("💸 支出", f"¥{overview['expense']:.0f}"),
    ("📊 结余", f"¥{overview['balance']:.0f}"),
    ("📋 记录数", f"{overview['records']}"),
]

for col, (label, value) in zip(cols, metrics_data):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

# ===== 数据预处理 =====
cat_df = expense_by_category(month_df)
subcat_df = expense_by_subcategory(month_df)
daily_df = daily_expense_trend(month_df)
habit = consumption_habit(month_df)
alerts_data = consumption_alerts(month_df)
score_data = spending_efficiency_score(month_df)
monthly_df = monthly_trend(master_df)
mom_data = month_over_month(master_df, selected_month)
share_df = monthly_category_share(master_df)
rhythm_df = monthly_rhythm_heatmap(master_df, selected_month)
digest = monthly_insight_digest(master_df, selected_month)

# ===== 月度对比 =====
st.markdown("---")
st.markdown("### 📆 月度洞察中心")

if not monthly_df.empty:
    mt1, mt2, mt3, mt4 = st.tabs(["📈 趋势总览", "🧩 结构透视", "🔥 消费节律", "🧠 智能洞察"])

    with mt1:
        col_month_chart, col_month_metric = st.columns([2, 1])

        with col_month_chart:
            trend_long = monthly_df.melt(
                id_vars="月份",
                value_vars=["收入", "支出", "结余"],
                var_name="指标",
                value_name="金额",
            )
            fig_month = px.line(
                trend_long,
                x="月份",
                y="金额",
                color="指标",
                markers=True,
                line_shape="spline",
            )
            fig_month.update_layout(
                height=330,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"),
                legend_title_text="",
            )
            st.plotly_chart(fig_month, use_container_width=True)

        with col_month_metric:
            selected_row = monthly_df[monthly_df["月份"] == selected_month]
            if not selected_row.empty:
                savings_rate = float(selected_row.iloc[0]["储蓄率"])
                st.metric("当月储蓄率", f"{savings_rate:.1f}%")

            if mom_data["has_previous"]:
                st.metric(
                    f"支出环比 ({mom_data['previous_month']}→{selected_month})",
                    f"¥{mom_data['expense_delta']:+.0f}",
                    f"{mom_data['expense_delta_pct']:+.1f}%",
                )
                st.metric(
                    "收入环比",
                    f"¥{mom_data['income_delta']:+.0f}",
                    f"{mom_data['income_delta_pct']:+.1f}%",
                )
                st.metric(
                    "结余环比",
                    f"¥{mom_data['balance_delta']:+.0f}",
                    f"{mom_data['balance_delta_pct']:+.1f}%",
                )
            else:
                st.info("当前月份没有上月可比较")

    with mt2:
        if not share_df.empty:
            col_stack, col_3d = st.columns([1.3, 1])

            with col_stack:
                fig_area = px.area(
                    share_df,
                    x="月份",
                    y="占比",
                    color="分类",
                    groupnorm="percent",
                )
                fig_area.update_layout(
                    height=330,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e0e0e0"),
                    yaxis_title="分类占比(%)",
                )
                st.plotly_chart(fig_area, use_container_width=True)

            with col_3d:
                share_3d = share_df.copy()
                months_order = sorted(share_3d["月份"].unique().tolist())
                share_3d["月序"] = share_3d["月份"].apply(lambda m: months_order.index(m) + 1)
                fig_3d = px.scatter_3d(
                    share_3d,
                    x="月序",
                    y="分类",
                    z="金额",
                    color="占比",
                    size="金额",
                    color_continuous_scale="Tealgrn",
                )
                fig_3d.update_layout(
                    height=330,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    scene=dict(
                        bgcolor="rgba(0,0,0,0)",
                        xaxis_title="月序",
                        yaxis_title="分类",
                        zaxis_title="金额",
                    ),
                    font=dict(color="#e0e0e0"),
                )
                st.plotly_chart(fig_3d, use_container_width=True)

    with mt3:
        if not rhythm_df.empty:
            pivot = rhythm_df.pivot(index="周序", columns="周几", values="金额").fillna(0.0)
            weekday_order = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            pivot = pivot.reindex(columns=weekday_order, fill_value=0.0)
            z_values = pivot.values.tolist()

            fig_heat = go.Figure(
                data=go.Heatmap(
                    z=z_values,
                    x=weekday_order,
                    y=[f"第{int(i)}周" for i in pivot.index.tolist()],
                    colorscale="YlGnBu",
                    hovertemplate="%{y} %{x}<br>金额: ¥%{z:.2f}<extra></extra>",
                )
            )
            fig_heat.update_layout(
                height=320,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"),
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("该月支出记录不足，无法生成节律热力图")

    with mt4:
        c1, c2, c3 = st.columns(3)
        c1.metric("支出强度排名", f"{digest['expense_rank']}/{digest['month_count']}")
        c2.metric("储蓄率排名", f"{digest['savings_rank']}/{digest['month_count']}")
        c3.metric("日波动系数", f"{digest['volatility']:.1f}%")

        st.markdown(f"**支出最集中的分类**: {digest['top_category']} ({digest['top_category_ratio']:.1f}%)")
        st.markdown("**本月洞察结论**")
        for item in digest["insights"]:
            st.caption(f"• {item}")

    with st.expander("查看月度汇总表"):
        display_monthly = monthly_df.copy()
        for c in ["收入", "支出", "结余"]:
            display_monthly[c] = display_monthly[c].apply(lambda x: f"¥{x:.2f}")
        display_monthly["储蓄率"] = display_monthly["储蓄率"].apply(lambda x: f"{x:.2f}%")
        st.dataframe(display_monthly, use_container_width=True, hide_index=True)

# ===== 分析标签页 =====
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 支出分析",
    "🧠 消费洞察",
    "⚠️ 风险预警",
    "📋 详细账目"
])

# TAB 1: 支出分析
with tab1:
    st.subheader("支出分析")
    
    if not cat_df.empty:
        col_pie, col_bar = st.columns([2, 1.5])
        
        # 饼图
        with col_pie:
            st.markdown("#### 💳 支出占比")
            fig_pie = px.pie(cat_df, names="分类", values="金额", hole=0.3)
            fig_pie.update_layout(height=400, margin=dict(l=0,r=0,t=0,b=0),
                                 paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 font=dict(color="#e0e0e0"))
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # 分类选择器（用 selectbox 避免重复 key）
            st.markdown("#### 📋 选择分类查看")
            cat_list = [""] + cat_df["分类"].tolist()
            selected_cat = st.selectbox("分类", cat_list, key="cat_select", 
                                       format_func=lambda x: "-- 选择 --" if x == "" else x)
            
            if selected_cat:
                subcat_detail = subcategory_by_parent(month_df, selected_cat)
                if not subcat_detail.empty:
                    st.markdown(f"**{selected_cat} 详情:**")
                    display_df = subcat_detail.copy()
                    display_df["金额"] = display_df["金额"].apply(lambda x: f"¥{x:.2f}")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # 柱图
        with col_bar:
            st.markdown("#### 🍽️ 次分类排行")
            if not subcat_df.empty:
                fig_bar = px.bar(subcat_df.head(8), x="金额", y="二级分类", orientation="h",
                                color="金额", color_continuous_scale="Blues")
                fig_bar.update_layout(height=400, margin=dict(l=0,r=0,t=0,b=0),
                                     paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                     font=dict(color="#e0e0e0"), showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # 趋势图
        st.markdown("#### 📅 日趋势")
        if not daily_df.empty:
            fig_line = px.line(daily_df, x="日期", y="金额", markers=True, line_shape="spline")
            fig_line.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0),
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#e0e0e0"))
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("📭 无支出数据")

# TAB 2: 消费洞察
with tab2:
    st.subheader("消费洞察")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 效率评分")
        st.markdown(f'**{score_data["score"]}分** - {score_data["level"]}')
        st.markdown("**建议:**")
        for tip in score_data["tips"][:2]:
            st.caption(f"• {tip}")
    
    with col2:
        st.markdown("#### 消费指标")
        metric_cols = st.columns(2)
        with metric_cols[0]:
            st.metric("总支出", f"¥{habit.get('total_expense', 0):.0f}")
            st.metric("平均单笔", f"¥{habit.get('avg_per_transaction', 0):.0f}")
        with metric_cols[1]:
            st.metric("日均消费", f"¥{habit.get('avg_daily_expense', 0):.0f}")
            st.metric("消费天数", f"{habit.get('expense_days', 0)}天")

# TAB 3: 风险预警
with tab3:
    st.subheader("风险预警")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("日均支出", f"¥{alerts_data['daily_avg']:.2f}")
        st.metric("最高消费日", alerts_data['highest_day'])
    with col2:
        st.metric("波动度", f"¥{alerts_data['daily_std']:.2f}")
        st.metric("单日最高", f"¥{alerts_data['highest_day_amount']:.2f}")
    
    st.markdown("#### 异常警告")
    if alerts_data['alerts']:
        for alert in alerts_data['alerts'][:5]:
            st.markdown(f"""
            <div class="alert-card">
            {alert['类型']} | {alert['日期']} | <b>¥{alert['金额']:.2f}</b>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✓ 消费正常")

# TAB 4: 详细账目
with tab4:
    st.subheader("详细账目")
    
    detail_tabs = st.tabs(["📊 汇总", "🔥 Top10", "💡 预算", "📝 原始"])
    
    with detail_tabs[0]:
        st.markdown("**分类汇总**")
        display_df = cat_df.copy()
        display_df["金额"] = display_df["金额"].apply(lambda x: f"¥{x:.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    with detail_tabs[1]:
        st.markdown("**高额支出排行**")
        top_df = top_expenses(month_df, 10)
        if not top_df.empty:
            display_df = top_df.copy()
            display_df["金额"] = display_df["金额"].apply(lambda x: f"¥{x:.2f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    with detail_tabs[2]:
        st.markdown("**下月预算建议**")
        budget_df = generate_budget_suggestion(month_df)
        if not budget_df.empty:
            display_df = budget_df.copy()
            display_df["本月支出"] = display_df["本月支出"].apply(lambda x: f"¥{x:.2f}")
            display_df["建议下月预算"] = display_df["建议下月预算"].apply(lambda x: f"¥{x:.2f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    with detail_tabs[3]:
        st.markdown("**原始明细**")
        detail_df = prepare_detail_table(month_df)
        if not detail_df.empty:
            display_df = detail_df.copy()
            display_df["金额"] = display_df["金额"].apply(lambda x: f"¥{x:.2f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("© 2026 个人财务分析系统 v0.5 | 月度分析增强版")
