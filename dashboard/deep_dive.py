"""Deep dive tab: selected use case metrics, distribution plots, cost waterfall."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from dashboard.styles import COLORS, decision_emoji
from neowatt.use_case_model import ModelResult


def _esc_prose(text: str) -> str:
    """Escape lone dollar signs in prose text without breaking $$ LaTeX blocks."""
    if not text:
        return text
    import re
    # Replace single $ not adjacent to another $ with escaped version
    return re.sub(r'(?<!\$)\$(?!\$)', r'\\$', text).replace("~", "\\~")


def render_deep_dive(result: ModelResult, uc_params: dict, required_margin: float):
    dec = result.decision
    st.markdown(f"## {decision_emoji(dec.label)} Deep Dive: {result.use_case_name}")

    # Description and incumbent
    meta = uc_params["meta"]
    inc = uc_params["incumbent"]
    st.caption(f"**Category:** {result.category} | **Horizon:** {result.time_horizon} | "
               f"**Incumbent:** {inc.get('name', 'N/A')}")

    # Model explanation (prose + maths from YAML)
    model_prose = meta.get("model_prose", "")
    model_maths = meta.get("model_maths", "")

    if model_prose or model_maths:
        with st.expander("Model details", expanded=True):
            if model_prose:
                st.markdown(_esc_prose(model_prose))
            if model_maths:
                st.divider()
                st.markdown(model_maths)

    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("P(viable)", f"{result.p_viable:.0%}")
    with col2:
        st.metric("Cust. saving (median)", f"{result.customer_saving_pct_median * 100:+.0f}%")
    with col3:
        st.metric("Gross margin (median)", f"{result.gross_margin_median * 100:.0f}%")
    with col4:
        st.metric("Cost/W (median)", f"${result.cost_per_W_median:,.0f}")
    with col5:
        st.metric("NPV (median)", f"${result.npv_median:,.0f}")

    # Distribution plots
    col_a, col_b = st.columns(2)

    with col_a:
        fig_cust = go.Figure()
        fig_cust.add_trace(go.Histogram(
            x=result.customer_saving_pct * 100,
            nbinsx=60,
            marker_color=COLORS["primary"],
            opacity=0.85,
            name="Customer saving %",
        ))
        fig_cust.add_vline(
            x=required_margin * 100, line_dash="dash", line_color=COLORS["kill"],
            annotation_text=f"Required: {required_margin:.0%}",
        )
        fig_cust.add_vline(x=0, line_dash="dot", line_color=COLORS["text_muted"])
        fig_cust.update_layout(
            title="Customer savings vs incumbent",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,17,23,1)",
            xaxis_title="Saving (%)", yaxis_title="Count",
            font_family="Syne", height=300, margin=dict(t=40, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_cust, use_container_width=True)

    with col_b:
        fig_gm = go.Figure()
        fig_gm.add_trace(go.Histogram(
            x=result.gross_margin * 100,
            nbinsx=60,
            marker_color=COLORS["go"],
            opacity=0.85,
            name="Gross margin %",
        ))
        fig_gm.add_vline(
            x=0, line_dash="dash", line_color=COLORS["kill"],
            annotation_text="Break-even",
        )
        fig_gm.update_layout(
            title="Gross margin distribution",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,17,23,1)",
            xaxis_title="Gross margin (%)", yaxis_title="Count",
            font_family="Syne", height=300, margin=dict(t=40, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_gm, use_container_width=True)

    # NPV distribution
    fig_npv = go.Figure()
    fig_npv.add_trace(go.Histogram(
        x=result.net_present_value / 1000,
        nbinsx=60,
        marker_color="#a371f7",
        opacity=0.85,
        name="NPV ($k)",
    ))
    fig_npv.add_vline(x=0, line_dash="dash", line_color=COLORS["kill"],
                      annotation_text="Break-even")
    fig_npv.update_layout(
        title="Net Present Value distribution",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        xaxis_title="NPV ($k)", yaxis_title="Count",
        font_family="Syne", height=280, margin=dict(t=40, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_npv, use_container_width=True)
