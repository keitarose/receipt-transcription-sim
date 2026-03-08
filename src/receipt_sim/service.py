"""Transcription service — stateless receipt processing."""

from __future__ import annotations

import numpy as np

from receipt_sim.models import ReceiptRequest, ReceiptResponse, SimConfig
from receipt_sim.retailers import RetailerProfile, RetailerType


def process_receipt(
    request: ReceiptRequest,
    quality_score: float,
    retailer_profiles: dict[RetailerType, RetailerProfile],
    config: SimConfig,
    rng: np.random.Generator,
) -> ReceiptResponse | None:
    """Process a receipt through the transcription service pipeline."""
    retailer = retailer_profiles[RetailerType(request.retailer_type)]

    p_fail = compute_effective_p_fail(
        config.service.base_p_fail, quality_score, retailer
    )
    if not attempt_service(p_fail, rng):
        return None

    p_correct = compute_effective_p_correct(
        config.service.base_p_correct, quality_score, retailer
    )
    corrected = determine_correction(p_correct, rng)

    response_time = sample_response_time(corrected, config, rng)
    decision, tokens = decide_approval(config, rng)

    return build_response(request, response_time, corrected, decision, tokens)


def compute_effective_p_fail(
    base: float, quality: float, retailer: RetailerProfile
) -> float:
    """Compute effective failure probability."""
    return min(1.0, max(0.0, base * (1.0 - quality) * retailer.fail_modifier))


def compute_effective_p_correct(
    base: float, quality: float, retailer: RetailerProfile
) -> float:
    """Compute effective correction probability."""
    return min(1.0, max(0.0, base * (1.0 - quality) * retailer.correct_modifier))


def attempt_service(p_fail: float, rng: np.random.Generator) -> bool:
    """Return True if the receipt survives (not failed)."""
    return rng.random() >= p_fail


def determine_correction(p_correct: float, rng: np.random.Generator) -> bool:
    """Return True if the receipt needs correction."""
    return rng.random() < p_correct


def sample_response_time(
    corrected: bool, config: SimConfig, rng: np.random.Generator
) -> float:
    """Sample response time from the appropriate distribution."""
    if corrected:
        t = rng.normal(config.service.mu_slow, config.service.sigma_slow)
    else:
        t = rng.normal(config.service.mu_fast, config.service.sigma_fast)
    return max(0.0, t)


def decide_approval(config: SimConfig, rng: np.random.Generator) -> tuple[str, int]:
    """Decide approval and compute token reward."""
    if rng.random() < config.service.base_p_approve:
        return ("approved", config.service.base_reward)
    else:
        return ("rejected", 0)


def build_response(
    request: ReceiptRequest,
    response_time: float,
    corrected: bool,
    decision: str,
    tokens: int,
) -> ReceiptResponse:
    """Construct a ReceiptResponse."""
    message = None if decision == "approved" else _generate_rejection_reason(corrected)
    return ReceiptResponse(
        receipt_id=request.receipt_id,
        user_id=request.user_id,
        timestamp=request.timestamp + response_time,
        response_time=response_time,
        was_corrected=corrected,
        decision=decision,
        tokens_awarded=tokens,
        message=message,
    )


def _generate_rejection_reason(corrected: bool) -> str:
    """Generate a rejection reason string."""
    if corrected:
        return "Receipt content unclear after correction"
    return "Receipt could not be verified"
