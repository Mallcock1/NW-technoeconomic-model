"""Market sizing and "Why Now?" trajectory views."""

import streamlit as st
import plotly.graph_objects as go

from dashboard.styles import COLORS
from neowatt.use_case_model import ModelResult


def render_market_size(results: dict[str, ModelResult]):
    st.markdown("### Market Sizing (TAM / SAM / SOM)")

    # Collect market data
    names = []
    tam_vals = []
    sam_vals = []
    som_vals = []

    for slug, r in results.items():
        if r.tam_k > 0:
            names.append(r.use_case_name)
            tam_vals.append(r.tam_k / 1000)  # Convert to $M
            sam_vals.append(r.sam_k / 1000)
            som_vals.append(r.som_k / 1000)

    if not names:
        st.info("No market sizing data available.")
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(name="TAM ($M)", x=names, y=tam_vals,
                         marker_color="#8b949e", opacity=0.5))
    fig.add_trace(go.Bar(name="SAM ($M)", x=names, y=sam_vals,
                         marker_color=COLORS["primary"], opacity=0.7))
    fig.add_trace(go.Bar(name="SOM ($M)", x=names, y=som_vals,
                         marker_color=COLORS["go"]))

    fig.update_layout(
        barmode="overlay",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        yaxis_title="Market size ($M)",
        font_family="Syne",
        height=400,
        margin=dict(t=10, b=10),
        xaxis_tickangle=-30,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_why_now(trajectory: dict, use_case_name: str):
    st.markdown(f"### Why Now? — {use_case_name}")
    st.caption("How does viability evolve as launch costs decline?")

    if not trajectory or not trajectory.get("years"):
        st.info("No trajectory data available.")
        return

    fig = go.Figure()

    # P(viable) line
    fig.add_trace(go.Scatter(
        x=trajectory["years"],
        y=[p * 100 for p in trajectory["p_viable"]],
        mode="lines+markers",
        name="P(viable) %",
        line=dict(color=COLORS["primary"], width=3),
        marker=dict(size=10),
    ))

    # GO threshold
    fig.add_hline(y=60, line_dash="dash", line_color=COLORS["go"],
                  annotation_text="GO threshold")
    fig.add_hline(y=30, line_dash="dot", line_color=COLORS["marginal"],
                  annotation_text="MARGINAL threshold")

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        xaxis_title="Year",
        yaxis_title="P(viable) %",
        yaxis_range=[0, 105],
        font_family="Syne",
        height=350,
        margin=dict(t=10, b=10),
    )

    st.plotly_chart(fig, use_container_width=True)
