"""Discrete-event simulation engine."""

from __future__ import annotations

import heapq
import uuid

import numpy as np

from receipt_sim.events import (
    EventType,
    create_arrival_event,
    create_outcome_event,
    create_period_tick,
    create_service_event,
)
from receipt_sim.incentives import (
    apply_reward,
    apply_tenure_decay,
    effective_submission_rate,
)
from receipt_sim.logger import SimulationLogger
from receipt_sim.models import PopulationMember, ReceiptRequest, SimConfig, SimEvent
from receipt_sim.population import generate_population
from receipt_sim.retailers import (
    RetailerProfile,
    RetailerType,
    load_retailer_profiles,
    sample_retailer,
)
from receipt_sim.service import process_receipt


class SimulationEngine:
    """Heap-based discrete-event simulation engine."""

    def __init__(self, config: SimConfig) -> None:
        self.config = config
        self.rng = np.random.default_rng(config.simulation.seed)
        self.clock: float = 0.0
        self.event_queue: list[SimEvent] = []
        self.population: list[PopulationMember] = []
        self.user_index: dict[str, PopulationMember] = {}
        self.retailer_profiles: dict[RetailerType, RetailerProfile] = {}
        self.logger = SimulationLogger()
        self._current_period: int = 0

    def initialize(self) -> None:
        """Set up population, retailer profiles, and schedule initial events."""
        self.population = generate_population(self.config, self.rng)
        self.user_index = {m.user_id: m for m in self.population}
        self.retailer_profiles = load_retailer_profiles(self.config)

        # Schedule period ticks
        period_len = self.config.simulation.period_length
        t = 0.0
        period = 0
        while t < self.config.simulation.duration:
            self._push_event(create_period_tick(t, period))
            t += period_len
            period += 1

        # Schedule first arrival for each member
        for member in self.population:
            self._schedule_next_arrival(member, 0.0)

    def run(self) -> SimulationLogger:
        """Execute the simulation until the event queue is empty or duration exceeded."""
        self.initialize()

        while self.event_queue:
            event = heapq.heappop(self.event_queue)
            if event.time > self.config.simulation.duration:
                break
            self.clock = event.time
            self._dispatch(event)

        return self.logger

    def _push_event(self, event: SimEvent) -> None:
        heapq.heappush(self.event_queue, event)

    def _dispatch(self, event: SimEvent) -> None:
        etype = event.event_type

        if etype == EventType.PERIOD_TICK:
            self._handle_period_tick(event)
        elif etype == EventType.RECEIPT_ARRIVAL:
            self._handle_arrival(event)
        elif etype == EventType.SERVICE_RESPONSE:
            self._handle_service_response(event)
        elif etype == EventType.RECEIPT_FAILED:
            self._handle_receipt_failed(event)
        elif etype == EventType.RECEIPT_APPROVED:
            self._handle_approved(event)
        elif etype == EventType.RECEIPT_REJECTED:
            self._handle_rejected(event)

        self.logger.log_event(event)

    def _handle_period_tick(self, event: SimEvent) -> None:
        self._current_period = event.data["period"]
        self.logger.set_period(self._current_period)

    def _handle_arrival(self, event: SimEvent) -> None:
        user_id = event.data["user_id"]
        member = self.user_index[user_id]

        request = ReceiptRequest(
            receipt_id=event.data["receipt_id"],
            user_id=user_id,
            timestamp=event.time,
            retailer_type=event.data["retailer_type"],
        )

        response = process_receipt(
            request, member.quality_score, self.retailer_profiles, self.config, self.rng
        )

        service_event = create_service_event(event.time, request, response)
        if response is not None:
            self._push_event(
                SimEvent(
                    time=event.time + response.response_time,
                    event_type=service_event.event_type,
                    data=service_event.data,
                )
            )
        else:
            self._push_event(service_event)

        # Schedule next arrival for this member
        self._schedule_next_arrival(member, event.time)

    def _handle_service_response(self, event: SimEvent) -> None:
        from receipt_sim.models import ReceiptResponse as RR

        response = RR(
            receipt_id=event.data["receipt_id"],
            user_id=event.data["user_id"],
            timestamp=event.data["timestamp"],
            response_time=event.data["response_time"],
            was_corrected=event.data["was_corrected"],
            decision=event.data["decision"],
            tokens_awarded=event.data["tokens_awarded"],
            message=event.data.get("message"),
        )
        outcome = create_outcome_event(event.time, response)
        self._push_event(outcome)

    def _handle_receipt_failed(self, event: SimEvent) -> None:
        pass  # failure already logged

    def _handle_approved(self, event: SimEvent) -> None:
        user_id = event.data["user_id"]
        member = self.user_index[user_id]
        from receipt_sim.models import ReceiptResponse as RR

        response = RR(
            receipt_id=event.data["receipt_id"],
            user_id=user_id,
            timestamp=event.data["timestamp"],
            response_time=event.data["response_time"],
            was_corrected=event.data["was_corrected"],
            decision=event.data["decision"],
            tokens_awarded=event.data["tokens_awarded"],
            message=event.data.get("message"),
        )
        apply_reward(member, response)

    def _handle_rejected(self, event: SimEvent) -> None:
        pass  # rejection already logged

    def _schedule_next_arrival(self, member: PopulationMember, after: float) -> None:
        """Schedule the next receipt arrival for a member."""
        seasonal_mult = self._get_seasonal_multiplier(after)
        rate = effective_submission_rate(member, self.config, seasonal_mult)
        rate = apply_tenure_decay(rate, member, self.config)

        if rate <= 0:
            return

        inter_arrival = self.rng.exponential(1.0 / rate)
        arrival_time = after + inter_arrival

        if arrival_time > self.config.simulation.duration:
            return

        retailer_type = sample_retailer(member.retailer_mix, self.rng)

        # Generate receipt_id using two 64-bit draws (avoid 2**128 overflow)
        hi = int(self.rng.integers(0, 2**64, dtype=np.uint64))
        lo = int(self.rng.integers(0, 2**64, dtype=np.uint64))
        receipt_id = str(uuid.UUID(int=(hi << 64) | lo))

        self._push_event(
            create_arrival_event(
                arrival_time, member.user_id, receipt_id, retailer_type
            )
        )

    def _get_seasonal_multiplier(self, time: float) -> float:
        """Look up the seasonal multiplier for the current simulation time."""
        hours_per_month = self.config.simulation.duration / 12.0
        if hours_per_month <= 0:
            return 0.0
        month_index = int(time / hours_per_month) % 12
        return self.config.activity.seasonal_multipliers[month_index]
