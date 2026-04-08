"""Tests for notification service, escalation engine, and notification API routes."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from apps.escalation_engine import EscalationEngine
from apps.notification_service import NotificationService

# ---------------------------------------------------------------------------
# NotificationService tests
# ---------------------------------------------------------------------------


class TestNotificationService:
    """Tests for the NotificationService class."""

    def test_send_notification_teams_dry_run(self) -> None:
        """Test sending a Teams notification in dry_run mode."""
        svc = NotificationService(dry_run=True)
        log = svc.send_notification(
            notification_type="teams",
            recipient="https://webhook.example.com/test",
            subject="Test Alert",
            body="Something happened",
        )
        assert log["status"] == "sent"
        assert log["notification_type"] == "teams"
        assert log["subject"] == "Test Alert"
        assert log["sent_at"] is not None
        assert log["error_message"] is None

    def test_send_notification_email_dry_run(self) -> None:
        """Test sending an email notification in dry_run mode."""
        svc = NotificationService(dry_run=True)
        log = svc.send_notification(
            notification_type="email",
            recipient="admin@example.com",
            subject="Incident Report",
            body="Details here",
        )
        assert log["status"] == "sent"
        assert log["notification_type"] == "email"
        assert log["recipient"] == "admin@example.com"

    def test_send_notification_sms_dry_run(self) -> None:
        """Test sending an SMS notification in dry_run mode."""
        svc = NotificationService(dry_run=True)
        log = svc.send_notification(
            notification_type="sms",
            recipient="+81-90-1234-5678",
            subject="Alert",
            body="Emergency",
        )
        assert log["status"] == "sent"

    def test_send_notification_unknown_type(self) -> None:
        """Test sending a notification with unknown type."""
        svc = NotificationService(dry_run=True)
        log = svc.send_notification(
            notification_type="pigeon",
            recipient="park",
            subject="Help",
            body="Emergency",
        )
        assert log["status"] == "failed"
        assert "Unknown type" in log["error_message"]

    def test_logs_accumulate(self) -> None:
        """Test that notification logs accumulate correctly."""
        svc = NotificationService(dry_run=True)
        svc.send_notification("teams", "url", "Sub1", "Body1")
        svc.send_notification("email", "a@b.com", "Sub2", "Body2")
        svc.send_notification("teams", "url2", "Sub3", "Body3")
        assert len(svc.logs) == 3
        assert svc.logs[0]["subject"] == "Sub1"
        assert svc.logs[2]["subject"] == "Sub3"

    def test_send_notification_with_incident_id(self) -> None:
        """Test that incident_id is stored in the log."""
        svc = NotificationService(dry_run=True)
        iid = uuid.uuid4()
        log = svc.send_notification(
            notification_type="teams",
            recipient="url",
            subject="Linked",
            body="Body",
            incident_id=iid,
        )
        assert log["incident_id"] == iid

    def test_send_teams_webhook_success(self) -> None:
        """Test Teams webhook send (non-dry-run) succeeds."""
        svc = NotificationService(dry_run=False)
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        with patch("apps.notification_service.httpx.post", return_value=mock_response) as mock_post:
            result = svc.send_teams_webhook("https://webhook.example.com", "Alert", "Body")
        mock_post.assert_called_once()
        assert result["status"] == "sent"
        assert result["error_message"] is None

    def test_send_teams_webhook_failure(self) -> None:
        """Test Teams webhook send (non-dry-run) fails gracefully."""
        svc = NotificationService(dry_run=False)
        with patch("apps.notification_service.httpx.post", side_effect=Exception("Connection refused")):
            result = svc.send_teams_webhook("https://webhook.example.com", "Alert", "Body")
        assert result["status"] == "failed"
        assert "Connection refused" in result["error_message"]

    def test_send_email_success(self) -> None:
        """Test email send (non-dry-run) succeeds."""
        svc = NotificationService(dry_run=False)
        mock_smtp_instance = MagicMock()
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            result = svc.send_email("admin@example.com", "Test Subject", "Test body")
        assert result["status"] == "sent"
        assert result["error_message"] is None

    def test_send_email_failure(self) -> None:
        """Test email send (non-dry-run) fails gracefully."""
        svc = NotificationService(dry_run=False)
        with patch("smtplib.SMTP", side_effect=Exception("SMTP connection failed")):
            result = svc.send_email("admin@example.com", "Test Subject", "Test body")
        assert result["status"] == "failed"
        assert "SMTP connection failed" in result["error_message"]

    def test_send_notification_sms_not_dry_run(self) -> None:
        """Test that SMS non-dry-run returns failed status (SMS not configured)."""
        svc = NotificationService(dry_run=False)
        log = svc.send_notification(
            notification_type="sms",
            recipient="+81-90-1234-5678",
            subject="Alert",
            body="Emergency",
        )
        assert log["status"] == "failed"
        assert "SMS not configured" in log["error_message"]


# ---------------------------------------------------------------------------
# EscalationEngine tests
# ---------------------------------------------------------------------------


class TestEscalationEngine:
    """Tests for the EscalationEngine class."""

    def test_get_escalation_plan_p1(self) -> None:
        """Test getting the P1 escalation plan."""
        engine = EscalationEngine()
        plan = engine.get_escalation_plan("p1")
        assert plan["severity"] == "p1"
        assert plan["plan_name"] == "P1 Full BCP Activation"
        assert len(plan["levels"]) == 4
        assert plan["levels"][0]["level"] == 1
        assert plan["levels"][0]["delay_minutes"] == 0
        assert plan["levels"][3]["level"] == 4
        assert plan["levels"][3]["delay_minutes"] == 30

    def test_get_escalation_plan_p2(self) -> None:
        """Test getting the P2 escalation plan."""
        engine = EscalationEngine()
        plan = engine.get_escalation_plan("p2")
        assert plan["plan_name"] == "P2 Partial BCP Activation"
        assert len(plan["levels"]) == 2

    def test_get_escalation_plan_p3(self) -> None:
        """Test getting the P3 escalation plan."""
        engine = EscalationEngine()
        plan = engine.get_escalation_plan("p3")
        assert plan["plan_name"] == "P3 Monitoring"
        assert len(plan["levels"]) == 1

    def test_get_escalation_plan_unknown(self) -> None:
        """Test getting an escalation plan for unknown severity."""
        engine = EscalationEngine()
        plan = engine.get_escalation_plan("p99")
        assert plan["plan_name"] == "Unknown"
        assert plan["levels"] == []

    def test_trigger_escalation_p1(self) -> None:
        """Test triggering a P1 escalation."""
        svc = NotificationService(dry_run=True)
        engine = EscalationEngine(notification_service=svc)
        iid = uuid.uuid4()
        result = engine.trigger_escalation(
            incident_id=iid,
            severity="p1",
            contacts=[
                {"role": "対応チーム", "name": "Team A", "teams_id": "team-a"},
                {"role": "IT部門長", "name": "Manager", "email": "mgr@co.jp", "teams_id": "mgr"},
            ],
        )
        assert result["incident_id"] == iid
        assert result["plan_name"] == "P1 Full BCP Activation"
        # P1 has 4 levels; L1=1ch, L2=2ch, L3=1ch, L4=2ch => 6 notifications
        assert result["notifications_queued"] == 6
        assert len(result["notifications"]) == 6
        # All should be sent (dry_run)
        for n in result["notifications"]:
            assert n["status"] == "sent"

    def test_trigger_escalation_p2(self) -> None:
        """Test triggering a P2 escalation."""
        svc = NotificationService(dry_run=True)
        engine = EscalationEngine(notification_service=svc)
        iid = uuid.uuid4()
        result = engine.trigger_escalation(incident_id=iid, severity="p2")
        # P2: L1=1ch, L2=2ch => 3 notifications
        assert result["notifications_queued"] == 3

    def test_get_escalation_status(self) -> None:
        """Test getting escalation status after trigger."""
        svc = NotificationService(dry_run=True)
        engine = EscalationEngine(notification_service=svc)
        iid = uuid.uuid4()
        engine.trigger_escalation(incident_id=iid, severity="p1")
        status = engine.get_escalation_status(iid)
        assert status["incident_id"] == iid
        assert status["total_notifications"] == 6
        assert status["sent"] == 6
        assert status["pending"] == 0
        assert status["failed"] == 0

    def test_get_escalation_status_no_escalation(self) -> None:
        """Test getting escalation status when none triggered."""
        engine = EscalationEngine()
        status = engine.get_escalation_status(uuid.uuid4())
        assert status["total_notifications"] == 0

    def test_trigger_escalation_else_channel(self) -> None:
        """Test else-branch (line 164) when channel is neither 'teams' nor 'email'."""
        svc = NotificationService(dry_run=True)
        engine = EscalationEngine(notification_service=svc)
        iid = uuid.uuid4()
        # Mock get_escalation_plan to return a plan with a 'phone' channel
        custom_plan = {
            "severity": "p1",
            "plan_name": "Custom Phone Plan",
            "levels": [
                {
                    "level": 1,
                    "role": "担当者",
                    "delay_minutes": 0,
                    "channels": ["phone"],
                }
            ],
        }
        with patch.object(engine, "get_escalation_plan", return_value=custom_plan):
            result = engine.trigger_escalation(
                incident_id=iid,
                severity="p1",
                contacts=[{"role": "担当者", "name": "Test User", "email": "user@test.local"}],
            )
        assert result["notifications_queued"] == 1
        # recipient should be email fallback (contact.get("email") or role)
        assert result["notifications"][0]["recipient"] == "user@test.local"

    def test_send_email_with_smtp_auth(self) -> None:
        """Test email send uses starttls/login when SMTP_USER is configured (lines 102-103)."""
        svc = NotificationService(dry_run=False)
        mock_smtp_instance = MagicMock()
        with patch("smtplib.SMTP") as mock_smtp, patch("apps.notification_service.settings") as mock_settings:
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USER = "user@example.com"
            mock_settings.SMTP_PASSWORD = "secret"
            mock_settings.SMTP_FROM = "noreply@example.com"
            result = svc.send_email("admin@example.com", "Test Subject", "Test body")
        assert result["status"] == "sent"
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("user@example.com", "secret")


# ---------------------------------------------------------------------------
# API route tests
# ---------------------------------------------------------------------------


class TestNotificationAPI:
    """Tests for the notification API endpoints."""

    @pytest.fixture(autouse=True)
    def _setup(self, client: TestClient) -> None:
        """Store client and reset module-level services."""
        self.client = client
        # Reset the module-level services before each test
        from apps.routers import notifications as notif_mod

        notif_mod._notification_service = NotificationService(dry_run=True)
        notif_mod._escalation_engine = EscalationEngine(notification_service=notif_mod._notification_service)

    def test_send_notification_api(self) -> None:
        """Test POST /api/notifications/send."""
        resp = self.client.post(
            "/api/notifications/send",
            json={
                "notification_type": "teams",
                "recipient": "https://webhook.test",
                "subject": "API Test",
                "body": "Hello from API",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "sent"
        assert data["subject"] == "API Test"
        assert data["notification_type"] == "teams"

    def test_list_notification_logs(self) -> None:
        """Test GET /api/notifications/logs."""
        # Send a couple of notifications first
        self.client.post(
            "/api/notifications/send",
            json={
                "notification_type": "email",
                "recipient": "a@b.com",
                "subject": "Log1",
                "body": "B1",
            },
        )
        self.client.post(
            "/api/notifications/send",
            json={
                "notification_type": "teams",
                "recipient": "url",
                "subject": "Log2",
                "body": "B2",
            },
        )
        resp = self.client.get("/api/notifications/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        # Most recent first
        assert data[0]["subject"] == "Log2"

    def test_get_logs_by_incident(self) -> None:
        """Test GET /api/notifications/logs/{incident_id}."""
        iid = str(uuid.uuid4())
        self.client.post(
            "/api/notifications/send",
            json={
                "notification_type": "email",
                "recipient": "x@y.com",
                "subject": "Linked",
                "body": "Body",
                "incident_id": iid,
            },
        )
        self.client.post(
            "/api/notifications/send",
            json={
                "notification_type": "teams",
                "recipient": "url",
                "subject": "Unlinked",
                "body": "Body",
            },
        )
        resp = self.client.get(f"/api/notifications/logs/{iid}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["subject"] == "Linked"

    def test_get_escalation_plan_api(self) -> None:
        """Test GET /api/escalation/plan/{severity}."""
        resp = self.client.get("/api/escalation/plan/p1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["severity"] == "p1"
        assert data["plan_name"] == "P1 Full BCP Activation"
        assert len(data["levels"]) == 4

    def test_trigger_escalation_api(self) -> None:
        """Test POST /api/escalation/trigger."""
        iid = str(uuid.uuid4())
        resp = self.client.post(
            "/api/escalation/trigger",
            json={
                "incident_id": iid,
                "severity": "p2",
                "contacts": [
                    {"role": "対応チーム", "name": "Team A"},
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_name"] == "P2 Partial BCP Activation"
        assert data["notifications_queued"] == 3

    def test_get_escalation_status_api(self) -> None:
        """Test GET /api/escalation/status/{incident_id}."""
        iid = str(uuid.uuid4())
        # Trigger first
        self.client.post(
            "/api/escalation/trigger",
            json={
                "incident_id": iid,
                "severity": "p1",
                "contacts": [],
            },
        )
        resp = self.client.get(f"/api/escalation/status/{iid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_notifications"] == 6
        assert data["sent"] == 6
