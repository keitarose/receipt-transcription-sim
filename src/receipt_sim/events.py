"""Event type definitions and factory functions."""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum

from receipt_sim.models import ReceiptRequest, ReceiptResponse, SimEvent


class EventType(str, Enum):
    RECEIPT_ARRIVAL = "RECEIPT_ARRIVAL"
    SERVICE_RESPONSE = "SERVICE_RESPONSE"
    RECEIPT_FAILED = "RECEIPT_FAILED"
    RECEIPT_APPROVED = "RECEIPT_APPROVED"
    RECEIPT_REJECTED = "RECEIPT_REJECTED"
    PERIOD_TICK = "PERIOD_TICK"


def create_arrival_event(
    time: float, user_id: str, receipt_id: str, retailer_type: str
) -> SimEvent:
    """Create a RECEIPT_ARRIVAL event."""
    return SimEvent(
        time=time,
        event_type=EventType.RECEIPT_ARRIVAL,
        data={
            "user_id": user_id,
            "receipt_id": receipt_id,
            "retailer_type": retailer_type,
        },
    )


def create_service_event(
    time: float, request: ReceiptRequest, response: ReceiptResponse | None
) -> SimEvent:
    """Create a service event: RECEIPT_FAILED if response is None, else SERVICE_RESPONSE."""
    if response is None:
        return SimEvent(
            time=time,
            event_type=EventType.RECEIPT_FAILED,
            data=asdict(request),
        )
    else:
        data = {**asdict(request), **asdict(response)}
        return SimEvent(
            time=time,
            event_type=EventType.SERVICE_RESPONSE,
            data=data,
        )


def create_outcome_event(time: float, response: ReceiptResponse) -> SimEvent:
    """Create an APPROVED or REJECTED outcome event."""
    if response.decision == "approved":
        event_type = EventType.RECEIPT_APPROVED
    else:
        event_type = EventType.RECEIPT_REJECTED
    return SimEvent(
        time=time,
        event_type=event_type,
        data=asdict(response),
    )


def create_period_tick(time: float, period: int) -> SimEvent:
    """Create a PERIOD_TICK event."""
    return SimEvent(
        time=time,
        event_type=EventType.PERIOD_TICK,
        data={"period": period},
    )
