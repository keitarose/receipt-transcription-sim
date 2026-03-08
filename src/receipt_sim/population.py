"""Population generation and segmentation."""

from __future__ import annotations

import uuid

import numpy as np

from receipt_sim.models import PopulationMember, SimConfig


def generate_population(
    config: SimConfig, rng: np.random.Generator
) -> list[PopulationMember]:
    """Generate the full population of panel members."""
    members: list[PopulationMember] = []
    for _ in range(config.population.size):
        hi = int(rng.integers(0, 2**64, dtype=np.uint64))
        lo = int(rng.integers(0, 2**64, dtype=np.uint64))
        user_id = str(uuid.UUID(int=(hi << 64) | lo))
        segmentation = assign_segmentation(config, rng)
        lambda_i = assign_submission_rate(config, rng)
        quality_score = assign_quality_score(config, rng)
        retailer_mix = assign_retailer_mix(config, rng)
        seg_modifier = compute_segmentation_modifier(config, segmentation)
        engagement = assign_baseline_engagement(config, segmentation, rng)

        members.append(
            PopulationMember(
                user_id=user_id,
                age_group=segmentation["age_group"],
                lifestage=segmentation["lifestage"],
                social_grade=segmentation["social_grade"],
                geography=segmentation["geography"],
                household_size=segmentation["household_size"],
                has_dogs=segmentation["has_dogs"],
                has_cats=segmentation["has_cats"],
                panel_tenure_months=segmentation["panel_tenure_months"],
                lambda_i=lambda_i,
                quality_score=quality_score,
                retailer_mix=retailer_mix,
                baseline_engagement=engagement,
                segmentation_modifier=seg_modifier,
            )
        )
    return members


def _weighted_choice(weights: dict, rng: np.random.Generator):
    """Sample one key from a dict of {key: probability} weights."""
    keys = list(weights.keys())
    probs = list(weights.values())
    return rng.choice(keys, p=probs)


def assign_segmentation(config: SimConfig, rng: np.random.Generator) -> dict:
    """Draw segmentation attributes for one member."""
    pop = config.population

    age_group = _weighted_choice(pop.age_groups, rng)
    lifestage = _weighted_choice(pop.lifestages, rng)
    social_grade = _weighted_choice(pop.social_grades, rng)
    geography = _weighted_choice(pop.geographies, rng)
    household_size = int(_weighted_choice(pop.household_size_weights, rng))

    has_dogs = bool(rng.random() < pop.pet_dog_probability)
    has_cats = bool(rng.random() < pop.pet_cat_probability)

    panel_tenure_months = float(rng.uniform(0, pop.tenure_max_months))

    return {
        "age_group": age_group,
        "lifestage": lifestage,
        "social_grade": social_grade,
        "geography": geography,
        "household_size": household_size,
        "has_dogs": has_dogs,
        "has_cats": has_cats,
        "panel_tenure_months": panel_tenure_months,
    }


def assign_submission_rate(config: SimConfig, rng: np.random.Generator) -> float:
    """Draw a personal submission rate from a Gamma distribution."""
    return float(
        rng.gamma(config.population.lambda_alpha, config.population.lambda_beta)
    )


def assign_quality_score(config: SimConfig, rng: np.random.Generator) -> float:
    """Draw a quality score from a Beta distribution."""
    return float(rng.beta(config.population.quality_a, config.population.quality_b))


def assign_retailer_mix(
    config: SimConfig, rng: np.random.Generator
) -> dict[str, float]:
    """Draw a personalised retailer mix via Dirichlet perturbation."""
    retailer_names = list(config.retailers.keys())
    base_weights = [config.retailers[r].mix_weight for r in retailer_names]
    alphas = [w * config.population.dirichlet_concentration for w in base_weights]
    drawn = rng.dirichlet(alphas)
    return {name: float(p) for name, p in zip(retailer_names, drawn)}


def compute_segmentation_modifier(config: SimConfig, segmentation: dict) -> float:
    """Compute additive activity modifier from segmentation attributes."""
    modifier = 0.0
    weights = config.activity.segmentation_weights

    # Household size effect
    modifier += (segmentation["household_size"] - 1) * weights[
        "household_size_per_extra"
    ]

    # Family lifestage boost
    if segmentation["lifestage"] in ("Young Family", "Middle Family"):
        modifier += weights["family_lifestage_boost"]

    # Pet ownership boost
    if segmentation["has_dogs"]:
        modifier += weights["pet_owner_boost"]
    if segmentation["has_cats"]:
        modifier += weights["pet_owner_boost"]

    # Social grade effect
    if segmentation["social_grade"] == "AB":
        modifier += weights["high_social_grade_boost"]
    elif segmentation["social_grade"] == "DE":
        modifier += weights["low_social_grade_penalty"]

    return modifier


def assign_baseline_engagement(
    config: SimConfig, segmentation: dict, rng: np.random.Generator
) -> float:
    """Draw baseline engagement, adjusted by tenure."""
    base = float(
        rng.beta(config.population.engagement_a, config.population.engagement_b)
    )
    tenure_factor = max(
        0,
        1.0
        - segmentation["panel_tenure_months"]
        / config.population.tenure_max_months
        * 0.2,
    )
    return min(1.0, base * (0.8 + 0.2 * tenure_factor))
