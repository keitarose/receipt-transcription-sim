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
    """Load a YAML config file, optionally merging a scenario overlay."""
    with open(path, "r") as f:
        base = yaml.safe_load(f)

    if scenario is not None:
        scenario_path = Path(path).parent / "scenarios" / f"{scenario}.yaml"
        with open(scenario_path, "r") as f:
            overrides = yaml.safe_load(f)
        if overrides:
            base = merge_configs(base, overrides)

    validate_config(base)
    return _build_sim_config(base)


def load_config_from_dict(raw: dict) -> SimConfig:
    """Build a SimConfig from an already-validated raw dict."""
    validate_config(raw)
    return _build_sim_config(raw)


def merge_configs(base: dict, override: dict) -> dict:
    """Deep-merge override onto base, returning a new dict."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def validate_config(raw: dict) -> None:
    """Validate a raw config dict. Raises ConfigValidationError on failure."""
    required_sections = ["simulation", "service", "population", "activity", "retailers"]
    for section in required_sections:
        if section not in raw:
            raise ConfigValidationError(f"Missing required section: '{section}'")

    svc = raw["service"]
    prob_fields = [
        ("service", "base_p_fail"),
        ("service", "base_p_correct"),
        ("service", "base_p_approve"),
    ]
    for section_name, field in prob_fields:
        val = raw[section_name].get(field)
        if val is not None and not (0.0 <= val <= 1.0):
            raise ConfigValidationError(
                f"{section_name}.{field} must be in [0, 1], got {val}"
            )

    pop = raw["population"]
    for field in ("pet_dog_probability", "pet_cat_probability"):
        val = pop.get(field)
        if val is not None and not (0.0 <= val <= 1.0):
            raise ConfigValidationError(
                f"population.{field} must be in [0, 1], got {val}"
            )

    for field in ("sigma_fast", "sigma_slow"):
        val = svc.get(field)
        if val is not None and val <= 0:
            raise ConfigValidationError(f"service.{field} must be > 0, got {val}")

    sim = raw["simulation"]
    if sim.get("duration") is not None and sim["duration"] <= 0:
        raise ConfigValidationError("simulation.duration must be > 0")
    if sim.get("period_length") is not None and sim["period_length"] <= 0:
        raise ConfigValidationError("simulation.period_length must be > 0")

    if pop.get("size") is not None and pop["size"] <= 0:
        raise ConfigValidationError("population.size must be > 0")

    activity = raw["activity"]
    multipliers = activity.get("seasonal_multipliers", [])
    if len(multipliers) != 12:
        raise ConfigValidationError(
            f"activity.seasonal_multipliers must have 12 entries, got {len(multipliers)}"
        )

    retailers = raw["retailers"]
    if not retailers:
        raise ConfigValidationError("At least one retailer must be defined")
    for rname, rdata in retailers.items():
        for required_key in ("fail_modifier", "correct_modifier", "mix_weight"):
            if required_key not in rdata:
                raise ConfigValidationError(
                    f"Retailer '{rname}' missing required key: '{required_key}'"
                )


def _build_sim_config(raw: dict) -> SimConfig:
    """Construct a SimConfig from a validated raw dict."""
    sim = raw["simulation"]
    svc = raw["service"]
    pop = raw["population"]
    act = raw["activity"]
    ret = raw["retailers"]

    # Convert household_size_weights keys to int
    hsw = pop.get("household_size_weights", {})
    household_size_weights = {int(k): v for k, v in hsw.items()}

    return SimConfig(
        simulation=SimulationConfig(
            seed=sim["seed"],
            duration=float(sim["duration"]),
            time_unit=sim["time_unit"],
            period_length=float(sim["period_length"]),
        ),
        service=ServiceConfig(
            base_p_fail=float(svc["base_p_fail"]),
            base_p_correct=float(svc["base_p_correct"]),
            mu_fast=float(svc["mu_fast"]),
            sigma_fast=float(svc["sigma_fast"]),
            mu_slow=float(svc["mu_slow"]),
            sigma_slow=float(svc["sigma_slow"]),
            base_p_approve=float(svc["base_p_approve"]),
            base_reward=int(svc["base_reward"]),
        ),
        population=PopulationConfig(
            size=int(pop["size"]),
            lambda_alpha=float(pop["lambda_alpha"]),
            lambda_beta=float(pop["lambda_beta"]),
            quality_a=float(pop["quality_a"]),
            quality_b=float(pop["quality_b"]),
            engagement_a=float(pop["engagement_a"]),
            engagement_b=float(pop["engagement_b"]),
            tenure_max_months=float(pop["tenure_max_months"]),
            dirichlet_concentration=float(pop["dirichlet_concentration"]),
            age_groups=dict(pop["age_groups"]),
            lifestages=dict(pop["lifestages"]),
            social_grades=dict(pop["social_grades"]),
            geographies=dict(pop["geographies"]),
            household_size_weights=household_size_weights,
            pet_dog_probability=float(pop["pet_dog_probability"]),
            pet_cat_probability=float(pop["pet_cat_probability"]),
        ),
        activity=ActivityConfig(
            seasonal_multipliers=list(act["seasonal_multipliers"]),
            segmentation_weights=dict(act["segmentation_weights"]),
            tenure_decay_rate=float(act["tenure_decay_rate"]),
        ),
        retailers={
            name: RetailerConfig(
                fail_modifier=float(data["fail_modifier"]),
                correct_modifier=float(data["correct_modifier"]),
                mix_weight=float(data["mix_weight"]),
            )
            for name, data in ret.items()
        },
    )
