"""Tests for report generation endpoints and ReportGenerator class."""

from unittest.mock import AsyncMock, patch

import pytest

from apps.report_generator import ReportGenerator
from tests.conftest import MockExercise, MockSystem

# ---------------------------------------------------------------------------
# ReportGenerator unit tests
# ---------------------------------------------------------------------------


class TestReportGeneratorReadiness:
    """Tests for generate_readiness_report."""

    def test_empty_systems(self):
        gen = ReportGenerator(systems=[], exercises=[], incidents=[])
        report = gen.generate_readiness_report()
        assert report["report_id"] == "RPT-001"
        assert report["overall_score"] == 0.0
        assert report["total_systems"] == 0

    def test_with_tested_systems(self):
        systems = [
            {
                "system_name": "System A",
                "rto_target_hours": 4.0,
                "rpo_target_hours": 1.0,
                "last_dr_test": "2026-01-01",
                "last_test_rto": 3.0,
                "fallback_system": "Backup A",
            },
            {
                "system_name": "System B",
                "rto_target_hours": 8.0,
                "rpo_target_hours": 2.0,
                "last_dr_test": None,
                "last_test_rto": None,
                "fallback_system": None,
            },
        ]
        gen = ReportGenerator(systems=systems, exercises=[], incidents=[])
        report = gen.generate_readiness_report()
        assert report["total_systems"] == 2
        assert report["tested_systems"] == 1
        assert report["rto_met_systems"] == 1
        assert "System B" in report["untested_systems"]
        assert report["overall_score"] > 0
        assert len(report["system_readiness"]) == 2

    def test_recommendations_generated(self):
        systems = [
            {
                "system_name": "Sys",
                "rto_target_hours": 1.0,
                "rpo_target_hours": 1.0,
                "last_dr_test": None,
                "last_test_rto": None,
                "fallback_system": None,
            }
        ]
        gen = ReportGenerator(systems=systems, exercises=[], incidents=[])
        report = gen.generate_readiness_report()
        assert len(report["recommendations"]) > 0


class TestReportGeneratorRTOCompliance:
    """Tests for generate_rto_compliance_report."""

    def test_empty_systems(self):
        gen = ReportGenerator(systems=[], exercises=[], incidents=[])
        report = gen.generate_rto_compliance_report()
        assert report["report_id"] == "RPT-002"
        assert report["compliance_rate"] == 0.0

    def test_compliance_calculation(self):
        systems = [
            {
                "system_name": "Compliant",
                "rto_target_hours": 4.0,
                "last_test_rto": 3.0,
            },
            {
                "system_name": "Non-compliant",
                "rto_target_hours": 2.0,
                "last_test_rto": 5.0,
            },
        ]
        gen = ReportGenerator(systems=systems, exercises=[], incidents=[])
        report = gen.generate_rto_compliance_report()
        assert report["compliance_rate"] == 50.0
        assert report["compliant_systems"] == 1
        assert "Non-compliant" in report["overdue_systems"]


class TestReportGeneratorExerciseTrend:
    """Tests for generate_exercise_trend_report."""

    def test_empty_exercises(self):
        gen = ReportGenerator(systems=[], exercises=[], incidents=[])
        report = gen.generate_exercise_trend_report()
        assert report["report_id"] == "RPT-003"
        assert report["total_exercises"] == 0
        assert report["yearly_trends"] == []

    def test_with_exercises(self):
        exercises = [
            {
                "scheduled_date": "2026-03-01T00:00:00Z",
                "status": "completed",
                "overall_result": "pass",
                "findings": None,
                "improvements": None,
            },
            {
                "scheduled_date": "2026-06-01T00:00:00Z",
                "status": "completed",
                "overall_result": "fail",
                "findings": None,
                "improvements": None,
            },
        ]
        gen = ReportGenerator(systems=[], exercises=exercises, incidents=[])
        report = gen.generate_exercise_trend_report()
        assert report["total_exercises"] == 2
        assert len(report["yearly_trends"]) == 1
        assert report["yearly_trends"][0]["year"] == 2026
        assert report["yearly_trends"][0]["achievement_rate"] == 50.0


class TestReportGeneratorISO20000:
    """Tests for generate_iso20000_report."""

    def test_empty_data(self):
        gen = ReportGenerator(systems=[], exercises=[], incidents=[])
        report = gen.generate_iso20000_report()
        assert report["report_id"] == "RPT-004"
        assert report["compliance_rate"] == 0.0
        assert len(report["non_compliant_items"]) == 8

    def test_partial_compliance(self):
        systems = [
            {
                "system_name": "Sys",
                "rto_target_hours": 4.0,
                "fallback_system": "Backup",
                "last_dr_test": "2026-01-01",
            }
        ]
        exercises = [
            {
                "scheduled_date": "2026-01-01T00:00:00Z",
                "status": "completed",
                "overall_result": "pass",
                "findings": None,
                "improvements": None,
            }
        ]
        gen = ReportGenerator(systems=systems, exercises=exercises, incidents=[])
        report = gen.generate_iso20000_report()
        assert report["compliance_rate"] > 0.0
        assert report["compliant_items"] > 0


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def _mock_crud():
    """Mock all crud functions used by report endpoints."""
    with (
        patch("apps.routers.dashboard.crud.get_all_systems", new_callable=AsyncMock) as mock_sys,
        patch("apps.routers.dashboard.crud.get_all_exercises", new_callable=AsyncMock) as mock_ex,
        patch("apps.routers.dashboard.crud.get_all_incidents", new_callable=AsyncMock) as mock_inc,
    ):
        mock_sys.return_value = [
            MockSystem(
                rpo_target_hours=1.0,
                last_dr_test="2026-01-01",
                last_test_rto=3.0,
                fallback_system="Backup",
            ),
        ]
        mock_ex.return_value = [
            MockExercise(status="completed", overall_result="pass"),
        ]
        mock_inc.return_value = []
        yield


@pytest.mark.usefixtures("_mock_crud")
class TestReportEndpoints:
    """Tests for the report API endpoints."""

    def test_readiness_report(self, client):
        resp = client.get("/api/dashboard/reports/readiness")
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] == "RPT-001"
        assert "overall_score" in data

    def test_rto_compliance_report(self, client):
        resp = client.get("/api/dashboard/reports/rto-compliance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] == "RPT-002"
        assert "compliance_rate" in data

    def test_exercise_trend_report(self, client):
        resp = client.get("/api/dashboard/reports/exercise-trends")
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] == "RPT-003"
        assert "yearly_trends" in data

    def test_iso20000_report(self, client):
        resp = client.get("/api/dashboard/reports/iso20000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_id"] == "RPT-004"
        assert "compliance_rate" in data
