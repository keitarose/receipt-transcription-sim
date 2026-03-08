"""Tests for the incentive engine."""

from dataclasses import replace
from pathlib import Path

from receipt_sim.config import load_config
from receipt_sim.incentives import (
    apply_reward,
    apply_tenure_decay,
    compute_engagement_boost,
    compute_tenure_decay,
    effective_submission_rate,
)
from receipt_sim.models import PopulationMember, ReceiptResponse, SimConfig

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "default.yaml")


def _base_config() -> SimConfig:
    return load_config(CONFIG_PATH)


def _make_member(**overrides) -> PopulationMember:
    defaults = dict(
        user_id="u-001",
        age_group="25-34",
        lifestage="Young Family",
        social_grade="C1",
        geography="London",
        household_size=3,
        has_dogs=False,
        has_cats=False,
        panel_tenure_months=6.0,
        lambda_i=2.0,
        quality_score=0.7,
        retailer_mix={"grocery_major": 1.0},
        baseline_engagement=0.8,
        segmentation_modifier=0.1,
        token_balance=0,
    )
    defaults.update(overrides)
    return PopulationMember(**defaults)


def _make_response(**overrides) -> ReceiptResponse:
    defaults = dict(
        receipt_id="r-001",
        user_id="u-001",
        timestamp=10.0,
        response_time=2.0,
        was_corrected=False,
        decision="approved",
        tokens_awarded=10,
        message=None,
    )
    defaults.update(overrides)
    return ReceiptResponse(**defaults)


class TestApplyReward:
    def test_credit_tokens(self):
        """TC-INC-01: Tokens are added to member balance."""
        member = _make_member(token_balance=5)
        resp = _make_response(tokens_awarded=10)
        new_balance = apply_reward(member, resp)
        assert new_balance == 15
        assert member.token_balance == 15

    def test_zero_reward_no_change(self):
        """TC-INC-02: Zero-award response doesn't change balance."""
        member = _make_member(token_balance=20)
        resp = _make_response(tokens_awarded=0)
        apply_reward(member, resp)
        assert member.token_balance == 20


class TestEngagementBoost:
    def test_zero_balance_no_boost(self):
        """TC-INC-03: Zero balance gives zero boost."""
        member = _make_member(token_balance=0)
        config = _base_config()
        assert compute_engagement_boost(member, config) == 0.0

    def test_moderate_balance(self):
        """TC-INC-04: Moderate balance gives proportional boost."""
        member = _make_member(token_balance=100)
        config = _base_config()
        boost = compute_engagement_boost(member, config)
        assert abs(boost - 0.1) < 1e-9

    def test_cap_applied(self):
        """TC-INC-05: Very high balance is capped at 0.3."""
        member = _make_member(token_balance=10_000)
        config = _base_config()
        assert compute_engagement_boost(member, config) == 0.3


class TestEffectiveSubmissionRate:
    def test_positive_rate(self):
        """TC-INC-06: Rate is positive under normal conditions."""
        member = _make_member()
        config = _base_config()
        rate = effective_submission_rate(member, config, seasonal_mult=0.0)
        assert rate > 0.0

    def test_seasonal_effect(self):
        """TC-INC-07: Positive seasonal multiplier increases rate."""
        member = _make_member()
        config = _base_config()
        rate_base = effective_submission_rate(member, config, 0.0)
        rate_high = effective_submission_rate(member, config, 0.3)
        assert rate_high > rate_base

    def test_negative_seasonal_clamps(self):
        """TC-INC-08: Extremely negative multiplier clamps rate at 0."""
        member = _make_member(
            lambda_i=0.1, segmentation_modifier=0.0, baseline_engagement=0.1
        )
        config = _base_config()
        rate = effective_submission_rate(member, config, -100.0)
        assert rate == 0.0


class TestTenureDecay:
    def test_zero_tenure_no_decay(self):
        """TC-INC-09: Zero tenure gives decay factor 1.0."""
        member = _make_member(panel_tenure_months=0.0)
        config = _base_config()
        assert compute_tenure_decay(member, config) == 1.0

    def test_long_tenure_decays(self):
        """TC-INC-10: Long tenure reduces decay factor."""
        member = _make_member(panel_tenure_months=60.0)
        config = _base_config()
        decay = compute_tenure_decay(member, config)
        assert decay < 1.0
        assert decay >= 0.0

    def test_apply_tenure_decay(self):
        """TC-INC-11: apply_tenure_decay reduces rate consistently."""
        member = _make_member(panel_tenure_months=20.0)
        config = _base_config()
        rate = 5.0
        decayed = apply_tenure_decay(rate, member, config)
        expected = rate * (1.0 - config.activity.tenure_decay_rate * 20.0)
        assert abs(decayed - expected) < 1e-9
