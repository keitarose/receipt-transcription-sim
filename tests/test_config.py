"""Tests for configuration loading, merging, and validation."""

from pathlib import Path

import pytest

from receipt_sim.config import load_config, merge_configs, validate_config
from receipt_sim.models import ConfigValidationError, SimConfig

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "default.yaml")


def _load_raw_config() -> dict:
    """Helper: load default.yaml as a raw dict for test manipulation."""
    import yaml

    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def test_load_valid_config():
    """TC-CFG-01: Load default.yaml and check key values."""
    config = load_config(CONFIG_PATH)
    assert isinstance(config, SimConfig)
    assert config.service.base_p_fail == 0.05
    assert config.population.size == 1000
    assert len(config.retailers) == 8


def test_load_with_scenario_override():
    """TC-CFG-02: Scenario override merges correctly."""
    config = load_config(CONFIG_PATH, scenario="high_failure")
    assert config.service.base_p_fail == 0.20
    assert config.simulation.seed == 42  # unchanged from base


def test_missing_required_key():
    """TC-CFG-03: Missing section raises ConfigValidationError."""
    raw = _load_raw_config()
    del raw["service"]
    with pytest.raises(ConfigValidationError):
        validate_config(raw)


def test_probability_out_of_range():
    """TC-CFG-04: Probability outside [0, 1] raises error."""
    raw = _load_raw_config()
    raw["service"]["base_p_fail"] = 1.5
    with pytest.raises(ConfigValidationError):
        validate_config(raw)

    raw2 = _load_raw_config()
    raw2["service"]["base_p_fail"] = -0.1
    with pytest.raises(ConfigValidationError):
        validate_config(raw2)


def test_negative_std_deviation():
    """TC-CFG-05: Negative sigma raises error."""
    raw = _load_raw_config()
    raw["service"]["sigma_fast"] = -1.0
    with pytest.raises(ConfigValidationError):
        validate_config(raw)


def test_missing_retailer_modifier():
    """TC-CFG-06: Retailer missing required key raises error."""
    raw = _load_raw_config()
    del raw["retailers"]["grocery_major"]["correct_modifier"]
    with pytest.raises(ConfigValidationError):
        validate_config(raw)


def test_merge_deep_override():
    """TC-CFG-07: Deep merge works correctly."""
    base = {"a": {"b": 1, "c": 2}}
    override = {"a": {"b": 99}}
    result = merge_configs(base, override)
    assert result == {"a": {"b": 99, "c": 2}}
    # Ensure inputs not mutated
    assert base == {"a": {"b": 1, "c": 2}}
