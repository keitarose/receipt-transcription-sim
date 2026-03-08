"""Tests for the simulation logger."""

import pandas as pd

from receipt_sim.events import EventType
from receipt_sim.logger import PeriodSummary, SimulationLogger
from receipt_sim.models import SimEvent


def _event(etype: str, time: float = 0.0, **data) -> SimEvent:
    return SimEvent(time=time, event_type=etype, data=data)


class TestPeriodSummary:
    def test_failure_rate_zero_arrivals(self):
        """TC-LOG-01: Division-safe when no arrivals."""
        s = PeriodSummary(period=0)
        assert s.failure_rate == 0.0

    def test_failure_rate(self):
        """TC-LOG-02: Correct failure rate."""
        s = PeriodSummary(period=0, arrivals=100, failures=20)
        assert abs(s.failure_rate - 0.2) < 1e-9

    def test_approval_rate(self):
        """TC-LOG-03: Correct approval rate."""
        s = PeriodSummary(period=0, approvals=80, rejections=20)
        assert abs(s.approval_rate - 0.8) < 1e-9

    def test_correction_rate(self):
        """TC-LOG-04: Correct correction rate."""
        s = PeriodSummary(period=0, responses=100, corrections=30)
        assert abs(s.correction_rate - 0.3) < 1e-9

    def test_mean_response_time(self):
        """TC-LOG-05: Correct mean response time."""
        s = PeriodSummary(period=0, responses=4, total_response_time=20.0)
        assert abs(s.mean_response_time - 5.0) < 1e-9


class TestSimulationLogger:
    def test_log_arrivals(self):
        """TC-LOG-06: Arrival events count correctly."""
        logger = SimulationLogger()
        logger.log_event(_event(EventType.RECEIPT_ARRIVAL, user_id="u1"))
        logger.log_event(_event(EventType.RECEIPT_ARRIVAL, user_id="u2"))
        summaries = logger.get_period_summaries()
        assert len(summaries) == 1
        assert summaries[0].arrivals == 2

    def test_log_failure(self):
        """TC-LOG-07: Failed events increment failures."""
        logger = SimulationLogger()
        logger.log_event(_event(EventType.RECEIPT_ARRIVAL))
        logger.log_event(_event(EventType.RECEIPT_FAILED))
        s = logger.get_period_summaries()[0]
        assert s.arrivals == 1
        assert s.failures == 1

    def test_log_response_with_correction(self):
        """TC-LOG-08: Service response with correction tracked."""
        logger = SimulationLogger()
        logger.log_event(
            _event(
                EventType.SERVICE_RESPONSE,
                response_time=3.0,
                was_corrected=True,
            )
        )
        s = logger.get_period_summaries()[0]
        assert s.responses == 1
        assert s.corrections == 1
        assert abs(s.total_response_time - 3.0) < 1e-9

    def test_log_approval(self):
        """TC-LOG-09: Approved events track tokens."""
        logger = SimulationLogger()
        logger.log_event(_event(EventType.RECEIPT_APPROVED, tokens_awarded=10))
        s = logger.get_period_summaries()[0]
        assert s.approvals == 1
        assert s.total_tokens == 10

    def test_log_rejection(self):
        """TC-LOG-10: Rejected events increment rejections."""
        logger = SimulationLogger()
        logger.log_event(_event(EventType.RECEIPT_REJECTED))
        s = logger.get_period_summaries()[0]
        assert s.rejections == 1

    def test_period_advancement(self):
        """TC-LOG-11: Events go to correct period after set_period."""
        logger = SimulationLogger()
        logger.log_event(_event(EventType.RECEIPT_ARRIVAL))
        logger.set_period(1)
        logger.log_event(_event(EventType.RECEIPT_ARRIVAL))
        summaries = logger.get_period_summaries()
        assert len(summaries) == 2
        assert summaries[0].period == 0
        assert summaries[0].arrivals == 1
        assert summaries[1].period == 1
        assert summaries[1].arrivals == 1

    def test_to_dataframe(self):
        """TC-LOG-12: to_dataframe returns valid DataFrame."""
        logger = SimulationLogger()
        logger.log_event(_event(EventType.RECEIPT_ARRIVAL))
        logger.log_event(_event(EventType.RECEIPT_APPROVED, tokens_awarded=10))
        df = logger.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "period" in df.columns
        assert "failure_rate" in df.columns

    def test_to_dataframe_empty(self):
        """TC-LOG-13: Empty logger returns empty DataFrame."""
        logger = SimulationLogger()
        df = logger.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_events_to_dataframe(self):
        """TC-LOG-14: events_to_dataframe preserves all events."""
        logger = SimulationLogger()
        logger.log_event(_event(EventType.RECEIPT_ARRIVAL, time=1.0, user_id="u1"))
        logger.log_event(_event(EventType.RECEIPT_FAILED, time=2.0))
        df = logger.events_to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df.iloc[0]["time"] == 1.0
