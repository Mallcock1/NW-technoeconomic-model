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

    Uses launch_cost_trajectory and laser_cost_trajectory from global_params
    to project how viability evolves from 2025 to 2035.

    Returns dict with 'years' and 'p_viable' lists.
    """
    trajectories = {}
    gp = global_params["global"]

    # Collect all trajectories
    for key in ["launch_cost_trajectory", "laser_cost_trajectory", "photovoltaic_efficiency_trajectory"]:
        if key in gp:
            t = gp[key]
            trajectories[key] = dict(zip(t["years"], t["values"]))

    # Get all unique years
    all_years = sorted(set(
        year for t in trajectories.values() for year in t.keys()
    ))

    results = {"years": [], "p_viable": [], "cost_per_W_median": []}

    for year in all_years:
        modified_gp = copy.deepcopy(global_params)

        # Update launch cost if trajectory exists
        if "launch_cost_trajectory" in trajectories:
            t = trajectories["launch_cost_trajectory"]
            if year in t:
                lc = t[year]
                modified_gp["global"]["launch_cost_per_kg"]["value"] = lc
                d = modified_gp["global"]["launch_cost_per_kg"].get("distribution", {})
                if d:
                    ratio = lc / global_params["global"]["launch_cost_per_kg"]["value"]
                    if "low" in d:
                        d["low"] = d["low"] * ratio
                    if "mode" in d:
                        d["mode"] = lc
                    if "high" in d:
                        d["high"] = d["high"] * ratio

        r = run_single_use_case(slug, use_cases, modified_gp, n_simulations, seed)
        results["years"].append(year)
        results["p_viable"].append(r.p_viable)
        results["cost_per_W_median"].append(r.cost_per_W_median)

    return results
