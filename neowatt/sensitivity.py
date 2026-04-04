"""
Sensitivity analysis: tornado charts and 2D parameter sweeps.
"""

import numpy as np
import copy

from neowatt.monte_carlo import run_single_use_case
from neowatt.use_case_model import ModelResult


def _scale_param(param_spec: dict, multiplier: float):
    """Scale a parameter spec's value AND distribution by a multiplier.

    This ensures that when we perturb a parameter for sensitivity analysis,
    the entire distribution shifts, not just the base value.
    """
    if "value" in param_spec:
        param_spec["value"] = param_spec["value"] * multiplier

    dist = param_spec.get("distribution")
    if dist is None:
        return

    dtype = dist.get("type", "fixed")
    if dtype == "fixed":
        return

    # Scale all numeric distribution parameters
    for key in ["low", "mode", "high", "mean"]:
        if key in dist:
            dist[key] = dist[key] * multiplier

    # For normal/lognormal, also scale std proportionally
    if "std" in dist:
        dist["std"] = dist["std"] * multiplier


def tornado_analysis(
    slug: str,
    use_cases: dict,
    global_params: dict,
    target_metric: str = "customer_saving_pct",
    perturbation: float = 0.25,
    n_simulations: int = 3000,
    seed: int = 42,
) -> list[dict]:
    """Run tornado sensitivity analysis for a single use case.

    For each parameter, perturb ±perturbation from base value and measure
    the change in the target metric's median.

    Returns list of dicts: [{param, group, low_value, high_value, base_median, low_median, high_median, swing}]
    """
    # Base run
    base_result = run_single_use_case(slug, use_cases, global_params, n_simulations, seed)
    base_median = float(np.median(getattr(base_result, target_metric)))

    # Identify all numeric parameters to test
    uc_params = use_cases[slug]
    params_to_test = []
    for group in ["technical", "cost", "economic"]:
        if group not in uc_params:
            continue
        for pname, pspec in uc_params[group].items():
            if isinstance(pspec, dict) and "value" in pspec and pspec["value"] != 0:
                params_to_test.append((group, pname, pspec["value"]))

    # Also test incumbent params
    for pname, pspec in uc_params.get("incumbent", {}).items():
        if isinstance(pspec, dict) and "value" in pspec and pspec["value"] != 0:
            params_to_test.append(("incumbent", pname, pspec["value"]))

    results = []
    for group, pname, base_val in params_to_test:
        row = {
            "param": pname,
            "group": group,
            "base_value": base_val,
            "unit": uc_params[group][pname].get("unit", ""),
        }

        for direction, mult in [("low", 1 - perturbation), ("high", 1 + perturbation)]:
            modified_cases = copy.deepcopy(use_cases)
            _scale_param(modified_cases[slug][group][pname], mult)

            r = run_single_use_case(slug, modified_cases, global_params, n_simulations, seed)
            median_val = float(np.median(getattr(r, target_metric)))
            row[f"{direction}_value"] = base_val * mult
            row[f"{direction}_median"] = median_val

        row["base_median"] = base_median
        row["swing"] = abs(row["high_median"] - row["low_median"])
        results.append(row)

    # Sort by swing (most sensitive first)
    results.sort(key=lambda x: x["swing"], reverse=True)
    return results


def sensitivity_2d(
    slug: str,
    use_cases: dict,
    global_params: dict,
    param_x: tuple[str, str],  # (group, param_name)
    param_y: tuple[str, str],  # (group, param_name)
    target_metric: str = "p_viable",
    n_steps: int = 8,
    perturbation: float = 0.5,
    n_simulations: int = 2000,
    seed: int = 42,
) -> dict:
    """2D sensitivity: vary two parameters and compute metric grid.

    Returns dict with x_values, y_values, z_grid (n_steps x n_steps).
    """
    uc_params = use_cases[slug]
    base_x = uc_params[param_x[0]][param_x[1]]["value"]
    base_y = uc_params[param_y[0]][param_y[1]]["value"]

    x_values = np.linspace(base_x * (1 - perturbation), base_x * (1 + perturbation), n_steps)
    y_values = np.linspace(base_y * (1 - perturbation), base_y * (1 + perturbation), n_steps)

    z_grid = np.zeros((n_steps, n_steps))

    for i, xv in enumerate(x_values):
        for j, yv in enumerate(y_values):
            modified = copy.deepcopy(use_cases)
            _scale_param(modified[slug][param_x[0]][param_x[1]], xv / base_x)
            _scale_param(modified[slug][param_y[0]][param_y[1]], yv / base_y)

            r = run_single_use_case(slug, modified, global_params, n_simulations, seed)

            if target_metric == "p_viable":
                z_grid[j, i] = r.p_viable
            else:
                z_grid[j, i] = float(np.median(getattr(r, target_metric)))

    return {
        "x_values": x_values,
        "y_values": y_values,
        "z_grid": z_grid,
        "x_label": f"{param_x[1]} ({uc_params[param_x[0]][param_x[1]].get('unit', '')})",
        "y_label": f"{param_y[1]} ({uc_params[param_y[0]][param_y[1]].get('unit', '')})",
    }
