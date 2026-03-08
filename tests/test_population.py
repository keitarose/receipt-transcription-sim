"""Tests for population generation."""

from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy import stats  # type: ignore[import-untyped]

from receipt_sim.config import load_config
from receipt_sim.population import generate_population

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "default.yaml")


def _config_with_size(size: int):
    config = load_config(CONFIG_PATH)
    new_pop = replace(config.population, size=size)
    return replace(config, population=new_pop)


class TestPopulationGeneration:
    def test_correct_population_size(self):
        """TC-POP-01: Generated population has correct size."""
        config = _config_with_size(100)
        rng = np.random.default_rng(42)
        pop = generate_population(config, rng)
        assert len(pop) == 100

    def test_unique_user_ids(self):
        """TC-POP-02: All user_ids are unique."""
        config = _config_with_size(200)
        rng = np.random.default_rng(42)
        pop = generate_population(config, rng)
        ids = [m.user_id for m in pop]
        assert len(set(ids)) == 200

    def test_lambda_distribution(self):
        """TC-POP-03: Lambda values follow Gamma distribution."""
        config = _config_with_size(10_000)
        rng = np.random.default_rng(42)
        pop = generate_population(config, rng)
        lambdas = [m.lambda_i for m in pop]

        alpha = config.population.lambda_alpha
        beta = config.population.lambda_beta
        expected_mean = alpha * beta
        expected_var = alpha * beta**2

        observed_mean = np.mean(lambdas)
        observed_var = np.var(lambdas, ddof=1)

        se_mean = np.sqrt(expected_var / len(lambdas))
        assert abs(observed_mean - expected_mean) < 2 * se_mean

        # Variance of sample variance for Gamma: roughly 2*var^2/(n-1)
        se_var = expected_var * np.sqrt(2.0 / (len(lambdas) - 1))
        assert abs(observed_var - expected_var) < 2 * se_var

    def test_quality_score_bounds(self):
        """TC-POP-04: All quality scores in [0, 1]."""
        config = _config_with_size(1000)
        rng = np.random.default_rng(42)
        pop = generate_population(config, rng)
        for m in pop:
            assert 0.0 <= m.quality_score <= 1.0

    def test_retailer_mix_sums_to_one(self):
        """TC-POP-05: Retailer mix probabilities sum to 1."""
        config = _config_with_size(100)
        rng = np.random.default_rng(42)
        pop = generate_population(config, rng)
        for m in pop:
            assert abs(sum(m.retailer_mix.values()) - 1.0) < 1e-9

    def test_segmentation_categories_valid(self):
        """TC-POP-06: All segmentation values are from configured sets."""
        config = _config_with_size(100)
        rng = np.random.default_rng(42)
        pop = generate_population(config, rng)

        valid_age = set(config.population.age_groups.keys())
        valid_ls = set(config.population.lifestages.keys())
        valid_sg = set(config.population.social_grades.keys())
        valid_geo = set(config.population.geographies.keys())

        for m in pop:
            assert m.age_group in valid_age
            assert m.lifestage in valid_ls
            assert m.social_grade in valid_sg
            assert m.geography in valid_geo

    def test_reproducibility(self):
        """TC-POP-07: Same seed produces identical populations."""
        config = _config_with_size(50)

        rng1 = np.random.default_rng(42)
        pop1 = generate_population(config, rng1)

        rng2 = np.random.default_rng(42)
        pop2 = generate_population(config, rng2)

        for m1, m2 in zip(pop1, pop2):
            assert m1.user_id == m2.user_id
            assert m1.age_group == m2.age_group
            assert m1.lambda_i == m2.lambda_i
            assert m1.quality_score == m2.quality_score
            assert m1.retailer_mix == m2.retailer_mix
            assert m1.baseline_engagement == m2.baseline_engagement
            assert m1.segmentation_modifier == m2.segmentation_modifier

    def test_engagement_influenced_by_segmentation(self):
        """TC-POP-08: Larger households have higher segmentation modifier."""
        config = _config_with_size(5000)
        rng = np.random.default_rng(42)
        pop = generate_population(config, rng)

        small = [m.segmentation_modifier for m in pop if m.household_size == 1]
        large = [m.segmentation_modifier for m in pop if m.household_size >= 4]

        assert len(small) > 10 and len(large) > 10
        result = stats.ttest_ind(large, small, alternative="greater")
        assert result.pvalue < 0.05  # type: ignore[union-attr]

    def test_household_size_valid(self):
        """TC-POP-09: All household sizes >= 1."""
        config = _config_with_size(1000)
        rng = np.random.default_rng(42)
        pop = generate_population(config, rng)
        for m in pop:
            assert m.household_size >= 1

    def test_panel_tenure_non_negative(self):
        """TC-POP-10: All panel tenures >= 0."""
        config = _config_with_size(1000)
        rng = np.random.default_rng(42)
        pop = generate_population(config, rng)
        for m in pop:
            assert m.panel_tenure_months >= 0
