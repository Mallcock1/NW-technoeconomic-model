"""Portfolio analysis: shared TX platform serving multiple use cases."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.styles import COLORS, decision_emoji
from dashboard.point_estimates import _compute_point_estimate
from neowatt.data_loader import get_param_value


def _esc(text: str) -> str:
    if not text:
        return ""
    return text.replace("$", "\\$").replace("~", "\\~")


def render_portfolio(use_cases: dict, global_params: dict, required_margin: float):
    """Render portfolio analysis where one TX platform serves multiple use cases.

    The key insight: TX hardware + launch is the biggest CAPEX component.
    If one TX can serve LEO Eclipse, Peak Power, and In-Orbit Servicing customers
    (all in LEO), the TX cost is amortised across multiple revenue streams.
    """
    st.markdown("## Portfolio Analysis")
    st.caption("Model a shared TX platform serving multiple use cases simultaneously. "
               "TX CAPEX is amortised across selected use cases; each contributes its "
               "own RX revenue stream.")

    # Let user select which use cases share a TX platform
    all_names = {uc["meta"]["name"]: slug for slug, uc in use_cases.items()}
    default_selection = [n for n, s in all_names.items()
                         if s in ("leo_eclipse_power", "peak_power", "in_orbit_servicing")]

    selected = st.multiselect(
        "Select use cases sharing a TX platform",
        list(all_names.keys()),
        default=default_selection,
    )

    if len(selected) < 2:
        st.info("Select at least 2 use cases to see portfolio effects.")
        return

    selected_slugs = [all_names[n] for n in selected]

    # Compute individual estimates
    estimates = {}
    for slug in selected_slugs:
        estimates[slug] = _compute_point_estimate(use_cases[slug], global_params, required_margin)

    # Use the largest TX cost as the shared platform cost
    tx_costs = {slug: e["tx_cost"] for slug, e in estimates.items()}
    shared_tx_cost = max(tx_costs.values())
    shared_tx_slug = max(tx_costs, key=tx_costs.get)

    st.markdown(f"### Shared TX Platform")
    st.markdown(f"Using the largest TX system (from **{estimates[shared_tx_slug]['name']}**) "
                f"at **\\${shared_tx_cost:,.0f}** as the shared platform.")

    # Portfolio economics
    n_use_cases = len(selected_slugs)
    tx_share = shared_tx_cost / n_use_cases  # Each use case bears 1/N of TX cost

    portfolio_rows = []
    total_annual_revenue = 0
    total_rx_cost = 0
    total_opex = 0

    for slug in selected_slugs:
        e = estimates[slug]
        # Recompute CAPEX with shared TX
        new_capex = tx_share + e["rx_cost"] + e["ground_cost"]
        new_total_cost = new_capex + e["opex_yr"] * e["amort_years"]

        if e["annual_revenue"] > 0:
            new_margin = (e["annual_revenue"] * e["amort_years"] - new_total_cost) / (
                e["annual_revenue"] * e["amort_years"])
        else:
            new_margin = -999

        net_annual = e["annual_revenue"] - e["opex_yr"]
        new_payback = new_capex / net_annual if net_annual > 0 else float("inf")

        total_annual_revenue += e["annual_revenue"]
        total_rx_cost += e["rx_cost"]
        total_opex += e["opex_yr"]

        portfolio_rows.append({
            "name": e["name"],
            "slug": slug,
            "decision_standalone": e["decision"],
            "capex_standalone": e["capex"],
            "capex_portfolio": new_capex,
            "capex_saving": e["capex"] - new_capex,
            "capex_saving_pct": (e["capex"] - new_capex) / e["capex"] * 100 if e["capex"] > 0 else 0,
            "margin_standalone": e["gross_margin"],
            "margin_portfolio": new_margin,
            "annual_revenue": e["annual_revenue"],
            "payback_standalone": e["capex"] / net_annual if net_annual > 0 else float("inf"),
            "payback_portfolio": new_payback,
            "breakeven_price": e["breakeven_price"],
        })

    # Platform-level metrics
    platform_capex = shared_tx_cost + total_rx_cost + sum(
        estimates[s]["ground_cost"] for s in selected_slugs)
    platform_net_annual = total_annual_revenue - total_opex
    platform_payback = platform_capex / platform_net_annual if platform_net_annual > 0 else float("inf")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Platform CAPEX", f"${platform_capex:,.0f}")
    with col2:
        st.metric("Combined Revenue/yr", f"${total_annual_revenue:,.0f}")
    with col3:
        st.metric("Platform Net Profit/yr", f"${platform_net_annual:,.0f}")
    with col4:
        st.metric("Platform Payback",
                  f"{platform_payback:.1f} yr" if platform_payback < 50 else "Never")

    # Per-use-case comparison table
    st.markdown("### Per-Use-Case: Standalone vs Portfolio")
    table = []
    for r in portfolio_rows:
        table.append({
            "Use Case": r["name"],
            "Standalone CAPEX": f"${r['capex_standalone']:,.0f}",
            "Portfolio CAPEX": f"${r['capex_portfolio']:,.0f}",
            "CAPEX Saving": f"{r['capex_saving_pct']:.0f}%",
            "Standalone Margin": f"{r['margin_standalone'] * 100:.0f}%",
            "Portfolio Margin": f"{r['margin_portfolio'] * 100:.0f}%",
            "Standalone Payback": f"{r['payback_standalone']:.1f}yr" if r["payback_standalone"] < 50 else "Never",
            "Portfolio Payback": f"{r['payback_portfolio']:.1f}yr" if r["payback_portfolio"] < 50 else "Never",
        })

    df = pd.DataFrame(table)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Payback comparison chart
    st.markdown("### Payback: Standalone vs Portfolio")
    names = [r["name"] for r in portfolio_rows]
    standalone_pb = [min(r["payback_standalone"], 30) for r in portfolio_rows]
    portfolio_pb = [min(r["payback_portfolio"], 30) for r in portfolio_rows]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Standalone", x=names, y=standalone_pb,
                         marker_color=COLORS["text_muted"], opacity=0.6))
    fig.add_trace(go.Bar(name="Portfolio", x=names, y=portfolio_pb,
                         marker_color=COLORS["go"]))

    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        yaxis_title="Payback (years)",
        font_family="Syne",
        height=350,
        margin=dict(t=10, b=10),
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig, use_container_width=True)

    # CAPEX savings chart
    st.markdown("### CAPEX Reduction from Shared TX")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Standalone CAPEX", x=names,
                          y=[r["capex_standalone"] / 1000 for r in portfolio_rows],
                          marker_color=COLORS["text_muted"], opacity=0.6))
    fig2.add_trace(go.Bar(name="Portfolio CAPEX", x=names,
                          y=[r["capex_portfolio"] / 1000 for r in portfolio_rows],
                          marker_color=COLORS["primary"]))

    fig2.update_layout(
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        yaxis_title="CAPEX ($k)",
        font_family="Syne",
        height=350,
        margin=dict(t=10, b=10),
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig2, use_container_width=True)
