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
