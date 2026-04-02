"""Tests for BCP scenario CRUD endpoints — error paths and edge cases."""

import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from tests.conftest import FIXED_UUID


class MockScenario:
    """Mock object mimicking a BCPScenario ORM instance."""

    def __init__(self, **overrides: object) -> None:
        from tests.conftest import FIXED_NOW

        defaults = {
            "id": FIXED_UUID,
            "scenario_id": "SCN-2026-001",
            "title": "DC Failure Scenario",
            "scenario_type": "dc_failure",
            "severity": "critical",
            "description": "Data center power failure",
            "affected_systems": ["AD", "File Server"],
            "mitigation_steps": ["Activate backup power", "Failover to DR site"],
            "is_active": True,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(self, k, v)

    def model_dump(self) -> dict:
        return self.__dict__


class TestScenarioErrorPaths:
    """Test 404 and other error paths for scenario endpoints."""

    def test_get_scenario_not_found(self, client: TestClient) -> None:
        """GET /api/scenarios/{id} returns 404 when scenario does not exist."""
        nonexistent_id = uuid.uuid4()

        with patch("apps.crud.get_scenario", new_callable=AsyncMock, return_value=None):
            resp = client.get(f"/api/scenarios/{nonexistent_id}")

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Scenario not found"

    def test_update_scenario_not_found(self, client: TestClient) -> None:
        """PUT /api/scenarios/{id} returns 404 when scenario does not exist."""
        nonexistent_id = uuid.uuid4()

        with patch("apps.crud.update_scenario", new_callable=AsyncMock, return_value=None):
            resp = client.put(
                f"/api/scenarios/{nonexistent_id}",
                json={"title": "Updated Title"},
            )

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Scenario not found"

    def test_delete_scenario_not_found(self, client: TestClient) -> None:
        """DELETE /api/scenarios/{id} returns 404 when scenario does not exist."""
        nonexistent_id = uuid.uuid4()

        with patch("apps.crud.delete_scenario", new_callable=AsyncMock, return_value=False):
            resp = client.delete(f"/api/scenarios/{nonexistent_id}")

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Scenario not found"

    def test_list_scenarios_empty(self, client: TestClient) -> None:
        """GET /api/scenarios returns empty list when no records exist."""
        with patch("apps.crud.get_all_scenarios", new_callable=AsyncMock, return_value=[]):
            resp = client.get("/api/scenarios")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_scenarios_pagination(self, client: TestClient) -> None:
        """GET /api/scenarios with skip/limit query params returns 200."""
        with patch("apps.crud.get_all_scenarios", new_callable=AsyncMock, return_value=[]):
            resp = client.get("/api/scenarios?skip=0&limit=10")

        assert resp.status_code == 200

    def test_list_scenarios_invalid_skip(self, client: TestClient) -> None:
        """GET /api/scenarios with negative skip returns 422."""
        resp = client.get("/api/scenarios?skip=-1")
        assert resp.status_code == 422

    def test_list_scenarios_invalid_limit(self, client: TestClient) -> None:
        """GET /api/scenarios with limit > 500 returns 422."""
        resp = client.get("/api/scenarios?limit=501")
        assert resp.status_code == 422
