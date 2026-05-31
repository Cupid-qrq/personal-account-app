from __future__ import annotations

import streamlit as st


def apply_v1_theme() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,500;6..72,650&display=swap');

:root {
    --paper: #f7f3ea;
    --paper-soft: #fbf8f1;
    --ink: #161513;
    --muted: #6f6a60;
    --hairline: rgba(31, 29, 24, 0.12);
    --hairline-strong: rgba(31, 29, 24, 0.22);
    --graphite: #20201d;
    --graphite-2: #30302b;
    --copper: #b66d38;
    --moss: #60735f;
    --blueprint: #315f72;
    --signal: #0b6bcb;
    --danger: #b14a3b;
}

.stApp {
    background:
        linear-gradient(90deg, rgba(22, 21, 19, 0.035) 1px, transparent 1px),
        linear-gradient(180deg, rgba(22, 21, 19, 0.03) 1px, transparent 1px),
        radial-gradient(circle at 50% -20%, rgba(182, 109, 56, 0.16), transparent 32%),
        linear-gradient(180deg, var(--paper-soft), var(--paper));
    background-size: 42px 42px, 42px 42px, auto, auto;
    color: var(--ink);
    font-family: 'IBM Plex Sans', 'Microsoft YaHei', sans-serif;
}

#MainMenu,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
header[data-testid="stHeader"] {
    display: none !important;
}

[data-testid="stMainBlockContainer"] {
    max-width: 1280px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--graphite), var(--graphite-2));
    border-right: 1px solid rgba(255,255,255,0.08);
}

[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.86);
}

.v1-topline {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 18px;
    padding: 18px 0 8px 0;
}

.v1-kicker {
    color: var(--copper);
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.v1-title {
    margin: 6px 0 0 0;
    color: var(--ink);
    font-family: 'Newsreader', 'SimSun', serif;
    font-size: clamp(2.25rem, 5vw, 5rem);
    font-weight: 650;
    line-height: 0.92;
    letter-spacing: 0;
}

.v1-subtitle {
    max-width: 760px;
    margin: 14px 0 0 0;
    color: var(--muted);
    font-size: 0.98rem;
    line-height: 1.62;
}

.v1-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 18px;
}

.v1-chip {
    display: inline-flex;
    align-items: center;
    min-height: 28px;
    padding: 5px 10px;
    border: 1px solid var(--hairline);
    border-radius: 999px;
    background: rgba(255,255,255,0.42);
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 600;
}

.v1-rule {
    height: 1px;
    background: linear-gradient(90deg, var(--hairline-strong), transparent);
    margin: 24px 0 18px 0;
}

.v1-card {
    border: 1px solid var(--hairline);
    border-radius: 8px;
    background: rgba(255,255,255,0.58);
    box-shadow: 0 18px 55px rgba(30, 27, 23, 0.08);
    padding: 18px;
}

.v1-insight {
    border: 1px solid var(--hairline);
    border-radius: 8px;
    padding: 14px 15px;
    margin-bottom: 10px;
    background: rgba(255,255,255,0.54);
    box-shadow: 0 10px 34px rgba(30, 27, 23, 0.06);
}

.v1-insight-accent {
    border-color: rgba(182, 109, 56, 0.35);
    background: linear-gradient(135deg, rgba(182, 109, 56, 0.11), rgba(255,255,255,0.55));
}

.v1-insight-blue {
    border-color: rgba(49, 95, 114, 0.32);
    background: linear-gradient(135deg, rgba(49, 95, 114, 0.11), rgba(255,255,255,0.55));
}

.v1-insight-title {
    color: var(--ink);
    font-size: 0.78rem;
    font-weight: 750;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.v1-insight-body {
    margin-top: 7px;
    color: var(--muted);
    font-size: 0.9rem;
    line-height: 1.48;
}

.v1-metric {
    min-height: 142px;
    border: 1px solid var(--hairline);
    border-radius: 8px;
    padding: 18px;
    background:
        linear-gradient(180deg, rgba(255,255,255,0.74), rgba(255,255,255,0.42));
    box-shadow: 0 12px 42px rgba(30, 27, 23, 0.07);
}

.v1-metric-label {
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.v1-metric-value {
    margin-top: 10px;
    color: var(--ink);
    font-family: 'Newsreader', 'SimSun', serif;
    font-size: 2.2rem;
    line-height: 1;
    letter-spacing: 0;
}

.v1-metric-caption {
    margin-top: 12px;
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.35;
}

.v1-rank-list {
    border: 1px solid var(--hairline);
    border-radius: 8px;
    overflow: hidden;
    background: rgba(255,255,255,0.48);
}

.v1-rank-row {
    display: grid;
    grid-template-columns: 46px 1fr auto;
    gap: 12px;
    align-items: center;
    padding: 12px 14px;
    border-bottom: 1px solid var(--hairline);
}

.v1-rank-row:last-child {
    border-bottom: 0;
}

.v1-rank-index {
    color: var(--copper);
    font-family: 'Newsreader', 'SimSun', serif;
    font-size: 1.2rem;
    font-weight: 650;
}

.v1-rank-title {
    color: var(--ink);
    font-size: 0.92rem;
    font-weight: 700;
}

.v1-rank-caption {
    margin-top: 3px;
    color: var(--muted);
    font-size: 0.78rem;
}

.v1-rank-value {
    color: var(--ink);
    font-family: 'Newsreader', 'SimSun', serif;
    font-size: 1.1rem;
    font-weight: 650;
}

.v1-section {
    margin-top: 26px;
    margin-bottom: 12px;
}

.v1-section h2 {
    margin: 0;
    color: var(--ink);
    font-family: 'Newsreader', 'SimSun', serif;
    font-size: 1.65rem;
    letter-spacing: 0;
}

.v1-section p {
    margin: 6px 0 0 0;
    color: var(--muted);
    font-size: 0.9rem;
    line-height: 1.5;
}

.v1-note {
    border-left: 3px solid var(--copper);
    padding: 10px 12px;
    background: rgba(182, 109, 56, 0.08);
    color: var(--ink);
    font-size: 0.9rem;
    line-height: 1.55;
}

.v1-healthbar {
    width: 100%;
    height: 10px;
    overflow: hidden;
    border-radius: 999px;
    background: rgba(22, 21, 19, 0.09);
}

.v1-healthbar > div {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--moss), var(--signal));
}

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 1px solid var(--hairline);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    color: var(--muted);
    font-weight: 650;
}

.stTabs [aria-selected="true"] {
    background: rgba(255,255,255,0.6);
    color: var(--ink);
    border-bottom: 2px solid var(--copper);
}

.stButton > button,
.stDownloadButton > button {
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.16);
    background: var(--graphite);
    color: white;
    font-weight: 700;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: var(--copper);
    background: #11110f;
}

[data-testid="stMetric"] {
    border: 1px solid var(--hairline);
    border-radius: 8px;
    background: rgba(255,255,255,0.5);
    padding: 14px;
}

hr {
    border-color: var(--hairline);
}
</style>
        """,
        unsafe_allow_html=True,
    )
