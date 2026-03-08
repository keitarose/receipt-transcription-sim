"""Tests for the transcription service."""

from dataclasses import replace
from pathlib import Path

import numpy as np

from receipt_sim.config import load_config
from receipt_sim.models import ReceiptRequest, SimConfig
from receipt_sim.retailers import RetailerProfile, RetailerType, load_retailer_profiles
from receipt_sim.service import (
    compute_effective_p_correct,
    compute_effective_p_fail,
    process_receipt,
)

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "default.yaml")


def _base_config() -> SimConfig:
    return load_config(CONFIG_PATH)


def _config_with_service(**overrides) -> SimConfig:
    config = _base_config()
    new_svc = replace(config.service, **overrides)
    return replace(config, service=new_svc)


def _make_request() -> ReceiptRequest:
    return ReceiptRequest(
        receipt_id="r-001",
        user_id="u-001",
        timestamp=10.0,
        retailer_type="grocery_major",
    )


def _profiles(config: SimConfig | None = None):
    return load_retailer_profiles(config or _base_config())


class TestProcessReceipt:
    def test_failure_returns_none(self):
        """TC-SVC-01: Guaranteed failure returns None."""
        config = _config_with_service(base_p_fail=1.0)
        profiles = _profiles(config)
        # quality=0 and fail_modifier for grocery_major=0.6 gives p_fail = 1.0*1.0*0.6=0.6
        # To guarantee failure we need p_fail=1.0, so use quality=0 and a profile w/ modifier>=1
        profile_override = {
            rt: RetailerProfile(rt, fail_modifier=1.0, correct_modifier=1.0)
            for rt in profiles
        }
        rng = np.random.default_rng(42)
        result = process_receipt(_make_request(), 0.0, profile_override, config, rng)
        assert result is None

    def test_non_failure_returns_response(self):
        """TC-SVC-02: Zero failure rate always returns a response."""
        config = _config_with_service(base_p_fail=0.0)
        profiles = _profiles(config)
        rng = np.random.default_rng(42)
        result = process_receipt(_make_request(), 0.5, profiles, config, rng)
        assert result is not None


class TestEffectiveProbabilities:
    def test_effective_p_fail_computation(self):
        """TC-SVC-03: p_fail calculation and clamping."""
        profile = RetailerProfile(RetailerType.INDEPENDENT, 1.5, 1.0)
        assert abs(compute_effective_p_fail(0.5, 0.5, profile) - 0.375) < 1e-9

        # Test clamping to 1.0
        profile_high = RetailerProfile(RetailerType.INDEPENDENT, 10.0, 1.0)
        assert compute_effective_p_fail(1.0, 0.0, profile_high) == 1.0

    def test_effective_p_correct_computation(self):
        """TC-SVC-04: p_correct calculation and clamping."""
        profile = RetailerProfile(RetailerType.INDEPENDENT, 1.0, 1.5)
        assert abs(compute_effective_p_correct(0.5, 0.5, profile) - 0.375) < 1e-9


class TestResponseTime:
    def test_fast_path_response_time_distribution(self):
        """TC-SVC-05: Uncorrected path response times match mu_fast."""
        config = _config_with_service(base_p_fail=0.0, base_p_correct=0.0)
        profiles = _profiles(config)
        rng = np.random.default_rng(42)
        times = []
        for _ in range(10_000):
            resp = process_receipt(_make_request(), 0.5, profiles, config, rng)
            assert resp is not None
            times.append(resp.response_time)

        mean = np.mean(times)
        se = np.std(times, ddof=1) / np.sqrt(len(times))
        assert abs(mean - config.service.mu_fast) < 3 * se

    def test_slow_path_response_time_distribution(self):
        """TC-SVC-06: Corrected path response times match mu_slow."""
        config = _config_with_service(base_p_fail=0.0, base_p_correct=1.0)
        profiles = _profiles(config)
        rng = np.random.default_rng(42)
        times = []
        for _ in range(10_000):
            resp = process_receipt(_make_request(), 0.0, profiles, config, rng)
            # With quality=0.0 and base_p_correct=1.0, p_correct=1.0*1.0*modifier
            # For grocery_major correct_modifier=0.5, so p_correct=0.5
            # Use quality=0 to maximize p_correct
            if resp is not None:
                times.append(resp.response_time)

        # Some will be corrected, some not — use a config that forces correction
        config2 = _config_with_service(base_p_fail=0.0, base_p_correct=1.0)
        # Override profiles so correct_modifier is high enough
        forced_profiles = {
            rt: RetailerProfile(rt, fail_modifier=0.0, correct_modifier=100.0)
            for rt in profiles
        }
        times2 = []
        rng2 = np.random.default_rng(42)
        for _ in range(10_000):
            resp = process_receipt(_make_request(), 0.0, forced_profiles, config2, rng2)
            assert resp is not None
            assert resp.was_corrected
            times2.append(resp.response_time)

        mean = np.mean(times2)
        se = np.std(times2, ddof=1) / np.sqrt(len(times2))
        assert abs(mean - config2.service.mu_slow) < 3 * se

    def test_response_time_non_negative(self):
        """TC-SVC-07: All response times are >= 0 even with wide sigma."""
        config = _config_with_service(base_p_fail=0.0, sigma_fast=5.0, sigma_slow=5.0)
        profiles = _profiles(config)
        rng = np.random.default_rng(42)
        for _ in range(10_000):
            resp = process_receipt(_make_request(), 0.5, profiles, config, rng)
            assert resp is not None
            assert resp.response_time >= 0.0


class TestApproval:
    def test_approval_awards_base_reward(self):
        """TC-SVC-08: 100% approval gives base_reward tokens."""
        config = _config_with_service(base_p_fail=0.0, base_p_approve=1.0)
        profiles = _profiles(config)
        rng = np.random.default_rng(42)
        resp = process_receipt(_make_request(), 0.5, profiles, config, rng)
        assert resp is not None
        assert resp.tokens_awarded == config.service.base_reward

    def test_rejection_awards_zero(self):
        """TC-SVC-09: 0% approval gives zero tokens and a message."""
        config = _config_with_service(base_p_fail=0.0, base_p_approve=0.0)
        profiles = _profiles(config)
        rng = np.random.default_rng(42)
        resp = process_receipt(_make_request(), 0.5, profiles, config, rng)
        assert resp is not None
        assert resp.tokens_awarded == 0
        assert resp.message is not None

    def test_corrected_approval_same_reward(self):
        """TC-SVC-10: Corrected + approved still gives base_reward."""
        config = _config_with_service(
            base_p_fail=0.0, base_p_correct=1.0, base_p_approve=1.0
        )
        forced_profiles = {
            rt: RetailerProfile(rt, fail_modifier=0.0, correct_modifier=100.0)
            for rt in RetailerType
        }
        rng = np.random.default_rng(42)
        resp = process_receipt(_make_request(), 0.0, forced_profiles, config, rng)
        assert resp is not None
        assert resp.was_corrected is True
        assert resp.tokens_awarded == config.service.base_reward


class TestQualityEffect:
    def test_high_quality_reduces_failure(self):
        """TC-SVC-11: Higher quality = lower failure rate."""
        config = _config_with_service(base_p_fail=0.5)
        profiles = _profiles(config)
        n = 10_000

        rng_high = np.random.default_rng(42)
        failures_high_q = sum(
            1
            for _ in range(n)
            if process_receipt(_make_request(), 0.9, profiles, config, rng_high) is None
        )

        rng_low = np.random.default_rng(42)
        failures_low_q = sum(
            1
            for _ in range(n)
            if process_receipt(_make_request(), 0.1, profiles, config, rng_low) is None
        )

        rate_high_q = failures_high_q / n
        rate_low_q = failures_low_q / n
        assert rate_high_q < rate_low_q


class TestResponseEchoes:
    def test_response_echoes_request_ids(self):
        """TC-SVC-12: Response carries request IDs."""
        config = _config_with_service(base_p_fail=0.0)
        profiles = _profiles(config)
        rng = np.random.default_rng(42)
        req = _make_request()
        resp = process_receipt(req, 0.5, profiles, config, rng)
        assert resp is not None
        assert resp.receipt_id == req.receipt_id
        assert resp.user_id == req.user_id
