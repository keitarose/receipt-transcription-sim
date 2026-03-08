"""Retailer type definitions and sampling."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from receipt_sim.models import ConfigValidationError, SimConfig


class RetailerType(str, Enum):
    GROCERY_MAJOR = "grocery_major"
    GROCERY_DISCOUNTER = "grocery_discounter"
    CONVENIENCE = "convenience"
    ONLINE = "online"
    HEALTH_BEAUTY = "health_beauty"
    GENERAL_MERCHANDISE = "general_merchandise"
    INDEPENDENT = "independent"
    FUEL = "fuel"


@dataclass(frozen=True)
class RetailerProfile:
    retailer_type: RetailerType
    fail_modifier: float
    correct_modifier: float


def load_retailer_profiles(
    config: SimConfig,
) -> dict[RetailerType, RetailerProfile]:
    """Build retailer profiles from config. Raises if any type is missing."""
    profiles: dict[RetailerType, RetailerProfile] = {}
    for key, rc in config.retailers.items():
        rt = RetailerType(key)
        profiles[rt] = RetailerProfile(
            retailer_type=rt,
            fail_modifier=rc.fail_modifier,
            correct_modifier=rc.correct_modifier,
        )

    for member in RetailerType:
        if member not in profiles:
            raise ConfigValidationError(
                f"RetailerType '{member.value}' has no entry in config.retailers"
            )

    return profiles


def sample_retailer(mix: dict[str, float], rng: np.random.Generator) -> RetailerType:
    """Sample a single retailer type from a probability mix."""
    keys = list(mix.keys())
    probs = [mix[k] for k in keys]
    chosen = rng.choice(keys, p=probs)
    return RetailerType(chosen)
