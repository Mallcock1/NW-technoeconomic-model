"""Input distributions viewer: editable distribution params + theoretical PDF + MC histogram + justification."""

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy import stats

from dashboard.styles import COLORS
from neowatt.distributions import sample


def _esc(text: str) -> str:
    """Escape characters that Streamlit's markdown renderer interprets as formatting."""
    if not text:
        return text
    return (text
            .replace("$", "\\$")
            .replace("~", "\\~"))


DIST_TYPES = ["triangular", "uniform", "normal", "lognormal", "fixed"]


def render_inputs(uc_params: dict, slug: str, n_preview: int = 10000) -> dict:
    """Render input parameter distributions with fully editable distribution params.

    Returns a dict of overrides: {group: {param_name: new_value_or_dict}}
    """
    st.markdown("### Input Parameters")
    st.caption("Edit distribution type, parameters, and base value below. "
               "Changes update the Monte Carlo outputs. "
               "To persist changes, edit `data/use_cases.yaml`.")

    # Reset all button
    if st.button("Reset all to defaults", key=f"reset_all_mc_{slug}"):
        keys_to_clear = [k for k in st.session_state if k.startswith(f"mc_{slug}_")]
        for k in keys_to_clear:
            del st.session_state[k]
        ss_key = f"overrides_mc_{slug}"
        if ss_key in st.session_state:
            del st.session_state[ss_key]
        st.rerun()

    rng = np.random.default_rng(123)
    overrides = {}

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
            override = _render_single_param(pname, pspec, slug, group_key, n_preview, rng)
            if override is not None:
                overrides.setdefault(group_key, {})[pname] = override

    return overrides


def _theoretical_pdf(dist: dict, value: float, x: np.ndarray) -> np.ndarray | None:
    """Compute the theoretical PDF for a distribution spec over x values."""
    dtype = dist.get("type", "fixed")

    if dtype == "triangular":
        lo, mode, hi = dist["low"], dist.get("mode", value), dist["high"]
        if hi <= lo:
            return None
        c = (mode - lo) / (hi - lo)
        return stats.triang.pdf(x, c, loc=lo, scale=hi - lo)

    if dtype == "uniform":
        lo, hi = dist["low"], dist["high"]
        if hi <= lo:
            return None
        return stats.uniform.pdf(x, loc=lo, scale=hi - lo)

    if dtype == "normal":
        mean = dist.get("mean", value)
        std = dist["std"]
        return stats.norm.pdf(x, loc=mean, scale=std)

    if dtype == "lognormal":
        mean = dist.get("mean", value)
        std = dist["std"]
        variance = std ** 2
        mu = np.log(mean ** 2 / np.sqrt(variance + mean ** 2))
        sigma = np.sqrt(np.log(1 + variance / mean ** 2))
        return stats.lognorm.pdf(x, s=sigma, scale=np.exp(mu))

    return None


def _render_single_param(name, spec, slug, group, n, rng):
    """Render a single parameter with fully editable distribution.

    Returns an override dict if anything changed, else None.
    """
    value = spec["value"]
    unit = spec.get("unit", "")
    desc = spec.get("description", "")
    justification = spec.get("justification", "")
    dist = spec.get("distribution", {})
    dist_type = dist.get("type", "fixed") if dist else "fixed"

    with st.expander(f"**{name}** – {value} {unit}", expanded=False):
        col_edit, col_chart = st.columns([2, 3])

        changed = False
        new_spec = {"value": value}

        with col_edit:
            # Distribution type selector
            key_prefix = f"mc_{slug}_{group}_{name}"
            type_idx = DIST_TYPES.index(dist_type) if dist_type in DIST_TYPES else 0
            new_type = st.selectbox(
                "Distribution type",
                DIST_TYPES,
                index=type_idx,
                key=f"{key_prefix}_type",
            )

            if new_type != dist_type:
                changed = True

            # Base value
            if isinstance(value, int):
                new_val = st.number_input(
                    f"Base value ({unit})",
                    value=value,
                    step=max(1, value // 10) if value != 0 else 1,
                    key=f"{key_prefix}_val",
                )
            else:
                step = max(0.01, abs(value) / 20) if value != 0 else 0.01
                new_val = st.number_input(
                    f"Base value ({unit})",
                    value=float(value),
                    step=step,
                    format="%.4g",
                    key=f"{key_prefix}_val",
                )

            if new_val != value:
                changed = True
            new_spec["value"] = new_val

            # Distribution-specific parameters
            new_dist = {"type": new_type}

            if new_type == "triangular":
                d_low = dist.get("low", value * 0.5) if dist_type == "triangular" else value * 0.5
                d_mode = dist.get("mode", value) if dist_type == "triangular" else value
                d_high = dist.get("high", value * 1.5) if dist_type == "triangular" else value * 1.5

                new_low = st.number_input("Low", value=float(d_low), format="%.4g",
                                          key=f"{key_prefix}_low")
                new_mode = st.number_input("Mode", value=float(d_mode), format="%.4g",
                                           key=f"{key_prefix}_mode")
                new_high = st.number_input("High", value=float(d_high), format="%.4g",
                                           key=f"{key_prefix}_high")
                new_dist["low"] = new_low
                new_dist["mode"] = new_mode
                new_dist["high"] = new_high

                if (dist_type != "triangular"
                        or new_low != d_low or new_mode != d_mode or new_high != d_high):
                    changed = True

            elif new_type == "uniform":
                d_low = dist.get("low", value * 0.5) if dist_type == "uniform" else value * 0.5
                d_high = dist.get("high", value * 1.5) if dist_type == "uniform" else value * 1.5

                new_low = st.number_input("Low", value=float(d_low), format="%.4g",
                                          key=f"{key_prefix}_low")
                new_high = st.number_input("High", value=float(d_high), format="%.4g",
                                           key=f"{key_prefix}_high")
                new_dist["low"] = new_low
                new_dist["high"] = new_high

                if dist_type != "uniform" or new_low != d_low or new_high != d_high:
                    changed = True

            elif new_type == "normal":
                d_mean = dist.get("mean", value) if dist_type == "normal" else value
                d_std = dist.get("std", value * 0.2) if dist_type == "normal" else value * 0.2

                new_mean = st.number_input("Mean", value=float(d_mean), format="%.4g",
                                           key=f"{key_prefix}_mean")
                new_std = st.number_input("Std dev", value=float(d_std), format="%.4g",
                                          key=f"{key_prefix}_std")
                new_dist["mean"] = new_mean
                new_dist["std"] = new_std

                if dist_type != "normal" or new_mean != d_mean or new_std != d_std:
                    changed = True

            elif new_type == "lognormal":
                d_mean = dist.get("mean", value) if dist_type == "lognormal" else value
                d_std = dist.get("std", value * 0.5) if dist_type == "lognormal" else value * 0.5

                new_mean = st.number_input("Mean", value=float(d_mean), format="%.4g",
                                           key=f"{key_prefix}_mean")
                new_std = st.number_input("Std dev", value=float(d_std), format="%.4g",
                                          key=f"{key_prefix}_std")
                new_dist["mean"] = new_mean
                new_dist["std"] = new_std

                if dist_type != "lognormal" or new_mean != d_mean or new_std != d_std:
                    changed = True

            # else: fixed, no extra params

            new_spec["distribution"] = new_dist

            # Per-parameter reset
            if changed:
                if st.button("Reset to default", key=f"reset_{key_prefix}"):
                    keys_to_clear = [k for k in st.session_state if k.startswith(key_prefix)]
                    for k in keys_to_clear:
                        del st.session_state[k]
                    st.rerun()

        # Chart + justification
        with col_chart:
            active_dist = new_dist if changed else dist
            active_type = new_type if changed else dist_type
            active_val = new_val

            if active_type != "fixed" and active_val != 0:
                active_spec = {"value": active_val, "distribution": active_dist}
                try:
                    samples = sample(active_spec, n, rng)
                except Exception:
                    samples = None

                if samples is not None and len(samples) > 0:
                    fig = go.Figure()

                    fig.add_trace(go.Histogram(
                        x=samples,
                        nbinsx=50,
                        marker_color=COLORS["primary"],
                        opacity=0.5,
                        name="MC samples",
                        histnorm="probability density",
                    ))

                    x_range = np.linspace(samples.min(), samples.max(), 200)
                    pdf_vals = _theoretical_pdf(active_dist, active_val, x_range)
                    if pdf_vals is not None:
                        fig.add_trace(go.Scatter(
                            x=x_range, y=pdf_vals,
                            mode="lines", name="Theoretical PDF",
                            line=dict(color=COLORS["go"], width=2.5),
                        ))

                    fig.add_vline(
                        x=active_val, line_dash="dash", line_color="#ffffff",
                        annotation_text=f"Base: {active_val}",
                        annotation_position="top right",
                        annotation_font_size=10,
                    )

                    if active_type in ("triangular", "uniform"):
                        fig.add_vline(x=active_dist.get("low", 0), line_dash="dot",
                                      line_color=COLORS["text_muted"])
                        fig.add_vline(x=active_dist.get("high", 0), line_dash="dot",
                                      line_color=COLORS["text_muted"])

                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(13,17,23,1)",
                        xaxis_title=f"{name} ({unit})",
                        yaxis_title="Density",
                        font_family="Syne",
                        height=250,
                        margin=dict(t=10, b=30, l=40, r=10),
                        legend=dict(x=0.65, y=0.95, font_size=9),
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown(f"**Fixed value:** {active_val} {unit}")

            if desc:
                st.markdown(f"**Description:** {_esc(desc)}")
            if justification:
                st.markdown(f"**Justification:** {_esc(justification)}")

    return new_spec if changed else None
