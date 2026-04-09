"""Unit tests for apps/escalation_engine.py.

Verifies EscalationEngine business logic — escalation plans, trigger
workflows, and status tracking — using a dry-run NotificationService
so no external HTTP calls are made.
"""

import uuid
from typing import Any

from apps.escalation_engine import (
    ESCALATION_MATRIX,
    SEVERITY_MAP,
    EscalationEngine,
)
from apps.notification_service import NotificationService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_engine() -> EscalationEngine:
    """Return an EscalationEngine with dry-run notifications."""
    return EscalationEngine(notification_service=NotificationService(dry_run=True))


def _make_incident_id() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# ESCALATION_MATRIX / SEVERITY_MAP constants
# ---------------------------------------------------------------------------


class TestEscalationConstants:
    def test_severity_map_has_three_levels(self) -> None:
        assert set(SEVERITY_MAP.keys()) == {"p1", "p2", "p3"}

    def test_severity_map_values_in_matrix(self) -> None:
        for matrix_key in SEVERITY_MAP.values():
            assert matrix_key in ESCALATION_MATRIX

    def test_each_matrix_entry_has_levels(self) -> None:
        for key, entry in ESCALATION_MATRIX.items():
            assert "levels" in entry, f"{key} missing 'levels'"
            assert len(entry["levels"]) > 0

    def test_p1_has_four_escalation_levels(self) -> None:
        assert len(ESCALATION_MATRIX["P1_FULL_BCP"]["levels"]) == 4

    def test_p2_has_two_escalation_levels(self) -> None:
        assert len(ESCALATION_MATRIX["P2_PARTIAL_BCP"]["levels"]) == 2

    def test_p3_has_one_escalation_level(self) -> None:
        assert len(ESCALATION_MATRIX["P3_MONITORING"]["levels"]) == 1


# ---------------------------------------------------------------------------
# get_escalation_plan
# ---------------------------------------------------------------------------


class TestGetEscalationPlan:
    def test_p1_returns_correct_plan_name(self) -> None:
        engine = _make_engine()
        plan = engine.get_escalation_plan("p1")
        assert plan["plan_name"] == "P1 Full BCP Activation"

    def test_p2_returns_correct_plan_name(self) -> None:
        engine = _make_engine()
        plan = engine.get_escalation_plan("p2")
        assert plan["plan_name"] == "P2 Partial BCP Activation"

    def test_p3_returns_correct_plan_name(self) -> None:
        engine = _make_engine()
        plan = engine.get_escalation_plan("p3")
        assert plan["plan_name"] == "P3 Monitoring"

    def test_case_insensitive_severity(self) -> None:
        engine = _make_engine()
        plan_upper = engine.get_escalation_plan("P1")
        plan_lower = engine.get_escalation_plan("p1")
        assert plan_upper["plan_name"] == plan_lower["plan_name"]

    def test_unknown_severity_returns_unknown_plan(self) -> None:
        engine = _make_engine()
        plan = engine.get_escalation_plan("p99")
        assert plan["plan_name"] == "Unknown"
        assert plan["levels"] == []

    def test_plan_contains_severity_key(self) -> None:
        engine = _make_engine()
        plan = engine.get_escalation_plan("p1")
        assert "severity" in plan
        assert plan["severity"] == "p1"

    def test_p1_levels_ordered_by_level_number(self) -> None:
        engine = _make_engine()
        plan = engine.get_escalation_plan("p1")
        levels = [lvl["level"] for lvl in plan["levels"]]
        assert levels == sorted(levels)

    def test_first_level_has_zero_delay(self) -> None:
        engine = _make_engine()
        for severity in ("p1", "p2", "p3"):
            plan = engine.get_escalation_plan(severity)
            first = plan["levels"][0]
            assert first["delay_minutes"] == 0, f"{severity} first level delay should be 0"


# ---------------------------------------------------------------------------
# trigger_escalation
# ---------------------------------------------------------------------------


class TestTriggerEscalation:
    def test_returns_dict_with_required_keys(self) -> None:
        engine = _make_engine()
        result = engine.trigger_escalation(_make_incident_id(), "p1")
        assert "incident_id" in result
        assert "severity" in result
        assert "plan_name" in result
        assert "notifications_queued" in result
        assert "notifications" in result

    def test_p3_queues_one_notification(self) -> None:
        engine = _make_engine()
        result = engine.trigger_escalation(_make_incident_id(), "p3")
        # P3 has 1 level × 1 channel (teams) = 1 notification
        assert result["notifications_queued"] == 1

    def test_p1_queues_multiple_notifications(self) -> None:
        engine = _make_engine()
        result = engine.trigger_escalation(_make_incident_id(), "p1")
        # P1 has 4 levels; levels 1&3&4 have multi-channel → expect > 4
        assert result["notifications_queued"] > 1

    def test_notifications_list_length_matches_count(self) -> None:
        engine = _make_engine()
        result = engine.trigger_escalation(_make_incident_id(), "p2")
        assert len(result["notifications"]) == result["notifications_queued"]

    def test_notifications_have_status(self) -> None:
        engine = _make_engine()
        result = engine.trigger_escalation(_make_incident_id(), "p1")
        for notif in result["notifications"]:
            assert "status" in notif
            assert notif["status"] in ("sent", "pending", "failed")

    def test_notifications_have_escalation_metadata(self) -> None:
        engine = _make_engine()
        result = engine.trigger_escalation(_make_incident_id(), "p1")
        for notif in result["notifications"]:
            meta = notif.get("metadata", {})
            assert "escalation_level" in meta
            assert "delay_minutes" in meta
            assert "role" in meta

    def test_with_contacts_uses_contact_info(self) -> None:
        engine = _make_engine()
        contacts: list[dict[str, Any]] = [
            {
                "role": "対応チーム",
                "name": "Test Team",
                "email": "team@example.com",
                "teams_id": "https://teams.example.com/hook",
            }
        ]
        result = engine.trigger_escalation(_make_incident_id(), "p3", contacts=contacts)
        assert result["notifications_queued"] >= 1

    def test_unknown_severity_queues_zero_notifications(self) -> None:
        engine = _make_engine()
        result = engine.trigger_escalation(_make_incident_id(), "unknown")
        assert result["notifications_queued"] == 0
        assert result["notifications"] == []

    def test_stores_escalation_state(self) -> None:
        engine = _make_engine()
        incident_id = _make_incident_id()
        engine.trigger_escalation(incident_id, "p2")
        status = engine.get_escalation_status(incident_id)
        assert status["total_notifications"] > 0

    def test_multiple_incidents_tracked_independently(self) -> None:
        engine = _make_engine()
        id1, id2 = _make_incident_id(), _make_incident_id()
        engine.trigger_escalation(id1, "p3")
        engine.trigger_escalation(id2, "p2")
        status1 = engine.get_escalation_status(id1)
        status2 = engine.get_escalation_status(id2)
        assert status1["total_notifications"] != status2["total_notifications"]


# ---------------------------------------------------------------------------
# get_escalation_status
# ---------------------------------------------------------------------------


class TestGetEscalationStatus:
    def test_unknown_incident_returns_empty_status(self) -> None:
        engine = _make_engine()
        status = engine.get_escalation_status(_make_incident_id())
        assert status["total_notifications"] == 0
        assert status["sent"] == 0
        assert status["pending"] == 0
        assert status["failed"] == 0
        assert status["notifications"] == []

    def test_status_contains_incident_id(self) -> None:
        engine = _make_engine()
        incident_id = _make_incident_id()
        engine.trigger_escalation(incident_id, "p1")
        status = engine.get_escalation_status(incident_id)
        assert status["incident_id"] == incident_id

    def test_sent_plus_pending_plus_failed_equals_total(self) -> None:
        engine = _make_engine()
        incident_id = _make_incident_id()
        engine.trigger_escalation(incident_id, "p1")
        status = engine.get_escalation_status(incident_id)
        total = status["sent"] + status["pending"] + status["failed"]
        assert total == status["total_notifications"]

    def test_dry_run_marks_notifications_sent(self) -> None:
        # dry_run NotificationService always returns status='sent'
        engine = _make_engine()
        incident_id = _make_incident_id()
        engine.trigger_escalation(incident_id, "p3")
        status = engine.get_escalation_status(incident_id)
        assert status["sent"] >= 1


# ---------------------------------------------------------------------------
# EscalationEngine initialisation
# ---------------------------------------------------------------------------


class TestEscalationEngineInit:
    def test_default_init_creates_notification_service(self) -> None:
        # Constructing without injection should not raise
        engine = EscalationEngine()
        assert engine.notification_service is not None

    def test_injected_service_is_used(self) -> None:
        svc = NotificationService(dry_run=True)
        engine = EscalationEngine(notification_service=svc)
        assert engine.notification_service is svc

    def test_initial_escalation_state_is_empty(self) -> None:
        engine = _make_engine()
        assert engine._escalation_state == {}
