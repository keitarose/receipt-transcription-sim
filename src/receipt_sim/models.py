"""Data models for the receipt transcription simulation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SimulationConfig:
    seed: int
    duration: float
    time_unit: str
    period_length: float


@dataclass(frozen=True)
class ServiceConfig:
    base_p_fail: float
    base_p_correct: float
    mu_fast: float
    sigma_fast: float
    mu_slow: float
    sigma_slow: float
    base_p_approve: float
    base_reward: int


@dataclass(frozen=True)
class PopulationConfig:
    size: int
    lambda_alpha: float
    lambda_beta: float
    quality_a: float
    quality_b: float
    engagement_a: float
    engagement_b: float
    tenure_max_months: float
    dirichlet_concentration: float
    age_groups: dict[str, float]
    lifestages: dict[str, float]
    social_grades: dict[str, float]
    geographies: dict[str, float]
    household_size_weights: dict[int, float]
    pet_dog_probability: float
    pet_cat_probability: float


@dataclass(frozen=True)
class ActivityConfig:
    seasonal_multipliers: list[float]  # length 12
    segmentation_weights: dict[str, float]
    tenure_decay_rate: float


@dataclass(frozen=True)
class RetailerConfig:
    fail_modifier: float
    correct_modifier: float
    mix_weight: float


@dataclass(frozen=True)
class SimConfig:
    simulation: SimulationConfig
    service: ServiceConfig
    population: PopulationConfig
    activity: ActivityConfig
    retailers: dict[str, RetailerConfig]


@dataclass
class PopulationMember:
    user_id: str
    age_group: str
    lifestage: str
    social_grade: str
    geography: str
    household_size: int
    has_dogs: bool
    has_cats: bool
    panel_tenure_months: float
    lambda_i: float
    quality_score: float
    retailer_mix: dict[str, float]
    baseline_engagement: float
    segmentation_modifier: float
    token_balance: int = 0


@dataclass(frozen=True)
class ReceiptRequest:
    receipt_id: str
    user_id: str
    timestamp: float
    retailer_type: str


@dataclass(frozen=True)
class ReceiptResponse:
    receipt_id: str
    user_id: str
    timestamp: float
    response_time: float
    was_corrected: bool
    decision: str
    tokens_awarded: int
    message: str | None


@dataclass
class SimEvent:
    time: float
    event_type: str
    data: dict = field(default_factory=dict)

    def __lt__(self, other: "SimEvent") -> bool:
        return self.time < other.time

    def __le__(self, other: "SimEvent") -> bool:
        return self.time <= other.time


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass
