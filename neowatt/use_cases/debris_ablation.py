"""
Debris Laser Ablation model.

Revenue = WTP per object * objects per year
No receiver needed. Greenfield incumbent (no existing cost-effective solution).
Uses P(positive NPV) instead of P(beating incumbent).
"""

import numpy as np

from neowatt.use_case_model import UseCaseModel
from neowatt.distributions import sample
from neowatt.data_loader import get_param_value


class DebrisAblationModel(UseCaseModel):

    def compute_costs(self, n, rng):
        cost = self.params["cost"]
        launch_cost = sample(self.global_params["global"]["launch_cost_per_kg"], n, rng)

        tx_hw = sample(cost["tx_hardware_k"], n, rng) * 1000
        # No RX for debris ablation
        tx_launch = sample(cost["tx_mass_kg"], n, rng) * launch_cost
        ground = sample(cost["ground_segment_k"], n, rng) * 1000

        capex = tx_hw + tx_launch + ground
        annual_opex = sample(cost["ops_cost_k_yr"], n, rng) * 1000

        return capex, annual_opex

    def compute_annual_revenue(self, n, rng):
        tech = self.params["technical"]
        econ = self.params["economic"]

        objects = sample(tech["objects_per_year"], n, rng)
        wtp = sample(econ["wtp_per_object_k"], n, rng) * 1000
        avail = sample(tech.get("availability", {"value": 0.85}), n, rng)

        return objects * wtp * avail

    def compute_incumbent_cost_per_unit(self, n, rng):
        # Cost of inaction per object (regulatory/insurance)
        return sample(self.params["incumbent"]["cost_per_object_k"], n, rng) * 1000

    def compute_our_price_per_unit(self, n, rng):
        return sample(self.params["economic"]["wtp_per_object_k"], n, rng) * 1000

    def compute_market_size(self, n, rng):
        econ = self.params["economic"]
        tech = self.params["technical"]
        wtp = get_param_value(econ["wtp_per_object_k"])
        objects = get_param_value(tech["objects_per_year"])
        addressable = get_param_value(econ["addressable_units"])
        penetration = get_param_value(econ["penetration_rate"])

        tam = wtp * addressable / 1000  # $k (all addressable debris * WTP each)
        sam = wtp * objects * 10 / 1000  # 10 years of ops
        som = tam * penetration
        return {"tam_k": tam, "sam_k": sam, "som_k": som}
