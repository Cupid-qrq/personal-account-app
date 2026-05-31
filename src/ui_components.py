from __future__ import annotations

from typing import Iterable

import pandas as pd
import streamlit as st


def _streamlit_minor_version() -> tuple[int, int]:
    parts = st.__version__.split(".")[:2]
    try:
        return int(parts[0]), int(parts[1])
    except (IndexError, ValueError):
        return (0, 0)


def stretch_kwargs() -> dict[str, object]:
    if _streamlit_minor_version() >= (1, 56):
        return {"width": "stretch"}
    return {"use_container_width": True}


def money(value: float) -> str:
    return f"¥{float(value):,.0f}"


def pct(value: float) -> str:
    return f"{float(value):+.1f}%"


def plain_grade(text: str) -> str:
    return (
        str(text)
        .replace("🌟", "")
        .replace("✅", "")
        .replace("⚠️", "")
        .replace("❌", "")
        .replace("💡", "")
        .replace("📊", "")
        .replace("🎯", "")
        .replace("✨", "")
        .strip()
    )


def chips(items: Iterable[str]) -> None:
    html = "".join(f'<span class="v1-chip">{item}</span>' for item in items)
    st.markdown(f'<div class="v1-chip-row">{html}</div>', unsafe_allow_html=True)


def hero(title: str, subtitle: str, chips_items: Iterable[str]) -> None:
    st.markdown(
        f"""
<div class="v1-topline">
  <div>
    <div class="v1-kicker">Personal Ledger OS</div>
    <h1 class="v1-title">{title}</h1>
    <p class="v1-subtitle">{subtitle}</p>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    chips(chips_items)
    st.markdown('<div class="v1-rule"></div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, caption: str) -> None:
    st.markdown(
        f"""
<div class="v1-metric">
  <div class="v1-metric-label">{label}</div>
  <div class="v1-metric-value">{value}</div>
  <div class="v1-metric-caption">{caption}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(title: str, body: str, tone: str = "neutral") -> None:
    st.markdown(
        f"""
<div class="v1-insight v1-insight-{tone}">
  <div class="v1-insight-title">{title}</div>
  <div class="v1-insight-body">{body}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def rank_list(items: list[tuple[str, str, str]]) -> None:
    rows = []
    for index, (title, value, caption) in enumerate(items, 1):
        rows.append(
            f"""
<div class="v1-rank-row">
  <div class="v1-rank-index">{index:02d}</div>
  <div class="v1-rank-main">
    <div class="v1-rank-title">{title}</div>
    <div class="v1-rank-caption">{caption}</div>
  </div>
  <div class="v1-rank-value">{value}</div>
</div>
            """
        )
    st.markdown('<div class="v1-rank-list">' + "".join(rows) + "</div>", unsafe_allow_html=True)


def section(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
<div class="v1-section">
  <h2>{title}</h2>
  <p>{subtitle}</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def note(text: str) -> None:
    st.markdown(f'<div class="v1-note">{text}</div>', unsafe_allow_html=True)


def health_bar(value: float) -> None:
    width = max(0, min(100, float(value)))
    st.markdown(
        f'<div class="v1-healthbar"><div style="width:{width:.1f}%"></div></div>',
        unsafe_allow_html=True,
    )


def dataframe_money(df: pd.DataFrame, money_columns: list[str]) -> None:
    config = {
        col: st.column_config.NumberColumn(col, format="¥ %.2f")
        for col in money_columns
        if col in df.columns
    }
    st.dataframe(df, hide_index=True, column_config=config, **stretch_kwargs())
