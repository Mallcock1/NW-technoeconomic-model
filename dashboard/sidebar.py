"""Sidebar controls for the Streamlit dashboard."""

import streamlit as st


def render_sidebar(use_cases: dict, global_params: dict) -> dict:
    """Render sidebar controls and return settings dict.

    Returns dict with keys: n_simulations, launch_cost, required_margin,
    selected_slug, overrides.
    """
    gp = global_params["global"]

    with st.sidebar:
        st.markdown("### Global Parameters")

        n_sim = st.slider(
            "Monte Carlo simulations",
            1000, 50000,
            gp.get("default_n_simulations", 10000),
            step=1000,
        )

        launch_cost_val = gp["launch_cost_per_kg"]["value"]
        launch_cost = st.slider(
            "Launch cost ($/kg)",
            1000, 20000, int(launch_cost_val), step=500,
        )

        req_margin = st.slider(
            "Required margin over incumbent (%)",
            10, 80,
            int(gp.get("required_margin_over_incumbent", 0.50) * 100),
        ) / 100

        st.divider()
        st.markdown("### Select Use Case")

        # Build name -> slug mapping
        slug_names = {}
        for slug, uc in use_cases.items():
            name = uc["meta"]["name"]
            slug_names[name] = slug

        selected_name = st.selectbox("Use case to detail", list(slug_names.keys()))
        selected_slug = slug_names[selected_name]
        selected_uc = use_cases[selected_slug]

        st.divider()
        st.markdown("### Override Parameters")

        overrides = {}

        # Power delivered
        tech = selected_uc.get("technical", {})
        if "power_delivered_W" in tech:
            power_val = tech["power_delivered_W"]["value"]
            power = st.number_input("Power delivered (W)", value=int(power_val), step=100)
            if power != power_val:
                overrides.setdefault("technical", {})["power_delivered_W"] = power

        # Link efficiency
        if "link_efficiency" in tech:
            eff_val = tech["link_efficiency"]["value"]
            eff = st.slider("Link efficiency", 0.01, 0.50, float(eff_val), step=0.01)
            if eff != eff_val:
                overrides.setdefault("technical", {})["link_efficiency"] = eff

        # WTP (varies by model type)
        econ = selected_uc.get("economic", {})
        if "wtp_per_W" in econ:
            wtp_val = econ["wtp_per_W"]["value"]
            wtp = st.number_input("WTP ($/W)", value=float(wtp_val), step=10.0)
            if wtp != wtp_val:
                overrides.setdefault("economic", {})["wtp_per_W"] = wtp
        elif "wtp_per_kWh" in econ:
            wtp_val = econ["wtp_per_kWh"]["value"]
            wtp = st.number_input("WTP ($/kWh)", value=float(wtp_val), step=10.0)
            if wtp != wtp_val:
                overrides.setdefault("economic", {})["wtp_per_kWh"] = wtp
        elif "revenue_per_year_k" in econ:
            rev_val = econ["revenue_per_year_k"]["value"]
            rev = st.number_input("Revenue ($k/yr)", value=float(rev_val), step=100.0)
            if rev != rev_val:
                overrides.setdefault("economic", {})["revenue_per_year_k"] = rev
        elif "subscription_price_k_yr" in econ:
            sub_val = econ["subscription_price_k_yr"]["value"]
            sub = st.number_input("Subscription ($k/yr)", value=float(sub_val), step=10.0)
            if sub != sub_val:
                overrides.setdefault("economic", {})["subscription_price_k_yr"] = sub

        # Incumbent cost
        inc = selected_uc.get("incumbent", {})
        if "cost_per_W" in inc:
            inc_val = inc["cost_per_W"]["value"]
            inc_cost = st.number_input("Incumbent cost ($/W)", value=float(inc_val), step=10.0)
            if inc_cost != inc_val:
                overrides.setdefault("incumbent", {})["cost_per_W"] = inc_cost

    return {
        "n_simulations": n_sim,
        "launch_cost": launch_cost,
        "required_margin": req_margin,
        "selected_slug": selected_slug,
        "overrides": {selected_slug: overrides} if overrides else {},
    }
