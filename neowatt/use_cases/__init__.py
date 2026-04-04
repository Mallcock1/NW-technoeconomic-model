from neowatt.use_cases.standard_power import StandardPowerModel
from neowatt.use_cases.life_extension import LifeExtensionModel
from neowatt.use_cases.peak_power import PeakPowerModel
from neowatt.use_cases.power_as_service import PowerAsServiceModel
from neowatt.use_cases.lightweight_sc import LightweightSCModel
from neowatt.use_cases.attitude_independent import AttitudeIndependentModel
from neowatt.use_cases.stealth import StealthModel
from neowatt.use_cases.debris_ablation import DebrisAblationModel

MODEL_REGISTRY = {
    "StandardPowerModel": StandardPowerModel,
    "LifeExtensionModel": LifeExtensionModel,
    "PeakPowerModel": PeakPowerModel,
    "PowerAsServiceModel": PowerAsServiceModel,
    "LightweightSCModel": LightweightSCModel,
    "AttitudeIndependentModel": AttitudeIndependentModel,
    "StealthModel": StealthModel,
    "DebrisAblationModel": DebrisAblationModel,
}
