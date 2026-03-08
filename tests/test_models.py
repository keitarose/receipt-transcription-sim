"""Tests for data models."""

from receipt_sim.models import (
    PopulationMember,
    ReceiptRequest,
    ReceiptResponse,
    SimEvent,
)


class TestPopulationMember:
    def test_population_member_creation(self):
        """TC-MOD-01: Create a PopulationMember with all fields."""
        member = PopulationMember(
            user_id="abc-123",
            age_group="25-34",
            lifestage="Young Family",
            social_grade="C1",
            geography="London",
            household_size=3,
            has_dogs=True,
            has_cats=False,
            panel_tenure_months=12.5,
            lambda_i=2.5,
            quality_score=0.8,
            retailer_mix={"grocery_major": 0.6, "convenience": 0.4},
            baseline_engagement=0.7,
            segmentation_modifier=0.3,
        )
        assert member.user_id == "abc-123"
        assert member.age_group == "25-34"
        assert member.lifestage == "Young Family"
        assert member.social_grade == "C1"
        assert member.geography == "London"
        assert member.household_size == 3
        assert member.has_dogs is True
        assert member.has_cats is False
        assert member.panel_tenure_months == 12.5
        assert member.lambda_i == 2.5
        assert member.quality_score == 0.8
        assert member.retailer_mix == {"grocery_major": 0.6, "convenience": 0.4}
        assert member.baseline_engagement == 0.7
        assert member.segmentation_modifier == 0.3
        assert member.token_balance == 0


class TestReceiptRequest:
    def test_receipt_request_excludes_quality(self):
        """TC-MOD-02: ReceiptRequest has no quality_score attribute."""
        req = ReceiptRequest(
            receipt_id="r-001",
            user_id="u-001",
            timestamp=5.0,
            retailer_type="grocery_major",
        )
        assert not hasattr(req, "quality_score")
        assert not hasattr(req, "receipt_quality_score")


class TestReceiptResponse:
    def test_receipt_response_approved(self):
        """TC-MOD-03: Approved response fields."""
        resp = ReceiptResponse(
            receipt_id="r-001",
            user_id="u-001",
            timestamp=15.0,
            response_time=5.0,
            was_corrected=False,
            decision="approved",
            tokens_awarded=10,
            message=None,
        )
        assert resp.receipt_id == "r-001"
        assert resp.user_id == "u-001"
        assert resp.timestamp == 15.0
        assert resp.response_time == 5.0
        assert resp.was_corrected is False
        assert resp.decision == "approved"
        assert resp.tokens_awarded == 10
        assert resp.message is None

    def test_receipt_response_rejected(self):
        """TC-MOD-04: Rejected response fields."""
        resp = ReceiptResponse(
            receipt_id="r-002",
            user_id="u-002",
            timestamp=20.0,
            response_time=8.0,
            was_corrected=True,
            decision="rejected",
            tokens_awarded=0,
            message="Illegible receipt",
        )
        assert resp.decision == "rejected"
        assert resp.tokens_awarded == 0
        assert resp.message is not None
        assert resp.message == "Illegible receipt"


class TestSimEvent:
    def test_sim_event_ordering(self):
        """TC-MOD-05: Events are ordered by time."""
        e1 = SimEvent(time=1.0, event_type="A", data={})
        e2 = SimEvent(time=2.0, event_type="B", data={})
        assert e1 < e2
        assert not e2 < e1

        events = [
            SimEvent(time=5.0, event_type="E", data={}),
            SimEvent(time=1.0, event_type="A", data={}),
            SimEvent(time=3.0, event_type="C", data={}),
            SimEvent(time=4.0, event_type="D", data={}),
            SimEvent(time=2.0, event_type="B", data={}),
        ]
        sorted_events = sorted(events)
        times = [e.time for e in sorted_events]
        for i in range(len(times) - 1):
            assert times[i] <= times[i + 1]
