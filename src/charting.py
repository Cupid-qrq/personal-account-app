from __future__ import annotations

import plotly.graph_objects as go


PAPER = "rgba(0,0,0,0)"
PLOT = "rgba(255,255,255,0.30)"
INK = "#161513"
MUTED = "#746f65"
GRID = "rgba(31,29,24,0.10)"

PALETTE = [
    "#a95f32",
    "#315f72",
    "#60735f",
    "#8f6f4f",
    "#1f1f1c",
    "#d4a373",
    "#7b8794",
    "#9c6644",
]


def apply_chart_theme(fig: go.Figure, height: int = 340, showlegend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor=PAPER,
        plot_bgcolor=PLOT,
        font={"family": "IBM Plex Sans, Microsoft YaHei, sans-serif", "color": INK, "size": 13},
        margin={"l": 14, "r": 14, "t": 34, "b": 24},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "font": {"size": 12, "color": MUTED},
        },
        showlegend=showlegend,
        hoverlabel={
            "bgcolor": "#161513",
            "font_size": 12,
            "font_family": "IBM Plex Sans, Microsoft YaHei, sans-serif",
            "font_color": "#fffaf0",
            "bordercolor": "#b66d38",
        },
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=GRID,
        tickfont={"color": MUTED},
        title_font={"color": MUTED},
    )
    fig.update_yaxes(
        gridcolor=GRID,
        zeroline=False,
        linecolor=GRID,
        tickfont={"color": MUTED},
        title_font={"color": MUTED},
    )
    return fig


def add_reference_band(fig: go.Figure, y0: float, y1: float, color: str = "rgba(49,95,114,0.08)") -> go.Figure:
    fig.add_hrect(y0=y0, y1=y1, line_width=0, fillcolor=color, layer="below")
    return fig
