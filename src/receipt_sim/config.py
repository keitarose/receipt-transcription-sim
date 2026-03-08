"""Configuration loading, merging, and validation."""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

from receipt_sim.models import (
    ActivityConfig,
    ConfigValidationError,
    PopulationConfig,
    RetailerConfig,
    ServiceConfig,
    SimConfig,
    SimulationConfig,
)


def load_config(path: str, scenario: str | None = None) -> SimConfig:
    """Load YAML config, optionally merging a scenario overlay, and return SimConfig."""
    with open(path, "r") as f:
        base = yaml.safe_load(f)

    if scenario is not None:
        scenario_path = Path(path).parent / "scenarios" / f"{scenario}.yaml"
        with open(scenario_path, "r") as f:
            override = yaml.safe_load(f)
        if override:
            base = merge_configs(base, override)

    validate_config(base)
    return _build_config(base)


def merge_configs(base: dict, override: dict) -> dict:
    """Deep-merge override onto base. Returns a new dict without mutating inputs."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def validate_config(raw: dict) -> None:
    """Validate raw config dict. Raises ConfigValidationError on any violation."""
    required_sections = ["simulation", "service", "population", "activity", "retailers"]
    for section in required_sections:
        if section not in raw:
            raise ConfigValidationError(f"Missing required section: '{section}'")

    svc = raw["service"]
    prob_fields = [
        ("service.base_p_fail", svc.get("base_p_fail")),
        ("service.base_p_correct", svc.get("base_p_correct")),
        ("service.base_p_approve", svc.get("base_p_approve")),
    ]
    pop = raw["population"]
    prob_fields.extend(
        [
            ("population.pet_dog_probability", pop.get("pet_dog_probability")),
            ("population.pet_cat_probability", pop.get("pet_cat_probability")),
        ]
    )
    for name, value in prob_fields:
        if value is not None and not (0.0 <= value <= 1.0):
            raise ConfigValidationError(
                f"Probability {name} must be in [0, 1], got {value}"
            )

    for name, key in [
        ("service.sigma_fast", "sigma_fast"),
        ("service.sigma_slow", "sigma_slow"),
    ]:
        val = svc.get(key)
        if val is not None and val <= 0:
            raise ConfigValidationError(f"{name} must be > 0, got {val}")

    sim = raw["simulation"]
    if sim.get("duration") is not None and sim["duration"] <= 0:
        raise ConfigValidationError(
            f"simulation.duration must be > 0, got {sim['duration']}"
        )
    if sim.get("period_length") is not None and sim["period_length"] <= 0:
        raise ConfigValidationError(
            f"simulation.period_length must be > 0, got {sim['period_length']}"
        )

    if pop.get("size") is not None and pop["size"] <= 0:
        raise ConfigValidationError(f"population.size must be > 0, got {pop['size']}")

    activity = raw["activity"]
    multipliers = activity.get("seasonal_multipliers", [])
    if len(multipliers) != 12:
        raise ConfigValidationError(
            f"seasonal_multipliers must have exactly 12 entries, got {len(multipliers)}"
        )

    retailers = raw["retailers"]
    if not retailers:
        raise ConfigValidationError("At least one retailer must be defined")

    required_retailer_keys = ["fail_modifier", "correct_modifier", "mix_weight"]
    for r_name, r_data in retailers.items():
        for rk in required_retailer_keys:
            if rk not in r_data:
                raise ConfigValidationError(
                    f"Retailer '{r_name}' is missing required key '{rk}'"
                )


def _build_config(raw: dict) -> SimConfig:
    """Construct SimConfig from a validated raw dict."""
    sim = raw["simulation"]
    svc = raw["service"]
    pop = raw["population"]
    act = raw["activity"]

    # Ensure household_size_weights keys are ints
    household_weights = {int(k): v for k, v in pop["household_size_weights"].items()}

    retailers = {}
    for r_name, r_data in raw["retailers"].items():
        retailers[r_name] = RetailerConfig(
            fail_modifier=r_data["fail_modifier"],
            correct_modifier=r_data["correct_modifier"],
            mix_weight=r_data["mix_weight"],
        )

    return SimConfig(
        simulation=SimulationConfig(
            seed=sim["seed"],
            duration=float(sim["duration"]),
            time_unit=sim["time_unit"],
            period_length=float(sim["period_length"]),
        ),
        service=ServiceConfig(
            base_p_fail=svc["base_p_fail"],
            base_p_correct=svc["base_p_correct"],
            mu_fast=svc["mu_fast"],
            sigma_fast=svc["sigma_fast"],
            mu_slow=svc["mu_slow"],
            sigma_slow=svc["sigma_slow"],
            base_p_approve=svc["base_p_approve"],
            base_reward=svc["base_reward"],
        ),
        population=PopulationConfig(
            size=pop["size"],
            lambda_alpha=pop["lambda_alpha"],
            lambda_beta=pop["lambda_beta"],
            quality_a=pop["quality_a"],
            quality_b=pop["quality_b"],
            engagement_a=pop["engagement_a"],
            engagement_b=pop["engagement_b"],
            tenure_max_months=pop["tenure_max_months"],
            dirichlet_concentration=pop["dirichlet_concentration"],
            age_groups=pop["age_groups"],
            lifestages=pop["lifestages"],
            social_grades=pop["social_grades"],
            geographies=pop["geographies"],
            household_size_weights=household_weights,
            pet_dog_probability=pop["pet_dog_probability"],
            pet_cat_probability=pop["pet_cat_probability"],
        ),
        activity=ActivityConfig(
            seasonal_multipliers=act["seasonal_multipliers"],
            segmentation_weights=act["segmentation_weights"],
            tenure_decay_rate=act["tenure_decay_rate"],
        ),
        retailers=retailers,
    )
