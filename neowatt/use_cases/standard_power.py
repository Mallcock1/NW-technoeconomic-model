"""
Standard power delivery model — shared by LEO Eclipse, Shadow, HAPS, Lunar Night, In-Orbit Servicing.

Revenue = power_delivered * wtp_per_W (annual, based on duty cycle and availability)
Cost = TX hardware + RX hardware + launch + ground segment + annual ops
Incumbent comparison = incumbent $/W vs our $/W (WTP)
"""

import numpy as np

from neowatt.use_case_model import UseCaseModel
from neowatt.distributions import sample
from neowatt.data_loader import get_param_value


class StandardPowerModel(UseCaseModel):
    """Standard power delivery use case: beam power, charge per watt."""

    def compute_costs(self, n, rng):
        cost = self.params["cost"]
        launch_cost = sample(self.global_params["global"]["launch_cost_per_kg"], n, rng)

        tx_hw = sample(cost["tx_hardware_k"], n, rng) * 1000
        rx_hw = sample(cost["rx_hardware_k"], n, rng) * 1000
        tx_launch = sample(cost["tx_mass_kg"], n, rng) * launch_cost
        rx_launch = sample(cost["rx_mass_kg"], n, rng) * launch_cost
        ground = sample(cost["ground_segment_k"], n, rng) * 1000

        capex = tx_hw + rx_hw + tx_launch + rx_launch + ground
        annual_opex = sample(cost["ops_cost_k_yr"], n, rng) * 1000

        return capex, annual_opex

    def compute_annual_revenue(self, n, rng):
        tech = self.params["technical"]
        econ = self.params["economic"]

        power = sample(tech["power_delivered_W"], n, rng)
        wtp = sample(econ["wtp_per_W"], n, rng)
        duty = sample(tech.get("duty_cycle", {"value": 1.0}), n, rng)
        avail = sample(tech.get("availability", {"value": 0.90}), n, rng)

        return power * wtp * duty * avail

    def compute_incumbent_cost_per_unit(self, n, rng):
        return sample(self.params["incumbent"]["cost_per_W"], n, rng)

    def compute_our_price_per_unit(self, n, rng):
        return sample(self.params["economic"]["wtp_per_W"], n, rng)
