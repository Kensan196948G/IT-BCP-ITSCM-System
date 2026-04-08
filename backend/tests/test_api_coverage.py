"""API coverage tests: route existence, response format, OpenAPI completeness."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from apps.auth import AuthService
from main import app
from tests.conftest import _mock_admin_user


@pytest.fixture()
def raw_client() -> Generator[TestClient, None, None]:
    """TestClient without DB override -- for schema / route existence checks.

    Auth is overridden so that protected endpoints are reachable (the purpose
    of this fixture is to verify routes exist and return expected shapes, not
    to test authentication behaviour).
    """
    app.dependency_overrides[AuthService.get_current_user] = _mock_admin_user
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.pop(AuthService.get_current_user, None)


# ---------------------------------------------------------------------------
# 1. All API route existence (not 404/405)
# ---------------------------------------------------------------------------

EXPECTED_GET_ROUTES = [
    "/api/health",
    "/api/systems",
    "/api/exercises",
    "/api/incidents",
    "/api/dashboard/readiness",
    "/api/dashboard/rto-overview",
    "/api/procedures",
    "/api/contacts/emergency",
    "/api/contacts/vendors",
    "/api/bia",
    "/api/bia/summary",
    "/api/bia/risk-matrix",
    "/api/scenarios",
    "/api/notifications/logs",
    "/api/runbook/deployment-checklist",
    "/api/runbook/rollback-procedure",
    "/api/runbook/dr-failover",
    "/api/audit/logs",
    "/api/metrics",
    "/api/health/live",
    "/api/health/ready",
    "/api/health/detailed",
    "/api/dashboard/reports/readiness",
    "/api/dashboard/reports/rto-compliance",
    "/api/dashboard/reports/exercise-trends",
    "/api/dashboard/reports/iso20000",
]

EXPECTED_POST_ROUTES = [
    "/api/auth/login",
    "/api/escalation/trigger",
    "/api/notifications/send",
]


class TestRouteExistence:
    """Every registered route should respond (not 404 or 405)."""

    @pytest.mark.parametrize("path", EXPECTED_GET_ROUTES)
    def test_get_route_exists(self, raw_client: TestClient, path: str) -> None:
        resp = raw_client.get(path)
        assert resp.status_code != 404, f"GET {path} returned 404"
        assert resp.status_code != 405, f"GET {path} returned 405"

    @pytest.mark.parametrize("path", EXPECTED_POST_ROUTES)
    def test_post_route_exists(self, raw_client: TestClient, path: str) -> None:
        resp = raw_client.post(path, json={})
        assert resp.status_code != 404, f"POST {path} returned 404"
        assert resp.status_code != 405, f"POST {path} returned 405"


# ---------------------------------------------------------------------------
# 2. Response format checks for major endpoints
# ---------------------------------------------------------------------------


class TestResponseFormat:
    """Major endpoints should return well-structured JSON."""

    def test_health_returns_status_field(self, raw_client: TestClient) -> None:
        data = raw_client.get("/api/health").json()
        assert "status" in data
        assert "version" in data

    def test_health_live_returns_json(self, raw_client: TestClient) -> None:
        resp = raw_client.get("/api/health/live")
        assert resp.status_code == 200
        assert "status" in resp.json()

    def test_health_ready_returns_json(self, raw_client: TestClient) -> None:
        resp = raw_client.get("/api/health/ready")
        # May be 200 or 503 depending on DB
        assert resp.status_code in (200, 503)
        assert "status" in resp.json()

    def test_metrics_returns_text(self, raw_client: TestClient) -> None:
        resp = raw_client.get("/api/metrics")
        assert resp.status_code == 200

    def test_login_returns_token_on_success(self, raw_client: TestClient) -> None:
        resp = raw_client.post(
            "/api/auth/login",
            json={"user_id": "test_user", "password": "test", "role": "admin"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_role_returns_422(self, raw_client: TestClient) -> None:
        resp = raw_client.post(
            "/api/auth/login",
            json={"user_id": "u", "password": "", "role": "invalid_role"},
        )
        assert resp.status_code == 422

    def test_runbook_deployment_checklist_format(self, raw_client: TestClient) -> None:
        resp = raw_client.get("/api/runbook/deployment-checklist")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_runbook_rollback_format(self, raw_client: TestClient) -> None:
        resp = raw_client.get("/api/runbook/rollback-procedure")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_runbook_dr_failover_format(self, raw_client: TestClient) -> None:
        resp = raw_client.get("/api/runbook/dr-failover")
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_escalation_plan_returns_json(self, raw_client: TestClient) -> None:
        resp = raw_client.get("/api/escalation/plan/p1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# 3. OpenAPI schema completeness
# ---------------------------------------------------------------------------

# All routes that MUST appear in OpenAPI paths
MUST_HAVE_PATHS = [
    "/api/health",
    "/api/systems",
    "/api/systems/{system_id}",
    "/api/exercises",
    "/api/exercises/{exercise_id}",
    "/api/incidents",
    "/api/incidents/{incident_id}",
    "/api/dashboard/readiness",
    "/api/dashboard/rto-overview",
    "/api/procedures",
    "/api/procedures/{procedure_id}",
    "/api/contacts/emergency",
    "/api/contacts/vendors",
    "/api/bia",
    "/api/bia/{assessment_id}",
    "/api/scenarios",
    "/api/scenarios/{scenario_id}",
    "/api/notifications/send",
    "/api/notifications/logs",
    "/api/auth/login",
    "/api/auth/me",
    "/api/audit/logs",
    "/api/runbook/deployment-checklist",
    "/api/metrics",
    "/api/escalation/trigger",
]


class TestOpenAPICoverage:
    """OpenAPI schema should document all registered routes."""

    @pytest.fixture(autouse=True)
    def _load_schema(self, raw_client: TestClient) -> None:
        self.schema = raw_client.get("/openapi.json").json()
        self.paths = self.schema["paths"]

    @pytest.mark.parametrize("path", MUST_HAVE_PATHS)
    def test_path_in_openapi(self, path: str) -> None:
        assert path in self.paths, f"{path} missing from OpenAPI schema"

    def test_all_tags_documented(self) -> None:
        tag_names = {t["name"] for t in self.schema.get("tags", [])}
        expected = {
            "systems",
            "exercises",
            "incidents",
            "dashboard",
            "recovery-procedures",
            "contacts",
            "bia",
            "scenarios",
            "notifications",
            "monitoring",
            "runbook",
            "auth",
            "audit",
        }
        missing = expected - tag_names
        assert not missing, f"Missing tags: {missing}"

    def test_openapi_version_is_3(self) -> None:
        assert self.schema["openapi"].startswith("3.")

    def test_schema_has_components(self) -> None:
        assert "components" in self.schema
        assert "schemas" in self.schema["components"]

    def test_paths_have_methods(self) -> None:
        """Every path should define at least one HTTP method."""
        for path, methods in self.paths.items():
            http_methods = {k for k in methods.keys() if k in ("get", "post", "put", "delete", "patch")}
            assert http_methods, f"{path} has no HTTP methods defined"
