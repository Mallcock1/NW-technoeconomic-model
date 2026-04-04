"""Cross-use-case comparison scatter plot."""

import streamlit as st
import plotly.graph_objects as go

from dashboard.styles import COLORS, decision_color
from neowatt.use_case_model import ModelResult


def render_comparison(results: dict[str, ModelResult]):
    st.markdown("### Use Case Comparison")
    st.caption("Bubble size = TAM. Position = P(viable) vs SOM. Color = decision.")

    names = []
    x_vals = []  # P(viable)
    y_vals = []  # SOM ($M)
    sizes = []   # TAM for bubble size
    colors = []
    hover = []

    for slug, r in results.items():
        names.append(r.use_case_name)
        x_vals.append(r.p_viable * 100)
        y_vals.append(r.som_k / 1000)  # $M
        tam_m = r.tam_k / 1000
        sizes.append(max(tam_m, 1))  # minimum bubble size
        colors.append(decision_color(r.decision.label))
        hover.append(
            f"<b>{r.use_case_name}</b><br>"
            f"P(viable): {r.p_viable:.0%}<br>"
            f"SOM: ${r.som_k / 1000:.1f}M<br>"
            f"TAM: ${tam_m:.1f}M<br>"
            f"Decision: {r.decision.label}"
        )

    # Normalise bubble sizes
    max_size = max(sizes) if sizes else 1
    norm_sizes = [s / max_size * 60 + 10 for s in sizes]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers+text",
        text=names,
        textposition="top center",
        textfont=dict(size=9),
        marker=dict(
            size=norm_sizes,
            color=colors,
            opacity=0.8,
            line=dict(width=1, color="white"),
        ),
        hovertext=hover,
        hoverinfo="text",
    ))

    # Quadrant lines
    fig.add_vline(x=60, line_dash="dash", line_color=COLORS["text_muted"], opacity=0.5)
    fig.add_vline(x=30, line_dash="dot", line_color=COLORS["text_muted"], opacity=0.3)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        xaxis_title="P(viable) %",
        yaxis_title="SOM ($M)",
        font_family="Syne",
        height=500,
        margin=dict(t=10, b=10),
        showlegend=False,
        xaxis_range=[0, 105],
    )

    st.plotly_chart(fig, use_container_width=True)
