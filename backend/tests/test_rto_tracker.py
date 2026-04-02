"""Tests for RTO Tracker logic."""

from datetime import datetime, timedelta, timezone

from apps.rto_tracker import STATUS_COLORS, RTOTracker


class TestRTOTrackerCalculateStatus:
    """Tests for RTOTracker.calculate_status method."""

    def test_not_started_when_no_occurred_at(self) -> None:
        """Status should be not_started when no incident time is set."""
        tracker = RTOTracker(rto_target_hours=4.0)
        result = tracker.calculate_status()
        assert result["status"] == "not_started"
        assert result["color"] == STATUS_COLORS["not_started"]
        assert result["elapsed_hours"] is None
        assert result["remaining_hours"] is None
        assert result["rto_target"] == 4.0
        assert result["overdue_hours"] is None

    def test_on_track_when_plenty_of_time_remaining(self) -> None:
        """Status should be on_track when well within RTO target."""
        now = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
        occurred = now - timedelta(hours=1)  # 1h elapsed, 4h RTO -> 75% remaining
        tracker = RTOTracker(rto_target_hours=4.0, occurred_at=occurred)
        result = tracker.calculate_status(now=now)
        assert result["status"] == "on_track"
        assert result["color"] == STATUS_COLORS["on_track"]
        assert result["elapsed_hours"] == 1.0
        assert result["remaining_hours"] == 3.0
        assert result["overdue_hours"] is None

    def test_at_risk_when_near_rto_threshold(self) -> None:
        """Status should be at_risk when less than 20% of RTO remaining."""
        now = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
        # 4h RTO, 3.5h elapsed -> 0.5h remaining = 12.5% < 20%
        occurred = now - timedelta(hours=3, minutes=30)
        tracker = RTOTracker(rto_target_hours=4.0, occurred_at=occurred)
        result = tracker.calculate_status(now=now)
        assert result["status"] == "at_risk"
        assert result["color"] == STATUS_COLORS["at_risk"]
        assert result["elapsed_hours"] == 3.5
        assert result["remaining_hours"] == 0.5
        assert result["overdue_hours"] is None

    def test_overdue_when_past_rto(self) -> None:
        """Status should be overdue when elapsed time exceeds RTO target."""
        now = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
        occurred = now - timedelta(hours=6)  # 6h elapsed, 4h RTO
        tracker = RTOTracker(rto_target_hours=4.0, occurred_at=occurred)
        result = tracker.calculate_status(now=now)
        assert result["status"] == "overdue"
        assert result["color"] == STATUS_COLORS["overdue"]
        assert result["elapsed_hours"] == 6.0
        assert result["remaining_hours"] == 0.0
        assert result["overdue_hours"] == 2.0

    def test_recovered_when_resolved(self) -> None:
        """Status should be recovered when incident is resolved."""
        now = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
        occurred = now - timedelta(hours=3)
        resolved = now - timedelta(hours=1)  # took 2h to resolve
        tracker = RTOTracker(rto_target_hours=4.0, occurred_at=occurred, resolved_at=resolved, status="resolved")
        result = tracker.calculate_status(now=now)
        assert result["status"] == "recovered"
        assert result["color"] == STATUS_COLORS["recovered"]
        assert result["elapsed_hours"] == 2.0
        assert result["remaining_hours"] is None
        assert result["overdue_hours"] is None

    def test_recovered_overdue_when_resolved_past_rto(self) -> None:
        """Recovered status should include overdue_hours if resolution exceeded RTO."""
        now = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
        occurred = now - timedelta(hours=6)
        resolved = now - timedelta(hours=1)  # took 5h to resolve, RTO is 4h
        tracker = RTOTracker(rto_target_hours=4.0, occurred_at=occurred, resolved_at=resolved, status="resolved")
        result = tracker.calculate_status(now=now)
        assert result["status"] == "recovered"
        assert result["elapsed_hours"] == 5.0
        assert result["overdue_hours"] == 1.0

    def test_recovered_by_status_without_resolved_at(self) -> None:
        """Status should be recovered when status is 'closed' even without resolved_at."""
        now = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
        occurred = now - timedelta(hours=2)
        tracker = RTOTracker(rto_target_hours=4.0, occurred_at=occurred, status="closed")
        result = tracker.calculate_status(now=now)
        assert result["status"] == "recovered"


class TestRTOTrackerDashboard:
    """Tests for RTOTracker.get_dashboard static method."""

    def test_dashboard_no_incidents(self) -> None:
        """Dashboard with no incidents should show all systems as not_started."""
        systems = [
            {"system_name": "System A", "rto_target_hours": 4.0},
            {"system_name": "System B", "rto_target_hours": 8.0},
        ]
        result = RTOTracker.get_dashboard(systems, [])
        assert result["total_systems"] == 2
        assert result["active_incidents"] == 0
        assert result["readiness_score"] == 100.0
        assert result["systems_overdue"] == 0
        assert len(result["rto_statuses"]) == 2

    def test_dashboard_with_active_incident(self) -> None:
        """Dashboard should reflect active incident affecting a system."""
        now = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
        systems = [
            {"system_name": "System A", "rto_target_hours": 4.0},
            {"system_name": "System B", "rto_target_hours": 8.0},
        ]
        incidents = [
            {
                "affected_systems": ["System A"],
                "occurred_at": now - timedelta(hours=1),
                "resolved_at": None,
                "status": "active",
            }
        ]
        result = RTOTracker.get_dashboard(systems, incidents, now=now)
        assert result["total_systems"] == 2
        assert result["active_incidents"] == 1

        # System A should be on_track (1h elapsed, 4h target)
        system_a = [s for s in result["rto_statuses"] if s["system_name"] == "System A"][0]
        assert system_a["status"] == "on_track"

    def test_dashboard_overdue_reduces_readiness(self) -> None:
        """Readiness score should drop when systems are overdue."""
        now = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
        systems = [
            {"system_name": "System A", "rto_target_hours": 2.0},
            {"system_name": "System B", "rto_target_hours": 8.0},
        ]
        incidents = [
            {
                "affected_systems": ["System A"],
                "occurred_at": now - timedelta(hours=5),
                "resolved_at": None,
                "status": "active",
            }
        ]
        result = RTOTracker.get_dashboard(systems, incidents, now=now)
        assert result["systems_overdue"] == 1
        assert result["readiness_score"] == 50.0

    def test_dashboard_empty_systems(self) -> None:
        """Dashboard with no systems should return defaults."""
        result = RTOTracker.get_dashboard([], [])
        assert result["total_systems"] == 0
        assert result["readiness_score"] == 100.0
        assert result["rto_statuses"] == []

    def test_dashboard_at_risk_system(self) -> None:
        """Dashboard should count at_risk when system is near RTO threshold (< 20% remaining)."""
        now = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
        systems = [
            {"system_name": "System A", "rto_target_hours": 4.0},
        ]
        incidents = [
            {
                "affected_systems": ["System A"],
                "occurred_at": now - timedelta(hours=3, minutes=30),  # 87.5% elapsed
                "resolved_at": None,
                "status": "active",
            }
        ]
        result = RTOTracker.get_dashboard(systems, incidents, now=now)
        system_a = result["rto_statuses"][0]
        assert system_a["status"] == "at_risk"
        assert result["systems_overdue"] == 0
