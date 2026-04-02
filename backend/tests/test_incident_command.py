"""Tests for Phase 2 Incident Command endpoints (mocked DB)."""

import uuid
from unittest.mock import AsyncMock, patch

from tests.conftest import FIXED_NOW, FIXED_UUID, MockIncident, MockSystem

# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

TASK_UUID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
REPORT_UUID = uuid.UUID("11111111-2222-3333-4444-555555555555")


class MockIncidentTask:
    """Mock object mimicking an IncidentTask ORM instance."""

    def __init__(self, **overrides: object) -> None:
        defaults = {
            "id": TASK_UUID,
            "incident_id": FIXED_UUID,
            "task_title": "Restart core database",
            "description": "Restart the primary DB cluster",
            "assigned_to": "DB Team Lead",
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
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(self, k, v)


class MockSituationReport:
    """Mock object mimicking a SituationReport ORM instance."""

    def __init__(self, **overrides: object) -> None:
        defaults = {
            "id": REPORT_UUID,
            "incident_id": FIXED_UUID,
            "report_number": 1,
            "report_time": FIXED_NOW,
            "reporter": "Incident Commander",
            "summary": "Initial situation report.",
            "systems_status": {"Core Banking System": "overdue"},
            "tasks_summary": {"total": 1, "completed": 0},
            "next_actions": ["Restart DB"],
            "escalation_status": "active",
            "audience": "internal",
            "created_at": FIXED_NOW,
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# POST /api/incidents/{id}/tasks  (create task)
# ---------------------------------------------------------------------------


@patch("apps.crud.create_incident_task", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_create_task(mock_get_inc: AsyncMock, mock_create: AsyncMock, client) -> None:
    """POST /api/incidents/{id}/tasks should create a new task."""
    mock_get_inc.return_value = MockIncident()
    mock_create.return_value = MockIncidentTask()
    payload = {
        "task_title": "Restart core database",
        "priority": "critical",
        "assigned_team": "Database",
    }
    response = client.post(f"/api/incidents/{FIXED_UUID}/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["task_title"] == "Restart core database"
    assert data["priority"] == "critical"


@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_create_task_incident_not_found(mock_get: AsyncMock, client) -> None:
    """POST /api/incidents/{id}/tasks should return 404 if incident missing."""
    mock_get.return_value = None
    payload = {"task_title": "Some task"}
    response = client.post(f"/api/incidents/{uuid.uuid4()}/tasks", json=payload)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/incidents/{id}/tasks  (list tasks)
# ---------------------------------------------------------------------------


@patch("apps.crud.get_incident_tasks_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_list_tasks(mock_get_inc: AsyncMock, mock_list: AsyncMock, client) -> None:
    """GET /api/incidents/{id}/tasks should return task list."""
    mock_get_inc.return_value = MockIncident()
    mock_list.return_value = [MockIncidentTask(), MockIncidentTask(status="completed")]
    response = client.get(f"/api/incidents/{FIXED_UUID}/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_list_tasks_incident_not_found(mock_get: AsyncMock, client) -> None:
    """GET /api/incidents/{id}/tasks should return 404 if incident missing."""
    mock_get.return_value = None
    response = client.get(f"/api/incidents/{uuid.uuid4()}/tasks")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/incidents/{id}/tasks/{task_id}  (update task)
# ---------------------------------------------------------------------------


@patch("apps.crud.update_incident_task", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_update_task(mock_get_inc: AsyncMock, mock_update: AsyncMock, client) -> None:
    """PUT /api/incidents/{id}/tasks/{task_id} should update the task."""
    mock_get_inc.return_value = MockIncident()
    mock_update.return_value = MockIncidentTask(status="in_progress")
    response = client.put(
        f"/api/incidents/{FIXED_UUID}/tasks/{TASK_UUID}",
        json={"status": "in_progress"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@patch("apps.crud.update_incident_task", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_update_task_not_found(mock_get_inc: AsyncMock, mock_update: AsyncMock, client) -> None:
    """PUT should return 404 when task does not exist."""
    mock_get_inc.return_value = MockIncident()
    mock_update.return_value = None
    response = client.put(
        f"/api/incidents/{FIXED_UUID}/tasks/{uuid.uuid4()}",
        json={"status": "completed"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/incidents/{id}/situation-reports  (create report)
# ---------------------------------------------------------------------------


@patch("apps.crud.create_situation_report", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_create_situation_report(mock_get_inc: AsyncMock, mock_create: AsyncMock, client) -> None:
    """POST /api/incidents/{id}/situation-reports should create a report."""
    mock_get_inc.return_value = MockIncident()
    mock_create.return_value = MockSituationReport()
    payload = {
        "report_number": 1,
        "summary": "Initial situation report.",
        "audience": "internal",
    }
    response = client.post(f"/api/incidents/{FIXED_UUID}/situation-reports", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["report_number"] == 1
    assert data["summary"] == "Initial situation report."


# ---------------------------------------------------------------------------
# GET /api/incidents/{id}/situation-reports  (list reports)
# ---------------------------------------------------------------------------


@patch("apps.crud.get_situation_reports_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_list_situation_reports(mock_get_inc: AsyncMock, mock_list: AsyncMock, client) -> None:
    """GET /api/incidents/{id}/situation-reports should return list."""
    mock_get_inc.return_value = MockIncident()
    mock_list.return_value = [MockSituationReport()]
    response = client.get(f"/api/incidents/{FIXED_UUID}/situation-reports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


# ---------------------------------------------------------------------------
# POST /api/incidents/{id}/situation-reports/auto-generate
# ---------------------------------------------------------------------------


@patch("apps.crud.create_situation_report", new_callable=AsyncMock)
@patch("apps.crud.get_situation_reports_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
@patch("apps.crud.get_incident_tasks_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_auto_generate_situation_report(
    mock_get_inc: AsyncMock,
    mock_tasks: AsyncMock,
    mock_systems: AsyncMock,
    mock_reports: AsyncMock,
    mock_create: AsyncMock,
    client,
) -> None:
    """POST auto-generate should create a situation report automatically."""
    mock_get_inc.return_value = MockIncident()
    mock_tasks.return_value = [
        MockIncidentTask(status="completed"),
        MockIncidentTask(status="pending"),
    ]
    mock_systems.return_value = [MockSystem(system_name="Core Banking System", rto_target_hours=4.0)]
    mock_reports.return_value = []
    mock_create.return_value = MockSituationReport(report_number=1)

    response = client.post(f"/api/incidents/{FIXED_UUID}/situation-reports/auto-generate")
    assert response.status_code == 201
    data = response.json()
    assert data["report_number"] == 1


@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_auto_generate_incident_not_found(mock_get: AsyncMock, client) -> None:
    """POST auto-generate should return 404 for missing incident."""
    mock_get.return_value = None
    response = client.post(f"/api/incidents/{uuid.uuid4()}/situation-reports/auto-generate")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/incidents/{id}/command-dashboard
# ---------------------------------------------------------------------------


@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
@patch("apps.crud.get_situation_reports_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident_tasks_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_command_dashboard(
    mock_get_inc: AsyncMock,
    mock_tasks: AsyncMock,
    mock_reports: AsyncMock,
    mock_systems: AsyncMock,
    client,
) -> None:
    """GET /api/incidents/{id}/command-dashboard should return dashboard data."""
    mock_get_inc.return_value = MockIncident()
    mock_tasks.return_value = [MockIncidentTask(status="completed")]
    mock_reports.return_value = [MockSituationReport()]
    mock_systems.return_value = [MockSystem(system_name="Core Banking System", rto_target_hours=4.0)]

    response = client.get(f"/api/incidents/{FIXED_UUID}/command-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "incident" in data
    assert "tasks" in data
    assert "task_statistics" in data
    assert "latest_report" in data
    assert "rto_statuses" in data
    assert data["task_statistics"]["total"] == 1
    assert data["task_statistics"]["completed"] == 1
    assert data["task_statistics"]["completion_rate"] == 100.0


@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_command_dashboard_not_found(mock_get: AsyncMock, client) -> None:
    """GET command-dashboard should return 404 for missing incident."""
    mock_get.return_value = None
    response = client.get(f"/api/incidents/{uuid.uuid4()}/command-dashboard")
    assert response.status_code == 404


@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
@patch("apps.crud.get_situation_reports_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident_tasks_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_command_dashboard_no_tasks(
    mock_get_inc: AsyncMock,
    mock_tasks: AsyncMock,
    mock_reports: AsyncMock,
    mock_systems: AsyncMock,
    client,
) -> None:
    """GET /api/incidents/{id}/command-dashboard should return zero-stat TaskStatistics when no tasks exist."""
    mock_get_inc.return_value = MockIncident()
    mock_tasks.return_value = []
    mock_reports.return_value = []
    mock_systems.return_value = []

    response = client.get(f"/api/incidents/{FIXED_UUID}/command-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["task_statistics"]["total"] == 0
    assert data["task_statistics"]["completed"] == 0
    assert data["task_statistics"]["completion_rate"] == 0.0


def test_create_task_invalid_priority(client) -> None:
    """POST task with invalid priority should return 422."""
    payload = {
        "task_title": "Test task",
        "priority": "urgent",  # not valid
    }
    response = client.post(f"/api/incidents/{FIXED_UUID}/tasks", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Edge-case coverage for incident_commander.py uncovered branches
# ---------------------------------------------------------------------------


@patch("apps.crud.create_situation_report", new_callable=AsyncMock)
@patch("apps.crud.get_situation_reports_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
@patch("apps.crud.get_incident_tasks_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_auto_generate_with_empty_tasks(
    mock_get_inc: AsyncMock,
    mock_tasks: AsyncMock,
    mock_systems: AsyncMock,
    mock_reports: AsyncMock,
    mock_create: AsyncMock,
    client,
) -> None:
    """Auto-generate with zero tasks hits TaskStatistics() early return (line 26)."""
    mock_get_inc.return_value = MockIncident()
    mock_tasks.return_value = []  # no tasks → total == 0 branch
    mock_systems.return_value = [MockSystem(system_name="Core Banking System", rto_target_hours=4.0)]
    mock_reports.return_value = []
    mock_create.return_value = MockSituationReport(report_number=2)

    response = client.post(f"/api/incidents/{FIXED_UUID}/situation-reports/auto-generate")
    assert response.status_code == 201
    data = response.json()
    assert data["report_number"] == 2


@patch("apps.crud.create_situation_report", new_callable=AsyncMock)
@patch("apps.crud.get_situation_reports_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
@patch("apps.crud.get_incident_tasks_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_auto_generate_no_affected_systems(
    mock_get_inc: AsyncMock,
    mock_tasks: AsyncMock,
    mock_systems: AsyncMock,
    mock_reports: AsyncMock,
    mock_create: AsyncMock,
    client,
) -> None:
    """Auto-generate with empty affected_systems hits early [] return (line 48)."""
    incident = MockIncident(affected_systems=[])  # empty → _get_rto_statuses returns []
    mock_get_inc.return_value = incident
    mock_tasks.return_value = [MockIncidentTask(status="completed")]
    mock_systems.return_value = []
    mock_reports.return_value = []
    mock_create.return_value = MockSituationReport(report_number=3)

    response = client.post(f"/api/incidents/{FIXED_UUID}/situation-reports/auto-generate")
    assert response.status_code == 201


@patch("apps.crud.create_situation_report", new_callable=AsyncMock)
@patch("apps.crud.get_situation_reports_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
@patch("apps.crud.get_incident_tasks_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_auto_generate_with_blocked_task(
    mock_get_inc: AsyncMock,
    mock_tasks: AsyncMock,
    mock_systems: AsyncMock,
    mock_reports: AsyncMock,
    mock_create: AsyncMock,
    client,
) -> None:
    """Auto-generate with blocked task triggers 'Resolve blocked task(s)' next action (line 131)."""
    mock_get_inc.return_value = MockIncident()
    mock_tasks.return_value = [
        MockIncidentTask(status="blocked"),  # blocked_tasks > 0 branch
        MockIncidentTask(status="pending"),
    ]
    mock_systems.return_value = [MockSystem(system_name="Core Banking System", rto_target_hours=4.0)]
    mock_reports.return_value = []
    mock_create.return_value = MockSituationReport(report_number=4)

    response = client.post(f"/api/incidents/{FIXED_UUID}/situation-reports/auto-generate")
    assert response.status_code == 201


@patch("apps.crud.create_situation_report", new_callable=AsyncMock)
@patch("apps.crud.get_situation_reports_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
@patch("apps.crud.get_incident_tasks_by_incident", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_auto_generate_continue_monitoring_fallback(
    mock_get_inc: AsyncMock,
    mock_tasks: AsyncMock,
    mock_systems: AsyncMock,
    mock_reports: AsyncMock,
    mock_create: AsyncMock,
    client,
) -> None:
    """All tasks completed + no overdue systems → 'Continue monitoring' fallback (line 140)."""
    mock_get_inc.return_value = MockIncident()
    mock_tasks.return_value = [
        MockIncidentTask(status="completed"),
        MockIncidentTask(status="in_progress"),
    ]
    # RTO-compliant system (last_test_rto <= rto_target_hours) → no overdue
    mock_systems.return_value = [MockSystem(system_name="Core Banking System", rto_target_hours=999.0)]
    mock_reports.return_value = []
    mock_create.return_value = MockSituationReport(report_number=5)

    response = client.post(f"/api/incidents/{FIXED_UUID}/situation-reports/auto-generate")
    assert response.status_code == 201
