"""Tests for audit log service and API."""

from fastapi.testclient import TestClient

from apps.audit_service import AuditService


# ---------------------------------------------------------------------------
# AuditService unit tests
# ---------------------------------------------------------------------------


class TestAuditService:
    """Unit tests for the AuditService class."""

    def setup_method(self):
        self.svc = AuditService()

    def test_log_creates_entry(self):
        entry = self.svc.log(
            action="create",
            resource_type="system",
            user_id="admin1",
            role="admin",
        )
        assert entry["action"] == "create"
        assert entry["resource_type"] == "system"
        assert entry["user_id"] == "admin1"
        assert entry["status"] == "success"
        assert "id" in entry
        assert "timestamp" in entry

    def test_get_logs_returns_entries(self):
        self.svc.log(action="create", resource_type="system")
        self.svc.log(action="read", resource_type="incident")
        logs = self.svc.get_logs()
        assert len(logs) == 2

    def test_get_logs_filter_by_action(self):
        self.svc.log(action="create", resource_type="system")
        self.svc.log(action="read", resource_type="system")
        self.svc.log(action="delete", resource_type="system")
        logs = self.svc.get_logs(action="create")
        assert len(logs) == 1
        assert logs[0]["action"] == "create"

    def test_get_logs_filter_by_resource_type(self):
        self.svc.log(action="create", resource_type="system")
        self.svc.log(action="create", resource_type="incident")
        logs = self.svc.get_logs(resource_type="incident")
        assert len(logs) == 1

    def test_get_logs_filter_by_user_id(self):
        self.svc.log(action="create", resource_type="system", user_id="admin1")
        self.svc.log(action="read", resource_type="system", user_id="viewer1")
        logs = self.svc.get_logs(user_id="admin1")
        assert len(logs) == 1

    def test_get_logs_limit(self):
        for i in range(10):
            self.svc.log(action="read", resource_type="system")
        logs = self.svc.get_logs(limit=3)
        assert len(logs) == 3

    def test_get_logs_by_incident(self):
        self.svc.log(
            action="create",
            resource_type="incident",
            resource_id="INC-001",
        )
        self.svc.log(
            action="update",
            resource_type="incident",
            resource_id="INC-001",
        )
        self.svc.log(
            action="create",
            resource_type="incident",
            resource_id="INC-002",
        )
        logs = self.svc.get_logs_by_incident("INC-001")
        assert len(logs) == 2

    def test_export_logs_json(self):
        self.svc.log(action="login", resource_type="auth")
        export = self.svc.export_logs(fmt="json")
        assert export["format"] == "json"
        assert export["total_count"] == 1
        assert export["standard"] == "ISO20000-ITSCM"
        assert len(export["logs"]) == 1

    def test_log_with_details(self):
        entry = self.svc.log(
            action="escalation",
            resource_type="incident",
            resource_id="INC-001",
            details={"level": 3, "target": "CISO"},
            status="success",
        )
        assert entry["details"]["level"] == 3

    def test_log_failure_status(self):
        entry = self.svc.log(
            action="login",
            resource_type="auth",
            status="failure",
        )
        assert entry["status"] == "failure"


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestAuditAPI:
    """API-level audit log tests."""

    def test_get_audit_logs_empty(self, client: TestClient):
        resp = client.get("/api/audit/logs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_export_audit_logs(self, client: TestClient):
        resp = client.get("/api/audit/logs/export")
        assert resp.status_code == 200
        data = resp.json()
        assert "exported_at" in data
        assert "total_count" in data
        assert data["standard"] == "ISO20000-ITSCM"

    def test_get_incident_logs(self, client: TestClient):
        resp = client.get("/api/audit/logs/incident/INC-001")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
