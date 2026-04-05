"""
PV-Free Spacecraft hardware sale model.

Customer buys TX+RX hardware from NEOWATT and integrates on their own platform.
Value is measured in mass saved (removed solar arrays) and the associated
launch cost + array hardware cost savings.
"""

import numpy as np

from neowatt.use_case_model import UseCaseModel
from neowatt.distributions import sample
from neowatt.data_loader import get_param_value


class HardwarePVFreeModel(UseCaseModel):
    """PV-Free Spacecraft: sell hardware, value from mass/array savings."""

    def compute_costs(self, n, rng):
        cost = self.params["cost"]

        # NEOWATT manufacturing costs only
        tx_hw = sample(cost["tx_hardware_k"], n, rng) * 1000
        rx_hw = sample(cost["rx_hardware_k"], n, rng) * 1000
        ground = sample(cost["ground_segment_k"], n, rng) * 1000

        capex = tx_hw + rx_hw + ground

        support_cost = sample(
            self.params.get("cost", {}).get("support_cost_k_yr", {"value": 5}), n, rng
        ) * 1000

        return capex, support_cost

    def compute_annual_revenue(self, n, rng):
        econ = self.params["economic"]

        # Sale price annualised
        tx_sale = sample(econ["tx_sale_price_k"], n, rng) * 1000
        rx_sale = sample(econ["rx_sale_price_k"], n, rng) * 1000
        amort = get_param_value(econ.get("amortization_years", {"value": 7}))
        support = sample(econ.get("annual_support_k", {"value": 0}), n, rng) * 1000

        return (tx_sale + rx_sale) / amort + support

    def compute_incumbent_cost_per_unit(self, n, rng):
        # Incumbent cost per kg of solar array
        return sample(self.params["incumbent"]["array_cost_per_kg"], n, rng)

    def compute_our_price_per_unit(self, n, rng):
        # Customer's cost per kg of mass saved by buying our RX
        econ = self.params["economic"]
        tech = self.params["technical"]

        rx_sale = sample(econ["rx_sale_price_k"], n, rng) * 1000
        mass_saved = sample(tech["mass_saved_kg"], n, rng)

        return np.where(mass_saved > 0, rx_sale / mass_saved, np.inf)
