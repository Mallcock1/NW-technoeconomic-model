"""Time-dependent output views for both point estimates and Monte Carlo."""

import streamlit as st
import plotly.graph_objects as go

from dashboard.styles import COLORS, decision_color, decision_emoji


def _chart_layout(**kwargs):
    """Shared chart layout defaults."""
    base = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        font_family="Syne",
        margin=dict(t=40, b=10),
    )
    base.update(kwargs)
    return base


# ── Point Estimates ──────────────────────────────────────────────────────────

def render_temporal_point(time_series: dict, selected_slug: str, required_margin: float):
    """Render time-dependent point estimate results."""
    st.markdown("## Time-Dependent Analysis (Point Estimates)")
    st.caption("Shows how model outputs evolve as time-dependent parameters "
               "(e.g. launch cost) change over the selected year range.")

    # All use cases: customer saving over time
    st.markdown("### Customer Saving vs Incumbent Over Time")
    _plot_all_use_cases_line(
        time_series, selected_slug, "customer_saving",
        y_label="Customer Saving (%)",
        multiplier=100,
        hlines=[(required_margin * 100, "dash", COLORS["go"],
                 f"Required margin ({required_margin:.0%})"),
                (0, "dot", COLORS["text_muted"], None)],
    )

    # Selected use case detail
    ts = time_series[selected_slug]
    st.markdown(f"### {ts['name']} – Detail Over Time")

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts["years"], y=[c / 1000 for c in ts["capex"]],
            mode="lines+markers", name="CAPEX ($k)",
            line=dict(color=COLORS["kill"], width=2),
        ))
        fig.add_trace(go.Scatter(
            x=ts["years"], y=[r / 1000 for r in ts["annual_revenue"]],
            mode="lines+markers", name="Revenue/yr ($k)",
            line=dict(color=COLORS["go"], width=2),
        ))
        fig.update_layout(**_chart_layout(
            title="CAPEX and Revenue over time",
            xaxis_title="Year", yaxis_title="$k", height=300,
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts["years"], y=[m * 100 for m in ts["gross_margin"]],
            mode="lines+markers", name="Gross Margin (%)",
            line=dict(color=COLORS["primary"], width=2),
        ))
        fig.add_hline(y=0, line_dash="dot", line_color=COLORS["text_muted"])
        fig.update_layout(**_chart_layout(
            title="Gross Margin over time",
            xaxis_title="Year", yaxis_title="Gross Margin (%)", height=300,
        ))
        st.plotly_chart(fig, use_container_width=True)

    # Decision trajectory
    _render_decision_row(ts["years"], ts["decision"])


# ── Monte Carlo ──────────────────────────────────────────────────────────────

def render_temporal_mc(time_series: dict, selected_slug: str, required_margin: float):
    """Render time-dependent MC results for all use cases."""
    st.markdown("## Time-Dependent Analysis (Monte Carlo)")
    st.caption("Shows how MC outputs evolve as time-dependent parameters change. "
               "P(viable) reflects the fraction of simulations beating the required margin.")

    # All use cases: P(viable) over time
    st.markdown("### P(viable) Over Time – All Use Cases")
    _plot_all_use_cases_line(
        time_series, selected_slug, "p_viable",
        y_label="P(viable) %",
        multiplier=100,
        hlines=[(60, "dash", COLORS["go"], "GO threshold (60%)"),
                (30, "dot", COLORS["marginal"], "MARGINAL (30%)")],
        y_range=[0, 105],
    )

    # Selected use case detail
    ts = time_series[selected_slug]
    st.markdown(f"### {ts['name']} – Detail Over Time")

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts["years"], y=[p * 100 for p in ts["p_viable"]],
            mode="lines+markers", name="P(viable) %",
            line=dict(color=COLORS["primary"], width=3),
            marker=dict(size=10),
        ))
        fig.add_hline(y=60, line_dash="dash", line_color=COLORS["go"],
                      annotation_text="GO threshold")
        fig.add_hline(y=30, line_dash="dot", line_color=COLORS["marginal"],
                      annotation_text="MARGINAL")
        fig.update_layout(**_chart_layout(
            title="P(viable) over time",
            xaxis_title="Year", yaxis_title="P(viable) %",
            yaxis_range=[0, 105], height=300,
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts["years"], y=ts["cost_per_W_median"],
            mode="lines+markers", name="Cost/W (median)",
            line=dict(color=COLORS["marginal"], width=3),
            marker=dict(size=10),
        ))
        fig.update_layout(**_chart_layout(
            title="Median Cost/W over time",
            xaxis_title="Year", yaxis_title="Cost/W ($)", height=300,
        ))
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts["years"], y=[m * 100 for m in ts["gross_margin_median"]],
            mode="lines+markers", name="Gross Margin (median %)",
            line=dict(color=COLORS["go"], width=2),
        ))
        fig.add_hline(y=0, line_dash="dot", line_color=COLORS["text_muted"])
        fig.update_layout(**_chart_layout(
            title="Median Gross Margin over time",
            xaxis_title="Year", yaxis_title="Gross Margin (%)", height=300,
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts["years"], y=[s * 100 for s in ts["customer_saving_median"]],
            mode="lines+markers", name="Customer Saving (median %)",
            line=dict(color=COLORS["primary"], width=2),
        ))
        fig.add_hline(y=required_margin * 100, line_dash="dash",
                      line_color=COLORS["go"], opacity=0.6,
                      annotation_text=f"Required ({required_margin:.0%})")
        fig.add_hline(y=0, line_dash="dot", line_color=COLORS["text_muted"])
        fig.update_layout(**_chart_layout(
            title="Median Customer Saving over time",
            xaxis_title="Year", yaxis_title="Customer Saving (%)", height=300,
        ))
        st.plotly_chart(fig, use_container_width=True)

    # Decision trajectory
    _render_decision_row(ts["years"], ts["decision"])


# ── Shared helpers ───────────────────────────────────────────────────────────

def _plot_all_use_cases_line(time_series, selected_slug, metric_key,
                             y_label, multiplier=1, hlines=None, y_range=None):
    """Plot a metric over time for all use cases, highlighting the selected one."""
    fig = go.Figure()
    for slug, ts in time_series.items():
        is_selected = slug == selected_slug
        fig.add_trace(go.Scatter(
            x=ts["years"],
            y=[v * multiplier for v in ts[metric_key]],
            mode="lines+markers",
            name=ts["name"],
            line=dict(width=3 if is_selected else 1.5,
                      dash=None if is_selected else "dot"),
            opacity=1.0 if is_selected else 0.5,
        ))

    if hlines:
        for y, dash, color, text in hlines:
            kwargs = dict(y=y, line_dash=dash, line_color=color, opacity=0.6)
            if text:
                kwargs["annotation_text"] = text
            fig.add_hline(**kwargs)

    layout = _chart_layout(xaxis_title="Year", yaxis_title=y_label, height=400)
    if y_range:
        layout["yaxis_range"] = y_range
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def _render_decision_row(years, decisions):
    """Render a row of decision badges for each year."""
    st.markdown("### Decision Over Time")
    # Limit columns to avoid tiny cells on wide ranges
    max_cols = min(len(years), 12)
    if len(years) > max_cols:
        years = years[:max_cols]
        decisions = decisions[:max_cols]

    cols = st.columns(len(years))
    for i, (yr, dec) in enumerate(zip(years, decisions)):
        with cols[i]:
            st.markdown(f"**{yr}**")
            st.markdown(f"{decision_emoji(dec)} {dec}")
