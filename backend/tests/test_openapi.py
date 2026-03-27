"""Tests for OpenAPI schema and documentation endpoints."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture()
def raw_client():
    """TestClient without DB override -- only hitting docs/openapi endpoints."""
    return TestClient(app, raise_server_exceptions=False)


class TestOpenAPIDocs:
    """Verify /docs and /openapi.json are accessible and correct."""

    def test_docs_endpoint_exists(self, raw_client: TestClient) -> None:
        """GET /docs should return 200 with HTML."""
        response = raw_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_json_returns_json(self, raw_client: TestClient) -> None:
        """GET /openapi.json should return valid JSON."""
        response = raw_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_openapi_info_metadata(self, raw_client: TestClient) -> None:
        """OpenAPI info block should contain correct title and version."""
        data = raw_client.get("/openapi.json").json()
        info = data["info"]
        assert info["title"] == "IT-BCP-ITSCM-System API"
        assert info["version"] == "0.1.0"
        assert "ISO20000" in info["description"] or "BCP" in info["description"]

    def test_openapi_contains_system_routes(self, raw_client: TestClient) -> None:
        """OpenAPI paths should include /api/systems endpoints."""
        paths = raw_client.get("/openapi.json").json()["paths"]
        assert "/api/systems" in paths
        assert "/api/systems/{system_id}" in paths

    def test_openapi_contains_exercise_routes(self, raw_client: TestClient) -> None:
        """OpenAPI paths should include /api/exercises endpoints."""
        paths = raw_client.get("/openapi.json").json()["paths"]
        assert "/api/exercises" in paths
        assert "/api/exercises/{exercise_id}" in paths

    def test_openapi_contains_incident_routes(self, raw_client: TestClient) -> None:
        """OpenAPI paths should include /api/incidents endpoints."""
        paths = raw_client.get("/openapi.json").json()["paths"]
        assert "/api/incidents" in paths
        assert "/api/incidents/{incident_id}" in paths

    def test_openapi_contains_dashboard_routes(self, raw_client: TestClient) -> None:
        """OpenAPI paths should include /api/dashboard endpoints."""
        paths = raw_client.get("/openapi.json").json()["paths"]
        assert "/api/dashboard/readiness" in paths
        assert "/api/dashboard/rto-overview" in paths

    def test_openapi_contains_health_route(self, raw_client: TestClient) -> None:
        """OpenAPI paths should include /api/health."""
        paths = raw_client.get("/openapi.json").json()["paths"]
        assert "/api/health" in paths

    def test_openapi_tags_present(self, raw_client: TestClient) -> None:
        """OpenAPI schema should include tag definitions."""
        data = raw_client.get("/openapi.json").json()
        assert "tags" in data
        tag_names = [t["name"] for t in data["tags"]]
        assert "systems" in tag_names
        assert "exercises" in tag_names
        assert "incidents" in tag_names
        assert "dashboard" in tag_names
