from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import (
    category_trend,
    consumption_alerts,
    consumption_habit,
    daily_expense_trend,
    expense_by_category,
    expense_by_subcategory,
    filter_month,
    generate_budget_suggestion,
    monthly_overview,
    prepare_detail_table,
    spending_efficiency_score,
    subcategory_by_parent,
    top_expenses,
)
from src.data_pipeline import (
    discover_root_csv_files,
    import_csv_bytes,
    import_csv_file,
    load_master,
)

st.set_page_config(page_title="个人账本分析系统", layout="wide", initial_sidebar_state="expanded")

# ============ 高级 CSS 样式（科技感） ============
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
    }
    
    body {
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        background: linear-gradient(135deg, #0f0f1e 0%, #1a1a3e 50%, #0f0f1e 100%);
        color: #e0e0e0;
    }
    
    /* 毛玻璃卡片容器 */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin: 12px 0;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(104, 211, 255, 0.3);
        box-shadow: 0 12px 48px rgba(104, 211, 255, 0.2);
        transform: translateY(-4px);
    }
    
    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, rgba(104, 211, 255, 0.15), rgba(142, 158, 255, 0.15));
        border: 1px solid rgba(104, 211, 255, 0.3);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        background: linear-gradient(135deg, rgba(104, 211, 255, 0.25), rgba(142, 158, 255, 0.25));
        border-color: rgba(104, 211, 255, 0.6);
        box-shadow: 0 8px 24px rgba(104, 211, 255, 0.2);
        transform: translateY(-3px);
    }
    
    .metric-label {
        font-size: 13px;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
        color: #68d3ff;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #68d3ff 0%, #8e9eff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 8px 0;
    }
    
    /* 警告卡片 */
    .alert-card {
        background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(255, 193, 107, 0.1));
        border-left: 4px solid #ff6b6b;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    
    /* 评分卡 */
    .score-card {
        background: linear-gradient(135deg, rgba(76, 255, 200, 0.1), rgba(104, 211, 255, 0.1));
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
    
    .score-value {
        font-size: 48px;
        font-weight: 700;
        background: linear-gradient(135deg, #4cffc8, #68d3ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .score-level {
        font-size: 14px;
        font-weight: 600;
        margin-top: 8px;
        color: #4cffc8;
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #68d3ff 0%, #8e9eff 100%);
        color: #0f0f1e;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(104, 211, 255, 0.3);
    }
    
    .stButton > button:hover {
        box-shadow: 0 8px 24px rgba(104, 211, 255, 0.5);
        transform: translateY(-2px);
    }
    
    /* 选择框 */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(104, 211, 255, 0.3);
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        background: linear-gradient(135deg, #68d3ff 0%, #4cffc8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
</style>
""", unsafe_allow_html=True)

PROJECT_ROOT = Path(__file__).parent
ARCHIVE_DIR = PROJECT_ROOT / "data" / "archive"
MASTER_FILE = PROJECT_ROOT / "data" / "processed" / "ledger_master.csv"

# Session state
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None
if "detail_expanded" not in st.session_state:
    st.session_state.detail_expanded = False
if "analysis_tab" not in st.session_state:
    st.session_state.analysis_tab = "概览"

# ============ 侧边栏 ============
with st.sidebar:
    st.markdown("## 📊 数据管理中心")
    
    tab1, tab2 = st.tabs(["📤 上传导入", "🔍 批量导入"])
    
    with tab1:
        uploaded = st.file_uploader("选择月度账单 CSV", type=["csv"])
        if uploaded is not None and st.button("✅ 导入数据", key="upload_btn"):
            result = import_csv_bytes(uploaded.getvalue(), ARCHIVE_DIR, MASTER_FILE, uploaded.name)
            st.success(
                f"✓ 成功导入 {result['imported_rows']} 条记录\n"
                f"📅 归档月份: {', '.join(result['months_saved']) or '无'}\n"
                f"📊 主表总数: {result['master_rows']}"
            )
            st.rerun()
    
    with tab2:
        if st.button("🔄 扫描并批量导入", key="batch_btn"):
            files = discover_root_csv_files(PROJECT_ROOT)
            if not files:
                st.info("📭 未发现可导入的 CSV 文件")
            else:
                for f in files:
                    import_csv_file(f, ARCHIVE_DIR, MASTER_FILE)
                st.success(f"✓ 批量导入完成：{len(files)} 个文件")
                st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ 使用说明")
    st.caption("1. 上传或扫描导入月度 CSV\n2. 选择分析月份\n3. 查看详细分析报告\n4. 获取个性化建议")

# ============ 主页面 ============
master_df = load_master(MASTER_FILE)

if master_df.empty:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.error("⚠️ 暂无数据 - 请先在左侧导入账单文件")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# 页面标题
st.markdown("# 💳 个人财务智能分析系统")
st.markdown("*AI 驱动的消费洞察 | 实时风险预警 | 个性化建议*")

months = sorted(master_df["月份"].dropna().unique().tolist())
selected_month = st.selectbox("📅 选择分析月份", options=months, index=len(months) - 1)

month_df = filter_month(master_df, selected_month)
overview = monthly_overview(month_df)

# ============ 概览看板 ============
st.markdown("---")
st.markdown("### 📈 财务概览")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">💰 收入</div>
        <div class="metric-value">¥{overview['income']:.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">💸 支出</div>
        <div class="metric-value">¥{overview['expense']:.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    balance_status = "📈" if overview['balance'] >= 0 else "📉"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{balance_status} 结余</div>
        <div class="metric-value">¥{overview['balance']:.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">📊 记录数</div>
        <div class="metric-value">{overview['records']}</div>
    </div>
    """, unsafe_allow_html=True)

# ============ 核心分析区域 ============
st.markdown("---")

# 获取分析数据
cat_df = expense_by_category(month_df)
subcat_df = expense_by_subcategory(month_df)
daily_df = daily_expense_trend(month_df)
habit = consumption_habit(month_df)
alerts_data = consumption_alerts(month_df)
score_data = spending_efficiency_score(month_df)

# 分析标签页
tab_overview, tab_insight, tab_alerts, tab_detail = st.tabs([
    "🎯 支出分析",
    "🧠 消费洞察",
    "⚠️ 风险预警",
    "📋 详细账目"
])

# ============ TAB 1: 支出分析 ============
with tab_overview:
    st.markdown("### 支出分析仪表板")
    
    # 饼图 + 二级分类柱图（大比例）
    pie_col, bar_col = st.columns([2, 1.5])
    
    with pie_col:
        st.markdown("#### 💳 支出分类占比（点击查看详情）")
        if not cat_df.empty:
            fig_pie = px.pie(
                cat_df,
                names="分类",
                values="金额",
                hole=0.3,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_pie.update_traces(
                hovertemplate="<b>%{label}</b><br>¥%{value:.2f}<br>占比：%{percent}",
                textposition="auto",
                textinfo="label+percent",
                marker=dict(line=dict(color="rgba(15,15,30,0.3)", width=2)),
            )
            fig_pie.update_layout(
                height=500,
                margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0", size=12),
            )
            st.plotly_chart(fig_pie, width='stretch', use_container_width=True)
            
            st.markdown("**分类快捷查看：**")
            cols_cat = st.columns(len(cat_df))
            for idx, (_, row) in enumerate(cat_df.iterrows()):
                with cols_cat[idx]:
                    category = row["分类"]
                    amount = row["金额"]
                    if st.button(f"{category}\n¥{amount:.0f}", key=f"cat_{category}", use_container_width=True):
                        st.session_state.selected_category = category
                        st.rerun()
        else:
            st.info("本月暂无支出数据")
    
    with bar_col:
        st.markdown("#### 🍽️ 二级分类排行")
        if not subcat_df.empty:
            fig_bar = px.bar(
                subcat_df.head(10),
                x="金额",
                y="二级分类",
                orientation="h",
                color="金额",
                color_continuous_scale="Blues",
            )
            fig_bar.update_traces(
                hovertemplate="<b>%{y}</b><br>¥%{x:.2f}",
            )
            fig_bar.update_layout(
                height=500,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"),
            )
            st.plotly_chart(fig_bar, width='stretch', use_container_width=True)
        else:
            st.info("本月暂无支出数据")
    
    # 日趋势图
    st.markdown("#### 📅 每日支出趋势")
    if not daily_df.empty:
        fig_line = px.line(
            daily_df,
            x="日期",
            y="金额",
            markers=True,
            line_shape="spline",
        )
        fig_line.update_traces(
            hovertemplate="<b>%{x}</b><br>¥%{y:.2f}",
            line=dict(color="#68d3ff", width=3),
            marker=dict(size=8, color="#4cffc8"),
        )
        fig_line.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0"),
            hovermode="x unified",
        )
        st.plotly_chart(fig_line, width='stretch', use_container_width=True)
    else:
        st.info("本月暂无支出趋势数据")

# ============ 分类详情展示 ============
if st.session_state.selected_category:
    st.markdown("---")
    st.markdown(f"### 🔍 {st.session_state.selected_category} 分类详情")
    
    subcat_detail = subcategory_by_parent(month_df, st.session_state.selected_category)
    if not subcat_detail.empty:
        detail_col, detail_table = st.columns([2, 1])
        
        with detail_col:
            fig_detail = px.bar(
                subcat_detail,
                x="二级分类",
                y="金额",
                color="金额",
                color_continuous_scale="Viridis",
            )
            fig_detail.update_traces(
                hovertemplate="<b>%{x}</b><br>¥%{y:.2f}",
            )
            fig_detail.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"),
            )
            st.plotly_chart(fig_detail, width='stretch', use_container_width=True)
        
        with detail_table:
            st.markdown("**二级分类汇总**")
            subcat_display = subcat_detail.copy()
            subcat_display["金额"] = subcat_display["金额"].apply(lambda x: f"¥{x:.0f}")
            st.dataframe(subcat_display, width='stretch', hide_index=True, use_container_width=True)
    
    if st.button("❌ 关闭详情"):
        st.session_state.selected_category = None
        st.rerun()

# ============ TAB 2: 消费洞察 ============
with tab_insight:
    st.markdown("### 🧠 AI 消费洞察分析")
    
    insight_col1, insight_col2, insight_col3 = st.columns(3)
    
    with insight_col1:
        st.markdown('<div class="score-card">', unsafe_allow_html=True)
        st.markdown(f"**📊 消费效率评分**")
        st.markdown(f'<div class="score-value">{score_data["score"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="score-level">{score_data["level"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("#### 💡 改进建议")
        for tip in score_data["tips"]:
            st.write(f"• {tip}")
    
    with insight_col2:
        st.markdown("#### 📈 消费习惯")
        st.metric("总支出", f"¥{habit.get('total_expense', 0):.0f}")
        st.metric("平均日消费", f"¥{habit.get('avg_daily_expense', 0):.0f}")
        st.metric("平均单笔", f"¥{habit.get('avg_per_transaction', 0):.0f}")
        st.metric("消费天数", f"{habit.get('expense_days', 0)} 天")
    
    with insight_col3:
        st.markdown("#### 🏆 消费偏好")
        st.write(f"**最高频分类：** {habit.get('most_freq_category', '无')}")
        st.write(f"**频次：** {habit.get('most_freq_count', 0)} 笔")
        st.write(f"**数据完整度：** {len(month_df)} 条记录")
        st.write(f"**本月储蓄率：** {round((overview['balance']/overview['income']*100) if overview['income'] > 0 else 0, 1)}%")
    
    # 评分详情
    st.markdown("#### 📊 评分细项")
    score_cols = st.columns(4)
    for idx, (key, val) in enumerate(score_data["details"].items()):
        with score_cols[idx]:
            st.metric(key, f"{val:.1f}分")

# ============ TAB 3: 风险预警 ============
with tab_alerts:
    st.markdown("### ⚠️ 财务风险预警")
    
    alert_col1, alert_col2 = st.columns(2)
    
    with alert_col1:
        st.markdown("#### 📊 日均消费分析")
        st.metric("日均支出", f"¥{alerts_data['daily_avg']:.2f}")
        st.metric("消费波动度", f"¥{alerts_data['daily_std']:.2f}")
        st.metric("最高消费日", alerts_data['highest_day'])
        st.metric("最高单日支出", f"¥{alerts_data['highest_day_amount']:.2f}")
    
    with alert_col2:
        st.markdown("#### 🎯 预警阈值说明")
        st.info(
            f"超过 ¥{alerts_data['daily_avg'] + alerts_data['daily_std']:.2f} 的日支出将触发预警\n\n"
            f"当日支出显著高于日均水平时，系统会自动标记"
        )
    
    if alerts_data['alerts']:
        st.markdown("#### 🚨 异常支出记录")
        for alert in alerts_data['alerts']:
            st.markdown(f"""
            <div class="alert-card">
                <b>{alert['类型']}</b> | 📅 {alert['日期']} | 💰 ¥{alert['金额']:.2f} | 
                偏差 +¥{alert['偏差']:.2f}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✓ 本月消费稳定，无异常预警")

# ============ TAB 4: 详细账目 ============
with tab_detail:
    st.markdown("### 📝 原始交易详情")
    
    if st.button("📂 展开/收起账目明细", key="detail_toggle"):
        st.session_state.detail_expanded = not st.session_state.detail_expanded
    
    if st.session_state.detail_expanded:
        detail_df = prepare_detail_table(month_df)
        if not detail_df.empty:
            detail_display = detail_df.copy()
            detail_display["金额"] = detail_display["金额"].apply(lambda x: f"¥{x:.2f}")
            st.dataframe(detail_display, width='stretch', hide_index=True, use_container_width=True)
        else:
            st.info("本月暂无支出明细")
    else:
        st.info("💼 点击上方按钮展开交易明细")
    
    # 其他分析卡片
    st.markdown("---")
    st.markdown("#### 💡 其他分析")
    
    other_col1, other_col2 = st.columns(2)
    
    with other_col1:
        st.markdown("**🔥 Top10 高额支出**")
        top_df = top_expenses(month_df, 10)
        if not top_df.empty:
            display_df = top_df.copy()
            display_df["金额"] = display_df["金额"].apply(lambda x: f"¥{x:.2f}")
            st.dataframe(display_df, width='stretch', hide_index=True, use_container_width=True)
        else:
            st.info("本月暂无支出数据")
    
    with other_col2:
        st.markdown("**💡 下月预算建议**")
        budget_df = generate_budget_suggestion(month_df)
        if not budget_df.empty:
            display_df = budget_df.copy()
            display_df["本月支出"] = display_df["本月支出"].apply(lambda x: f"¥{x:.2f}")
            display_df["建议下月预算"] = display_df["建议下月预算"].apply(lambda x: f"¥{x:.2f}")
            st.dataframe(display_df, width='stretch', hide_index=True, use_container_width=True)
        else:
            st.info("本月暂无支出数据")
