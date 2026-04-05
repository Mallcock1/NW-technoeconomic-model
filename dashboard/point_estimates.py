"""Point estimates tab: deterministic model results using base values only (no Monte Carlo)."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import re

from dashboard.styles import COLORS, decision_emoji
from neowatt.data_loader import get_param_value


def _esc_prose(text: str) -> str:
    """Escape lone dollar signs in prose text without breaking $$ LaTeX blocks."""
    if not text:
        return text
    return re.sub(r'(?<!\$)\$(?!\$)', r'\\$', text).replace("~", "\\~")

def _compute_point_estimate(uc_params: dict, global_params: dict, required_margin: float) -> dict:
    """Compute a single deterministic point estimate for a use case."""
    meta = uc_params["meta"]
    slug = meta["slug"]
    inc = uc_params.get("incumbent", {})
    tech = uc_params.get("technical", {})
    cost = uc_params.get("cost", {})
    econ = uc_params.get("economic", {})
    gp = global_params["global"]

    launch_cost = get_param_value(econ.get("launch_cost_per_kg", {"value": 5000}))
    model_class_name = meta["model_class"]
    is_hardware_sale = model_class_name in (
        "HardwareSaleModel", "HardwarePVFreeModel", "HardwareCovertModel",
    )

    # CAPEX
    tx_hw = get_param_value(cost.get("tx_hardware_k", {"value": 0})) * 1000
    rx_hw = get_param_value(cost.get("rx_hardware_k", {"value": 0})) * 1000
    tx_mass = get_param_value(cost.get("tx_mass_kg", {"value": 0}))
    rx_mass = get_param_value(cost.get("rx_mass_kg", {"value": 0}))
    ground = get_param_value(cost.get("ground_segment_k", {"value": 0})) * 1000

    if is_hardware_sale:
        # Hardware sale: NEOWATT pays manufacturing only, no launch
        capex = tx_hw + rx_hw + ground
    else:
        # Service: NEOWATT pays manufacturing + launch
        capex = tx_hw + rx_hw + (tx_mass + rx_mass) * launch_cost + ground

    # Annual OPEX
    opex_yr = get_param_value(cost.get("ops_cost_k_yr", {"value": 0})) * 1000

    # Amortization
    amort = get_param_value(econ.get("amortization_years", {"value": 7}))

    # Total cost
    total_cost = capex + opex_yr * amort

    # Annual revenue (model-dependent)
    annual_revenue = _compute_annual_revenue_point(model_class_name, uc_params, gp)

    # Total revenue
    total_revenue = annual_revenue * amort

    # Gross margin
    if total_revenue > 0:
        gross_margin = (total_revenue - total_cost) / total_revenue
    else:
        gross_margin = -999

    # Power and cost/W
    power = get_param_value(tech.get("power_delivered_W", {"value": 1}))
    cost_per_W = total_cost / power if power > 0 else float("inf")

    # Incumbent cost and customer saving
    incumbent_type = meta.get("incumbent_type", "standard")
    inc_cost, our_price, saving = _compute_saving_point(model_class_name, uc_params, gp, amort)

    # Decision
    if incumbent_type == "greenfield":
        viable = total_revenue > total_cost
        label = "GO" if viable else "KILL"
    else:
        viable = saving >= required_margin
        if viable:
            label = "GO"
        elif saving >= required_margin * 0.5:
            label = "MARGINAL"
        else:
            label = "KILL"

    # TX and RX cost breakdown (for charts)
    if is_hardware_sale:
        tx_total = tx_hw  # no launch cost for NEOWATT
        rx_total = rx_hw
    else:
        tx_total = tx_hw + tx_mass * launch_cost
        rx_total = rx_hw + rx_mass * launch_cost

    # Breakeven price: the max we can charge and still meet required_margin
    # saving = (inc_cost - price) / inc_cost >= required_margin
    # => price <= inc_cost * (1 - required_margin)
    if inc_cost > 0 and incumbent_type != "greenfield":
        breakeven_price = inc_cost * (1 - required_margin)
    else:
        breakeven_price = None

    return {
        "slug": slug,
        "name": meta["name"],
        "model_class": model_class_name,
        "category": meta.get("category", ""),
        "horizon": meta.get("time_horizon", ""),
        "incumbent_name": inc.get("name", "N/A"),
        "incumbent_type": incumbent_type,
        "capex": capex,
        "tx_cost": tx_total,
        "rx_cost": rx_total,
        "opex_yr": opex_yr,
        "total_cost": total_cost,
        "annual_revenue": annual_revenue,
        "total_revenue": total_revenue,
        "gross_margin": gross_margin,
        "cost_per_W": cost_per_W,
        "power_W": power,
        "inc_cost": inc_cost,
        "our_price": our_price,
        "customer_saving": saving,
        "amort_years": amort,
        "decision": label,
        "breakeven_price": breakeven_price,
        "ground_cost": ground,
    }


def _compute_annual_revenue_point(model_class: str, uc_params: dict, gp: dict) -> float:
    """Compute annual revenue from point estimates, dispatched by model class."""
    tech = uc_params.get("technical", {})
    econ = uc_params.get("economic", {})

    if model_class == "StandardPowerModel":
        power = get_param_value(tech.get("power_delivered_W", {"value": 0}))
        wtp = get_param_value(econ.get("wtp_per_W", {"value": 0}))
        duty = get_param_value(tech.get("duty_cycle", {"value": 1.0}))
        avail = get_param_value(tech.get("availability", {"value": 0.90}))
        return power * wtp * duty * avail

    if model_class == "LifeExtensionModel":
        return get_param_value(econ.get("revenue_per_year_k", {"value": 0})) * 1000

    if model_class == "PeakPowerModel":
        power_kW = get_param_value(tech.get("power_delivered_W", {"value": 0})) / 1000
        burst = get_param_value(tech.get("burst_duration_hrs", {"value": 0}))
        events = get_param_value(tech.get("events_per_year", {"value": 0}))
        wtp_kwh = get_param_value(econ.get("wtp_per_kWh", {"value": 0}))
        avail = get_param_value(tech.get("availability", {"value": 0.85}))
        return wtp_kwh * power_kW * burst * events * avail

    if model_class == "PowerAsServiceModel":
        sub = get_param_value(econ.get("subscription_price_k_yr", {"value": 0})) * 1000
        customers = get_param_value(econ.get("customers_served", {"value": 1}))
        return sub * customers

    if model_class == "LightweightSCModel":
        mass_saved = get_param_value(tech.get("mass_saved_kg", {"value": 0}))
        launch_cost = get_param_value(econ.get("launch_cost_per_kg", {"value": 5000}))
        array_cost = get_param_value(uc_params["incumbent"].get("array_cost_per_kg", {"value": 0}))
        amort = get_param_value(econ.get("amortization_years", {"value": 7}))
        return (mass_saved * (launch_cost + array_cost)) / amort

    if model_class == "AttitudeIndependentModel":
        return get_param_value(tech.get("payload_ops_gain_k_yr", {"value": 0})) * 1000

    if model_class == "StealthModel":
        power = get_param_value(tech.get("power_delivered_W", {"value": 0}))
        wtp = get_param_value(econ.get("wtp_per_W", {"value": 0}))
        premium = get_param_value(tech.get("defence_wtp_premium", {"value": 1.0}))
        avail = get_param_value(tech.get("availability", {"value": 0.90}))
        return power * wtp * premium * avail

    if model_class == "DebrisAblationModel":
        objects = get_param_value(tech.get("objects_per_year", {"value": 0}))
        wtp = get_param_value(econ.get("wtp_per_object_k", {"value": 0})) * 1000
        avail = get_param_value(tech.get("availability", {"value": 0.85}))
        return objects * wtp * avail

    if model_class in ("HardwareSaleModel", "HardwarePVFreeModel"):
        tx_sale = get_param_value(econ.get("tx_sale_price_k", {"value": 0})) * 1000
        rx_sale = get_param_value(econ.get("rx_sale_price_k", {"value": 0})) * 1000
        amort = get_param_value(econ.get("amortization_years", {"value": 7}))
        support = get_param_value(econ.get("annual_support_k", {"value": 0})) * 1000
        return (tx_sale + rx_sale) / amort + support

    if model_class == "HardwareCovertModel":
        tx_sale = get_param_value(econ.get("tx_sale_price_k", {"value": 0})) * 1000
        rx_sale = get_param_value(econ.get("rx_sale_price_k", {"value": 0})) * 1000
        premium = get_param_value(tech.get("defence_wtp_premium", {"value": 1.0}))
        amort = get_param_value(econ.get("amortization_years", {"value": 8}))
        support = get_param_value(econ.get("annual_support_k", {"value": 0})) * 1000
        return (tx_sale + rx_sale) * premium / amort + support

    return 0


def _compute_saving_point(model_class: str, uc_params: dict, gp: dict, amort: float):
    """Compute incumbent cost, our price, and customer saving % from point estimates."""
    inc = uc_params.get("incumbent", {})
    econ = uc_params.get("economic", {})
    tech = uc_params.get("technical", {})
    cost = uc_params.get("cost", {})

    if model_class in ("StandardPowerModel",):
        inc_cost = get_param_value(inc.get("cost_per_W", {"value": 0}))
        our_price = get_param_value(econ.get("wtp_per_W", {"value": 0}))
    elif model_class == "LifeExtensionModel":
        inc_cost = get_param_value(inc.get("cost_per_year_k", {"value": 0})) * 1000
        our_price = get_param_value(econ.get("revenue_per_year_k", {"value": 0})) * 1000
    elif model_class == "PowerAsServiceModel":
        inc_cost = get_param_value(inc.get("capex_avoided_per_customer_k", {"value": 0})) * 1000
        our_price = get_param_value(econ.get("subscription_price_k_yr", {"value": 0})) * 1000 * amort
    elif model_class == "LightweightSCModel":
        inc_cost = get_param_value(inc.get("array_cost_per_kg", {"value": 0}))
        launch_cost = get_param_value(econ.get("launch_cost_per_kg", {"value": 5000}))
        rx_hw = get_param_value(cost.get("rx_hardware_k", {"value": 0})) * 1000
        rx_mass = get_param_value(cost.get("rx_mass_kg", {"value": 0}))
        mass_saved = get_param_value(tech.get("mass_saved_kg", {"value": 1}))
        our_price = (rx_hw + rx_mass * launch_cost) / max(mass_saved, 1)
    elif model_class == "AttitudeIndependentModel":
        inc_cost = get_param_value(inc.get("cost_per_spacecraft_k", {"value": 0})) * 1000
        rx_hw = get_param_value(cost.get("rx_hardware_k", {"value": 0})) * 1000
        launch_cost = get_param_value(econ.get("launch_cost_per_kg", {"value": 5000}))
        rx_mass = get_param_value(cost.get("rx_mass_kg", {"value": 0}))
        our_price = rx_hw + rx_mass * launch_cost
    elif model_class == "StealthModel":
        inc_cost = get_param_value(inc.get("cost_per_spacecraft_k", {"value": 0})) * 1000
        wtp = get_param_value(econ.get("wtp_per_W", {"value": 0}))
        power = get_param_value(tech.get("power_delivered_W", {"value": 0}))
        our_price = wtp * power
    elif model_class == "PeakPowerModel":
        inc_cost = get_param_value(inc.get("cost_per_W", {"value": 0}))
        wtp_kwh = get_param_value(econ.get("wtp_per_kWh", {"value": 0}))
        power_kW = get_param_value(tech.get("power_delivered_W", {"value": 0})) / 1000
        burst = get_param_value(tech.get("burst_duration_hrs", {"value": 0}))
        events = get_param_value(tech.get("events_per_year", {"value": 0}))
        avail = get_param_value(tech.get("availability", {"value": 0.85}))
        power_W = get_param_value(tech.get("power_delivered_W", {"value": 1}))
        total_cost_cust = wtp_kwh * power_kW * burst * events * avail * amort
        our_price = total_cost_cust / power_W if power_W > 0 else float("inf")
    elif model_class == "DebrisAblationModel":
        inc_cost = get_param_value(inc.get("cost_per_object_k", {"value": 0})) * 1000
        our_price = get_param_value(econ.get("wtp_per_object_k", {"value": 0})) * 1000
    elif model_class == "HardwareSaleModel":
        inc_cost = get_param_value(inc.get("cost_per_W", {"value": 0}))
        tx_sale = get_param_value(econ.get("tx_sale_price_k", {"value": 0})) * 1000
        rx_sale = get_param_value(econ.get("rx_sale_price_k", {"value": 0})) * 1000
        power = get_param_value(tech.get("power_delivered_W", {"value": 1}))
        our_price = (tx_sale + rx_sale) / power if power > 0 else float("inf")
    elif model_class == "HardwarePVFreeModel":
        inc_cost = get_param_value(inc.get("array_cost_per_kg", {"value": 0}))
        rx_sale = get_param_value(econ.get("rx_sale_price_k", {"value": 0})) * 1000
        mass_saved = get_param_value(tech.get("mass_saved_kg", {"value": 1}))
        our_price = rx_sale / max(mass_saved, 1)
    elif model_class == "HardwareCovertModel":
        inc_cost = get_param_value(inc.get("cost_per_spacecraft_k", {"value": 0})) * 1000
        tx_sale = get_param_value(econ.get("tx_sale_price_k", {"value": 0})) * 1000
        rx_sale = get_param_value(econ.get("rx_sale_price_k", {"value": 0})) * 1000
        our_price = tx_sale + rx_sale
    else:
        inc_cost = 0
        our_price = 0

    if inc_cost > 0:
        saving = (inc_cost - our_price) / inc_cost
    else:
        saving = 0

    return inc_cost, our_price, saving


def render_point_estimates(use_cases: dict, global_params: dict, settings: dict):
    """Render the Point Estimates tab with deterministic model results."""
    required_margin = settings["required_margin"]
    selected_slug = settings["selected_slug"]

    st.markdown("## Overview")
    st.caption("Deterministic evaluation using base values for all parameters.")

    # Compute all point estimates
    estimates = {}
    for slug, uc in use_cases.items():
        estimates[slug] = _compute_point_estimate(uc, global_params, required_margin)

    # Summary table
    rows = []
    for slug, e in estimates.items():
        rows.append({
            "Use Case": e["name"],
            "Category": e["category"],
            "Horizon": e["horizon"],
            "Decision": f"{decision_emoji(e['decision'])} {e['decision']}",
            "CAPEX": f"${e['capex']:,.0f}",
            "OPEX/yr": f"${e['opex_yr']:,.0f}",
            "Revenue/yr": f"${e['annual_revenue']:,.0f}",
            "Gross Margin": f"{e['gross_margin'] * 100:.0f}%",
            "Cust. Saving": f"{e['customer_saving'] * 100:+.0f}%",
            "Cost/W": f"${e['cost_per_W']:,.0f}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detail for selected use case
    st.divider()
    e = estimates[selected_slug]
    uc = use_cases[selected_slug]
    meta = uc["meta"]

    st.markdown(f"### {decision_emoji(e['decision'])} {e['name']}")

    # Use case description
    uc_description = meta.get("description", "")
    if uc_description:
        with st.expander("Use case description", expanded=False):
            st.markdown(_esc_prose(uc_description))

    # Model details
    model_prose = meta.get("model_prose", "")
    model_maths = meta.get("model_maths", "")
    if model_prose or model_maths:
        with st.expander("Model details", expanded=False):
            if model_prose:
                st.markdown(_esc_prose(model_prose))
            if model_maths:
                st.divider()
                st.markdown(model_maths)

    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("CAPEX", f"${e['capex']:,.0f}")
    with col2:
        st.metric("Annual Revenue", f"${e['annual_revenue']:,.0f}")
    with col3:
        st.metric("Gross Margin", f"{e['gross_margin'] * 100:.0f}%")
    with col4:
        st.metric("Customer Saving", f"{e['customer_saving'] * 100:+.0f}%")
    with col5:
        st.metric("Cost/W", f"${e['cost_per_W']:,.0f}")

    # Cost waterfall
    st.markdown("#### NEOWATT Cost Breakdown")
    lc = get_param_value(uc.get("economic", {}).get("launch_cost_per_kg", {"value": 5000}))
    cost_data = uc.get("cost", {})

    items = []
    vals = []
    colors = []

    tx_hw_val = get_param_value(cost_data.get("tx_hardware_k", {"value": 0})) * 1000
    items.append("TX Manufacturing"); vals.append(tx_hw_val); colors.append(COLORS["primary"])

    rx_hw_val = get_param_value(cost_data.get("rx_hardware_k", {"value": 0})) * 1000
    if rx_hw_val > 0:
        items.append("RX Manufacturing"); vals.append(rx_hw_val); colors.append(COLORS["primary"])

    # Only show launch costs for service models (NEOWATT pays launch)
    if not is_hardware_sale:
        tx_launch_val = get_param_value(cost_data.get("tx_mass_kg", {"value": 0})) * lc
        items.append("TX Launch"); vals.append(tx_launch_val); colors.append(COLORS["primary"])

        rx_mass_val = get_param_value(cost_data.get("rx_mass_kg", {"value": 0}))
        rx_launch_val = rx_mass_val * lc
        if rx_launch_val > 0:
            items.append("RX Launch"); vals.append(rx_launch_val); colors.append(COLORS["primary"])

    ground_val = get_param_value(cost_data.get("ground_segment_k", {"value": 0})) * 1000
    items.append("Ground Segment"); vals.append(ground_val); colors.append(COLORS["primary"])

    opex_total = e["opex_yr"] * e["amort_years"]
    items.append(f"Total OPEX\n({e['amort_years']:.0f}yr lifetime)")
    vals.append(opex_total)
    colors.append(COLORS["marginal"])

    fig = go.Figure(go.Bar(
        x=items,
        y=[v / 1000 for v in vals],
        marker_color=colors,
        text=[f"${v/1000:.0f}k" for v in vals],
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        yaxis_title="Cost ($k)",
        font_family="Syne",
        height=350,
        margin=dict(t=20, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


