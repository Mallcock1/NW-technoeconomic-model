"""
Distribution sampling factory for Monte Carlo technoeconomic modelling.

Each parameter in the YAML config can specify a distribution type and parameters.
This module converts those specs into numpy arrays of samples.
"""

import numpy as np


def sample(param_spec: dict, n: int, rng: np.random.Generator) -> np.ndarray:
    """Sample n values from the distribution defined in param_spec.

    param_spec must have a 'value' key. If it also has a 'distribution' key,
    samples are drawn from the specified distribution. Otherwise returns
    a constant array of the base value.

    Supported distribution types:
        - triangular: keys low, mode (optional, defaults to value), high
        - normal: keys mean (optional, defaults to value), std
        - uniform: keys low, high
        - lognormal: keys mean, std (of the underlying normal)
        - fixed: no extra keys needed
    """
    value = param_spec["value"]
    dist = param_spec.get("distribution")

    if dist is None or dist.get("type") == "fixed":
        return np.full(n, value, dtype=np.float64)

    dtype = dist["type"]

    if dtype == "triangular":
        lo = dist["low"]
        mode = dist.get("mode", value)
        hi = dist["high"]
        return rng.triangular(lo, mode, hi, n)

    if dtype == "normal":
        mean = dist.get("mean", value)
        std = dist["std"]
        return rng.normal(mean, std, n)

    if dtype == "uniform":
        lo = dist["low"]
        hi = dist["high"]
        return rng.uniform(lo, hi, n)

    if dtype == "lognormal":
        mean = dist.get("mean", value)
        std = dist["std"]
        # Convert mean/std of the distribution to underlying normal params
        variance = std ** 2
        mu = np.log(mean ** 2 / np.sqrt(variance + mean ** 2))
        sigma = np.sqrt(np.log(1 + variance / mean ** 2))
        return rng.lognormal(mu, sigma, n)

    raise ValueError(f"Unknown distribution type: {dtype}")


def sample_params(params_group: dict, n: int, rng: np.random.Generator) -> dict:
    """Sample all parameters in a group (e.g. 'technical', 'cost').

    Returns a dict mapping parameter names to numpy arrays of shape (n,).
    """
    out = {}
    for name, spec in params_group.items():
        if isinstance(spec, dict) and "value" in spec:
            out[name] = sample(spec, n, rng)
        # Skip non-parameter entries (e.g. 'name', 'description' strings)
    return out
