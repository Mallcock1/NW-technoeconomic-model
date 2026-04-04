"""
Time-dependent parameter interpolation and trajectory analysis.

Parameters with a 'trajectory' key in their YAML spec define how the value
evolves over time. This module interpolates values for any target year and
runs the model across a year range to produce time-series outputs.
"""

import copy
import numpy as np
from neowatt.data_loader import get_param_value


def interpolate_param_for_year(param_spec: dict, year: int) -> dict:
    """Return a modified param_spec with value (and distribution) scaled to a target year.

    If the param has no trajectory, returns the original spec unchanged.
    """
    traj = param_spec.get("trajectory")
    if traj is None:
        return param_spec

    years = traj["years"]
    values = traj["values"]
    base_value = param_spec["value"]

    # Interpolate
    interp_value = float(np.interp(year, years, values))

    out = copy.deepcopy(param_spec)
    out["value"] = interp_value

    # Scale distribution proportionally if it exists
    dist = out.get("distribution")
    if dist and base_value != 0:
        ratio = interp_value / base_value
        dtype = dist.get("type", "fixed")
        if dtype != "fixed":
            for key in ["low", "mode", "high", "mean"]:
                if key in dist:
                    dist[key] = dist[key] * ratio
            if "std" in dist:
                dist["std"] = dist["std"] * abs(ratio)

    return out


def apply_year_to_use_case(uc_params: dict, year: int) -> dict:
    """Return a deep copy of uc_params with all trajectory params interpolated to year."""
    out = copy.deepcopy(uc_params)

    for group in ["technical", "cost", "economic", "incumbent"]:
        if group not in out:
            continue
        for pname, pspec in out[group].items():
            if isinstance(pspec, dict) and "trajectory" in pspec:
                out[group][pname] = interpolate_param_for_year(pspec, year)

    return out


def run_time_series_point(
    use_cases: dict,
    global_params: dict,
    year_start: int,
    year_end: int,
    year_step: int,
    required_margin: float,
) -> dict:
    """Run point estimates for all use cases across a year range.

    Returns: {slug: {"years": [...], "capex": [...], "annual_revenue": [...],
              "gross_margin": [...], "customer_saving": [...], "cost_per_W": [...],
              "decision": [...]}}
    """
    from dashboard.point_estimates import _compute_point_estimate

    years = list(range(year_start, year_end + 1, year_step))
    results = {}

    for slug, uc in use_cases.items():
        ts = {
            "years": years,
            "capex": [],
            "annual_revenue": [],
            "gross_margin": [],
            "customer_saving": [],
            "cost_per_W": [],
            "decision": [],
            "name": uc["meta"]["name"],
        }

        for year in years:
            uc_year = apply_year_to_use_case(uc, year)
            e = _compute_point_estimate(uc_year, global_params, required_margin)
            ts["capex"].append(e["capex"])
            ts["annual_revenue"].append(e["annual_revenue"])
            ts["gross_margin"].append(e["gross_margin"])
            ts["customer_saving"].append(e["customer_saving"])
            ts["cost_per_W"].append(e["cost_per_W"])
            ts["decision"].append(e["decision"])

        results[slug] = ts

    return results


def run_time_series_mc(
    use_cases: dict,
    global_params: dict,
    year_start: int,
    year_end: int,
    year_step: int,
    n_simulations: int = 3000,
    seed: int = 42,
) -> dict:
    """Run MC for all use cases across a year range.

    Returns: {slug: {"years": [...], "p_viable": [...], "cost_per_W_median": [...],
              "gross_margin_median": [...], "npv_median": [...], "decision": [...],
              "customer_saving_median": [...], "name": str}}
    """
    from neowatt.monte_carlo import run_single_use_case

    years = list(range(year_start, year_end + 1, year_step))
    all_results = {}

    for slug, uc in use_cases.items():
        ts = {
            "years": years,
            "p_viable": [],
            "cost_per_W_median": [],
            "gross_margin_median": [],
            "npv_median": [],
            "customer_saving_median": [],
            "decision": [],
            "name": uc["meta"]["name"],
        }

        for year in years:
            modified_cases = copy.deepcopy(use_cases)
            modified_cases[slug] = apply_year_to_use_case(uc, year)

            r = run_single_use_case(slug, modified_cases, global_params, n_simulations, seed)
            ts["p_viable"].append(r.p_viable)
            ts["cost_per_W_median"].append(r.cost_per_W_median)
            ts["gross_margin_median"].append(r.gross_margin_median)
            ts["npv_median"].append(r.npv_median)
            ts["customer_saving_median"].append(r.customer_saving_pct_median)
            ts["decision"].append(r.decision.label)

        all_results[slug] = ts

    return all_results
