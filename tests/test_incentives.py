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
    member = PopulationMember(
        user_id=overrides.get("user_id", "u-001"),  # type: ignore[arg-type]
        age_group=overrides.get("age_group", "25-34"),  # type: ignore[arg-type]
        lifestage=overrides.get("lifestage", "Young Family"),  # type: ignore[arg-type]
        social_grade=overrides.get("social_grade", "C1"),  # type: ignore[arg-type]
        geography=overrides.get("geography", "London"),  # type: ignore[arg-type]
        household_size=overrides.get("household_size", 3),  # type: ignore[arg-type]
        has_dogs=overrides.get("has_dogs", False),  # type: ignore[arg-type]
        has_cats=overrides.get("has_cats", False),  # type: ignore[arg-type]
        panel_tenure_months=overrides.get("panel_tenure_months", 6.0),  # type: ignore[arg-type]
        lambda_i=overrides.get("lambda_i", 2.0),  # type: ignore[arg-type]
        quality_score=overrides.get("quality_score", 0.7),  # type: ignore[arg-type]
        retailer_mix=overrides.get("retailer_mix", {"grocery_major": 1.0}),  # type: ignore[arg-type]
        baseline_engagement=overrides.get("baseline_engagement", 0.8),  # type: ignore[arg-type]
        segmentation_modifier=overrides.get("segmentation_modifier", 0.1),  # type: ignore[arg-type]
        token_balance=overrides.get("token_balance", 0),  # type: ignore[arg-type]
    )
    return member


def _make_response(**overrides) -> ReceiptResponse:
    return ReceiptResponse(
        receipt_id=overrides.get("receipt_id", "r-001"),  # type: ignore[arg-type]
        user_id=overrides.get("user_id", "u-001"),  # type: ignore[arg-type]
        timestamp=overrides.get("timestamp", 10.0),  # type: ignore[arg-type]
        response_time=overrides.get("response_time", 2.0),  # type: ignore[arg-type]
        was_corrected=overrides.get("was_corrected", False),  # type: ignore[arg-type]
        decision=overrides.get("decision", "approved"),  # type: ignore[arg-type]
        tokens_awarded=overrides.get("tokens_awarded", 10),  # type: ignore[arg-type]
        message=overrides.get("message", None),  # type: ignore[arg-type]
    )


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
        assert compute_engagement_boost(member) == 0.0

    def test_moderate_balance(self):
        """TC-INC-04: Moderate balance gives proportional boost."""
        member = _make_member(token_balance=100)
        boost = compute_engagement_boost(member)
        assert abs(boost - 0.1) < 1e-9

    def test_cap_applied(self):
        """TC-INC-05: Very high balance is capped at 0.3."""
        member = _make_member(token_balance=10_000)
        assert compute_engagement_boost(member) == 0.3


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
