"""Simulation logger — collects events and produces per-period summaries."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from receipt_sim.events import EventType
from receipt_sim.models import SimEvent


@dataclass
class PeriodSummary:
    """Aggregated metrics for one simulation period (e.g., one day)."""

    period: int
    arrivals: int = 0
    failures: int = 0
    responses: int = 0
    approvals: int = 0
    rejections: int = 0
    corrections: int = 0
    total_tokens: int = 0
    total_response_time: float = 0.0

    @property
    def failure_rate(self) -> float:
        total = self.arrivals
        return self.failures / total if total > 0 else 0.0

    @property
    def approval_rate(self) -> float:
        decided = self.approvals + self.rejections
        return self.approvals / decided if decided > 0 else 0.0

    @property
    def correction_rate(self) -> float:
        return self.corrections / self.responses if self.responses > 0 else 0.0

    @property
    def mean_response_time(self) -> float:
        return self.total_response_time / self.responses if self.responses > 0 else 0.0


class SimulationLogger:
    """Collects events and produces summary DataFrames."""

    def __init__(self) -> None:
        self.events: list[SimEvent] = []
        self._summaries: dict[int, PeriodSummary] = {}
        self._current_period: int = 0

    def log_event(self, event: SimEvent) -> None:
        """Record a simulation event."""
        self.events.append(event)
        self._update_summary(event)

    def set_period(self, period: int) -> None:
        """Advance the current period counter."""
        self._current_period = period

    def _get_summary(self, period: int) -> PeriodSummary:
        if period not in self._summaries:
            self._summaries[period] = PeriodSummary(period=period)
        return self._summaries[period]

    def _update_summary(self, event: SimEvent) -> None:
        summary = self._get_summary(self._current_period)
        etype = event.event_type

        if etype == EventType.RECEIPT_ARRIVAL:
            summary.arrivals += 1
        elif etype == EventType.RECEIPT_FAILED:
            summary.failures += 1
        elif etype == EventType.SERVICE_RESPONSE:
            summary.responses += 1
            summary.total_response_time += event.data.get("response_time", 0.0)
            if event.data.get("was_corrected", False):
                summary.corrections += 1
        elif etype == EventType.RECEIPT_APPROVED:
            summary.approvals += 1
            summary.total_tokens += event.data.get("tokens_awarded", 0)
        elif etype == EventType.RECEIPT_REJECTED:
            summary.rejections += 1

    def get_period_summaries(self) -> list[PeriodSummary]:
        """Return summaries sorted by period."""
        return [self._summaries[k] for k in sorted(self._summaries)]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert period summaries to a pandas DataFrame."""
        summaries = self.get_period_summaries()
        if not summaries:
            return pd.DataFrame()

        records = []
        for s in summaries:
            records.append(
                {
                    "period": s.period,
                    "arrivals": s.arrivals,
                    "failures": s.failures,
                    "responses": s.responses,
                    "approvals": s.approvals,
                    "rejections": s.rejections,
                    "corrections": s.corrections,
                    "total_tokens": s.total_tokens,
                    "failure_rate": s.failure_rate,
                    "approval_rate": s.approval_rate,
                    "correction_rate": s.correction_rate,
                    "mean_response_time": s.mean_response_time,
                }
            )
        return pd.DataFrame(records)

    def events_to_dataframe(self) -> pd.DataFrame:
        """Convert raw events to a pandas DataFrame."""
        if not self.events:
            return pd.DataFrame()
        return pd.DataFrame(
            [
                {"time": e.time, "event_type": e.event_type, **e.data}
                for e in self.events
            ]
        )
