"""Cross-use-case comparison scatter plot."""

import streamlit as st
import plotly.graph_objects as go

from dashboard.styles import COLORS, decision_color, decision_emoji
from neowatt.use_case_model import ModelResult


def render_comparison(results: dict[str, ModelResult]):
    st.markdown("### Use Case Comparison")
    st.caption("X = customer saving vs incumbent. Y = gross margin. Color = decision.")

    names = []
    x_vals = []  # customer saving %
    y_vals = []  # gross margin %
    colors = []
    hover = []

    for slug, r in results.items():
        names.append(r.use_case_name)
        x_vals.append(r.customer_saving_pct_median * 100)
        y_vals.append(r.gross_margin_median * 100)
        colors.append(decision_color(r.decision.label))
        hover.append(
            f"<b>{r.use_case_name}</b><br>"
            f"Customer saving: {r.customer_saving_pct_median * 100:+.0f}%<br>"
            f"Gross margin: {r.gross_margin_median * 100:.0f}%<br>"
            f"Decision: {r.decision.label}"
        )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers+text",
        text=names,
        textposition="top center",
        textfont=dict(size=9),
        marker=dict(
            size=16,
            color=colors,
            opacity=0.85,
            line=dict(width=1, color="white"),
        ),
        hovertext=hover,
        hoverinfo="text",
    ))

    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["text_muted"], opacity=0.4)
    fig.add_vline(x=0, line_dash="dot", line_color=COLORS["text_muted"], opacity=0.4)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        xaxis_title="Customer Saving vs Incumbent (%)",
        yaxis_title="Gross Margin (%)",
        font_family="Syne",
        height=500,
        margin=dict(t=10, b=10),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_comparison_point(use_cases: dict, global_params: dict, required_margin: float):
    """Point-estimate comparison: customer saving vs gross margin scatter."""
    from dashboard.point_estimates import _compute_point_estimate

    st.markdown("### Use Case Comparison")
    st.caption("X = customer saving %. Y = gross margin %. Color = decision.")

    names = []
    x_vals = []
    y_vals = []
    colors = []
    hover = []

    for slug, uc in use_cases.items():
        e = _compute_point_estimate(uc, global_params, required_margin)
        names.append(e["name"])
        x_vals.append(e["customer_saving"] * 100)
        y_vals.append(e["gross_margin"] * 100)
        colors.append(decision_color(e["decision"]))
        hover.append(
            f"<b>{e['name']}</b><br>"
            f"Saving: {e['customer_saving']*100:+.0f}%<br>"
            f"Margin: {e['gross_margin']*100:.0f}%<br>"
            f"Cost/W: ${e['cost_per_W']:,.0f}<br>"
            f"Decision: {e['decision']}"
        )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers+text",
        text=names,
        textposition="top center",
        textfont=dict(size=9),
        marker=dict(size=16, color=colors, opacity=0.85,
                    line=dict(width=1, color="white")),
        hovertext=hover,
        hoverinfo="text",
    ))

    fig.add_vline(x=required_margin * 100, line_dash="dash",
                  line_color=COLORS["go"], opacity=0.6,
                  annotation_text=f"Required margin ({required_margin:.0%})")
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["text_muted"], opacity=0.4)
    fig.add_vline(x=0, line_dash="dot", line_color=COLORS["text_muted"], opacity=0.4)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        xaxis_title="Customer Saving vs Incumbent (%)",
        yaxis_title="Gross Margin (%)",
        font_family="Syne",
        height=500,
        margin=dict(t=10, b=10),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)
