"""Tests for Active Incident API endpoints (mocked DB)."""

import uuid
from unittest.mock import AsyncMock, patch

from tests.conftest import FIXED_UUID, MockIncident, MockSystem, sample_incident_payload

# ---------------------------------------------------------------------------
# GET /api/incidents  (list)
# ---------------------------------------------------------------------------


@patch("apps.crud.get_all_incidents", new_callable=AsyncMock)
def test_list_incidents(mock_get_all: AsyncMock, client) -> None:
    """GET /api/incidents should return a list of incidents."""
    mock_get_all.return_value = [MockIncident()]
    response = client.get("/api/incidents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["incident_id"] == "BCP-2026-001"


# ---------------------------------------------------------------------------
# POST /api/incidents  (create)
# ---------------------------------------------------------------------------


@patch("apps.crud.create_incident", new_callable=AsyncMock)
def test_create_incident(mock_create: AsyncMock, client) -> None:
    """POST /api/incidents should create and return the incident."""
    mock_create.return_value = MockIncident()
    payload = sample_incident_payload()
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "DC power failure"
    assert data["severity"] == "p1"


def test_create_incident_invalid_severity(client) -> None:
    """POST /api/incidents should reject invalid severity."""
    payload = sample_incident_payload()
    payload["severity"] = "critical"  # not p1/p2/p3
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/incidents/{id}  (detail)
# ---------------------------------------------------------------------------


@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_get_incident(mock_get: AsyncMock, client) -> None:
    """GET /api/incidents/{id} should return the incident."""
    mock_get.return_value = MockIncident()
    response = client.get(f"/api/incidents/{FIXED_UUID}")
    assert response.status_code == 200
    assert response.json()["scenario_type"] == "dc_failure"


@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_get_incident_not_found(mock_get: AsyncMock, client) -> None:
    """GET /api/incidents/{id} should return 404 when not found."""
    mock_get.return_value = None
    response = client.get(f"/api/incidents/{uuid.uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/incidents/{id}  (update)
# ---------------------------------------------------------------------------


@patch("apps.crud.update_incident", new_callable=AsyncMock)
def test_update_incident(mock_update: AsyncMock, client) -> None:
    """PUT /api/incidents/{id} should update and return the incident."""
    mock_update.return_value = MockIncident(status="resolved", actual_rto_hours=3.5)
    response = client.put(
        f"/api/incidents/{FIXED_UUID}",
        json={"status": "resolved", "actual_rto_hours": 3.5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"


# ---------------------------------------------------------------------------
# GET /api/incidents/{id}/rto-dashboard
# ---------------------------------------------------------------------------


@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_incident_rto_dashboard(mock_get_inc: AsyncMock, mock_get_sys: AsyncMock, client) -> None:
    """GET /api/incidents/{id}/rto-dashboard should return RTO statuses."""
    mock_get_inc.return_value = MockIncident(affected_systems=["Core Banking System"])
    mock_get_sys.return_value = [MockSystem(system_name="Core Banking System", rto_target_hours=4.0)]

    response = client.get(f"/api/incidents/{FIXED_UUID}/rto-dashboard")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["system_name"] == "Core Banking System"


@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_incident_rto_dashboard_not_found(mock_get: AsyncMock, client) -> None:
    """GET /api/incidents/{id}/rto-dashboard should return 404 for missing incident."""
    mock_get.return_value = None
    response = client.get(f"/api/incidents/{uuid.uuid4()}/rto-dashboard")
    assert response.status_code == 404


@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_incident_rto_dashboard_no_affected_systems(mock_get_inc: AsyncMock, mock_get_sys: AsyncMock, client) -> None:
    """GET /api/incidents/{id}/rto-dashboard returns [] when no affected_systems (line 87)."""
    mock_get_inc.return_value = MockIncident(affected_systems=[])
    response = client.get(f"/api/incidents/{FIXED_UUID}/rto-dashboard")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# PUT /api/incidents/{id}  (update) — not found
# ---------------------------------------------------------------------------


@patch("apps.crud.update_incident", new_callable=AsyncMock)
def test_update_incident_not_found(mock_update: AsyncMock, client) -> None:
    """PUT /api/incidents/{id} should return 404 when update returns None (line 71)."""
    mock_update.return_value = None
    response = client.put(
        f"/api/incidents/{uuid.uuid4()}",
        json={"status": "resolved"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/incidents/{id}/tasks/{task_id}  — incident not found
# ---------------------------------------------------------------------------


@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_update_incident_task_incident_not_found(mock_get: AsyncMock, client) -> None:
    """PUT /api/incidents/{id}/tasks/{task_id} returns 404 when incident missing (line 178)."""
    mock_get.return_value = None
    response = client.put(
        f"/api/incidents/{FIXED_UUID}/tasks/{FIXED_UUID}",
        json={"status": "completed"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/incidents/{id}/situation-reports  — incident not found
# ---------------------------------------------------------------------------


@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_create_situation_report_incident_not_found(mock_get: AsyncMock, client) -> None:
    """POST /api/incidents/{id}/situation-reports returns 404 when incident missing (line 203)."""
    mock_get.return_value = None
    response = client.post(
        f"/api/incidents/{FIXED_UUID}/situation-reports",
        json={"report_number": 1, "summary": "Status update"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/incidents/{id}/situation-reports  — incident not found
# ---------------------------------------------------------------------------


@patch("apps.crud.get_incident", new_callable=AsyncMock)
def test_list_situation_reports_incident_not_found(mock_get: AsyncMock, client) -> None:
    """GET /api/incidents/{id}/situation-reports returns 404 when incident missing (line 220)."""
    mock_get.return_value = None
    response = client.get(f"/api/incidents/{FIXED_UUID}/situation-reports")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/incidents/escalation/plan/{severity}
# ---------------------------------------------------------------------------


def test_get_escalation_plan_p1(client) -> None:
    """GET /api/incidents/escalation/plan/p1 returns P1 Full BCP plan."""
    response = client.get("/api/incidents/escalation/plan/p1")
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "p1"
    assert data["plan_name"] == "P1 Full BCP Activation"
    assert len(data["levels"]) == 4


def test_get_escalation_plan_p2(client) -> None:
    """GET /api/incidents/escalation/plan/p2 returns P2 Partial BCP plan."""
    response = client.get("/api/incidents/escalation/plan/p2")
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "p2"
    assert len(data["levels"]) == 2


def test_get_escalation_plan_p3(client) -> None:
    """GET /api/incidents/escalation/plan/p3 returns P3 Monitoring plan."""
    response = client.get("/api/incidents/escalation/plan/p3")
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "p3"
    assert len(data["levels"]) == 1


def test_get_escalation_plan_unknown_severity(client) -> None:
    """GET /api/incidents/escalation/plan/p9 returns 404 for unknown severity."""
    response = client.get("/api/incidents/escalation/plan/p9")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/incidents/escalation/trigger
# ---------------------------------------------------------------------------


def test_trigger_escalation_p1(client) -> None:
    """POST /api/incidents/escalation/trigger triggers P1 escalation notifications."""
    payload = {
        "incident_id": str(FIXED_UUID),
        "severity": "p1",
        "contacts": [
            {"role": "IT部門長", "name": "田中部長", "email": "tanaka@example.com"},
        ],
    }
    response = client.post("/api/incidents/escalation/trigger", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["severity"] == "p1"
    assert data["plan_name"] == "P1 Full BCP Activation"
    assert data["notifications_queued"] > 0


def test_trigger_escalation_invalid_severity(client) -> None:
    """POST /api/incidents/escalation/trigger rejects invalid severity."""
    payload = {
        "incident_id": str(FIXED_UUID),
        "severity": "p9",
        "contacts": [],
    }
    response = client.post("/api/incidents/escalation/trigger", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/incidents/escalation/status/{incident_id}
# ---------------------------------------------------------------------------


def test_get_escalation_status_empty(client) -> None:
    """GET /api/incidents/escalation/status/{id} returns empty status for unknown incident."""
    response = client.get(f"/api/incidents/escalation/status/{uuid.uuid4()}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_notifications"] == 0
    assert data["sent"] == 0


def test_get_escalation_status_after_trigger(client) -> None:
    """GET /api/incidents/escalation/status returns notifications after trigger."""
    trigger_payload = {
        "incident_id": str(FIXED_UUID),
        "severity": "p2",
        "contacts": [],
    }
    client.post("/api/incidents/escalation/trigger", json=trigger_payload)

    response = client.get(f"/api/incidents/escalation/status/{FIXED_UUID}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_notifications"] >= 0


# ---------------------------------------------------------------------------
# POST /api/incidents/notifications/send
# ---------------------------------------------------------------------------


def test_send_notification_teams(client) -> None:
    """POST /api/incidents/notifications/send sends a Teams notification (dry-run)."""
    payload = {
        "notification_type": "teams",
        "recipient": "teams-channel-001",
        "subject": "BCP Drill Test",
        "body": "This is a dry-run notification test.",
        "incident_id": str(FIXED_UUID),
    }
    response = client.post("/api/incidents/notifications/send", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["notification_type"] == "teams"
    assert data["recipient"] == "teams-channel-001"
    assert data["status"] in ("sent", "pending", "failed")


def test_send_notification_invalid_type(client) -> None:
    """POST /api/incidents/notifications/send rejects invalid notification_type."""
    payload = {
        "notification_type": "slack",
        "recipient": "someone",
        "subject": "Test",
        "body": "Test body",
    }
    response = client.post("/api/incidents/notifications/send", json=payload)
    assert response.status_code == 422
