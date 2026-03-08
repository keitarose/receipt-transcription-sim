"""Tests for retailer definitions and sampling."""

from pathlib import Path

import numpy as np

from receipt_sim.config import load_config
from receipt_sim.retailers import RetailerType, load_retailer_profiles, sample_retailer

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "default.yaml")


def _get_config_and_profiles():
    config = load_config(CONFIG_PATH)
    profiles = load_retailer_profiles(config)
    return config, profiles


class TestRetailerProfiles:
    def test_all_types_have_profiles(self):
        """TC-RET-01: Every RetailerType member has a profile."""
        _, profiles = _get_config_and_profiles()
        for member in RetailerType:
            assert member in profiles

    def test_modifier_values_positive(self):
        """TC-RET-02: All modifiers are positive."""
        _, profiles = _get_config_and_profiles()
        for profile in profiles.values():
            assert profile.fail_modifier > 0
            assert profile.correct_modifier > 0


class TestSampleRetailer:
    def test_sample_retailer_respects_mix(self):
        """TC-RET-03: Sampling frequencies match mix probabilities."""
        rng = np.random.default_rng(42)
        mix = {"grocery_major": 0.7, "independent": 0.3}
        n = 10_000
        counts = {"grocery_major": 0, "independent": 0}
        for _ in range(n):
            r = sample_retailer(mix, rng)
            counts[r.value] += 1

        observed_freq = counts["grocery_major"] / n
        assert abs(observed_freq - 0.7) < 0.03

    def test_sample_retailer_deterministic(self):
        """TC-RET-04: Same seed produces identical sequences."""
        mix = {"grocery_major": 0.5, "convenience": 0.3, "fuel": 0.2}
        n = 100

        rng1 = np.random.default_rng(123)
        seq1 = [sample_retailer(mix, rng1) for _ in range(n)]

        rng2 = np.random.default_rng(123)
        seq2 = [sample_retailer(mix, rng2) for _ in range(n)]

        assert seq1 == seq2
