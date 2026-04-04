"""
YAML data loading for use case definitions and global parameters.
"""

import yaml
from pathlib import Path


def load_yaml(filepath: str | Path) -> dict:
    """Load a YAML file and return as dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_global_params(data_dir: str | Path = None) -> dict:
    """Load global_params.yaml from the data directory."""
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"
    return load_yaml(Path(data_dir) / "global_params.yaml")


def load_use_cases(data_dir: str | Path = None) -> dict:
    """Load use_cases.yaml and return the use_cases dict."""
    if data_dir is None:
        data_dir = Path(__file__).parent.parent / "data"
    data = load_yaml(Path(data_dir) / "use_cases.yaml")
    return data["use_cases"]


def get_param_value(param_spec) -> float:
    """Extract the base value from a parameter spec.

    Handles both dict specs (with 'value' key) and plain numbers.
    """
    if isinstance(param_spec, dict):
        return param_spec["value"]
    return float(param_spec)
