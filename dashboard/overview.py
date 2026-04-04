"""Overview tab: summary table + P(viable) bar chart."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.styles import decision_emoji, decision_color, COLORS
from neowatt.use_case_model import ModelResult


def render_overview(results: dict[str, ModelResult], required_margin: float):
    st.markdown("## Use Case Overview")

    # Summary table
    rows = []
    for slug, r in results.items():
        dec = r.decision
        rows.append({
            "Use Case": r.use_case_name,
            "Category": r.category,
            "Horizon": r.time_horizon,
            "Status": f"{decision_emoji(dec.label)} {dec.label}",
            "P(viable)": f"{r.p_viable:.0%}",
            "Cust. saving (median)": f"{r.customer_saving_pct_median * 100:+.0f}%",
            "Gross margin (median)": f"{r.gross_margin_median * 100:.0f}%",
            "Cost/W (median)": f"${r.cost_per_W_median:,.0f}",
            "NPV (median)": f"${r.npv_median:,.0f}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # P(viable) bar chart
    st.markdown("## Probability of Viability")

    names = [r.use_case_name for r in results.values()]
    pviable = [r.p_viable for r in results.values()]
    colors = [decision_color(r.decision.label) for r in results.values()]

    fig = go.Figure(go.Bar(
        x=names,
        y=[p * 100 for p in pviable],
        marker_color=colors,
        text=[f"{p:.0%}" for p in pviable],
        textposition="outside",
    ))

    fig.add_hline(
        y=60, line_dash="dash", line_color=COLORS["text_muted"],
        annotation_text="GO threshold (60%)", annotation_position="right",
    )
    fig.add_hline(
        y=30, line_dash="dot", line_color=COLORS["text_muted"],
        annotation_text="MARGINAL (30%)", annotation_position="right",
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        yaxis_title="P(viable) %",
        yaxis_range=[0, 110],
        font_family="Syne",
        margin=dict(t=30, b=10),
        height=400,
        xaxis_tickangle=-30,
    )

    st.plotly_chart(fig, use_container_width=True)
