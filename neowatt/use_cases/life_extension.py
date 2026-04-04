"""
Satellite Life Extension model.

Revenue = annual service fee per satellite * years extended
Incumbent = replacement launch cost or MEV contract price per year
Customer saving = (incumbent annual cost - our annual price) / incumbent annual cost
"""

import numpy as np

from neowatt.use_case_model import UseCaseModel
from neowatt.distributions import sample


class LifeExtensionModel(UseCaseModel):

    def compute_costs(self, n, rng):
        cost = self.params["cost"]
        launch_cost = sample(self.params["economic"]["launch_cost_per_kg"], n, rng)

        tx_hw = sample(cost["tx_hardware_k"], n, rng) * 1000
        rx_hw = sample(cost["rx_hardware_k"], n, rng) * 1000
        tx_launch = sample(cost["tx_mass_kg"], n, rng) * launch_cost
        rx_launch = sample(cost["rx_mass_kg"], n, rng) * launch_cost
        ground = sample(cost["ground_segment_k"], n, rng) * 1000

        capex = tx_hw + rx_hw + tx_launch + rx_launch + ground
        annual_opex = sample(cost["ops_cost_k_yr"], n, rng) * 1000

        return capex, annual_opex

    def compute_annual_revenue(self, n, rng):
        econ = self.params["economic"]
        return sample(econ["revenue_per_year_k"], n, rng) * 1000

    def compute_incumbent_cost_per_unit(self, n, rng):
        # Incumbent cost per year of life extension
        return sample(self.params["incumbent"]["cost_per_year_k"], n, rng) * 1000

    def compute_our_price_per_unit(self, n, rng):
        # Our annual service price
        return sample(self.params["economic"]["revenue_per_year_k"], n, rng) * 1000

