"""Input distributions viewer: shows each parameter's distribution shape, values, and justification."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go

from dashboard.styles import COLORS
from neowatt.distributions import sample


def render_inputs(uc_params: dict, n_preview: int = 10000):
    """Render input parameter distributions with justifications for a use case."""
    st.markdown("### Input Parameter Distributions")
    st.caption("Each parameter below is sampled from the specified distribution during Monte Carlo. "
               "Edit `data/use_cases.yaml` to change values, distributions, or justifications.")

    rng = np.random.default_rng(123)

    # Collect all parameter groups
    groups = [
        ("Incumbent", "incumbent"),
        ("Technical", "technical"),
        ("Cost", "cost"),
        ("Economic", "economic"),
    ]

    for group_label, group_key in groups:
        group_data = uc_params.get(group_key, {})
        param_specs = {k: v for k, v in group_data.items()
                       if isinstance(v, dict) and "value" in v}

        if not param_specs:
            continue

        st.markdown(f"#### {group_label} Parameters")

        for pname, pspec in param_specs.items():
            _render_single_param(pname, pspec, group_key, n_preview, rng)


def _render_single_param(name: str, spec: dict, group: str, n: int, rng):
    """Render a single parameter: distribution plot + metadata + justification."""
    value = spec["value"]
    unit = spec.get("unit", "")
    desc = spec.get("description", "")
    justification = spec.get("justification", "")
    dist = spec.get("distribution", {})
    dist_type = dist.get("type", "fixed") if dist else "fixed"

    with st.expander(f"**{name}** — {value} {unit}", expanded=False):
        col_chart, col_info = st.columns([3, 2])

        with col_chart:
            if dist_type != "fixed" and value != 0:
                samples = sample(spec, n, rng)
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=samples,
                    nbinsx=50,
                    marker_color=COLORS["primary"],
                    opacity=0.8,
                    name=name,
                ))
                # Mark the mode/base value
                fig.add_vline(
                    x=value, line_dash="dash", line_color=COLORS["go"],
                    annotation_text=f"Base: {value}",
                    annotation_position="top right",
                )

                # Distribution-specific annotations
                if dist_type == "triangular":
                    fig.add_vline(x=dist["low"], line_dash="dot",
                                  line_color=COLORS["text_muted"])
                    fig.add_vline(x=dist["high"], line_dash="dot",
                                  line_color=COLORS["text_muted"])
                elif dist_type == "uniform":
                    fig.add_vline(x=dist["low"], line_dash="dot",
                                  line_color=COLORS["text_muted"])
                    fig.add_vline(x=dist["high"], line_dash="dot",
                                  line_color=COLORS["text_muted"])

                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(13,17,23,1)",
                    xaxis_title=f"{name} ({unit})",
                    yaxis_title="Count",
                    font_family="Syne",
                    height=200,
                    margin=dict(t=10, b=30, l=40, r=10),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown(f"**Fixed value:** {value} {unit}")

        with col_info:
            st.markdown(f"**Description:** {desc}")
            st.markdown(f"**Distribution:** `{dist_type}`")

            if dist_type == "triangular":
                st.markdown(f"- Low: {dist['low']} {unit}")
                st.markdown(f"- Mode: {dist.get('mode', value)} {unit}")
                st.markdown(f"- High: {dist['high']} {unit}")
            elif dist_type == "uniform":
                st.markdown(f"- Low: {dist['low']} {unit}")
                st.markdown(f"- High: {dist['high']} {unit}")
            elif dist_type == "normal":
                st.markdown(f"- Mean: {dist.get('mean', value)} {unit}")
                st.markdown(f"- Std: {dist['std']} {unit}")
            elif dist_type == "lognormal":
                st.markdown(f"- Mean: {dist['mean']} {unit}")
                st.markdown(f"- Std: {dist['std']} {unit}")

            if justification:
                st.markdown(f"**Justification:** {justification}")
