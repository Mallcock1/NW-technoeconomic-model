"""
Market sizing (TAM/SAM/SOM) and "Why Now?" time-dependent trajectory analysis.
"""

import numpy as np
import copy

from neowatt.monte_carlo import run_single_use_case
from neowatt.use_case_model import ModelResult


def why_now_analysis(
    slug: str,
    use_cases: dict,
    global_params: dict,
    n_simulations: int = 3000,
    seed: int = 42,
) -> dict:
    """Compute P(viable) trajectory over time as costs decline.

    Uses launch_cost_trajectory from global_params to project how viability
    evolves from 2025 to 2035. Modifies the use case's economic.launch_cost_per_kg.

    Returns dict with 'years', 'p_viable', and 'cost_per_W_median' lists.
    """
    trajectories = {}
    gp = global_params["global"]

    for key in ["launch_cost_trajectory", "laser_cost_trajectory", "photovoltaic_efficiency_trajectory"]:
        if key in gp:
            t = gp[key]
            trajectories[key] = dict(zip(t["years"], t["values"]))

    all_years = sorted(set(
        year for t in trajectories.values() for year in t.keys()
    ))

    # Get the base launch cost from the use case's economic params
    uc_params = use_cases[slug]
    base_lc_spec = uc_params.get("economic", {}).get("launch_cost_per_kg", {})
    base_lc = base_lc_spec.get("value", 5000)

    results = {"years": [], "p_viable": [], "cost_per_W_median": []}

    for year in all_years:
        modified_cases = copy.deepcopy(use_cases)

        # Update launch cost in the use case's economic params
        if "launch_cost_trajectory" in trajectories:
            t = trajectories["launch_cost_trajectory"]
            if year in t:
                lc = t[year]
                lc_spec = modified_cases[slug]["economic"]["launch_cost_per_kg"]
                ratio = lc / base_lc if base_lc > 0 else 1.0
                lc_spec["value"] = lc
                dist = lc_spec.get("distribution", {})
                if dist:
                    if "low" in dist:
                        dist["low"] = dist["low"] * ratio
                    if "mode" in dist:
                        dist["mode"] = lc
                    if "high" in dist:
                        dist["high"] = dist["high"] * ratio

        r = run_single_use_case(slug, modified_cases, global_params, n_simulations, seed)
        results["years"].append(year)
        results["p_viable"].append(r.p_viable)
        results["cost_per_W_median"].append(r.cost_per_W_median)

    return results
