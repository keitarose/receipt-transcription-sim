"""Incentive engine — token balance management and reward computation."""

from __future__ import annotations

from receipt_sim.models import PopulationMember, ReceiptResponse, SimConfig


def apply_reward(member: PopulationMember, response: ReceiptResponse) -> int:
    """Credit awarded tokens to the member and return new balance."""
    member.token_balance += response.tokens_awarded
    return member.token_balance


_ENGAGEMENT_BOOST_RATE = 0.001  # tokens → engagement points conversion rate
_ENGAGEMENT_BOOST_CAP = 0.3  # max engagement boost from tokens


def compute_engagement_boost(member: PopulationMember) -> float:
    """Compute an engagement multiplier based on recent token income.

    Higher balance → slight increase in submission frequency.
    Uses a soft-saturation curve: boost = min(cap, balance * rate).
    """
    return min(_ENGAGEMENT_BOOST_CAP, member.token_balance * _ENGAGEMENT_BOOST_RATE)


def effective_submission_rate(
    member: PopulationMember, config: SimConfig, seasonal_mult: float
) -> float:
    """Compute the instantaneous submission rate for a member.

    Combines:
      - base rate (lambda_i)
      - segmentation modifier (additive)
      - seasonal multiplier (additive on log-scale → multiplicative)
      - engagement boost from incentives (additive)
      - baseline engagement (multiplicative)
    """
    engagement_boost = compute_engagement_boost(member)
    rate = member.lambda_i * (
        1.0 + member.segmentation_modifier + seasonal_mult + engagement_boost
    )
    rate *= member.baseline_engagement
    return max(0.0, rate)


def compute_tenure_decay(member: PopulationMember, config: SimConfig) -> float:
    """Compute tenure-based decay factor for submission rate."""
    decay = 1.0 - config.activity.tenure_decay_rate * member.panel_tenure_months
    return max(0.0, decay)


def apply_tenure_decay(
    rate: float, member: PopulationMember, config: SimConfig
) -> float:
    """Apply tenure decay to a submission rate."""
    return rate * compute_tenure_decay(member, config)
