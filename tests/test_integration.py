"""Integration tests — end-to-end simulation validation."""

from dataclasses import replace
from pathlib import Path

import numpy as np

from receipt_sim.config import load_config
from receipt_sim.engine import SimulationEngine
from receipt_sim.events import EventType
from receipt_sim.models import SimConfig

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "default.yaml")
HIGH_FAILURE_PATH = str(
    Path(__file__).parent.parent / "config" / "scenarios" / "high_failure.yaml"
)


def _small_config(**sim_overrides) -> SimConfig:
    config = load_config(CONFIG_PATH)
    pop = replace(config.population, size=20)
    sim = replace(config.simulation, duration=72.0, **sim_overrides)
    return replace(config, population=pop, simulation=sim)


class TestEndToEnd:
    def test_full_run_no_crash(self):
        """TC-INT-01: Full simulation runs without errors."""
        config = _small_config()
        engine = SimulationEngine(config)
        logger = engine.run()
        assert len(logger.events) > 0

    def test_event_type_coverage(self):
        """TC-INT-02: All expected event types appear in output."""
        config = _small_config()
        engine = SimulationEngine(config)
        logger = engine.run()
        types = {e.event_type for e in logger.events}
        # At minimum we should have arrivals, period ticks, and some outcomes
        assert EventType.PERIOD_TICK in types
        assert EventType.RECEIPT_ARRIVAL in types

    def test_arrival_leads_to_outcome(self):
        """TC-INT-03: Arrivals produce downstream events."""
        config = _small_config()
        svc = replace(config.service, base_p_fail=0.0, base_p_approve=1.0)
        config = replace(config, service=svc)
        engine = SimulationEngine(config)
        logger = engine.run()

        arrivals = [
            e for e in logger.events if e.event_type == EventType.RECEIPT_ARRIVAL
        ]
        approved = [
            e for e in logger.events if e.event_type == EventType.RECEIPT_APPROVED
        ]
        assert len(arrivals) > 0
        assert len(approved) > 0

    def test_token_balance_accumulates(self):
        """TC-INT-04: Members accumulate tokens."""
        config = _small_config()
        svc = replace(config.service, base_p_fail=0.0, base_p_approve=1.0)
        config = replace(config, service=svc)
        engine = SimulationEngine(config)
        engine.run()

        total_tokens = sum(m.token_balance for m in engine.population)
        assert total_tokens > 0

    def test_determinism(self):
        """TC-INT-05: Same config + seed produces identical run."""
        config = _small_config(seed=7)
        logger1 = SimulationEngine(config).run()
        logger2 = SimulationEngine(config).run()

        assert len(logger1.events) == len(logger2.events)
        for e1, e2 in zip(logger1.events, logger2.events):
            assert e1.time == e2.time
            assert e1.event_type == e2.event_type

    def test_high_failure_scenario(self):
        """TC-INT-06: High failure scenario produces more failures."""
        base_config = _small_config(seed=42)
        high_config = load_config(CONFIG_PATH, HIGH_FAILURE_PATH)
        high_config = replace(
            high_config,
            population=replace(high_config.population, size=20),
            simulation=replace(high_config.simulation, duration=72.0, seed=42),
        )

        logger_base = SimulationEngine(base_config).run()
        logger_high = SimulationEngine(high_config).run()

        base_summaries = logger_base.get_period_summaries()
        high_summaries = logger_high.get_period_summaries()

        base_failures = sum(s.failures for s in base_summaries)
        high_failures = sum(s.failures for s in high_summaries)

        base_arrivals = sum(s.arrivals for s in base_summaries)
        high_arrivals = sum(s.arrivals for s in high_summaries)

        base_rate = base_failures / base_arrivals if base_arrivals else 0
        high_rate = high_failures / high_arrivals if high_arrivals else 0

        assert high_rate > base_rate

    def test_dataframe_consistency(self):
        """TC-INT-07: DataFrame totals match logger summaries."""
        config = _small_config()
        engine = SimulationEngine(config)
        logger = engine.run()

        df = logger.to_dataframe()
        summaries = logger.get_period_summaries()

        assert len(df) == len(summaries)
        assert df["arrivals"].sum() == sum(s.arrivals for s in summaries)
        assert df["failures"].sum() == sum(s.failures for s in summaries)

    def test_time_monotonicity(self):
        """TC-INT-08: All events have monotonically non-decreasing times."""
        config = _small_config()
        engine = SimulationEngine(config)
        logger = engine.run()
        times = [e.time for e in logger.events]
        for i in range(1, len(times)):
            assert times[i] >= times[i - 1]

    def test_no_negative_tokens(self):
        """TC-INT-09: No member has negative token balance."""
        config = _small_config()
        engine = SimulationEngine(config)
        engine.run()
        for m in engine.population:
            assert m.token_balance >= 0

    def test_seasonal_variation_visible(self):
        """TC-INT-10: Seasonal multipliers produce rate variation across periods."""
        config = load_config(CONFIG_PATH)
        # Use full duration to cover multiple months, but small pop
        config = replace(
            config,
            population=replace(config.population, size=50),
            simulation=replace(config.simulation, seed=42),
        )
        engine = SimulationEngine(config)
        logger = engine.run()
        summaries = logger.get_period_summaries()
        arrival_counts = [s.arrivals for s in summaries if s.arrivals > 0]
        # With seasonal variation, we expect some variance in daily arrivals
        if len(arrival_counts) > 5:
            std = np.std(arrival_counts)
            assert std > 0  # not all identical
