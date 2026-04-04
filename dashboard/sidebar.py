"""Sidebar controls for the Streamlit dashboard."""

import streamlit as st


def render_sidebar(use_cases: dict, global_params: dict) -> dict:
    """Render sidebar controls and return settings dict."""
    gp = global_params["global"]

    with st.sidebar:
        st.markdown("## ⚡ NEOWATT")
        st.markdown("#### Technoeconomic Analysis")
        st.caption("Space power beaming · Use case prioritisation · Monte Carlo analysis")

        with st.expander("About", expanded=False):
            st.markdown(
                "This dashboard evaluates **12 use cases** for space power beaming technology. "
                "For each use case, a technoeconomic model computes costs, revenues, and customer "
                "savings vs the incumbent solution. **Point Estimates** give a quick deterministic "
                "view; **Monte Carlo** propagates uncertainty through every input parameter to "
                "produce probability distributions on viability."
            )

        st.divider()
        st.markdown("### Analysis Mode")
        mode = st.radio(
            "Mode",
            ["Point Estimates", "Monte Carlo"],
            horizontal=True,
            label_visibility="collapsed",
        )

        st.divider()
        st.markdown("### Select Use Case")

        slug_names = {}
        for slug, uc in use_cases.items():
            name = uc["meta"]["name"]
            slug_names[name] = slug

        selected_name = st.selectbox("Use case to detail", list(slug_names.keys()))
        selected_slug = slug_names[selected_name]

        st.divider()
        st.markdown("### Global Parameters")

        req_margin = st.slider(
            "Required margin over incumbent (%)",
            0, 1000,
            int(gp.get("required_margin_over_incumbent", 0.50) * 100),
        ) / 100

        # MC-only: simulation count
        n_sim = gp.get("default_n_simulations", 10000)
        if mode == "Monte Carlo":
            n_sim = st.slider(
                "Monte Carlo simulations",
                10, 100000,
                n_sim,
                step=10,
            )

        # Time dependency
        st.divider()
        st.markdown("### Time Dependency")
        time_dependent = st.toggle("Enable time-dependent parameters", value=False)

        year_start = 2025
        year_end = 2035
        year_step = 1

        if time_dependent:
            year_range = st.slider(
                "Year range",
                2025, 2040,
                (2025, 2035),
            )
            year_start, year_end = year_range
            year_step = st.selectbox("Year step", [1, 2, 5], index=0)

    return {
        "mode": mode,
        "n_simulations": n_sim,
        "required_margin": req_margin,
        "selected_slug": selected_slug,
        "time_dependent": time_dependent,
        "year_start": year_start,
        "year_end": year_end,
        "year_step": year_step,
    }
