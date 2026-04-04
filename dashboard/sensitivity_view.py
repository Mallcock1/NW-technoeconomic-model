"""Sensitivity analysis views: tornado chart and 2D heatmap."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.styles import COLORS


def render_sensitivity(tornado_results: list[dict], base_metric_name: str = "customer saving"):
    st.markdown("### Sensitivity Analysis (Tornado)")
    st.caption(f"How much does each input shift {base_metric_name}? (±25% perturbation)")

    if not tornado_results:
        st.info("No sensitivity data available.")
        return

    # Take top 12 most sensitive params
    top = tornado_results[:12]

    params = [f"{r['param']}" for r in reversed(top)]
    high_swings = [r["high_median"] - r["base_median"] for r in reversed(top)]
    low_swings = [r["low_median"] - r["base_median"] for r in reversed(top)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=params,
        x=[s * 100 for s in high_swings],
        orientation="h",
        name="+25%",
        marker_color=COLORS["go"],
    ))
    fig.add_trace(go.Bar(
        y=params,
        x=[s * 100 for s in low_swings],
        orientation="h",
        name="-25%",
        marker_color=COLORS["kill"],
    ))

    fig.update_layout(
        barmode="relative",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        xaxis_title=f"Change in {base_metric_name} (pp)",
        font_family="Syne",
        height=max(300, len(top) * 30 + 80),
        margin=dict(t=10, b=10, l=150),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_sensitivity_2d(data: dict):
    """Render 2D sensitivity heatmap."""
    st.markdown("### 2D Sensitivity Heatmap")

    import numpy as np

    fig = go.Figure(data=go.Heatmap(
        z=data["z_grid"] * 100,
        x=[f"{v:.1f}" for v in data["x_values"]],
        y=[f"{v:.1f}" for v in data["y_values"]],
        colorscale=[[0, COLORS["kill"]], [0.5, COLORS["marginal"]], [1, COLORS["go"]]],
        colorbar_title="P(viable) %",
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        xaxis_title=data["x_label"],
        yaxis_title=data["y_label"],
        font_family="Syne",
        height=400,
        margin=dict(t=10, b=10),
    )

    st.plotly_chart(fig, use_container_width=True)
