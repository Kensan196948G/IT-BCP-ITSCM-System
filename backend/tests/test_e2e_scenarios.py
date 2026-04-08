"""End-to-end scenario tests simulating real-world BCP workflows."""

import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from database import get_db
from main import app

FIXED_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")
FIXED_UUID_2 = uuid.UUID("22222222-2222-2222-2222-222222222222")
FIXED_UUID_3 = uuid.UUID("33333333-3333-3333-3333-333333333333")
FIXED_NOW = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


class _M:
    """Generic mock object builder."""

    @staticmethod
    def system(**kw: object) -> object:
        defaults: dict[str, object] = {
            "id": FIXED_UUID,
            "system_name": "Core Banking System",
            "system_type": "onprem",
            "criticality": "tier1",
            "rto_target_hours": 4.0,
            "rpo_target_hours": 1.0,
            "mtpd_hours": 24.0,
            "fallback_system": None,
            "fallback_procedure": None,
            "primary_owner": "IT Ops",
            "vendor_name": None,
            "last_dr_test": None,
            "last_test_rto": None,
            "is_active": True,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(kw)
        obj = type("MockSystem", (), defaults)()
        return obj

    @staticmethod
    def incident(**kw: object) -> object:
        defaults: dict[str, object] = {
            "id": FIXED_UUID,
            "incident_id": "BCP-2026-001",
            "title": "Major Earthquake Impact",
            "scenario_type": "earthquake",
            "severity": "p1",
            "occurred_at": FIXED_NOW,
            "detected_at": FIXED_NOW,
            "declared_at": None,
            "incident_commander": "Incident Commander",
            "status": "active",
            "situation_report": None,
            "affected_systems": ["Core Banking System"],
            "affected_users": 1000,
            "estimated_impact": "Critical",
            "resolved_at": None,
            "actual_rto_hours": None,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(kw)
        return type("MockIncident", (), defaults)()

    @staticmethod
    def task(**kw: object) -> object:
        defaults: dict[str, object] = {
            "id": FIXED_UUID_2,
            "incident_id": FIXED_UUID,
            "task_title": "Emergency response",
            "description": "Immediate actions",
            "assigned_to": "Team Lead",
            "assigned_team": "Operations",
            "priority": "critical",
            "status": "pending",
            "target_system": "Core Banking System",
            "due_hours": 2.0,
            "started_at": None,
            "completed_at": None,
            "notes": None,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(kw)
        return type("MockTask", (), defaults)()

    @staticmethod
    def sitrep(**kw: object) -> object:
        defaults: dict[str, object] = {
            "id": FIXED_UUID_3,
            "incident_id": FIXED_UUID,
            "report_number": 1,
            "report_time": FIXED_NOW,
            "reporter": "Incident Commander",
            "summary": "Recovery in progress",
            "systems_status": {"Core Banking System": "recovering"},
            "tasks_summary": {"total": 1, "completed": 0},
            "next_actions": ["Continue recovery"],
            "escalation_status": "active",
            "audience": "internal",
            "created_at": FIXED_NOW,
        }
        defaults.update(kw)
        return type("MockSitReport", (), defaults)()

    @staticmethod
    def exercise(**kw: object) -> object:
        defaults: dict[str, object] = {
            "id": FIXED_UUID,
            "exercise_id": "EX-2026-001",
            "title": "DR Exercise",
            "exercise_type": "tabletop",
            "scenario_description": "DC failure",
            "scheduled_date": FIXED_NOW,
            "actual_date": None,
            "duration_hours": 2.0,
            "facilitator": "IT Manager",
            "status": "planned",
            "overall_result": None,
            "findings": None,
            "improvements": None,
            "lessons_learned": None,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(kw)
        return type("MockExercise", (), defaults)()

    @staticmethod
    def rto_record(**kw: object) -> object:
        defaults: dict[str, object] = {
            "id": FIXED_UUID_2,
            "exercise_id": FIXED_UUID,
            "system_name": "Core Banking System",
            "rto_target_hours": 4.0,
            "rto_actual_hours": 3.5,
            "achieved": True,
            "recorded_at": FIXED_NOW,
            "recorded_by": "Tester",
            "notes": None,
        }
        defaults.update(kw)
        return type("MockRTORecord", (), defaults)()

    @staticmethod
    def scenario(**kw: object) -> object:
        defaults: dict[str, object] = {
            "id": FIXED_UUID,
            "scenario_id": "SCN-2026-001",
            "title": "Large Earthquake",
            "scenario_type": "earthquake",
            "description": "M7+ earthquake affecting data center",
            "initial_inject": "Earthquake detected at DC",
            "injects": [
                {"time": 0, "event": "Initial shock"},
                {"time": 30, "event": "Aftershock"},
            ],
            "affected_systems": ["Core Banking System"],
            "expected_duration_hours": 8.0,
            "difficulty": "hard",
            "is_active": True,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(kw)
        return type("MockScenario", (), defaults)()

    @staticmethod
    def bia(**kw: object) -> object:
        defaults: dict[str, object] = {
            "id": FIXED_UUID,
            "assessment_id": "BIA-2026-001",
            "system_name": "Core Banking System",
            "assessment_date": date(2026, 3, 27),
            "assessor": "Risk Manager",
            "business_processes": ["Payment processing"],
            "financial_impact_per_hour": 500.0,
            "financial_impact_per_day": 12000.0,
            "max_tolerable_downtime_hours": 24.0,
            "regulatory_risks": ["Regulatory report"],
            "reputation_impact": "high",
            "operational_impact": "critical",
            "recommended_rto_hours": 4.0,
            "recommended_rpo_hours": 1.0,
            "risk_score": 72,
            "mitigation_measures": ["DR environment"],
            "status": "reviewed",
            "notes": None,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(kw)
        return type("MockBIA", (), defaults)()


def _fake_db() -> Any:
    async def _gen() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    return _gen


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = _fake_db()
    yield TestClient(app)
    app.dependency_overrides.clear()


# ===================================================================
# E2E_001: Large Earthquake Scenario
# ===================================================================


class TestE2E001LargeEarthquake:
    """Full BCP activation flow for a large earthquake scenario."""

    @patch("apps.crud.create_incident", new_callable=AsyncMock)
    def test_step1_bcp_activation(self, mock_create: AsyncMock, client: TestClient) -> None:
        """Step 1: Create a P1 incident (BCP activation)."""
        mock_create.return_value = _M.incident()
        payload = {
            "incident_id": "BCP-2026-001",
            "title": "Major Earthquake Impact",
            "scenario_type": "earthquake",
            "severity": "p1",
            "occurred_at": "2026-03-27T12:00:00Z",
            "detected_at": "2026-03-27T12:01:00Z",
            "affected_systems": ["Core Banking System"],
            "affected_users": 1000,
        }
        resp = client.post("/api/incidents", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["severity"] == "p1"
        assert data["scenario_type"] == "earthquake"

    def test_step2_escalation(self, client: TestClient) -> None:
        """Step 2: Trigger P1 escalation with emergency contacts."""
        payload = {
            "incident_id": str(FIXED_UUID),
            "severity": "p1",
            "contacts": [
                {"role": "CTO", "name": "Tanaka", "email": "cto@corp.jp"},
                {"role": "CISO", "name": "Suzuki", "email": "ciso@corp.jp"},
            ],
        }
        resp = client.post("/api/escalation/trigger", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_name"] is not None
        assert data["notifications_queued"] >= 1

    @patch("apps.crud.create_incident_task", new_callable=AsyncMock)
    @patch("apps.crud.get_incident", new_callable=AsyncMock)
    def test_step3_task_assignment(self, mock_get: AsyncMock, mock_create: AsyncMock, client: TestClient) -> None:
        """Step 3: Assign recovery tasks to teams."""
        mock_get.return_value = _M.incident()
        mock_create.return_value = _M.task()
        payload = {
            "task_title": "Emergency response",
            "priority": "critical",
            "assigned_to": "Team Lead",
            "assigned_team": "Operations",
            "target_system": "Core Banking System",
            "due_hours": 2.0,
        }
        resp = client.post(f"/api/incidents/{FIXED_UUID}/tasks", json=payload)
        assert resp.status_code == 201
        assert resp.json()["priority"] == "critical"

    @patch("apps.crud.get_incident", new_callable=AsyncMock)
    @patch("apps.crud.get_all_systems", new_callable=AsyncMock)
    def test_step4_rto_tracking(self, mock_systems: AsyncMock, mock_incident: AsyncMock, client: TestClient) -> None:
        """Step 4: Check RTO dashboard for affected systems."""
        mock_incident.return_value = _M.incident()
        mock_systems.return_value = [_M.system()]
        resp = client.get(f"/api/incidents/{FIXED_UUID}/rto-dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @patch("apps.crud.create_situation_report", new_callable=AsyncMock)
    @patch("apps.crud.get_incident", new_callable=AsyncMock)
    def test_step5_situation_report(self, mock_get: AsyncMock, mock_create: AsyncMock, client: TestClient) -> None:
        """Step 5: Generate situation report."""
        mock_get.return_value = _M.incident()
        mock_create.return_value = _M.sitrep()
        payload = {
            "report_number": 1,
            "summary": "Recovery in progress. ETA 3 hours.",
            "audience": "management",
        }
        resp = client.post(
            f"/api/incidents/{FIXED_UUID}/situation-reports",
            json=payload,
        )
        assert resp.status_code == 201
        assert resp.json()["report_number"] == 1

    @patch("apps.crud.update_incident", new_callable=AsyncMock)
    def test_step6_incident_resolution(self, mock_update: AsyncMock, client: TestClient) -> None:
        """Step 6: Resolve the incident."""
        mock_update.return_value = _M.incident(
            status="resolved",
            resolved_at=FIXED_NOW,
            actual_rto_hours=3.5,
        )
        payload = {
            "status": "resolved",
            "resolved_at": "2026-03-27T15:30:00Z",
            "actual_rto_hours": 3.5,
        }
        resp = client.put(f"/api/incidents/{FIXED_UUID}", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"


# ===================================================================
# E2E_002: Ransomware Scenario (compact)
# ===================================================================


class TestE2E002Ransomware:
    """Ransomware incident flow: create incident + escalation."""

    @patch("apps.crud.create_incident", new_callable=AsyncMock)
    def test_ransomware_incident_and_escalation(self, mock_create: AsyncMock, client: TestClient) -> None:
        """Create ransomware incident then trigger escalation."""
        mock_create.return_value = _M.incident(
            incident_id="BCP-2026-002",
            title="Ransomware Attack Detected",
            scenario_type="ransomware",
            severity="p1",
        )
        payload = {
            "incident_id": "BCP-2026-002",
            "title": "Ransomware Attack Detected",
            "scenario_type": "ransomware",
            "severity": "p1",
            "occurred_at": "2026-03-27T14:00:00Z",
            "detected_at": "2026-03-27T14:05:00Z",
            "affected_systems": ["Core Banking System"],
        }
        resp = client.post("/api/incidents", json=payload)
        assert resp.status_code == 201
        assert resp.json()["scenario_type"] == "ransomware"

        # Escalation
        esc_payload = {
            "incident_id": str(FIXED_UUID),
            "severity": "p1",
            "contacts": [
                {"role": "CISO", "name": "Sato", "email": "ciso@corp.jp"},
            ],
        }
        resp2 = client.post("/api/escalation/trigger", json=esc_payload)
        assert resp2.status_code == 200
        assert resp2.json()["notifications_queued"] >= 1

    @patch("apps.crud.update_incident", new_callable=AsyncMock)
    def test_ransomware_resolution(self, mock_update: AsyncMock, client: TestClient) -> None:
        """Resolve ransomware incident."""
        mock_update.return_value = _M.incident(
            status="resolved",
            resolved_at=FIXED_NOW,
            actual_rto_hours=6.0,
        )
        resp = client.put(
            f"/api/incidents/{FIXED_UUID}",
            json={"status": "resolved", "actual_rto_hours": 6.0},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"


# ===================================================================
# E2E_003: BCP Training Exercise Flow
# ===================================================================


class TestE2E003TrainingExercise:
    """Full BCP training flow: scenario -> exercise -> RTO -> report."""

    @patch("apps.crud.create_scenario", new_callable=AsyncMock)
    def test_step1_create_scenario(self, mock_create: AsyncMock, client: TestClient) -> None:
        """Step 1: Create a training scenario."""
        mock_create.return_value = _M.scenario()
        payload = {
            "scenario_id": "SCN-2026-001",
            "title": "Large Earthquake",
            "scenario_type": "earthquake",
            "description": "M7+ earthquake affecting data center",
            "initial_inject": "Earthquake detected at DC",
            "injects": [
                {"time": 0, "event": "Initial shock"},
                {"time": 30, "event": "Aftershock"},
            ],
            "difficulty": "hard",
        }
        resp = client.post("/api/scenarios", json=payload)
        assert resp.status_code == 201
        assert resp.json()["scenario_type"] == "earthquake"

    @patch("apps.crud.create_exercise", new_callable=AsyncMock)
    def test_step2_create_exercise(self, mock_create: AsyncMock, client: TestClient) -> None:
        """Step 2: Create an exercise linked to the scenario."""
        mock_create.return_value = _M.exercise()
        payload = {
            "exercise_id": "EX-2026-001",
            "title": "DR Exercise",
            "exercise_type": "tabletop",
            "scheduled_date": "2026-04-01T10:00:00Z",
        }
        resp = client.post("/api/exercises", json=payload)
        assert resp.status_code == 201
        assert resp.json()["status"] == "planned"

    @patch("apps.exercise_engine.ExerciseEngine.start_exercise", new_callable=AsyncMock)
    def test_step3_start_exercise(self, mock_start: AsyncMock, client: TestClient) -> None:
        """Step 3: Start the exercise."""
        mock_start.return_value = _M.exercise(status="in_progress")
        resp = client.post(f"/api/exercises/{FIXED_UUID}/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    @patch("apps.exercise_engine.ExerciseEngine.record_rto", new_callable=AsyncMock)
    def test_step4_record_rto(self, mock_rto: AsyncMock, client: TestClient) -> None:
        """Step 4: Record RTO measurement during exercise."""
        mock_rto.return_value = _M.rto_record()
        payload = {
            "system_name": "Core Banking System",
            "rto_target_hours": 4.0,
            "rto_actual_hours": 3.5,
            "recorded_by": "Tester",
        }
        resp = client.post(
            f"/api/exercises/{FIXED_UUID}/rto-record",
            json=payload,
        )
        assert resp.status_code == 201
        assert resp.json()["achieved"] is True

    @patch("apps.exercise_engine.ExerciseEngine.complete_exercise", new_callable=AsyncMock)
    def test_step5_complete_exercise(self, mock_complete: AsyncMock, client: TestClient) -> None:
        """Step 5: Complete the exercise."""
        mock_complete.return_value = _M.exercise(
            status="completed",
            overall_result="pass",
        )
        resp = client.post(f"/api/exercises/{FIXED_UUID}/complete")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    @patch("apps.exercise_engine.ExerciseEngine.generate_report", new_callable=AsyncMock)
    def test_step6_generate_report(self, mock_report: AsyncMock, client: TestClient) -> None:
        """Step 6: Generate exercise report."""
        mock_report.return_value = {
            "exercise": _M.exercise(status="completed"),
            "rto_records": [_M.rto_record()],
            "rto_achievement_rate": 100.0,
            "total_systems_tested": 1,
            "systems_achieved": 1,
            "systems_failed": 0,
            "findings": ["All systems met RTO targets"],
            "recommendations": ["Continue regular testing"],
        }
        resp = client.get(f"/api/exercises/{FIXED_UUID}/report")
        assert resp.status_code == 200
        data = resp.json()
        assert data["rto_achievement_rate"] == 100.0
        assert data["total_systems_tested"] == 1


# ===================================================================
# E2E_004: BIA Assessment Flow
# ===================================================================


class TestE2E004BIAAssessment:
    """BIA assessment: create -> check risk score -> summary."""

    @patch("apps.crud.create_bia_assessment", new_callable=AsyncMock)
    def test_step1_create_assessment(self, mock_create: AsyncMock, client: TestClient) -> None:
        """Step 1: Create a BIA assessment."""
        mock_create.return_value = _M.bia()
        payload = {
            "assessment_id": "BIA-2026-001",
            "system_name": "Core Banking System",
            "assessment_date": "2026-03-27",
            "business_processes": ["Payment processing"],
            "financial_impact_per_hour": 500.0,
            "financial_impact_per_day": 12000.0,
            "risk_score": 72,
            "reputation_impact": "high",
            "operational_impact": "critical",
            "status": "reviewed",
        }
        resp = client.post("/api/bia", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["risk_score"] == 72
        assert data["status"] == "reviewed"

    @patch("apps.crud.get_bia_assessment", new_callable=AsyncMock)
    def test_step2_check_risk_score(self, mock_get: AsyncMock, client: TestClient) -> None:
        """Step 2: Retrieve assessment and verify risk score."""
        mock_get.return_value = _M.bia()
        resp = client.get(f"/api/bia/{FIXED_UUID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_score"] == 72
        assert data["reputation_impact"] == "high"

    @patch("apps.routers.bia.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("apps.routers.bia.set_cached", new_callable=AsyncMock)
    @patch("apps.crud.get_all_bia_assessments", new_callable=AsyncMock)
    def test_step3_get_summary(self, mock_list: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client: TestClient) -> None:
        """Step 3: Get BIA summary with aggregated statistics."""
        mock_list.return_value = [_M.bia()]
        resp = client.get("/api/bia/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_assessments"] == 1
        assert data["average_risk_score"] is not None
        assert data["highest_risk_system"] is not None

    @patch("apps.routers.bia.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("apps.routers.bia.set_cached", new_callable=AsyncMock)
    @patch("apps.crud.get_all_bia_assessments", new_callable=AsyncMock)
    def test_step4_risk_matrix(self, mock_list: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client: TestClient) -> None:
        """Step 4: Get risk matrix from BIA data."""
        mock_list.return_value = [_M.bia()]
        resp = client.get("/api/bia/risk-matrix")
        assert resp.status_code == 200
        data = resp.json()
        assert "matrix" in data
        assert len(data["matrix"]) == 5
