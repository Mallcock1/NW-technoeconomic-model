"""
Power-as-a-Service model.

Revenue = subscription price * customers served (from one TX platform)
Incumbent comparison = subscription cost vs CAPEX the customer avoids
"""

import numpy as np

from neowatt.use_case_model import UseCaseModel
from neowatt.distributions import sample
from neowatt.data_loader import get_param_value


class PowerAsServiceModel(UseCaseModel):

    def compute_costs(self, n, rng):
        cost = self.params["cost"]
        launch_cost = sample(self.params["economic"]["launch_cost_per_kg"], n, rng)

        tx_hw = sample(cost["tx_hardware_k"], n, rng) * 1000
        rx_hw = sample(cost["rx_hardware_k"], n, rng) * 1000
        # RX cost per customer * number of customers
        customers = sample(self.params["economic"]["customers_served"], n, rng)
        rx_total = rx_hw * customers

        tx_launch = sample(cost["tx_mass_kg"], n, rng) * launch_cost
        rx_launch = sample(cost["rx_mass_kg"], n, rng) * launch_cost * customers
        ground = sample(cost["ground_segment_k"], n, rng) * 1000

        capex = tx_hw + rx_total + tx_launch + rx_launch + ground
        annual_opex = sample(cost["ops_cost_k_yr"], n, rng) * 1000

        return capex, annual_opex

    def compute_annual_revenue(self, n, rng):
        econ = self.params["economic"]
        sub_price = sample(econ["subscription_price_k_yr"], n, rng) * 1000
        customers = sample(econ["customers_served"], n, rng)
        return sub_price * customers

    def compute_incumbent_cost_per_unit(self, n, rng):
        # Incumbent: total CAPEX the customer avoids over lifetime
        capex_avoided = sample(self.params["incumbent"]["capex_avoided_per_customer_k"], n, rng) * 1000
        return capex_avoided

    def compute_our_price_per_unit(self, n, rng):
        # Our total cost to customer over lifetime (subscription * years)
        sub = sample(self.params["economic"]["subscription_price_k_yr"], n, rng) * 1000
        amort = get_param_value(self.params["economic"]["amortization_years"])
        return sub * amort

