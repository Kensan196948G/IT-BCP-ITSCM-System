"""Tests for notification service, escalation engine, and notification API routes."""

import uuid

import pytest

from apps.escalation_engine import EscalationEngine
from apps.notification_service import NotificationService

# ---------------------------------------------------------------------------
# NotificationService tests
# ---------------------------------------------------------------------------


class TestNotificationService:
    """Tests for the NotificationService class."""

    def test_send_notification_teams_dry_run(self):
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

    def test_send_notification_email_dry_run(self):
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

    def test_send_notification_sms_dry_run(self):
        """Test sending an SMS notification in dry_run mode."""
        svc = NotificationService(dry_run=True)
        log = svc.send_notification(
            notification_type="sms",
            recipient="+81-90-1234-5678",
            subject="Alert",
            body="Emergency",
        )
        assert log["status"] == "sent"

    def test_send_notification_unknown_type(self):
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

    def test_logs_accumulate(self):
        """Test that notification logs accumulate correctly."""
        svc = NotificationService(dry_run=True)
        svc.send_notification("teams", "url", "Sub1", "Body1")
        svc.send_notification("email", "a@b.com", "Sub2", "Body2")
        svc.send_notification("teams", "url2", "Sub3", "Body3")
        assert len(svc.logs) == 3
        assert svc.logs[0]["subject"] == "Sub1"
        assert svc.logs[2]["subject"] == "Sub3"

    def test_send_notification_with_incident_id(self):
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


# ---------------------------------------------------------------------------
# EscalationEngine tests
# ---------------------------------------------------------------------------


class TestEscalationEngine:
    """Tests for the EscalationEngine class."""

    def test_get_escalation_plan_p1(self):
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

    def test_get_escalation_plan_p2(self):
        """Test getting the P2 escalation plan."""
        engine = EscalationEngine()
        plan = engine.get_escalation_plan("p2")
        assert plan["plan_name"] == "P2 Partial BCP Activation"
        assert len(plan["levels"]) == 2

    def test_get_escalation_plan_p3(self):
        """Test getting the P3 escalation plan."""
        engine = EscalationEngine()
        plan = engine.get_escalation_plan("p3")
        assert plan["plan_name"] == "P3 Monitoring"
        assert len(plan["levels"]) == 1

    def test_get_escalation_plan_unknown(self):
        """Test getting an escalation plan for unknown severity."""
        engine = EscalationEngine()
        plan = engine.get_escalation_plan("p99")
        assert plan["plan_name"] == "Unknown"
        assert plan["levels"] == []

    def test_trigger_escalation_p1(self):
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

    def test_trigger_escalation_p2(self):
        """Test triggering a P2 escalation."""
        svc = NotificationService(dry_run=True)
        engine = EscalationEngine(notification_service=svc)
        iid = uuid.uuid4()
        result = engine.trigger_escalation(incident_id=iid, severity="p2")
        # P2: L1=1ch, L2=2ch => 3 notifications
        assert result["notifications_queued"] == 3

    def test_get_escalation_status(self):
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

    def test_get_escalation_status_no_escalation(self):
        """Test getting escalation status when none triggered."""
        engine = EscalationEngine()
        status = engine.get_escalation_status(uuid.uuid4())
        assert status["total_notifications"] == 0


# ---------------------------------------------------------------------------
# API route tests
# ---------------------------------------------------------------------------


class TestNotificationAPI:
    """Tests for the notification API endpoints."""

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        """Store client and reset module-level services."""
        self.client = client
        # Reset the module-level services before each test
        from apps.routers import notifications as notif_mod

        notif_mod._notification_service = NotificationService(dry_run=True)
        notif_mod._escalation_engine = EscalationEngine(notification_service=notif_mod._notification_service)

    def test_send_notification_api(self):
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

    def test_list_notification_logs(self):
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

    def test_get_logs_by_incident(self):
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

    def test_get_escalation_plan_api(self):
        """Test GET /api/escalation/plan/{severity}."""
        resp = self.client.get("/api/escalation/plan/p1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["severity"] == "p1"
        assert data["plan_name"] == "P1 Full BCP Activation"
        assert len(data["levels"]) == 4

    def test_trigger_escalation_api(self):
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

    def test_get_escalation_status_api(self):
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
