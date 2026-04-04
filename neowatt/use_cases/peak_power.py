"""
Peak Power on Demand model.

Revenue = WTP per kWh * power_kW * burst_duration_hrs * events_per_year
Customer saving compares burst pricing vs cost of oversizing solar+battery for peak demand.
"""

import numpy as np

from neowatt.use_case_model import UseCaseModel
from neowatt.distributions import sample
from neowatt.data_loader import get_param_value


class PeakPowerModel(UseCaseModel):

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
        tech = self.params["technical"]
        econ = self.params["economic"]

        power_W = sample(tech["power_delivered_W"], n, rng)
        power_kW = power_W / 1000.0
        burst_hrs = sample(tech["burst_duration_hrs"], n, rng)
        events = sample(tech["events_per_year"], n, rng)
        wtp_kwh = sample(econ["wtp_per_kWh"], n, rng)
        avail = sample(tech.get("availability", {"value": 0.85}), n, rng)

        return wtp_kwh * power_kW * burst_hrs * events * avail

    def compute_incumbent_cost_per_unit(self, n, rng):
        return sample(self.params["incumbent"]["cost_per_W"], n, rng)

    def compute_our_price_per_unit(self, n, rng):
        # Our price in $/W-peak terms for fair comparison with incumbent $/W
        # Incumbent $/W = one-time cost to have 1W peak capacity via oversized arrays
        # Our $/W = total cost of our service over lifetime / peak power delivered
        econ = self.params["economic"]
        tech = self.params["technical"]

        wtp_kwh = sample(econ["wtp_per_kWh"], n, rng)
        power_kW = sample(tech["power_delivered_W"], n, rng) / 1000.0
        burst_hrs = sample(tech["burst_duration_hrs"], n, rng)
        events = sample(tech["events_per_year"], n, rng)
        amort = get_param_value(econ["amortization_years"])
        avail = sample(tech.get("availability", {"value": 0.85}), n, rng)

        # Total customer cost over lifetime
        total_cost_to_customer = wtp_kwh * power_kW * burst_hrs * events * avail * amort
        # Convert to per-W-peak for comparison
        power_W = sample(tech["power_delivered_W"], n, rng)
        return np.where(power_W > 0, total_cost_to_customer / power_W, np.inf)

