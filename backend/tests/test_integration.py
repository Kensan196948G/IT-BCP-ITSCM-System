"""Integration tests: cross-router workflows and monitoring endpoints."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient

from database import get_db
from main import app

FIXED_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")
FIXED_UUID_2 = uuid.UUID("22222222-2222-2222-2222-222222222222")
FIXED_NOW = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers: mock objects
# ---------------------------------------------------------------------------


class _MockSystem:
    def __init__(self, **kw: object) -> None:
        defaults = {
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
        for k, v in defaults.items():
            setattr(self, k, v)


class _MockExercise:
    def __init__(self, **kw: object) -> None:
        defaults = {
            "id": FIXED_UUID,
            "exercise_id": "EX-2026-001",
            "title": "Annual DR drill",
            "exercise_type": "tabletop",
            "scenario_description": "DC failure scenario",
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
        for k, v in defaults.items():
            setattr(self, k, v)


class _MockIncident:
    def __init__(self, **kw: object) -> None:
        defaults = {
            "id": FIXED_UUID,
            "incident_id": "BCP-2026-001",
            "title": "DC power failure",
            "scenario_type": "dc_failure",
            "severity": "p1",
            "occurred_at": FIXED_NOW,
            "detected_at": FIXED_NOW,
            "declared_at": None,
            "incident_commander": "Incident Lead",
            "status": "active",
            "situation_report": None,
            "affected_systems": ["Core Banking System"],
            "affected_users": 500,
            "estimated_impact": "High",
            "resolved_at": None,
            "actual_rto_hours": None,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(kw)
        for k, v in defaults.items():
            setattr(self, k, v)


class _MockTask:
    def __init__(self, **kw: object) -> None:
        defaults = {
            "id": FIXED_UUID_2,
            "incident_id": FIXED_UUID,
            "task_title": "Restore database",
            "description": "Restore from backup",
            "assigned_to": "DBA",
            "assigned_team": "Database",
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
        for k, v in defaults.items():
            setattr(self, k, v)


class _MockSitReport:
    def __init__(self, **kw: object) -> None:
        defaults = {
            "id": FIXED_UUID_2,
            "incident_id": FIXED_UUID,
            "report_number": 1,
            "report_time": FIXED_NOW,
            "reporter": "Incident Lead",
            "summary": "Recovery in progress",
            "systems_status": {"Core Banking System": "recovering"},
            "tasks_summary": {"total": 1, "completed": 0},
            "next_actions": ["Continue DB restore"],
            "escalation_status": "active",
            "audience": "internal",
            "created_at": FIXED_NOW,
        }
        defaults.update(kw)
        for k, v in defaults.items():
            setattr(self, k, v)


class _MockBIA:
    def __init__(self, **kw: object) -> None:
        defaults = {
            "id": FIXED_UUID,
            "assessment_id": "BIA-2026-001",
            "system_name": "Core Banking System",
            "assessment_date": date(2026, 3, 27),
            "assessor": "Risk Manager",
            "business_processes": ["Payment processing"],
            "financial_impact_per_hour": 500.0,
            "financial_impact_per_day": 12000.0,
            "max_tolerable_downtime_hours": 24.0,
            "regulatory_risks": ["Regulatory report required"],
            "reputation_impact": "high",
            "operational_impact": "critical",
            "recommended_rto_hours": 4.0,
            "recommended_rpo_hours": 1.0,
            "risk_score": 72,
            "mitigation_measures": ["DR setup"],
            "status": "draft",
            "notes": None,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(kw)
        for k, v in defaults.items():
            setattr(self, k, v)


def _fake_db() -> object:
    async def _gen() -> AsyncIterator[AsyncMock]:
        yield AsyncMock()

    return _gen


@pytest.fixture()
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = _fake_db()
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Metrics endpoint tests
# ---------------------------------------------------------------------------


def test_metrics_endpoint_returns_prometheus_format(client: TestClient) -> None:
    """GET /api/metrics returns Prometheus exposition format text."""
    resp = client.get("/api/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "itbcp_request_count" in body
    assert "itbcp_error_count" in body
    assert "itbcp_uptime_seconds" in body


def test_metrics_contains_all_metric_types(client: TestClient) -> None:
    """Metrics output includes all required metric names."""
    resp = client.get("/api/metrics")
    required = [
        "itbcp_request_count",
        "itbcp_request_duration_seconds",
        "itbcp_error_count",
        "itbcp_error_rate",
        "itbcp_average_duration_seconds",
        "itbcp_active_incidents",
        "itbcp_uptime_seconds",
    ]
    for metric in required:
        assert metric in resp.text, f"Missing metric: {metric}"


# ---------------------------------------------------------------------------
# 2. Health probe tests
# ---------------------------------------------------------------------------


@patch(
    "apps.monitoring.HealthChecker.check_database",
    new_callable=AsyncMock,
    return_value={"name": "database", "status": "healthy", "latency_ms": 1.0},
)
@patch(
    "apps.monitoring.HealthChecker.check_redis",
    new_callable=AsyncMock,
    return_value={"name": "redis", "status": "healthy", "latency_ms": 0.5},
)
def test_readiness_probe(_mock_redis: AsyncMock, _mock_db: AsyncMock, client: TestClient) -> None:
    """GET /api/health/ready returns readiness status (mocked deps for test isolation)."""
    resp = client.get("/api/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert len(data["checks"]) >= 2


def test_liveness_probe(client: TestClient) -> None:
    """GET /api/health/live returns liveness status."""
    resp = client.get("/api/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


def test_detailed_health(client: TestClient) -> None:
    """GET /api/health/detailed returns full health details."""
    resp = client.get("/api/health/detailed")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "checks" in data
    assert "metrics" in data
    assert "system" in data
    assert "cpu_usage_percent" in data["system"]
    assert "memory_usage_percent" in data["system"]


# ---------------------------------------------------------------------------
# 3. Systems -> Exercises -> Incidents workflow
# ---------------------------------------------------------------------------


@patch("apps.crud.create_system", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_systems_list_then_create(mock_list: AsyncMock, mock_create: AsyncMock, client: TestClient) -> None:
    """GET /api/systems then POST /api/systems workflow."""
    mock_list.return_value = []
    resp = client.get("/api/systems")
    assert resp.status_code == 200
    assert resp.json() == []

    mock_create.return_value = _MockSystem()
    payload = {
        "system_name": "Core Banking System",
        "system_type": "onprem",
        "criticality": "tier1",
        "rto_target_hours": 4.0,
        "rpo_target_hours": 1.0,
    }
    resp = client.post("/api/systems", json=payload)
    assert resp.status_code == 201
    assert resp.json()["system_name"] == "Core Banking System"


@patch("apps.crud.create_exercise", new_callable=AsyncMock)
@patch("apps.crud.get_all_exercises", new_callable=AsyncMock)
def test_exercises_list_then_create(mock_list: AsyncMock, mock_create: AsyncMock, client: TestClient) -> None:
    """GET /api/exercises then POST /api/exercises workflow."""
    mock_list.return_value = []
    resp = client.get("/api/exercises")
    assert resp.status_code == 200

    mock_create.return_value = _MockExercise()
    payload = {
        "exercise_id": "EX-2026-001",
        "title": "Annual DR drill",
        "exercise_type": "tabletop",
        "scheduled_date": "2026-03-27T12:00:00Z",
    }
    resp = client.post("/api/exercises", json=payload)
    assert resp.status_code == 201
    assert resp.json()["exercise_id"] == "EX-2026-001"


@patch("apps.crud.create_incident", new_callable=AsyncMock)
@patch("apps.crud.get_all_incidents", new_callable=AsyncMock)
def test_incidents_list_then_create(mock_list: AsyncMock, mock_create: AsyncMock, client: TestClient) -> None:
    """GET /api/incidents then POST /api/incidents workflow."""
    mock_list.return_value = []
    resp = client.get("/api/incidents")
    assert resp.status_code == 200

    mock_create.return_value = _MockIncident()
    payload = {
        "incident_id": "BCP-2026-001",
        "title": "DC power failure",
        "scenario_type": "dc_failure",
        "severity": "p1",
        "occurred_at": "2026-03-27T12:00:00Z",
        "detected_at": "2026-03-27T12:05:00Z",
        "affected_systems": ["Core Banking System"],
    }
    resp = client.post("/api/incidents", json=payload)
    assert resp.status_code == 201
    assert resp.json()["severity"] == "p1"


# ---------------------------------------------------------------------------
# 4. Incident -> Task -> Situation Report flow
# ---------------------------------------------------------------------------


@patch("apps.crud.create_incident_task", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_incident_task_creation(mock_get: AsyncMock, mock_create_task: AsyncMock, client: TestClient) -> None:
    """POST /api/incidents/{id}/tasks creates a task for an incident."""
    mock_get.return_value = _MockIncident()
    mock_create_task.return_value = _MockTask()
    payload = {
        "task_title": "Restore database",
        "priority": "critical",
        "assigned_to": "DBA",
    }
    resp = client.post(f"/api/incidents/{FIXED_UUID}/tasks", json=payload)
    assert resp.status_code == 201
    assert resp.json()["task_title"] == "Restore database"


@patch("apps.crud.create_situation_report", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_situation_report_creation(mock_get: AsyncMock, mock_create_sr: AsyncMock, client: TestClient) -> None:
    """POST /api/incidents/{id}/situation-reports creates a report."""
    mock_get.return_value = _MockIncident()
    mock_create_sr.return_value = _MockSitReport()
    payload = {
        "report_number": 1,
        "summary": "Recovery in progress",
        "audience": "internal",
    }
    resp = client.post(
        f"/api/incidents/{FIXED_UUID}/situation-reports",
        json=payload,
    )
    assert resp.status_code == 201
    assert resp.json()["summary"] == "Recovery in progress"


# ---------------------------------------------------------------------------
# 5. BIA -> Summary workflow
# ---------------------------------------------------------------------------


@patch("apps.routers.bia.get_cached", new_callable=AsyncMock, return_value=None)
@patch("apps.routers.bia.set_cached", new_callable=AsyncMock)
@patch("apps.crud.get_all_bia_assessments", new_callable=AsyncMock)
def test_bia_summary_integration(mock_list: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client: TestClient) -> None:
    """GET /api/bia/summary returns aggregated BIA statistics."""
    mock_list.return_value = [_MockBIA()]
    resp = client.get("/api/bia/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_assessments"] == 1
    assert data["average_risk_score"] is not None


@patch("apps.routers.bia.get_cached", new_callable=AsyncMock, return_value=None)
@patch("apps.routers.bia.set_cached", new_callable=AsyncMock)
@patch("apps.crud.get_all_bia_assessments", new_callable=AsyncMock)
def test_bia_risk_matrix_integration(mock_list: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client: TestClient) -> None:
    """GET /api/bia/risk-matrix returns risk matrix data."""
    mock_list.return_value = [_MockBIA()]
    resp = client.get("/api/bia/risk-matrix")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert "matrix" in data


# ---------------------------------------------------------------------------
# 6. Escalation -> Notification logs flow
# ---------------------------------------------------------------------------


def test_escalation_trigger_and_notification_logs(client: TestClient) -> None:
    """POST escalation then GET notification logs."""
    esc_payload = {
        "incident_id": str(FIXED_UUID),
        "severity": "p1",
        "contacts": [
            {"role": "CTO", "name": "Taro", "email": "cto@example.com"},
        ],
    }
    resp = client.post("/api/escalation/trigger", json=esc_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["severity"] == "p1"
    assert data["notifications_queued"] >= 1

    # Check notification logs
    resp2 = client.get("/api/notifications/logs")
    assert resp2.status_code == 200
    logs = resp2.json()
    assert len(logs) >= 1


# ---------------------------------------------------------------------------
# 7. Dashboard readiness
# ---------------------------------------------------------------------------


@patch("apps.routers.dashboard.get_cached", new_callable=AsyncMock, return_value=None)
@patch("apps.routers.dashboard.set_cached", new_callable=AsyncMock)
@patch("apps.crud.get_active_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_dashboard_readiness(
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client: TestClient
) -> None:
    """GET /api/dashboard/readiness returns readiness dashboard."""
    mock_systems.return_value = [_MockSystem()]
    mock_incidents.return_value = []
    resp = client.get("/api/dashboard/readiness")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_systems" in data
    assert "readiness_score" in data
    assert data["total_systems"] == 1
