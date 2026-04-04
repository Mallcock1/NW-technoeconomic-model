"""
Monte Carlo simulation engine.

Loads use case definitions from YAML, instantiates the appropriate model class,
runs simulations, and returns results for all use cases.
"""

import numpy as np

from neowatt.data_loader import load_global_params, load_use_cases
from neowatt.use_cases import MODEL_REGISTRY
from neowatt.use_case_model import ModelResult


def run_all_use_cases(
    use_cases: dict = None,
    global_params: dict = None,
    n_simulations: int = None,
    seed: int = 42,
    overrides: dict = None,
    data_dir: str = None,
) -> dict[str, ModelResult]:
    """Run Monte Carlo for all use cases and return results.

    Args:
        use_cases: dict of use case configs. If None, loaded from YAML.
        global_params: global config dict. If None, loaded from YAML.
        n_simulations: number of MC simulations. If None, uses global default.
        seed: random seed for reproducibility.
        overrides: dict of {slug: {param_group: {param_name: new_value}}} for UI overrides.
        data_dir: path to data directory containing YAML files.

    Returns:
        dict mapping use case slug to ModelResult.
    """
    if global_params is None:
        global_params = load_global_params(data_dir)
    if use_cases is None:
        use_cases = load_use_cases(data_dir)

    if n_simulations is None:
        n_simulations = global_params["global"].get("default_n_simulations", 10000)

    required_margin = global_params["global"].get("required_margin_over_incumbent", 0.50)

    results = {}
    rng = np.random.default_rng(seed)

    for slug, uc_params in use_cases.items():
        # Apply overrides if provided
        params = _apply_overrides(uc_params, overrides.get(slug, {}) if overrides else {})

        # Get model class
        model_class_name = params["meta"]["model_class"]
        model_class = MODEL_REGISTRY.get(model_class_name)
        if model_class is None:
            raise ValueError(f"Unknown model class '{model_class_name}' for use case '{slug}'")

        # Instantiate and run
        model = model_class(params, global_params)
        result = model.run(n_simulations, rng, required_margin)
        results[slug] = result

    return results


def run_single_use_case(
    slug: str,
    use_cases: dict = None,
    global_params: dict = None,
    n_simulations: int = 10000,
    seed: int = 42,
    overrides: dict = None,
    data_dir: str = None,
) -> ModelResult:
    """Run Monte Carlo for a single use case."""
    if global_params is None:
        global_params = load_global_params(data_dir)
    if use_cases is None:
        use_cases = load_use_cases(data_dir)

    required_margin = global_params["global"].get("required_margin_over_incumbent", 0.50)
    rng = np.random.default_rng(seed)

    uc_params = use_cases[slug]
    params = _apply_overrides(uc_params, overrides or {})

    model_class_name = params["meta"]["model_class"]
    model_class = MODEL_REGISTRY[model_class_name]
    model = model_class(params, global_params)

    return model.run(n_simulations, rng, required_margin)


def _apply_overrides(uc_params: dict, overrides: dict) -> dict:
    """Deep-merge overrides into use case params.

    overrides format: {param_group: {param_name: new_value}}
    e.g. {"economic": {"wtp_per_W": 300}} overrides the base value.
    """
    if not overrides:
        return uc_params

    import copy
    params = copy.deepcopy(uc_params)

    for group, group_overrides in overrides.items():
        if group not in params:
            continue
        for param_name, new_value in group_overrides.items():
            if param_name in params[group]:
                if isinstance(params[group][param_name], dict):
                    params[group][param_name]["value"] = new_value
                else:
                    params[group][param_name] = new_value

    return params
