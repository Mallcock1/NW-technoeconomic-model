"""
Stealth / Low-Observable Spacecraft model.

Standard power delivery model with a defence WTP premium multiplier.
"""

import numpy as np

from neowatt.use_case_model import UseCaseModel
from neowatt.distributions import sample
from neowatt.data_loader import get_param_value


class StealthModel(UseCaseModel):

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
        premium = sample(tech["defence_wtp_premium"], n, rng)
        avail = sample(tech.get("availability", {"value": 0.90}), n, rng)

        return power * wtp * premium * avail

    def compute_incumbent_cost_per_unit(self, n, rng):
        return sample(self.params["incumbent"]["cost_per_spacecraft_k"], n, rng) * 1000

    def compute_our_price_per_unit(self, n, rng):
        # Our price per spacecraft: WTP * power * premium (one-time equivalent)
        econ = self.params["economic"]
        tech = self.params["technical"]
        wtp = sample(econ["wtp_per_W"], n, rng)
        power = sample(tech["power_delivered_W"], n, rng)
        return wtp * power  # $/spacecraft equivalent

    def compute_market_size(self, n, rng):
        econ = self.params["economic"]
        tech = self.params["technical"]
        wtp = get_param_value(econ["wtp_per_W"])
        power = get_param_value(tech["power_delivered_W"])
        premium = get_param_value(tech["defence_wtp_premium"])
        addressable = get_param_value(econ["addressable_units"])
        penetration = get_param_value(econ["penetration_rate"])

        annual_per_cust = wtp * power * premium
        tam = annual_per_cust * addressable / 1000  # $k
        sam = tam * 0.3
        som = tam * penetration
        return {"tam_k": tam, "sam_k": sam, "som_k": som}
