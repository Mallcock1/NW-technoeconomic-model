"""
Incumbent cost modelling utilities.

Handles both standard (direct cost comparison) and greenfield
(cost-of-inaction) incumbent framings.
"""

import numpy as np

from neowatt.distributions import sample


def compute_incumbent_annual_cost(incumbent_params: dict, n: int,
                                  rng: np.random.Generator,
                                  incumbent_type: str = "standard") -> np.ndarray:
    """Compute annualised incumbent cost for comparison.

    For standard: uses cost_per_W or cost_per_year directly.
    For greenfield: uses cost_of_inaction framing (regulatory/insurance).
    """
    if "cost_per_W" in incumbent_params:
        return sample(incumbent_params["cost_per_W"], n, rng)

    if "cost_per_year_k" in incumbent_params:
        return sample(incumbent_params["cost_per_year_k"], n, rng) * 1000

    if "cost_per_object_k" in incumbent_params:
        return sample(incumbent_params["cost_per_object_k"], n, rng) * 1000

    if "capex_avoided_per_customer_k" in incumbent_params:
        return sample(incumbent_params["capex_avoided_per_customer_k"], n, rng) * 1000

    if "cost_per_spacecraft_k" in incumbent_params:
        return sample(incumbent_params["cost_per_spacecraft_k"], n, rng) * 1000

    if "array_cost_per_kg" in incumbent_params:
        return sample(incumbent_params["array_cost_per_kg"], n, rng)

    return np.zeros(n)
