"""
Base class for technoeconomic use case models and the ModelResult dataclass.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import numpy as np

from neowatt.distributions import sample, sample_params
from neowatt.npv import npv, build_cashflows
from neowatt.decision import decide, Decision
from neowatt.data_loader import get_param_value


@dataclass
class ModelResult:
    """Results from a Monte Carlo simulation of a single use case."""
    use_case_slug: str
    use_case_name: str
    category: str
    time_horizon: str
    n_simulations: int
    incumbent_type: str

    # Per-simulation arrays
    total_cost: np.ndarray = field(repr=False)
    total_revenue: np.ndarray = field(repr=False)
    net_present_value: np.ndarray = field(repr=False)
    gross_margin: np.ndarray = field(repr=False)
    customer_saving_pct: np.ndarray = field(repr=False)
    cost_per_W: np.ndarray = field(repr=False)

    # Scalars
    p_viable: float = 0.0
    decision: Decision = None

    @property
    def gross_margin_median(self) -> float:
        return float(np.median(self.gross_margin))

    @property
    def customer_saving_pct_median(self) -> float:
        return float(np.median(self.customer_saving_pct))

    @property
    def cost_per_W_median(self) -> float:
        return float(np.median(self.cost_per_W))

    @property
    def npv_median(self) -> float:
        return float(np.median(self.net_present_value))


class UseCaseModel(ABC):
    """Abstract base class for all use case technoeconomic models."""

    def __init__(self, params: dict, global_params: dict):
        """
        Args:
            params: use case config from YAML (meta, incumbent, technical, cost, economic)
            global_params: global config (launch_cost, discount_rate, thresholds, etc.)
        """
        self.params = params
        self.global_params = global_params
        self.meta = params["meta"]
        self.slug = self.meta["slug"]
        self.name = self.meta["name"]
        self.category = self.meta.get("category", "")
        self.time_horizon = self.meta.get("time_horizon", "")
        self.incumbent_type = self.meta.get("incumbent_type", "standard")

    @abstractmethod
    def compute_costs(self, n: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
        """Compute CAPEX and annual OPEX arrays.

        Returns:
            capex: shape (n,) – one-time capital expenditure
            annual_opex: shape (n,) – annual operating expenditure
        """

    @abstractmethod
    def compute_annual_revenue(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Compute annual revenue array. Shape (n,)."""

    @abstractmethod
    def compute_incumbent_cost_per_unit(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Compute incumbent cost per unit (typically $/W). Shape (n,)."""

    @abstractmethod
    def compute_our_price_per_unit(self, n: int, rng: np.random.Generator) -> np.ndarray:
        """Compute our price to the customer per unit ($/W). Shape (n,)."""

    def run(self, n: int, rng: np.random.Generator, required_margin: float) -> ModelResult:
        """Run Monte Carlo simulation and return results."""
        # Sample global params
        discount_rate = sample(self.global_params["global"]["discount_rate"], n, rng)

        # Compute costs and revenues
        capex, annual_opex = self.compute_costs(n, rng)
        annual_revenue = self.compute_annual_revenue(n, rng)

        # Build cashflows and compute NPV
        amort_spec = self.params.get("economic", {}).get("amortization_years", {"value": 7})
        n_years = int(get_param_value(amort_spec))
        cashflows = build_cashflows(capex, annual_revenue, annual_opex, n_years + 1)
        net_pv = npv(cashflows, discount_rate)

        # Total cost and revenue (undiscounted, for margin calc)
        total_cost = capex + annual_opex * n_years
        total_revenue = annual_revenue * n_years

        # Gross margin
        gross_margin = np.where(total_revenue > 0,
                                (total_revenue - total_cost) / total_revenue,
                                -np.inf)

        # Customer saving vs incumbent
        incumbent_cost = self.compute_incumbent_cost_per_unit(n, rng)
        our_price = self.compute_our_price_per_unit(n, rng)

        if self.incumbent_type == "greenfield":
            customer_saving_pct = np.where(net_pv > 0, 1.0, 0.0)
            viable = net_pv > 0
        else:
            customer_saving_pct = np.where(
                incumbent_cost > 0,
                (incumbent_cost - our_price) / incumbent_cost,
                0.0
            )
            viable = customer_saving_pct >= required_margin

        p_viable = float(viable.mean())

        # Cost per W
        power_spec = self.params.get("technical", {}).get("power_delivered_W", {"value": 1})
        power = sample(power_spec, n, rng)
        cost_per_W = np.where(power > 0, total_cost / power, np.inf)

        # Decision
        go_thresh = self.global_params["global"].get("go_threshold", 0.60)
        marg_thresh = self.global_params["global"].get("marginal_threshold", 0.30)
        decision = decide(p_viable, float(np.median(gross_margin)),
                          go_thresh, marg_thresh, self.incumbent_type)

        return ModelResult(
            use_case_slug=self.slug,
            use_case_name=self.name,
            category=self.category,
            time_horizon=self.time_horizon,
            n_simulations=n,
            incumbent_type=self.incumbent_type,
            total_cost=total_cost,
            total_revenue=total_revenue,
            net_present_value=net_pv,
            gross_margin=gross_margin,
            customer_saving_pct=customer_saving_pct,
            cost_per_W=cost_per_W,
            p_viable=p_viable,
            decision=decision,
        )
