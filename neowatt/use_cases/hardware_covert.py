"""
Covert Spacecraft hardware sale model.

Defence customer buys TX+RX hardware. Value includes a defence premium
multiplier. Incumbent cost is per-spacecraft stealth measures.
"""

import numpy as np

from neowatt.use_case_model import UseCaseModel
from neowatt.distributions import sample
from neowatt.data_loader import get_param_value


class HardwareCovertModel(UseCaseModel):
    """Covert Spacecraft: sell hardware to defence, defence premium pricing."""

    def compute_costs(self, n, rng):
        cost = self.params["cost"]

        tx_hw = sample(cost["tx_hardware_k"], n, rng) * 1000
        rx_hw = sample(cost["rx_hardware_k"], n, rng) * 1000
        ground = sample(cost["ground_segment_k"], n, rng) * 1000

        capex = tx_hw + rx_hw + ground
        annual_opex = sample(cost["ops_cost_k_yr"], n, rng) * 1000

        return capex, annual_opex

    def compute_annual_revenue(self, n, rng):
        econ = self.params["economic"]
        tech = self.params["technical"]

        tx_sale = sample(econ["tx_sale_price_k"], n, rng) * 1000
        rx_sale = sample(econ["rx_sale_price_k"], n, rng) * 1000
        premium = sample(tech["defence_wtp_premium"], n, rng)
        amort = get_param_value(econ.get("amortization_years", {"value": 8}))
        support = sample(econ.get("annual_support_k", {"value": 0}), n, rng) * 1000

        return (tx_sale + rx_sale) * premium / amort + support

    def compute_incumbent_cost_per_unit(self, n, rng):
        return sample(self.params["incumbent"]["cost_per_spacecraft_k"], n, rng) * 1000

    def compute_our_price_per_unit(self, n, rng):
        econ = self.params["economic"]

        tx_sale = sample(econ["tx_sale_price_k"], n, rng) * 1000
        rx_sale = sample(econ["rx_sale_price_k"], n, rng) * 1000

        return tx_sale + rx_sale  # per-spacecraft cost to customer
