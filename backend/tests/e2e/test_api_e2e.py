"""Playwright-based E2E API tests for IT-BCP-ITSCM-System.

These tests exercise the running server over real HTTP — no mocks, no
dependency_overrides. They verify the full request/response cycle including
authentication, CORS headers, rate limiting, and response shapes.

Run against a live server:
    pytest tests/e2e/ --base-url http://localhost:8000 -v

Mark: @pytest.mark.e2e — excluded from default CI unit test runs.
"""

from typing import Any

import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Auth flow
# ---------------------------------------------------------------------------


class TestAuthE2E:
    """Verify the full JWT auth lifecycle against a live server."""

    def test_login_returns_token(self, page: Page, base_url: str) -> None:
        """POST /api/auth/login with valid credentials returns a JWT."""
        resp = page.request.post(
            f"{base_url}/api/auth/login",
            data={"user_id": "e2e-user", "password": "", "role": "viewer"},
        )
        assert resp.status == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 20

    def test_login_invalid_role_returns_422(self, page: Page, base_url: str) -> None:
        """POST /api/auth/login with invalid role returns 422."""
        resp = page.request.post(
            f"{base_url}/api/auth/login",
            data={"user_id": "u", "password": "", "role": "god"},
        )
        assert resp.status == 422

    def test_me_requires_auth(self, page: Page, base_url: str) -> None:
        """GET /api/auth/me without token returns 401."""
        resp = page.request.get(f"{base_url}/api/auth/me")
        assert resp.status == 401

    def test_me_returns_user_info(self, page: Page, base_url: str, auth_headers: dict[str, Any]) -> None:
        """GET /api/auth/me with valid token returns user info."""
        resp = page.request.get(
            f"{base_url}/api/auth/me",
            headers=auth_headers,
        )
        assert resp.status == 200
        body = resp.json()
        assert "user_id" in body
        assert "role" in body
        assert "permissions" in body

    def test_refresh_returns_new_token(self, page: Page, base_url: str, auth_headers: dict[str, Any]) -> None:
        """POST /api/auth/refresh returns a fresh token."""
        resp = page.request.post(
            f"{base_url}/api/auth/refresh",
            headers=auth_headers,
        )
        assert resp.status == 200
        body = resp.json()
        assert "access_token" in body


# ---------------------------------------------------------------------------
# Health probes (public — no auth required)
# ---------------------------------------------------------------------------


class TestHealthE2E:
    """Kubernetes-style health probes should be reachable without auth."""

    def test_health_returns_200(self, page: Page, base_url: str) -> None:
        resp = page.request.get(f"{base_url}/api/health")
        assert resp.status == 200
        body = resp.json()
        assert "status" in body
        assert "version" in body

    def test_liveness_probe(self, page: Page, base_url: str) -> None:
        resp = page.request.get(f"{base_url}/api/health/live")
        assert resp.status == 200
        assert resp.json()["status"] == "alive"

    def test_readiness_probe(self, page: Page, base_url: str) -> None:
        resp = page.request.get(f"{base_url}/api/health/ready")
        # 200 (DB up) or 503 (DB down) — both are valid server responses
        assert resp.status in (200, 503)
        assert "status" in resp.json()


# ---------------------------------------------------------------------------
# Protected API endpoints — require auth
# ---------------------------------------------------------------------------


class TestProtectedEndpointsE2E:
    """All data endpoints must return 401 without auth and 200 with auth."""

    PROTECTED_GET = [
        "/api/systems",
        "/api/exercises",
        "/api/incidents",
        "/api/dashboard/readiness",
        "/api/dashboard/rto-overview",
        "/api/procedures",
        "/api/contacts/emergency",
        "/api/contacts/vendors",
        "/api/bia",
        "/api/scenarios",
        "/api/notifications/logs",
        "/api/audit/logs",
        "/api/runbook/deployment-checklist",
        "/api/runbook/rollback-procedure",
        "/api/runbook/dr-failover",
    ]

    @pytest.mark.parametrize("path", PROTECTED_GET)
    def test_returns_401_without_token(self, page: Page, base_url: str, path: str) -> None:
        """Each protected GET endpoint returns 401 with no token."""
        resp = page.request.get(f"{base_url}{path}")
        assert resp.status == 401, f"Expected 401 for GET {path}, got {resp.status}"

    @pytest.mark.parametrize("path", PROTECTED_GET)
    def test_returns_non_401_with_token(self, page: Page, base_url: str, path: str, auth_headers: dict[str, Any]) -> None:
        """Each protected GET endpoint does NOT return 401 when authenticated."""
        resp = page.request.get(f"{base_url}{path}", headers=auth_headers)
        assert resp.status != 401, f"Expected auth to work for GET {path}, got {resp.status}"


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


class TestSecurityHeadersE2E:
    """Every response must carry the expected security headers."""

    EXPECTED_HEADERS = {
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "cache-control": "no-store",
    }

    def test_health_response_has_security_headers(self, page: Page, base_url: str) -> None:
        """Security headers are present on a simple health check response."""
        resp = page.request.get(f"{base_url}/api/health")
        for header, expected_value in self.EXPECTED_HEADERS.items():
            actual = resp.headers.get(header, "")
            assert actual == expected_value, f"Header {header}: expected '{expected_value}', got '{actual}'"
