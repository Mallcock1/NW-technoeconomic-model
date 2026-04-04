"""Point-estimate input parameters: editable values with justifications, no distributions."""

import streamlit as st

from neowatt.data_loader import get_param_value


def _esc(text: str) -> str:
    if not text:
        return text
    return text.replace("$", "\\$").replace("~", "\\~")


def render_inputs_point(uc_params: dict, slug: str) -> dict:
    """Render editable point-estimate inputs for a use case.

    Returns a dict of overrides: {group: {param_name: new_value}}
    """
    st.markdown("### Input Parameters (Point Estimates)")
    st.caption("Edit values below to update the model outputs. "
               "Defaults are loaded from `data/use_cases.yaml`.")

    # Reset all button
    if st.button("Reset all to defaults", key=f"reset_all_pt_{slug}"):
        # Clear all session_state keys for this slug's point-estimate inputs
        keys_to_clear = [k for k in st.session_state if k.startswith(f"pt_{slug}_")]
        for k in keys_to_clear:
            del st.session_state[k]
        # Also clear the overrides
        ss_key = f"overrides_pt_{slug}"
        if ss_key in st.session_state:
            del st.session_state[ss_key]
        st.rerun()

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
            value = pspec["value"]
            unit = pspec.get("unit", "")
            desc = pspec.get("description", "")
            justification = pspec.get("justification", "")

            with st.expander(f"**{pname}** – {value} {unit}", expanded=False):
                col_input, col_info = st.columns([1, 2])

                with col_input:
                    key = f"pt_{slug}_{group_key}_{pname}"

                    if isinstance(value, int):
                        new_val = st.number_input(
                            f"{pname} ({unit})",
                            value=value,
                            step=max(1, value // 10) if value != 0 else 1,
                            key=key,
                        )
                    else:
                        step = max(0.01, abs(value) / 20) if value != 0 else 0.01
                        new_val = st.number_input(
                            f"{pname} ({unit})",
                            value=float(value),
                            step=step,
                            format="%.4g",
                            key=key,
                        )

                    # Per-parameter reset
                    if new_val != value:
                        overrides.setdefault(group_key, {})[pname] = new_val
                        if st.button("Reset to default", key=f"reset_pt_{slug}_{group_key}_{pname}"):
                            del st.session_state[key]
                            st.rerun()

                with col_info:
                    if desc:
                        st.markdown(f"**Description:** {_esc(desc)}")
                    if justification:
                        st.markdown(f"**Justification:** {_esc(justification)}")

    return overrides
