"""
Hardware sale model – NEOWATT sells TX and RX payload hardware to the customer.

The customer integrates the hardware on their own satellite/platform and pays
for their own launch. NEOWATT's costs are manufacturing and test/calibration;
revenue is the sale price plus an annual support/licensing fee.

Revenue = (TX sale price + RX sale price) / amortisation + annual support fee
Cost = TX manufacturing + RX manufacturing + ground segment (test/calibration)
       + internal cost of providing annual support
No launch costs, no satellite operations (customer operates everything).
"""

import numpy as np

from neowatt.use_case_model import UseCaseModel
from neowatt.distributions import sample
from neowatt.data_loader import get_param_value


class HardwareSaleModel(UseCaseModel):
    """Hardware sale model: sell TX+RX payload, customer operates."""

    def compute_costs(self, n, rng):
        cost = self.params["cost"]

        # NEOWATT's costs are manufacturing only (no launch – customer pays)
        tx_hw = sample(cost["tx_hardware_k"], n, rng) * 1000
        rx_hw = sample(cost["rx_hardware_k"], n, rng) * 1000
        ground = sample(cost["ground_segment_k"], n, rng) * 1000

        capex = tx_hw + rx_hw + ground

        # No satellite operations cost. Only cost of providing support service.
        support_cost = sample(
            self.params.get("cost", {}).get("support_cost_k_yr", {"value": 5}), n, rng
        ) * 1000

        return capex, support_cost

    def compute_annual_revenue(self, n, rng):
        econ = self.params["economic"]

        # Sale price (annualised over amortisation period)
        tx_sale = sample(econ["tx_sale_price_k"], n, rng) * 1000
        rx_sale = sample(econ["rx_sale_price_k"], n, rng) * 1000
        amort = get_param_value(econ.get("amortization_years", {"value": 7}))

        # Annual support/licensing fee
        support = sample(econ.get("annual_support_k", {"value": 0}), n, rng) * 1000

        return (tx_sale + rx_sale) / amort + support

    def compute_incumbent_cost_per_unit(self, n, rng):
        return sample(self.params["incumbent"]["cost_per_W"], n, rng)

    def compute_our_price_per_unit(self, n, rng):
        # Customer's total cost = hardware purchase + their own launch + support fees
        econ = self.params["economic"]
        tech = self.params["technical"]

        tx_sale = sample(econ["tx_sale_price_k"], n, rng) * 1000
        rx_sale = sample(econ["rx_sale_price_k"], n, rng) * 1000
        power = sample(tech["power_delivered_W"], n, rng)

        # Customer's cost per watt of delivered power
        total_hw_cost = tx_sale + rx_sale
        return np.where(power > 0, total_hw_cost / power, np.inf)
