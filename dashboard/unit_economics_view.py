"""Unit economics dashboard: gross margin, CLV, payback period, cost breakdown per use case."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.styles import COLORS, decision_emoji
from dashboard.point_estimates import _compute_point_estimate


def _esc(text: str) -> str:
    if not text:
        return ""
    return text.replace("$", "\\$").replace("~", "\\~")


def render_unit_economics(use_cases: dict, global_params: dict, required_margin: float):
    """Render unit economics for all use cases."""
    st.markdown("## Unit Economics")
    st.caption("NEOWATT's per-unit financial performance for each use case. "
               "CLV = Customer Lifetime Value. Payback = years to recover CAPEX from net revenue.")

    estimates = {}
    for slug, uc in use_cases.items():
        estimates[slug] = _compute_point_estimate(uc, global_params, required_margin)

    # Summary table
    rows = []
    for slug, e in estimates.items():
        # Customer Lifetime Value = total revenue over amortization
        clv = e["annual_revenue"] * e["amort_years"]

        # Net annual profit
        net_annual = e["annual_revenue"] - e["opex_yr"]

        # Payback period in years
        if net_annual > 0:
            payback = e["capex"] / net_annual
        else:
            payback = float("inf")

        # Revenue per TX dollar invested
        rev_per_tx = e["annual_revenue"] / e["tx_cost"] if e["tx_cost"] > 0 else 0

        rows.append({
            "slug": slug,
            "name": e["name"],
            "decision": e["decision"],
            "capex": e["capex"],
            "tx_cost": e["tx_cost"],
            "rx_cost": e["rx_cost"],
            "ground_cost": e["ground_cost"],
            "opex_yr": e["opex_yr"],
            "annual_revenue": e["annual_revenue"],
            "net_annual": net_annual,
            "clv": clv,
            "gross_margin": e["gross_margin"],
            "payback": payback,
            "cost_per_W": e["cost_per_W"],
            "rev_per_tx": rev_per_tx,
            "amort_years": e["amort_years"],
        })

    # Table
    st.markdown("### Summary")
    table = []
    for r in rows:
        table.append({
            "Use Case": r["name"],
            "Status": f"{decision_emoji(r['decision'])} {r['decision']}",
            "CAPEX": f"${r['capex']:,.0f}",
            "Revenue/yr": f"${r['annual_revenue']:,.0f}",
            "Net Profit/yr": f"${r['net_annual']:,.0f}",
            "CLV": f"${r['clv']:,.0f}",
            "Gross Margin": f"{r['gross_margin'] * 100:.0f}%",
            "Payback (yr)": f"{r['payback']:.1f}" if r["payback"] < 100 else "Never",
        })

    df = pd.DataFrame(table)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Payback chart
    st.markdown("### Payback Period")
    viable_rows = [r for r in rows if r["payback"] < 50]
    viable_rows.sort(key=lambda r: r["payback"])

    if viable_rows:
        fig = go.Figure(go.Bar(
            x=[r["name"] for r in viable_rows],
            y=[r["payback"] for r in viable_rows],
            marker_color=[COLORS["go"] if r["payback"] <= r["amort_years"]
                          else COLORS["kill"] for r in viable_rows],
            text=[f"{r['payback']:.1f}yr" for r in viable_rows],
            textposition="outside",
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,17,23,1)",
            yaxis_title="Years to payback",
            font_family="Syne",
            height=350,
            margin=dict(t=10, b=10),
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig, use_container_width=True)

    # CAPEX breakdown comparison
    st.markdown("### CAPEX Composition by Use Case")
    names = [r["name"] for r in rows]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="TX Hardware + Launch", x=names,
                         y=[r["tx_cost"] / 1000 for r in rows],
                         marker_color=COLORS["primary"]))
    fig.add_trace(go.Bar(name="RX Hardware + Launch", x=names,
                         y=[r["rx_cost"] / 1000 for r in rows],
                         marker_color=COLORS["go"]))
    fig.add_trace(go.Bar(name="Ground Segment", x=names,
                         y=[r["ground_cost"] / 1000 for r in rows],
                         marker_color=COLORS["marginal"]))

    fig.update_layout(
        barmode="stack",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        yaxis_title="CAPEX ($k)",
        font_family="Syne",
        height=400,
        margin=dict(t=10, b=10),
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig, use_container_width=True)
