"""Dashboard CSS and theming."""

import streamlit as st

COLORS = {
    "go": "#3fb950",
    "marginal": "#d29922",
    "kill": "#f85149",
    "primary": "#388bfd",
    "bg_dark": "#0d1117",
    "bg_card": "#161b22",
    "border": "#30363d",
    "text_muted": "#8b949e",
}


def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
    h1, h2, h3 { font-family: 'Syne', sans-serif; font-weight: 800; }
    code, .stCode { font-family: 'Space Mono', monospace; }

    .metric-card {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.3rem 0;
    }
    .viable { border-left: 4px solid #3fb950; }
    .marginal { border-left: 4px solid #d29922; }
    .dead { border-left: 4px solid #f85149; }
    </style>
    """, unsafe_allow_html=True)


def decision_color(decision_label: str) -> str:
    if decision_label == "GO":
        return COLORS["go"]
    elif decision_label == "MARGINAL":
        return COLORS["marginal"]
    return COLORS["kill"]


def decision_emoji(decision_label: str) -> str:
    if decision_label == "GO":
        return "🟢"
    elif decision_label == "MARGINAL":
        return "🟡"
    return "🔴"
