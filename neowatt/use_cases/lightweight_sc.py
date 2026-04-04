"""
Lightweight Spacecraft Design model.

Value = mass saved * launch cost per kg + drag reduction benefit
Customer compares: cost of NEOWATT RX + subscription vs savings from removing solar arrays.
"""

import numpy as np

from neowatt.use_case_model import UseCaseModel
from neowatt.distributions import sample
from neowatt.data_loader import get_param_value


class LightweightSCModel(UseCaseModel):

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
        launch_cost = sample(self.global_params["global"]["launch_cost_per_kg"], n, rng)

        # Value from mass savings
        mass_saved = sample(tech["mass_saved_kg"], n, rng)
        mass_value = mass_saved * launch_cost

        # Value from array cost savings
        array_cost_per_kg = sample(self.params["incumbent"]["array_cost_per_kg"], n, rng)
        array_value = mass_saved * array_cost_per_kg

        # Total value (annualised over amortization)
        amort = get_param_value(self.params["economic"]["amortization_years"])
        return (mass_value + array_value) / amort

    def compute_incumbent_cost_per_unit(self, n, rng):
        # Incumbent cost = solar array cost per kg (what it costs to have arrays)
        return sample(self.params["incumbent"]["array_cost_per_kg"], n, rng)

    def compute_our_price_per_unit(self, n, rng):
        # Our effective cost per kg saved
        cost = self.params["cost"]
        launch_cost = sample(self.global_params["global"]["launch_cost_per_kg"], n, rng)
        mass_saved = sample(self.params["technical"]["mass_saved_kg"], n, rng)

        rx_hw = sample(cost["rx_hardware_k"], n, rng) * 1000
        rx_launch = sample(cost["rx_mass_kg"], n, rng) * launch_cost

        # Customer's cost for our solution per kg of mass they save
        customer_cost = (rx_hw + rx_launch) / np.maximum(mass_saved, 1.0)
        return customer_cost
