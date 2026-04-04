"""
NEOWATT Technoeconomic Model — Streamlit App
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
from dashboard.overview import render_overview
from dashboard.deep_dive import render_deep_dive
from dashboard.sensitivity_view import render_sensitivity
from dashboard.market_view import render_market_size, render_why_now
from dashboard.comparison_view import render_comparison
from dashboard.inputs_view import render_inputs

from neowatt.data_loader import load_global_params, load_use_cases
from neowatt.monte_carlo import run_all_use_cases
from neowatt.sensitivity import tornado_analysis
from neowatt.market import why_now_analysis

# ── Styling ──────────────────────────────────────────────────────────────────
apply_styles()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("# ⚡ NEOWATT — Technoeconomic Model")
st.markdown("*Space power beaming · Use case prioritisation · Monte Carlo analysis*")
st.divider()

# ── Load data ────────────────────────────────────────────────────────────────
global_params = load_global_params()
use_cases = load_use_cases()

# ── Sidebar controls ────────────────────────────────────────────────────────
settings = render_sidebar(use_cases, global_params)

# Apply launch cost override to global params
modified_gp = copy.deepcopy(global_params)
modified_gp["global"]["launch_cost_per_kg"]["value"] = settings["launch_cost"]
modified_gp["global"]["required_margin_over_incumbent"] = settings["required_margin"]

# ── Run Monte Carlo ──────────────────────────────────────────────────────────
results = run_all_use_cases(
    use_cases=use_cases,
    global_params=modified_gp,
    n_simulations=settings["n_simulations"],
    overrides=settings["overrides"],
)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_overview, tab_deep, tab_inputs, tab_sens, tab_market, tab_compare = st.tabs([
    "Overview", "Deep Dive", "Inputs & Distributions", "Sensitivity", "Market & Why Now", "Comparison"
])

with tab_overview:
    render_overview(results, settings["required_margin"])

with tab_deep:
    selected = settings["selected_slug"]
    if selected in results:
        render_deep_dive(results[selected], use_cases[selected], settings["required_margin"])

with tab_inputs:
    selected = settings["selected_slug"]
    render_inputs(use_cases[selected])

with tab_sens:
    selected = settings["selected_slug"]
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

with tab_market:
    render_market_size(results)
    st.divider()
    selected = settings["selected_slug"]
    with st.spinner("Computing trajectory..."):
        trajectory = why_now_analysis(
            selected, use_cases, modified_gp,
            n_simulations=min(settings["n_simulations"], 3000),
        )
    render_why_now(trajectory, results[selected].use_case_name)

with tab_compare:
    render_comparison(results)

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "NEOWATT Technoeconomic Model v2.0 · "
    f"{settings['n_simulations']:,} simulations · "
    f"Required margin: {settings['required_margin']:.0%} · "
    "All parameters are estimates — validate through customer discovery"
)
