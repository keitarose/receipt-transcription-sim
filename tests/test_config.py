"""Tests for configuration loading, merging, and validation."""

import copy
from pathlib import Path

import pytest
import yaml

from receipt_sim.config import load_config, merge_configs, validate_config
from receipt_sim.models import ConfigValidationError, SimConfig

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "default.yaml")


def _load_raw() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


class TestLoadConfig:
    def test_load_valid_config(self):
        """TC-CFG-01: Load default.yaml and check key values."""
        config = load_config(CONFIG_PATH)
        assert isinstance(config, SimConfig)
        assert config.service.base_p_fail == 0.05
        assert config.population.size == 60000
        assert len(config.retailers) == 8

    def test_load_with_scenario_override(self):
        """TC-CFG-02: Scenario overrides merge correctly."""
        config = load_config(CONFIG_PATH, scenario="high_failure")
        assert config.service.base_p_fail == 0.20
        assert config.simulation.seed == 42  # unchanged from base


class TestValidateConfig:
    def test_missing_required_key(self):
        """TC-CFG-03: Missing top-level section raises error."""
        raw = _load_raw()
        del raw["service"]
        with pytest.raises(ConfigValidationError, match="service"):
            validate_config(raw)

    def test_probability_out_of_range(self):
        """TC-CFG-04: Probability > 1 or < 0 raises error."""
        raw = _load_raw()
        raw["service"]["base_p_fail"] = 1.5
        with pytest.raises(ConfigValidationError):
            validate_config(raw)

        raw2 = _load_raw()
        raw2["service"]["base_p_fail"] = -0.1
        with pytest.raises(ConfigValidationError):
            validate_config(raw2)

    def test_negative_std_deviation(self):
        """TC-CFG-05: Negative sigma raises error."""
        raw = _load_raw()
        raw["service"]["sigma_fast"] = -1.0
        with pytest.raises(ConfigValidationError):
            validate_config(raw)

    def test_missing_retailer_modifier(self):
        """TC-CFG-06: Retailer missing required key raises error."""
        raw = _load_raw()
        del raw["retailers"]["grocery_major"]["correct_modifier"]
        with pytest.raises(ConfigValidationError, match="correct_modifier"):
            validate_config(raw)


class TestMergeConfigs:
    def test_merge_deep_override(self):
        """TC-CFG-07: Deep merge preserves non-overridden keys."""
        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"b": 99}}
        result = merge_configs(base, override)
        assert result == {"a": {"b": 99, "c": 2}}
        # Ensure original not mutated
        assert base == {"a": {"b": 1, "c": 2}}
