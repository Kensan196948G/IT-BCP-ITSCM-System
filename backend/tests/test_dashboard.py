"""Tests for Dashboard API endpoints (mocked DB)."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from tests.conftest import MockExercise, MockIncident, MockSystem

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
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client: TestClient
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
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client: TestClient
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
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client: TestClient
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
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client: TestClient
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
    mock_systems: AsyncMock, mock_incidents: AsyncMock, _sc: AsyncMock, _gc: AsyncMock, client: TestClient
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


# ---------------------------------------------------------------------------
# GET /api/dashboard/reports/{report_type}/pdf
# ---------------------------------------------------------------------------


@patch("apps.crud.get_all_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_exercises", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_export_report_pdf_readiness(
    mock_systems: AsyncMock, mock_exercises: AsyncMock, mock_incidents: AsyncMock, client: TestClient
) -> None:
    """GET /api/dashboard/reports/readiness/pdf returns a PDF file."""
    mock_systems.return_value = [MockSystem()]
    mock_exercises.return_value = [MockExercise()]
    mock_incidents.return_value = [MockIncident()]

    response = client.get("/api/dashboard/reports/readiness/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert "bcp_readiness_report.pdf" in response.headers["content-disposition"]
    # Verify the response body is a real PDF (starts with %PDF)
    assert response.content[:4] == b"%PDF"


@patch("apps.crud.get_all_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_exercises", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_export_report_pdf_rto_compliance(
    mock_systems: AsyncMock, mock_exercises: AsyncMock, mock_incidents: AsyncMock, client: TestClient
) -> None:
    """GET /api/dashboard/reports/rto-compliance/pdf returns a PDF file."""
    mock_systems.return_value = [MockSystem()]
    mock_exercises.return_value = []
    mock_incidents.return_value = []

    response = client.get("/api/dashboard/reports/rto-compliance/pdf")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert "rto_compliance_report.pdf" in response.headers["content-disposition"]


@patch("apps.crud.get_all_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_exercises", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_export_report_pdf_exercise_trends(
    mock_systems: AsyncMock, mock_exercises: AsyncMock, mock_incidents: AsyncMock, client: TestClient
) -> None:
    """GET /api/dashboard/reports/exercise-trends/pdf returns a PDF file."""
    mock_systems.return_value = []
    mock_exercises.return_value = [MockExercise()]
    mock_incidents.return_value = []

    response = client.get("/api/dashboard/reports/exercise-trends/pdf")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert "exercise_trend_report.pdf" in response.headers["content-disposition"]


@patch("apps.crud.get_all_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_exercises", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_export_report_pdf_iso20000(
    mock_systems: AsyncMock, mock_exercises: AsyncMock, mock_incidents: AsyncMock, client: TestClient
) -> None:
    """GET /api/dashboard/reports/iso20000/pdf returns a PDF file."""
    mock_systems.return_value = []
    mock_exercises.return_value = []
    mock_incidents.return_value = []

    response = client.get("/api/dashboard/reports/iso20000/pdf")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert "iso20000_compliance_report.pdf" in response.headers["content-disposition"]


@patch("apps.crud.get_all_incidents", new_callable=AsyncMock)
@patch("apps.crud.get_all_exercises", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_export_report_pdf_unknown_type(
    mock_systems: AsyncMock, mock_exercises: AsyncMock, mock_incidents: AsyncMock, client: TestClient
) -> None:
    """GET /api/dashboard/reports/unknown/pdf returns 404."""
    mock_systems.return_value = []
    mock_exercises.return_value = []
    mock_incidents.return_value = []

    response = client.get("/api/dashboard/reports/unknown-type/pdf")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/dashboard/statistics
# ---------------------------------------------------------------------------


@patch("apps.crud.get_bcp_statistics", new_callable=AsyncMock)
def test_get_statistics_empty(mock_stats: AsyncMock, client: TestClient) -> None:
    """GET /api/dashboard/statistics returns 200 with all expected fields."""
    mock_stats.return_value = {
        "total_systems": 0,
        "systems_by_criticality": {},
        "avg_rto_target_hours": None,
        "total_incidents": 0,
        "active_incidents": 0,
        "resolved_incidents": 0,
        "mttr_hours": None,
        "rto_breach_count": 0,
        "rto_breach_rate": None,
    }
    response = client.get("/api/dashboard/statistics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_systems"] == 0
    assert data["rto_breach_count"] == 0
    assert data["mttr_hours"] is None


@patch("apps.crud.get_bcp_statistics", new_callable=AsyncMock)
def test_get_statistics_with_data(mock_stats: AsyncMock, client: TestClient) -> None:
    """GET /api/dashboard/statistics returns computed MTTR and breach rate."""
    mock_stats.return_value = {
        "total_systems": 5,
        "systems_by_criticality": {"tier1": 2, "tier2": 3},
        "avg_rto_target_hours": 6.0,
        "total_incidents": 10,
        "active_incidents": 2,
        "resolved_incidents": 8,
        "mttr_hours": 3.5,
        "rto_breach_count": 2,
        "rto_breach_rate": 0.25,
    }
    response = client.get("/api/dashboard/statistics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_systems"] == 5
    assert data["systems_by_criticality"]["tier1"] == 2
    assert data["avg_rto_target_hours"] == 6.0
    assert data["mttr_hours"] == 3.5
    assert data["rto_breach_rate"] == 0.25
