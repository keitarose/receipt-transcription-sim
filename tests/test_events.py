"""Tests for the event system."""

from receipt_sim.events import (
    EventType,
    create_arrival_event,
    create_outcome_event,
    create_period_tick,
    create_service_event,
)
from receipt_sim.models import ReceiptRequest, ReceiptResponse, SimEvent


def _make_request() -> ReceiptRequest:
    return ReceiptRequest(
        receipt_id="r-001",
        user_id="u-001",
        timestamp=10.0,
        retailer_type="grocery_major",
    )


def _make_response(decision: str = "approved") -> ReceiptResponse:
    tokens = 10 if decision == "approved" else 0
    message = None if decision == "approved" else "Receipt could not be verified"
    return ReceiptResponse(
        receipt_id="r-001",
        user_id="u-001",
        timestamp=12.0,
        response_time=2.0,
        was_corrected=False,
        decision=decision,
        tokens_awarded=tokens,
        message=message,
    )


class TestCreateArrivalEvent:
    def test_create_arrival_event(self):
        """TC-EVT-01: Arrival event has correct type and data."""
        event = create_arrival_event(5.0, "u-001", "r-001", "grocery_major")
        assert event.event_type == EventType.RECEIPT_ARRIVAL
        assert event.time == 5.0
        assert event.data["user_id"] == "u-001"
        assert event.data["receipt_id"] == "r-001"
        assert event.data["retailer_type"] == "grocery_major"


class TestCreateServiceEvent:
    def test_create_service_event_with_response(self):
        """TC-EVT-02: Service event with response is SERVICE_RESPONSE."""
        req = _make_request()
        resp = _make_response()
        event = create_service_event(12.0, req, resp)
        assert event.event_type == EventType.SERVICE_RESPONSE

    def test_create_service_event_failure(self):
        """TC-EVT-03: Service event with None response is RECEIPT_FAILED."""
        req = _make_request()
        event = create_service_event(10.0, req, None)
        assert event.event_type == EventType.RECEIPT_FAILED


class TestCreateOutcomeEvent:
    def test_create_outcome_event_approved(self):
        """TC-EVT-04: Approved outcome event."""
        resp = _make_response("approved")
        event = create_outcome_event(12.0, resp)
        assert event.event_type == EventType.RECEIPT_APPROVED

    def test_create_outcome_event_rejected(self):
        """TC-EVT-05: Rejected outcome event."""
        resp = _make_response("rejected")
        event = create_outcome_event(12.0, resp)
        assert event.event_type == EventType.RECEIPT_REJECTED


class TestEventOrdering:
    def test_event_comparison_by_time(self):
        """TC-EVT-06: Events sort by time."""
        events = [
            SimEvent(time=3.0, event_type="C", data={}),
            SimEvent(time=1.0, event_type="A", data={}),
            SimEvent(time=2.0, event_type="B", data={}),
        ]
        sorted_events = sorted(events)
        assert [e.time for e in sorted_events] == [1.0, 2.0, 3.0]
