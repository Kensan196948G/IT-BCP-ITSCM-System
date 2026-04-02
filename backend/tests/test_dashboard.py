"""Tests for Dashboard API endpoints (mocked DB)."""

from unittest.mock import AsyncMock, patch

from tests.conftest import MockIncident, MockSystem

# Cache is always bypassed in unit tests — Redis may be running locally and
# would serve stale data across test runs, breaking test isolation.
_patch_cache = patch("apps.routers.dashboard.get_cached", new_callable=AsyncMock, return_value=None)
_patch_set_cache = patch("apps.routers.dashboard.set_cached", new_callable=AsyncMock)

# ---------------------------------------------------------------------------
# GET /api/dashboard/readiness
# ---------------------------------------------------------------------------


@_patch_cache
@_patch_set_cache
@patch("apps.crud.get_active_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_readiness_no_incidents(
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client
) -> None:
    """Readiness endpoint should return 100% when there are no active incidents."""
    mock_systems.return_value = [MockSystem(), MockSystem(system_name="Email System", rto_target_hours=8.0)]
    mock_incidents.return_value = []

    response = client.get("/api/dashboard/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["total_systems"] == 2
    assert data["active_incidents"] == 0
    assert data["readiness_score"] == 100.0


@_patch_cache
@_patch_set_cache
@patch("apps.crud.get_active_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_readiness_with_incident(
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client
) -> None:
    """Readiness endpoint should reflect active incident impact."""
    mock_systems.return_value = [MockSystem()]
    mock_incidents.return_value = [MockIncident(affected_systems=["Core Banking System"])]

    response = client.get("/api/dashboard/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["active_incidents"] == 1
    assert len(data["rto_statuses"]) == 1


# ---------------------------------------------------------------------------
# GET /api/dashboard/rto-overview
# ---------------------------------------------------------------------------


@patch("apps.routers.dashboard.get_cached", new_callable=AsyncMock, return_value=None)
@patch("apps.routers.dashboard.set_cached", new_callable=AsyncMock)
@patch("apps.crud.get_active_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_rto_overview(
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client
) -> None:
    """RTO overview should list all systems with their RTO status."""
    mock_systems.return_value = [
        MockSystem(system_name="System A", rto_target_hours=4.0),
        MockSystem(system_name="System B", rto_target_hours=8.0),
    ]
    mock_incidents.return_value = []

    response = client.get("/api/dashboard/rto-overview")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    names = {item["system_name"] for item in data}
    assert names == {"System A", "System B"}


@patch("apps.routers.dashboard.get_cached", new_callable=AsyncMock, return_value=None)
@patch("apps.routers.dashboard.set_cached", new_callable=AsyncMock)
@patch("apps.crud.get_active_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_rto_overview_empty(
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client
) -> None:
    """RTO overview should return empty list when no systems exist."""
    mock_systems.return_value = []
    mock_incidents.return_value = []

    response = client.get("/api/dashboard/rto-overview")
    assert response.status_code == 200
    assert response.json() == []


@patch("apps.routers.dashboard.get_cached", new_callable=AsyncMock, return_value=None)
@patch("apps.routers.dashboard.set_cached", new_callable=AsyncMock)
@patch("apps.crud.get_active_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_rto_overview_with_matching_incident(
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client
) -> None:
    """RTO overview builds RTOTracker from matched incident (covers lines 57-59, 65)."""
    mock_systems.return_value = [MockSystem(system_name="Core Banking System", rto_target_hours=4.0)]
    mock_incidents.return_value = [MockIncident(affected_systems=["Core Banking System"])]

    response = client.get("/api/dashboard/rto-overview")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["system_name"] == "Core Banking System"
    # When incident exists, RTOTracker uses occurred_at so status is not "not_started"
    assert data[0]["status"] in ("on_track", "at_risk", "overdue")
