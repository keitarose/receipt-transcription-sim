"""Tests for the simulation engine."""

from dataclasses import replace
from pathlib import Path

import numpy as np

from receipt_sim.config import load_config
from receipt_sim.engine import SimulationEngine
from receipt_sim.events import EventType
from receipt_sim.models import SimConfig

CONFIG_PATH = str(Path(__file__).parent.parent / "config" / "default.yaml")


def _base_config() -> SimConfig:
    return load_config(CONFIG_PATH)


def _small_config(**sim_overrides) -> SimConfig:
    """Config with small population and short duration for fast tests."""
    config = _base_config()
    pop = replace(config.population, size=10)
    sim = replace(config.simulation, duration=48.0, **sim_overrides)
    return replace(config, population=pop, simulation=sim)


class TestEngineInitialization:
    def test_population_created(self):
        """TC-ENG-01: Engine creates population on initialize."""
        config = _small_config()
        engine = SimulationEngine(config)
        engine.initialize()
        assert len(engine.population) == 10

    def test_event_queue_populated(self):
        """TC-ENG-02: Event queue has period ticks and arrivals."""
        config = _small_config()
        engine = SimulationEngine(config)
        engine.initialize()
        assert len(engine.event_queue) > 0
        event_types = {e.event_type for e in engine.event_queue}
        assert EventType.PERIOD_TICK in event_types
        assert EventType.RECEIPT_ARRIVAL in event_types

    def test_retailer_profiles_loaded(self):
        """TC-ENG-03: Retailer profiles are loaded."""
        config = _small_config()
        engine = SimulationEngine(config)
        engine.initialize()
        assert len(engine.retailer_profiles) > 0


class TestEngineExecution:
    def test_run_completes(self):
        """TC-ENG-04: Engine runs to completion without error."""
        config = _small_config()
        engine = SimulationEngine(config)
        logger = engine.run()
        assert len(logger.events) > 0

    def test_events_ordered(self):
        """TC-ENG-05: Logged events are in non-decreasing time order."""
        config = _small_config()
        engine = SimulationEngine(config)
        logger = engine.run()
        times = [e.time for e in logger.events]
        for i in range(1, len(times)):
            assert times[i] >= times[i - 1]

    def test_clock_advances(self):
        """TC-ENG-06: Clock advances past zero."""
        config = _small_config()
        engine = SimulationEngine(config)
        engine.run()
        assert engine.clock > 0

    def test_no_events_past_duration(self):
        """TC-ENG-07: No events beyond simulation duration."""
        config = _small_config()
        engine = SimulationEngine(config)
        logger = engine.run()
        for event in logger.events:
            assert event.time <= config.simulation.duration

    def test_deterministic_with_same_seed(self):
        """TC-ENG-08: Same seed produces identical results."""
        config = _small_config(seed=123)
        engine1 = SimulationEngine(config)
        logger1 = engine1.run()

        engine2 = SimulationEngine(config)
        logger2 = engine2.run()

        assert len(logger1.events) == len(logger2.events)
        for e1, e2 in zip(logger1.events, logger2.events):
            assert e1.time == e2.time
            assert e1.event_type == e2.event_type

    def test_different_seeds_differ(self):
        """TC-ENG-09: Different seeds produce different results."""
        config1 = _small_config(seed=1)
        config2 = _small_config(seed=999)

        logger1 = SimulationEngine(config1).run()
        logger2 = SimulationEngine(config2).run()

        # Extremely unlikely to have exact same event count AND times
        times1 = [e.time for e in logger1.events]
        times2 = [e.time for e in logger2.events]
        assert times1 != times2


class TestEngineMetrics:
    def test_arrivals_logged(self):
        """TC-ENG-10: At least one arrival is logged."""
        config = _small_config()
        engine = SimulationEngine(config)
        logger = engine.run()
        arrivals = [
            e for e in logger.events if e.event_type == EventType.RECEIPT_ARRIVAL
        ]
        assert len(arrivals) > 0

    def test_period_summaries_exist(self):
        """TC-ENG-11: Period summaries are generated."""
        config = _small_config()
        engine = SimulationEngine(config)
        logger = engine.run()
        summaries = logger.get_period_summaries()
        assert len(summaries) > 0

    def test_tokens_awarded(self):
        """TC-ENG-12: Some tokens are awarded over the run."""
        config = _small_config()
        # Ensure high approval rate
        svc = replace(config.service, base_p_fail=0.0, base_p_approve=1.0)
        config = replace(config, service=svc)
        engine = SimulationEngine(config)
        logger = engine.run()
        summaries = logger.get_period_summaries()
        total = sum(s.total_tokens for s in summaries)
        assert total > 0

    def test_dataframe_output(self):
        """TC-ENG-13: to_dataframe produces valid data."""
        config = _small_config()
        engine = SimulationEngine(config)
        logger = engine.run()
        df = logger.to_dataframe()
        assert len(df) > 0
        assert "arrivals" in df.columns
        assert "failure_rate" in df.columns
