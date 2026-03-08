"""Shared test fixtures for the receipt transcription simulation."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from receipt_sim.config import load_config
from receipt_sim.models import (
    PopulationMember,
    ReceiptRequest,
    ReceiptResponse,
    SimConfig,
)
from receipt_sim.population import generate_population
from receipt_sim.retailers import load_retailer_profiles

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "default.yaml")


@pytest.fixture
def base_config() -> SimConfig:
    """Load the default simulation configuration."""
    return load_config(CONFIG_PATH)


@pytest.fixture
def small_config(base_config: SimConfig) -> SimConfig:
    """Config with small population (10) and short duration (48h)."""
    pop = replace(base_config.population, size=10)
    sim = replace(base_config.simulation, duration=48.0)
    return replace(base_config, population=pop, simulation=sim)


@pytest.fixture
def rng() -> np.random.Generator:
    """Seeded random generator for reproducible tests."""
    return np.random.default_rng(42)


@pytest.fixture
def sample_member() -> PopulationMember:
    """A typical population member for unit tests."""
    return PopulationMember(
        user_id="u-test-001",
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
        retailer_mix={"grocery_major": 0.5, "convenience": 0.3, "online": 0.2},
        baseline_engagement=0.8,
        segmentation_modifier=0.1,
        token_balance=0,
    )


@pytest.fixture
def sample_request() -> ReceiptRequest:
    """A typical receipt request for unit tests."""
    return ReceiptRequest(
        receipt_id="r-test-001",
        user_id="u-test-001",
        timestamp=10.0,
        retailer_type="grocery_major",
    )


@pytest.fixture
def sample_response() -> ReceiptResponse:
    """A typical approved receipt response for unit tests."""
    return ReceiptResponse(
        receipt_id="r-test-001",
        user_id="u-test-001",
        timestamp=12.0,
        response_time=2.0,
        was_corrected=False,
        decision="approved",
        tokens_awarded=10,
        message=None,
    )


@pytest.fixture
def retailer_profiles(base_config: SimConfig):
    """Load retailer profiles from the default config."""
    return load_retailer_profiles(base_config)


@pytest.fixture
def small_population(small_config: SimConfig, rng: np.random.Generator):
    """Generate a small population for integration tests."""
    return generate_population(small_config, rng)
