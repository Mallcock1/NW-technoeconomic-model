"""
NeoWatt Technoeconomic Model — Streamlit App
Run: pip install streamlit numpy pandas plotly && streamlit run neowatt_te_model.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass

st.set_page_config(
    page_title="NeoWatt | Technoeconomic Model",
    page_icon="⚡",
    layout="wide",
)

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif; font-weight: 800; }
code, .stCode { font-family: 'Space Mono', monospace; }

.metric-card {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.3rem 0;
}
.viable { border-left: 4px solid #3fb950; }
.marginal { border-left: 4px solid #d29922; }
.dead { border-left: 4px solid #f85149; }

.kill-badge {
    background: #f85149; color: white; border-radius: 4px;
    padding: 2px 8px; font-size: 0.75rem; font-weight: 700;
}
.go-badge {
    background: #3fb950; color: #0d1117; border-radius: 4px;
    padding: 2px 8px; font-size: 0.75rem; font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# ⚡ NeoWatt — Technoeconomic Model")
st.markdown("*Space power beaming · Use case prioritisation · Monte Carlo analysis*")
st.divider()

# ── Use Case Definitions ──────────────────────────────────────────────────────
USE_CASES = {
    "LEO Eclipse Extension": {
        "description": "Beam power to LEO satellites during eclipse to reduce solar panel overbuilding and extend duty cycle.",
        "incumbent": "Extra solar panels + batteries",
        "incumbent_cost_per_W": 300,   # $/W delivered in eclipse (battery + panel overbuild cost)
        "power_delivered_W": 500,
        "distance_km": 600,
        "link_efficiency": 0.12,
        "tx_cost_k": 180,
        "rx_cost_k": 60,
        "tx_mass_kg": 25,
        "rx_mass_kg": 8,
        "ops_cost_k_yr": 30,
        "amort_yrs": 7,
        "wtp_per_W": 220,
    },
    "HAPS Power (Terrestrial)": {
        "description": "Beam power from ground stations to HAPS vehicles, enabling indefinite station-keeping without fuel.",
        "incumbent": "Onboard solar + battery arrays",
        "incumbent_cost_per_W": 180,
        "power_delivered_W": 2000,
        "distance_km": 20,
        "link_efficiency": 0.22,
        "tx_cost_k": 120,
        "rx_cost_k": 40,
        "tx_mass_kg": 60,
        "rx_mass_kg": 5,
        "ops_cost_k_yr": 20,
        "amort_yrs": 10,
        "wtp_per_W": 140,
    },
    "Lunar Night Survival": {
        "description": "Beam power to lunar surface assets during the 14-day lunar night, replacing RTGs or hibernation.",
        "incumbent": "RTGs or mission hibernation",
        "incumbent_cost_per_W": 2500,
        "power_delivered_W": 200,
        "distance_km": 384400,
        "link_efficiency": 0.04,
        "tx_cost_k": 400,
        "rx_cost_k": 120,
        "tx_mass_kg": 80,
        "rx_mass_kg": 15,
        "ops_cost_k_yr": 80,
        "amort_yrs": 10,
        "wtp_per_W": 1800,
    },
    "In-Orbit Servicing": {
        "description": "Power for orbital tugs and servicers, enabling transfer manoeuvres without large onboard power systems.",
        "incumbent": "Onboard solar + battery",
        "incumbent_cost_per_W": 400,
        "power_delivered_W": 1000,
        "distance_km": 800,
        "link_efficiency": 0.10,
        "tx_cost_k": 200,
        "rx_cost_k": 80,
        "tx_mass_kg": 30,
        "rx_mass_kg": 12,
        "ops_cost_k_yr": 40,
        "amort_yrs": 8,
        "wtp_per_W": 300,
    },
    "Debris Laser Ablation": {
        "description": "Use high-power beamed laser to ablate debris surfaces, generating thrust to lower perigee for deorbit.",
        "incumbent": "No cost-effective solution exists",
        "incumbent_cost_per_W": 0,   # no clear incumbent $/W metric
        "power_delivered_W": 5000,
        "distance_km": 700,
        "link_efficiency": 0.08,
        "tx_cost_k": 600,
        "rx_cost_k": 0,  # no receiver — target IS the debris
        "tx_mass_kg": 100,
        "rx_mass_kg": 0,
        "ops_cost_k_yr": 100,
        "amort_yrs": 10,
        "wtp_per_W": 80,  # rough $/W equivalent from debris removal market
    },
}

LAUNCH_COST_PER_KG = 5000  # $/kg — current Falcon 9 rideshare approx

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Global Parameters")
    n_simulations = st.slider("Monte Carlo simulations", 1000, 50000, 10000, step=1000)
    launch_cost = st.slider("Launch cost ($/kg)", 1000, 20000, LAUNCH_COST_PER_KG, step=500)
    required_margin = st.slider("Required margin over incumbent (%)", 10, 80, 50) / 100
    uncertainty_pct = st.slider("Parameter uncertainty (±%)", 5, 50, 25)

    st.divider()
    st.markdown("### 📋 Select Use Case")
    selected_uc = st.selectbox("Use case to detail", list(USE_CASES.keys()))

    st.divider()
    st.markdown("### 🔧 Override Parameters")
    uc = USE_CASES[selected_uc]
    power_W = st.number_input("Power delivered (W)", value=uc["power_delivered_W"], step=100)
    link_eff = st.slider("Link efficiency", 0.01, 0.50, uc["link_efficiency"], step=0.01)
    wtp = st.number_input("WTP ($/W)", value=float(uc["wtp_per_W"]), step=10.0)
    incumbent_cost = st.number_input("Incumbent cost ($/W)", value=float(uc["incumbent_cost_per_W"]), step=10.0)

# ── Core calculation function ─────────────────────────────────────────────────
def run_model(uc_name, params, n_sim, launch_cost_per_kg, req_margin, unc):
    p = params.copy()
    unc_f = unc / 100

    def tri(val, f=unc_f):
        lo = val * (1 - f)
        hi = val * (1 + f)
        return np.random.triangular(lo, val, hi, n_sim)

    # Costs
    tx_cost = tri(p["tx_cost_k"]) * 1000
    rx_cost = tri(p["rx_cost_k"]) * 1000
    tx_launch = tri(p["tx_mass_kg"]) * launch_cost_per_kg
    rx_launch = tri(p["rx_mass_kg"]) * launch_cost_per_kg
    ops = tri(p["ops_cost_k_yr"]) * 1000 * p["amort_yrs"]
    total_cost = tx_cost + rx_cost + tx_launch + rx_launch + ops

    # Revenue / value
    power = tri(p["power_delivered_W"])
    wtp_sim = tri(p["wtp_per_W"])
    revenue = power * wtp_sim * p["amort_yrs"]  # simple: $/W × W × years (annualised)

    # Margin
    gross_margin = (revenue - total_cost) / revenue

    # Customer savings vs incumbent
    incumbent = tri(p["incumbent_cost_per_W"])
    customer_saving_pct = (incumbent - wtp_sim) / incumbent

    cost_per_W = total_cost / power  # our cost per W delivered
    viable = customer_saving_pct >= req_margin

    return {
        "gross_margin": gross_margin,
        "customer_saving_pct": customer_saving_pct,
        "cost_per_W": cost_per_W,
        "total_cost": total_cost,
        "revenue": revenue,
        "p_viable": viable.mean(),
        "viable": viable,
        "customer_saving_pct_median": np.median(customer_saving_pct),
        "cost_per_W_median": np.median(cost_per_W),
        "gross_margin_median": np.median(gross_margin),
    }

# ── Run models for all use cases ──────────────────────────────────────────────
np.random.seed(42)
results = {}
for name, params in USE_CASES.items():
    # Apply overrides for selected use case
    p = params.copy()
    if name == selected_uc:
        p["power_delivered_W"] = power_W
        p["link_efficiency"] = link_eff
        p["wtp_per_W"] = wtp
        p["incumbent_cost_per_W"] = incumbent_cost
    results[name] = run_model(name, p, n_simulations, launch_cost, required_margin, uncertainty_pct)  # noqa

# ── Overview Table ────────────────────────────────────────────────────────────
st.markdown("## 🗺️ Use Case Overview")

summary_rows = []
for name, r in results.items():
    pv = r["p_viable"]
    cs = r["customer_saving_pct_median"] * 100
    gm = r["gross_margin_median"] * 100
    cpw = r["cost_per_W_median"]

    if pv >= 0.6:
        status = "🟢 GO"
    elif pv >= 0.3:
        status = "🟡 MARGINAL"
    else:
        status = "🔴 KILL"

    summary_rows.append({
        "Use Case": name,
        "Status": status,
        "P(viable)": f"{pv:.0%}",
        "Cust. saving (median)": f"{cs:+.0f}%",
        "Our gross margin (median)": f"{gm:.0f}%",
        "Our cost/W (median)": f"${cpw:.0f}",
    })

df = pd.DataFrame(summary_rows)
st.dataframe(df, use_container_width=True, hide_index=True)

# ── P(viable) bar chart ───────────────────────────────────────────────────────
st.markdown("## 📊 Probability of Viability")
names = list(results.keys())
pviable = [results[n]["p_viable"] for n in names]
colors = ["#3fb950" if p >= 0.6 else "#d29922" if p >= 0.3 else "#f85149" for p in pviable]

fig_bar = go.Figure(go.Bar(
    x=names,
    y=[p * 100 for p in pviable],
    marker_color=colors,
    text=[f"{p:.0%}" for p in pviable],
    textposition="outside",
))
fig_bar.add_hline(y=required_margin * 100 * 0 + 60, line_dash="dash", line_color="#8b949e",
                  annotation_text="GO threshold (60%)", annotation_position="right")
fig_bar.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(13,17,23,1)",
    yaxis_title="P(viable) %",
    yaxis_range=[0, 110],
    font_family="Syne",
    margin=dict(t=30, b=10),
    height=350,
)
st.plotly_chart(fig_bar, use_container_width=True)

# ── Selected use case deep dive ───────────────────────────────────────────────
st.markdown(f"## 🔬 Deep Dive: {selected_uc}")
r = results[selected_uc]
uc_info = USE_CASES[selected_uc]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("P(viable)", f"{r['p_viable']:.0%}")
with col2:
    st.metric("Median cust. saving", f"{r['customer_saving_pct_median']*100:+.0f}%")
with col3:
    st.metric("Median gross margin", f"{r['gross_margin_median']*100:.0f}%")
with col4:
    st.metric("Median cost/W", f"${r['cost_per_W_median']:.0f}")

st.caption(f"**Incumbent:** {uc_info['incumbent']} | **Description:** {uc_info['description']}")

# Distribution plots
col_a, col_b = st.columns(2)

with col_a:
    fig_cust = go.Figure()
    fig_cust.add_trace(go.Histogram(
        x=r["customer_saving_pct"] * 100,
        nbinsx=60,
        marker_color="#388bfd",
        opacity=0.85,
        name="Customer saving %",
    ))
    fig_cust.add_vline(x=required_margin * 100, line_dash="dash", line_color="#f85149",
                       annotation_text=f"Required: {required_margin:.0%}")
    fig_cust.add_vline(x=0, line_dash="dot", line_color="#8b949e")
    fig_cust.update_layout(
        title="Customer savings vs incumbent",
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        xaxis_title="Saving (%)", yaxis_title="Count",
        font_family="Syne", height=300, margin=dict(t=40, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_cust, use_container_width=True)

with col_b:
    fig_gm = go.Figure()
    fig_gm.add_trace(go.Histogram(
        x=r["gross_margin"] * 100,
        nbinsx=60,
        marker_color="#3fb950",
        opacity=0.85,
        name="Gross margin %",
    ))
    fig_gm.add_vline(x=0, line_dash="dash", line_color="#f85149",
                     annotation_text="Break-even")
    fig_gm.update_layout(
        title="Our gross margin distribution",
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        xaxis_title="Gross margin (%)", yaxis_title="Count",
        font_family="Syne", height=300, margin=dict(t=40, b=10),
        showlegend=False,
    )
    st.plotly_chart(fig_gm, use_container_width=True)

# ── Sensitivity tornado ───────────────────────────────────────────────────────
st.markdown("### 🌪️ Sensitivity Analysis")
st.caption("How much does each input shift customer savings? (±1 std dev of base param)")

params_to_test = {
    "WTP ($/W)": "wtp_per_W",
    "Incumbent cost ($/W)": "incumbent_cost_per_W",
    "TX cost ($k)": "tx_cost_k",
    "RX cost ($k)": "rx_cost_k",
    "TX mass (kg)": "tx_mass_kg",
    "Power delivered (W)": "power_delivered_W",
    "Ops cost ($/yr)": "ops_cost_k_yr",
}

base_saving = r["customer_saving_pct_median"] * 100
tornado_rows = []

for label, key in params_to_test.items():
    base_val = USE_CASES[selected_uc][key]
    if base_val == 0:
        continue
    for direction, mult in [("high", 1.25), ("low", 0.75)]:
        p_mod = USE_CASES[selected_uc].copy()
        if selected_uc == selected_uc:  # apply overrides
            p_mod["power_delivered_W"] = power_W
            p_mod["link_efficiency"] = link_eff
            p_mod["wtp_per_W"] = wtp
            p_mod["incumbent_cost_per_W"] = incumbent_cost
        p_mod[key] = base_val * mult
        np.random.seed(42)
        r_mod = run_model(selected_uc, p_mod, 3000, launch_cost, required_margin, uncertainty_pct)
        tornado_rows.append({
            "param": label,
            "direction": direction,
            "saving": r_mod["customer_saving_pct_median"] * 100,
        })

tdf = pd.DataFrame(tornado_rows)
if not tdf.empty:
    tdf["swing"] = tdf["saving"] - base_saving
    tdf_piv = tdf.pivot(index="param", columns="direction", values="swing").fillna(0)
    tdf_piv["total_swing"] = tdf_piv.get("high", 0).abs() + tdf_piv.get("low", 0).abs()
    tdf_piv = tdf_piv.sort_values("total_swing")

    fig_tornado = go.Figure()
    fig_tornado.add_trace(go.Bar(
        y=tdf_piv.index,
        x=tdf_piv.get("high", 0),
        orientation="h",
        name="+25% param",
        marker_color="#3fb950",
    ))
    fig_tornado.add_trace(go.Bar(
        y=tdf_piv.index,
        x=tdf_piv.get("low", 0),
        orientation="h",
        name="-25% param",
        marker_color="#f85149",
    ))
    fig_tornado.update_layout(
        barmode="relative",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        xaxis_title="Change in customer saving (pp)",
        font_family="Syne", height=320, margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig_tornado, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("NeoWatt Technoeconomic Model v0.1 · All parameters are estimates — validate through customer discovery · Required margin set to beat incumbent by ≥50%")
