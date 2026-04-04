"""
Net Present Value and levelized cost calculations for technoeconomic modelling.
"""

import numpy as np


def npv(cashflows: np.ndarray, discount_rate: np.ndarray) -> np.ndarray:
    """Compute NPV for each simulation run.

    Args:
        cashflows: shape (n_sim, n_years). Year 0 = upfront, year 1+ = annual.
        discount_rate: shape (n_sim,). Annual discount rate per simulation.

    Returns:
        shape (n_sim,) — NPV for each simulation.
    """
    n_sim, n_years = cashflows.shape
    years = np.arange(n_years)  # [0, 1, 2, ...]
    # discount_factors shape: (n_sim, n_years)
    discount_factors = 1.0 / (1.0 + discount_rate[:, np.newaxis]) ** years[np.newaxis, :]
    return np.sum(cashflows * discount_factors, axis=1)


def build_cashflows(capex: np.ndarray, annual_revenue: np.ndarray,
                    annual_opex: np.ndarray, n_years: int) -> np.ndarray:
    """Build a cashflow matrix from CAPEX, annual revenue, and annual OPEX.

    Args:
        capex: shape (n_sim,) — upfront capital cost (positive = cost, will be negated)
        annual_revenue: shape (n_sim,) — annual revenue
        annual_opex: shape (n_sim,) — annual operating cost (positive = cost, will be negated)
        n_years: number of years including year 0

    Returns:
        shape (n_sim, n_years) — net cashflow per year
    """
    n_sim = capex.shape[0]
    cf = np.zeros((n_sim, n_years), dtype=np.float64)
    cf[:, 0] = -capex
    cf[:, 1:] = (annual_revenue - annual_opex)[:, np.newaxis]
    return cf


def levelized_cost(total_cost_npv: np.ndarray, total_power_delivered: np.ndarray) -> np.ndarray:
    """Compute levelized cost per watt delivered.

    Args:
        total_cost_npv: shape (n_sim,) — NPV of all costs
        total_power_delivered: shape (n_sim,) — total watts delivered over lifetime

    Returns:
        shape (n_sim,) — $/W levelized
    """
    return np.where(total_power_delivered > 0,
                    total_cost_npv / total_power_delivered,
                    np.inf)
