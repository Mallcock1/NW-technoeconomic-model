"""
NEOWATT Technoeconomic Model – Streamlit App
Run: pip install -r requirements.txt && streamlit run app.py
"""

import streamlit as st
import copy

st.set_page_config(
    page_title="NEOWATT | Technoeconomic Model",
    page_icon="⚡",
    layout="wide",
)

from dashboard.styles import apply_styles
from dashboard.sidebar import render_sidebar

from neowatt.data_loader import load_global_params, load_use_cases

# ── Styling ──────────────────────────────────────────────────────────────────
apply_styles()

# ── Load data ────────────────────────────────────────────────────────────────
global_params = load_global_params()
use_cases = load_use_cases()

# ── Sidebar controls ────────────────────────────────────────────────────────
settings = render_sidebar(use_cases, global_params)

# Apply global overrides
modified_gp = copy.deepcopy(global_params)
modified_gp["global"]["required_margin_over_incumbent"] = settings["required_margin"]

mode = settings["mode"]
selected = settings["selected_slug"]
time_dep = settings["time_dependent"]

# ── Point Estimates mode ────────────────────────────────────────────────────
if mode == "Point Estimates":
    from dashboard.point_estimates import render_point_estimates
    from dashboard.inputs_point import render_inputs_point
    from dashboard.comparison_view import render_comparison_point
    from dashboard.incumbent_view import render_incumbent_view
    from dashboard.unit_economics_view import render_unit_economics
    from dashboard.portfolio_view import render_portfolio

    # Initialise override storage in session_state
    ss_key = f"overrides_pt_{selected}"
    if ss_key not in st.session_state:
        st.session_state[ss_key] = {}

    tabs_list = ["Overview", "Input Parameters", "Unit Economics",
                 "Portfolio", "Incumbents", "Comparison"]
    if time_dep:
        tabs_list.append("Time Dependency")

    tabs = st.tabs(tabs_list)

    with tabs[1]:  # Input Parameters
        overrides = render_inputs_point(use_cases[selected], selected)
        if overrides:
            st.session_state[ss_key] = overrides

    # Apply overrides to use_cases for this run
    active_overrides = st.session_state.get(ss_key, {})
    uc_with_overrides = copy.deepcopy(use_cases)
    if active_overrides:
        for group, group_ov in active_overrides.items():
            for pname, new_val in group_ov.items():
                if (group in uc_with_overrides[selected]
                        and pname in uc_with_overrides[selected][group]):
                    uc_with_overrides[selected][group][pname]["value"] = new_val

    with tabs[0]:  # Overview
        settings_with_ov = {**settings, "overrides": {}}
        render_point_estimates(uc_with_overrides, modified_gp, settings_with_ov)

    with tabs[2]:  # Unit Economics
        render_unit_economics(uc_with_overrides, modified_gp, settings["required_margin"])

    with tabs[3]:  # Portfolio
        render_portfolio(uc_with_overrides, modified_gp, settings["required_margin"])

    with tabs[4]:  # Incumbents
        render_incumbent_view(uc_with_overrides)

    with tabs[5]:  # Comparison
        render_comparison_point(uc_with_overrides, modified_gp, settings["required_margin"])

    if time_dep:
        from dashboard.temporal_view import render_temporal_point
        from neowatt.temporal import run_time_series_point

        with tabs[6]:  # Time Dependency
            with st.spinner("Computing time-dependent results..."):
                ts_results = run_time_series_point(
                    uc_with_overrides, modified_gp,
                    settings["year_start"], settings["year_end"],
                    settings["year_step"], settings["required_margin"],
                )
            render_temporal_point(ts_results, selected, settings["required_margin"])

# ── Monte Carlo mode ────────────────────────────────────────────────────────
else:
    from dashboard.overview import render_overview
    from dashboard.deep_dive import render_deep_dive
    from dashboard.sensitivity_view import render_sensitivity
    from dashboard.comparison_view import render_comparison
    from dashboard.inputs_view import render_inputs
    from neowatt.monte_carlo import run_all_use_cases
    from neowatt.sensitivity import tornado_analysis

    # Initialise override storage
    ss_key = f"overrides_mc_{selected}"
    if ss_key not in st.session_state:
        st.session_state[ss_key] = {}

    tabs_list = ["Overview", "Deep Dive", "Inputs & Distributions",
                 "Sensitivity", "Comparison"]
    if time_dep:
        tabs_list.append("Time Dependency")

    tabs = st.tabs(tabs_list)

    # Collect overrides from inputs tab
    with tabs[2]:  # Inputs & Distributions
        overrides = render_inputs(use_cases[selected], selected)
        if overrides:
            st.session_state[ss_key] = overrides

    # Build overrides dict for MC engine
    active_overrides = st.session_state.get(ss_key, {})
    mc_overrides = {}
    if active_overrides:
        mc_overrides[selected] = active_overrides

    results = run_all_use_cases(
        use_cases=use_cases,
        global_params=modified_gp,
        n_simulations=settings["n_simulations"],
        overrides=mc_overrides,
    )

    with tabs[0]:  # Overview
        render_overview(results, settings["required_margin"])

    with tabs[1]:  # Deep Dive
        if selected in results:
            render_deep_dive(results[selected], use_cases[selected], settings["required_margin"])

    with tabs[3]:  # Sensitivity
        if selected in results:
            metric_choice = st.radio(
                "Sensitivity target metric",
                ["cost_per_W", "gross_margin", "customer_saving_pct"],
                horizontal=True,
            )
            metric_labels = {
                "cost_per_W": "cost/W",
                "gross_margin": "gross margin",
                "customer_saving_pct": "customer saving",
            }
            with st.spinner("Running sensitivity analysis..."):
                tornado = tornado_analysis(
                    selected, use_cases, modified_gp,
                    target_metric=metric_choice,
                    n_simulations=min(settings["n_simulations"], 3000),
                )
            render_sensitivity(tornado, base_metric_name=metric_labels[metric_choice])

    with tabs[4]:  # Comparison
        render_comparison(results)

    if time_dep:
        from dashboard.temporal_view import render_temporal_mc
        from neowatt.temporal import run_time_series_mc

        with tabs[5]:  # Time Dependency
            with st.spinner("Computing time-dependent MC results..."):
                mc_ts = run_time_series_mc(
                    use_cases, modified_gp,
                    settings["year_start"], settings["year_end"],
                    settings["year_step"],
                    n_simulations=min(settings["n_simulations"], 3000),
                )
            render_temporal_mc(mc_ts, selected, settings["required_margin"])

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
footer = f"NEOWATT Technoeconomic Model v2.0 · Mode: {mode}"
if mode == "Monte Carlo":
    footer += f" · {settings['n_simulations']:,} simulations"
if time_dep:
    footer += f" · Years: {settings['year_start']}-{settings['year_end']}"
footer += (f" · Required margin: {settings['required_margin']:.0%}"
           " · All parameters are estimates – validate through customer discovery")
st.caption(footer)
