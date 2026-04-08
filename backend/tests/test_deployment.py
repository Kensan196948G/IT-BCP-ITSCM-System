"""Deployment readiness tests.

Verify that critical API endpoints respond correctly and the application
is properly configured for deployment.
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health_returns_200() -> None:
    """GET /api/health should return 200."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_contains_required_fields() -> None:
    """Health response must include environment, version, and database."""
    data = client.get("/api/health").json()
    assert "environment" in data
    assert "version" in data
    assert "database" in data


def test_openapi_json_accessible() -> None:
    """GET /openapi.json should be retrievable."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data


def test_main_routes_not_404() -> None:
    """Each major route prefix should not return 404 (method may differ)."""
    routes = [
        "/api/health",
        "/api/systems",
        "/api/exercises",
        "/api/incidents",
        "/api/dashboard/readiness",
    ]
    for route in routes:
        response = client.get(route)
        assert response.status_code != 404, f"{route} returned 404"


def test_docs_endpoint_accessible() -> None:
    """GET /docs should be available for API documentation."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
