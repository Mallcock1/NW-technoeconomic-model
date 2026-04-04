"""Incumbent cost validation view: shows all incumbent assumptions across use cases."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.styles import COLORS
from neowatt.data_loader import get_param_value


def _esc(text: str) -> str:
    if not text:
        return ""
    return text.replace("$", "\\$").replace("~", "\\~")


CONFIDENCE_COLORS = {
    "measured": "#3fb950",
    "analogous": "#388bfd",
    "estimated": "#d29922",
    "guessed": "#f85149",
}

CONFIDENCE_ORDER = ["measured", "analogous", "estimated", "guessed"]


def render_incumbent_view(use_cases: dict):
    """Render a dedicated view of all incumbent cost assumptions."""
    st.markdown("## Incumbent Cost Assumptions")
    st.caption("All incumbent cost parameters across use cases. "
               "These are the ceilings NEOWATT must undercut. "
               "Confidence ratings indicate how well-validated each estimate is.")

    rows = []
    for slug, uc in use_cases.items():
        meta = uc["meta"]
        inc = uc.get("incumbent", {})
        name = meta["name"]
        inc_name = inc.get("name", "N/A")

        for pname, pspec in inc.items():
            if not isinstance(pspec, dict) or "value" not in pspec:
                continue

            rows.append({
                "slug": slug,
                "use_case": name,
                "incumbent": inc_name,
                "param": pname,
                "value": pspec["value"],
                "unit": pspec.get("unit", ""),
                "confidence": pspec.get("confidence", "guessed"),
                "source": pspec.get("source", ""),
                "justification": pspec.get("justification", ""),
                "description": pspec.get("description", ""),
            })

    if not rows:
        st.info("No incumbent cost data found.")
        return

    # Summary table
    st.markdown("### Overview")
    table_rows = []
    for r in rows:
        conf = r["confidence"]
        conf_emoji = {"measured": "🟢", "analogous": "🔵", "estimated": "🟡", "guessed": "🔴"}.get(conf, "⚪")
        table_rows.append({
            "Use Case": r["use_case"],
            "Incumbent": r["incumbent"],
            "Parameter": r["param"],
            "Value": f"{r['value']:,.0f} {r['unit']}",
            "Confidence": f"{conf_emoji} {conf}",
            "Source": r["source"][:60] + "..." if len(r["source"]) > 60 else r["source"],
        })

    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Confidence distribution
    st.markdown("### Confidence Distribution")
    conf_counts = {}
    for r in rows:
        c = r["confidence"]
        conf_counts[c] = conf_counts.get(c, 0) + 1

    ordered = [(c, conf_counts.get(c, 0)) for c in CONFIDENCE_ORDER if c in conf_counts]

    fig = go.Figure(go.Bar(
        x=[c for c, _ in ordered],
        y=[n for _, n in ordered],
        marker_color=[CONFIDENCE_COLORS.get(c, "#8b949e") for c, _ in ordered],
        text=[str(n) for _, n in ordered],
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,1)",
        yaxis_title="Number of parameters",
        font_family="Syne",
        height=250,
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detail per use case
    st.markdown("### Detail by Use Case")
    for r in rows:
        with st.expander(f"**{r['use_case']}** – {r['incumbent']} – {r['param']}: {r['value']:,.0f} {r['unit']}"):
            conf = r["confidence"]
            conf_color = CONFIDENCE_COLORS.get(conf, "#8b949e")
            st.markdown(f"**Confidence:** :{conf_color[1:]}[{conf}]" if False else
                        f"**Confidence:** {conf}")
            if r["description"]:
                st.markdown(f"**Description:** {_esc(r['description'])}")
            if r["source"]:
                st.markdown(f"**Source:** {_esc(r['source'])}")
            if r["justification"]:
                st.markdown(f"**Justification:** {_esc(r['justification'])}")
