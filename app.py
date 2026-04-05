"""
账本管理系统 v0.6.1 - 企业级财务分析平台

🚀 核心特性：
  ✅ RBAC 企业级权限系统 (7权限细粒度)
  ✅ 24+ 高级分析函数（年度对比、健康评分、异常检测、AI洞察）
  ✅ 现代深空主题 + 玻璃态设计 + 科技视感
  ✅ 实时财务洞察与可执行建议
  ✅ 审计日志追踪
  
📊 新增能力：
  • 财务健康指数 (0-100分级)
  • 异常检测系统 (IQR方法)
  • 智能建议生成 (规则驱动)
  • 预算预测 (3个月展望)
  • 年度对比分析

🎨 UI/UX：
  • 深空主题 (#0a141f)
  • 蓝橙配色系统
  • 玻璃态卡片 + 毛玻璃效果
  • 平滑动画 & 交互反馈
"""

from pathlib import Path
import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# ===== 导入 v0.6 新模块 =====
from src.analytics import (
    anomaly_detection,
    category_budget_forecast,
    consumption_alerts,
    consumption_habit,
    daily_expense_trend,
    expense_by_category,
    expense_by_subcategory,
    expense_health_index,
    filter_month,
    generate_budget_suggestion,
    generate_smart_insights,
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
    year_over_year_comparison,
)
from src.auth import (
    authenticate_user,
    can_export,
    can_manage_users,
    can_upload,
    get_user_permissions,
    PermissionManager,
)
from src.data_pipeline import (
    discover_root_csv_files,
    import_csv_bytes,
    import_csv_file,
    load_master,
)
from src.config import COLORS, FEATURES

# ============ Streamlit 配置 ============
st.set_page_config(
    page_title="账本系统 v0.6.1 | AI财务平台",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ 全局样式（现代深空主题）============
st.markdown(f"""
<style>
    /* 隐藏右上角 Share/菜单等系统控件 */
    #MainMenu {{ visibility: hidden; }}
    [data-testid="stToolbar"] {{ display: none !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}

    /* 深空主题背景 */
    .stApp {{
        background: linear-gradient(135deg, {COLORS['bg_primary']} 0%, {COLORS['bg_secondary']} 50%, {COLORS['bg_primary']} 100%);
        background-attachment: fixed;
        color: {COLORS['text_primary']};
    }}
    
    /* 主容器 */
    [data-testid="stMainBlockContainer"] {{
        background-color: transparent;
    }}
    
    /* 玻璃态卡片效果 */
    [data-testid="stVerticalBlock"] {{
        background: rgba(15, 26, 46, 0.4);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 1px solid rgba(58, 185, 255, 0.1);
    }}
    
    /* 顶部栏 */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: transparent;
        border-bottom: 2px solid rgba(58, 185, 255, 0.2);
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {COLORS['text_secondary']};
        border-bottom: 2px solid transparent;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: {COLORS['accent_blue']};
        border-bottom: 2px solid {COLORS['accent_blue']};
    }}
    
    /* 按钮样式 */
    .stButton > button {{
        background: linear-gradient(135deg, {COLORS['accent_blue']}, {COLORS['accent_purple']});
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['accent_blue']};
        border-radius: 8px;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background: linear-gradient(135deg, {COLORS['accent_purple']}, {COLORS['accent_blue']});
        box-shadow: 0 0 20px rgba(58, 185, 255, 0.5);
        transform: translateY(-2px);
    }}
    
    /* 输入框 */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select {{
        background-color: rgba(15, 26, 46, 0.6);
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: 8px;
    }}
    
    /* 指标卡片 */
    [data-testid="stMetric"] {{
        background: rgba(15, 26, 46, 0.5);
        border: 1px solid {COLORS['border_light']};
        border-radius: 12px;
        padding: 16px;
        transition: all 0.3s ease;
    }}
    
    [data-testid="stMetric"]:hover {{
        background: rgba(15, 26, 46, 0.8);
        border-color: {COLORS['accent_blue']};
        box-shadow: 0 8px 24px rgba(58, 185, 255, 0.2);
    }}
    
    /* 文字样式 */
    h1, h2, h3 {{
        color: {COLORS['text_primary']};
    }}
    
    /* 侧边栏 */
    [data-testid="stSidebar"] {{
        background: rgba(6, 17, 29, 0.8);
        border-right: 1px solid {COLORS['border_light']};
    }}
    
    /* 动画 */
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .metric-card {{
        animation: fadeInUp 0.6s ease;
    }}
</style>
""", unsafe_allow_html=True)

# ============ 常量配置 ============
PROJECT_ROOT = Path(__file__).parent
ARCHIVE_DIR = PROJECT_ROOT / "data" / "archive"
MASTER_FILE = PROJECT_ROOT / "data" / "processed" / "ledger_master.csv"

# ============ 会话初始化 ============
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.session_state.user_perms = []

# ============ 登录/未登录页面 ============
def login_page():
    """现代化登录页面"""
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("---")
        st.markdown(f"""
        <div style='text-align: center; font-size: 48px; margin: 30px 0;'>💳</div>
        <h1 style='text-align: center; font-size: 36px; letter-spacing: 1px;'>账本系统</h1>
        <h2 style='text-align: center; font-size: 18px; opacity: 0.7; font-weight: 400;'>v0.6.1 | AI财务分析平台</h2>
        <p style='text-align: center; color: {COLORS['text_secondary']}; margin-top: 24px;'>
            企业级权限管理 • 智能财务洞察 • 实时异常检测
        </p>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        username = st.text_input("👤 用户名", placeholder="输入用户名", key="login_user")
        password = st.text_input("🔑 密码", type="password", placeholder="输入密码", key="login_pass")
        
        if st.button("🚀 登录", use_container_width=True, key="do_login"):
            if not username or not password:
                st.error("❌ 用户名和密码不能为空")
            else:
                success, user_name, role = authenticate_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_role = role
                    st.session_state.user_perms = get_user_permissions(username)
                    st.success(f"🎉 欢迎, {user_name}!")
                    st.balloons()
                    import time
                    time.sleep(1.2)
                    st.rerun()
                else:
                    st.error("❌ 用户名或密码错误")
        
        st.markdown("---")
        with st.expander("📋 演示账号"):
            st.code("""
cupid / demonCupid2026  (🔑 管理员 - 所有权限)
dad / dad2026          (👁️ 访客 - 仅查看)
mom / mom2026          (👁️ 访客 - 仅查看)
            """)

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ============ 已登录主应用 ============

# ===== 侧边栏 =====
with st.sidebar:
    st.markdown("### 👤 账户信息")
    role_name_map = {
        "admin": "管理员",
        "viewer": "访客",
    }
    
    col_user1, col_user2 = st.columns(2)
    with col_user1:
        st.write(f"**{st.session_state.username}**")
    with col_user2:
        role_badge = "🔑" if st.session_state.user_role == "admin" else "👁️"
        role_text = role_name_map.get(st.session_state.user_role, st.session_state.user_role)
        st.write(f"__{role_badge} {role_text}__")
    
    if st.button("🔐 登出", use_container_width=True, key="do_logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_role = None
        st.session_state.user_perms = []
        st.rerun()
    
    st.markdown("---")
    
    # 数据导入面板 (仅限有权限的用户)
    if can_upload(st.session_state.user_role):
        st.markdown("### 📤 数据导入")
        st.info("你拥有数据上传权限")
        
        upload_choice = st.radio("选择方式", ["单文件上传", "批量扫描"], key="upload_mode")
        
        if upload_choice == "单文件上传":
            uploaded_file = st.file_uploader("选择 CSV 文件", type=["csv"], key="file_upload")
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
                            f"✅ 导入成功！\n"
                            f"• 新增 {result['imported_rows']} 条记录\n"
                            f"• 月份: {', '.join(result['months_saved']) if result['months_saved'] else '无'}"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 导入失败: {str(e)[:80]}")
        
        else:
            if st.button("🔄 批量扫描导入", use_container_width=True, key="do_batch"):
                try:
                    files = discover_root_csv_files(PROJECT_ROOT)
                    if files:
                        for f in files:
                            import_csv_file(f, ARCHIVE_DIR, MASTER_FILE)
                        st.success(f"✅ 批量导入完成 ({len(files)} 个文件)")
                        st.rerun()
                    else:
                        st.warning("⚠️ 未发现 CSV 文件")
                except Exception as e:
                    st.error(f"❌ 批量导入失败: {str(e)[:80]}")
    else:
        st.warning("💼 你是访客账户，仅可查看数据。")
    
    st.markdown("---")
    st.markdown("### 🔗 快速链接")
    col_link1, col_link2 = st.columns(2)
    with col_link1:
        st.link_button("⭐ Star", "https://github.com/Cupid-qrq/personal-account-app/stargazers")
    with col_link2:
        st.link_button("💻 GitHub项目", "https://github.com/Cupid-qrq/personal-account-app")

# ===== 主视图 =====
try:
    master_df = load_master(MASTER_FILE)
except Exception as e:
    st.error(f"❌ 数据加载失败: {str(e)[:100]}")
    st.stop()

if master_df.empty:
    st.warning("⚠️ 暂无数据，请上传账单文件开始使用")
    st.stop()

# 页面标题
st.markdown("""
# 💳 财务分析驾驶舱
**智能消费洞察 · 企业级分析 · v0.6.1**
""")

# 月份选择
months = sorted(master_df["月份"].dropna().unique().tolist())
if not months:
    st.error("❌ 没有有效的月份数据")
    st.stop()

selected_month = st.selectbox("📅 选择分析月份", months, index=len(months)-1, key="month_sel")

month_df = filter_month(master_df, selected_month)
if month_df.empty:
    st.warning(f"⚠️ {selected_month} 没有数据")
    st.stop()

# ===== 核心指标 (v0.6.1 新增：融合多维度信息) =====
st.markdown("---")
st.markdown("### 📊 财务概览 & 智能评分")

overview = monthly_overview(month_df)

# 第一行：基础指标
cols = st.columns(5)
metrics = [
    ("💰 收入", f"¥{overview['income']:.0f}", COLORS['accent_green']),
    ("💸 支出", f"¥{overview['expense']:.0f}", COLORS['accent_red']),
    ("📊 结余", f"¥{overview['balance']:.0f}", COLORS['accent_blue']),
    ("📋 笔数", f"{overview['records']}", COLORS['accent_orange']),
    ("v0.6.1 ✨", "已就绪", COLORS['accent_purple']),
]

for col, (label, value, _) in zip(cols, metrics):
    with col:
        st.metric(label, value)

# 第二行：v0.6+ 新功能（健康评分 + 异常检测 + 智能建议）
st.markdown("---")

if FEATURES["expense_health_index"]:
    health = expense_health_index(master_df)
    efficiency = spending_efficiency_score(month_df)
    
    col_health, col_efficiency, col_insights = st.columns(3, gap="medium")
    
    with col_health:
        st.markdown("#### ❤️ 财务健康指数")
        health_color = "#4caf50" if health["index"] >= 70 else "#ffc107" if health["index"] >= 50 else "#ff6464"
        st.markdown(f"""
        <div style='text-align: center; padding: 20px; border-radius: 12px; 
                    background: rgba({int(health_color[1:3], 16)}, {int(health_color[3:5], 16)}, {int(health_color[5:7], 16)}, 0.15);
                    border: 1px solid {health_color}; margin-bottom: 12px;'>
            <div style='font-size: 48px; font-weight: bold; color: {health_color};'>{health["index"]}</div>
            <div style='font-size: 14px; color: {COLORS['text_secondary']};'>{health["grade"]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**建议:**")
        for rec in health["recommendations"][:2]:
            st.caption(f"💡 {rec}")
    
    with col_efficiency:
        st.markdown("#### 📈 消费效率")
        st.markdown(f"""
        **评分**: {efficiency["score"]:.0f}/100  
        **等级**: {efficiency["level"]}
        """)
        
        cols_detail = st.columns(2)
        for i, (k, v) in enumerate(list(efficiency["details"].items())[:4]):
            with cols_detail[i % 2]:
                st.metric(k, f"{v:.1f}")
    
    with col_insights:
        st.markdown("#### 🧠 智能洞察")
        if FEATURES["smart_insights"]:
            insights = generate_smart_insights(master_df, selected_month)
            for insight in insights["insights"][:2]:
                st.info(f"💡 {insight}", icon="🎯")

# ===== 四维分析中心（v0.5+ 核心，v0.6.1 增强） =====
st.markdown("---")
st.markdown("### 🔍 四维分析中心")

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 趋势与同比",
    "🧩 结构透视",
    "🔥 消费节律",
    "🎯 异常检测"
])

with tab1:
    st.markdown("#### 📈 趋势分析")
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
            st.info("✓ 首个月份，无上月数据")

with tab2:
    st.markdown("#### 🧩 分类结构")
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
    st.markdown("#### 🔥 周期热力分析")
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
        st.info("📬 无足够数据生成热力图")

with tab4:
    st.markdown("#### 🚨 异常检测 (v0.6+ 新增)")
    
    if FEATURES["anomaly_detection"]:
        anomalies = anomaly_detection(month_df)
        
        col_high, col_rare = st.columns(2)
        
        with col_high:
            st.markdown("**超大金额异常**")
            if anomalies["high_amount_anomalies"]:
                for anom in anomalies["high_amount_anomalies"][:5]:
                    anom_date = anom.get("日期") or anom.get("时间") or "未知日期"
                    anom_cat = anom.get("分类", "未分类")
                    anom_amount = float(anom.get("金额", 0.0))
                    st.warning(f"⚠️ {anom_date} | {anom_cat} | **¥{anom_amount:.0f}**")
            else:
                st.success("✓ 无异常")
        
        with col_rare:
            st.markdown("**低频分类**")
            if anomalies["rare_categories"]:
                for cat in anomalies["rare_categories"][:5]:
                    st.info(f"📌 {cat}")
            else:
                st.success("✓ 分类多元充分")

# ===== 详细分析标签页 =====
st.markdown("---")
st.markdown("### 📋 详细分析")

detail_tab1, detail_tab2, detail_tab3, detail_tab4 = st.tabs([
    "💳 支出分析",
    "🔍 消费习惯",
    "📦 详细账目",
    "💼 预算建议"
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
        display_df["金额"] = display_df["金额"].apply(lambda x: f"¥{x:.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

with detail_tab4:
    budget_df = generate_budget_suggestion(month_df)
    if not budget_df.empty:
        display_df = budget_df.copy()
        for col_name in ["本月支出", "建议下月预算"]:
            display_df[col_name] = display_df[col_name].apply(lambda x: f"¥{x:.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# 页脚
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; opacity: 0.6; font-size: 12px; margin-top: 30px;'>
    <p>© 2026 账本管理系统 v0.6.1 | 企业级财务分析平台<br>
    最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 
    用户: {st.session_state.username} | 
    角色: {st.session_state.user_role}</p>
</div>
""", unsafe_allow_html=True)
