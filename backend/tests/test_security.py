"""Security middleware, headers, CORS and error handler tests."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from database import get_db
from main import app


def _fake_db_generator():
    async def _gen():
        yield AsyncMock()

    return _gen


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = _fake_db_generator()
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


# ---- Security headers ----


class TestSecurityHeaders:
    """Verify security headers are present on every response."""

    def test_x_content_type_options(self, client: TestClient):
        resp = client.get("/api/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self, client: TestClient):
        resp = client.get("/api/health")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_x_xss_protection(self, client: TestClient):
        resp = client.get("/api/health")
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_strict_transport_security(self, client: TestClient):
        resp = client.get("/api/health")
        assert "max-age=31536000" in resp.headers.get("Strict-Transport-Security", "")

    def test_cache_control(self, client: TestClient):
        resp = client.get("/api/health")
        assert resp.headers.get("Cache-Control") == "no-store"

    def test_content_security_policy(self, client: TestClient):
        resp = client.get("/api/health")
        assert resp.headers.get("Content-Security-Policy") == "default-src 'self'"


# ---- CORS ----


class TestCORS:
    """Basic CORS behaviour."""

    def test_cors_allowed_origin(self, client: TestClient):
        resp = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_disallowed_origin(self, client: TestClient):
        resp = client.options(
            "/api/health",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in resp.headers


# ---- Error handlers ----


class TestErrorHandlers:
    """Validate custom error handlers."""

    def test_validation_error_422(self, client: TestClient):
        """POST with invalid body should return 422."""
        resp = client.post(
            "/api/systems",
            json={"system_name": "", "system_type": "invalid"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert "detail" in body

    def test_not_found_404(self, client: TestClient):
        """Non-existent route should return 404."""
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
        body = resp.json()
        assert "detail" in body


# ---- Health check ----


class TestHealthCheck:
    """Health endpoint should return extended info."""

    def test_health_contains_environment(self, client: TestClient):
        resp = client.get("/api/health")
        body = resp.json()
        assert "environment" in body

    def test_health_contains_version(self, client: TestClient):
        resp = client.get("/api/health")
        body = resp.json()
        assert "version" in body
        assert body["version"] == "0.1.0"

    def test_health_contains_database_status(self, client: TestClient):
        resp = client.get("/api/health")
        body = resp.json()
        assert "database" in body
        assert body["database"] in ("connected", "disconnected")
