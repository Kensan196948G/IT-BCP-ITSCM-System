"""Escalation engine for automated incident escalation."""

import logging
import uuid
from typing import Any

from apps.notification_service import NotificationService

logger = logging.getLogger(__name__)


# Escalation matrix definitions
ESCALATION_MATRIX = {
    "P1_FULL_BCP": {
        "plan_name": "P1 Full BCP Activation",
        "levels": [
            {
                "level": 1,
                "role": "対応チーム",
                "delay_minutes": 0,
                "channels": ["teams"],
            },
            {
                "level": 2,
                "role": "IT部門長",
                "delay_minutes": 5,
                "channels": ["teams", "email"],
            },
            {
                "level": 3,
                "role": "経営層（CISO/CEO）",
                "delay_minutes": 15,
                "channels": ["email"],
            },
            {
                "level": 4,
                "role": "全部門長",
                "delay_minutes": 30,
                "channels": ["teams", "email"],
            },
        ],
    },
    "P2_PARTIAL_BCP": {
        "plan_name": "P2 Partial BCP Activation",
        "levels": [
            {
                "level": 1,
                "role": "対応チーム",
                "delay_minutes": 0,
                "channels": ["teams"],
            },
            {
                "level": 2,
                "role": "IT部門長",
                "delay_minutes": 15,
                "channels": ["teams", "email"],
            },
        ],
    },
    "P3_MONITORING": {
        "plan_name": "P3 Monitoring",
        "levels": [
            {
                "level": 1,
                "role": "対応チーム",
                "delay_minutes": 0,
                "channels": ["teams"],
            },
        ],
    },
}

# Severity to matrix key mapping
SEVERITY_MAP = {
    "p1": "P1_FULL_BCP",
    "p2": "P2_PARTIAL_BCP",
    "p3": "P3_MONITORING",
}


class EscalationEngine:
    """Engine for managing incident escalation workflows."""

    def __init__(self, notification_service: NotificationService | None = None):
        self.notification_service = notification_service or NotificationService()
        self._escalation_state: dict[str, list[dict[str, Any]]] = {}

    def get_escalation_plan(self, severity: str) -> dict[str, Any]:
        """Get the escalation plan for a given severity level.

        Args:
            severity: p1, p2, or p3

        Returns:
            Dict with severity, plan_name, and levels.
        """
        matrix_key = SEVERITY_MAP.get(severity.lower())
        if not matrix_key:
            return {
                "severity": severity,
                "plan_name": "Unknown",
                "levels": [],
            }

        matrix = ESCALATION_MATRIX[matrix_key]
        return {
            "severity": severity,
            "plan_name": matrix["plan_name"],
            "levels": matrix["levels"],
        }

    def trigger_escalation(
        self,
        incident_id: uuid.UUID,
        severity: str,
        contacts: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Trigger an escalation for an incident.

        Args:
            incident_id: The incident UUID.
            severity: p1, p2, or p3.
            contacts: Optional list of contact dicts with role, name, email, teams_id.

        Returns:
            Dict with incident_id, severity, plan_name, notifications list.
        """
        plan = self.get_escalation_plan(severity)
        notifications = []
        contacts = contacts or []

        # Build a role->contact lookup
        contact_by_role: dict[str, dict[str, Any]] = {}
        for c in contacts:
            role = c.get("role", "")
            contact_by_role[role] = c

        incident_id_str = str(incident_id)

        for level_def in plan["levels"]:
            level = level_def["level"]
            role = level_def["role"]
            delay = level_def["delay_minutes"]
            channels = level_def["channels"]

            # Find the matching contact or use a default recipient
            contact = contact_by_role.get(role, {})
            contact_name = contact.get("name", role)

            subject = f"[BCP Escalation L{level}] {plan['plan_name']} " f"- Incident {incident_id_str[:8]}"
            body = (
                f"Escalation Level {level}: {role}\n"
                f"Delay: {delay} minutes from incident detection\n"
                f"Recipient: {contact_name}\n"
                f"Severity: {severity.upper()}\n"
                f"Incident ID: {incident_id_str}"
            )

            for channel in channels:
                if channel == "teams":
                    recipient = contact.get("teams_id") or "teams-default"
                elif channel == "email":
                    recipient = contact.get("email") or f"{role}@itbcp.local"
                else:
                    recipient = contact.get("email") or role

                log_entry = self.notification_service.send_notification(
                    notification_type=channel,
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    incident_id=incident_id,
                )
                log_entry["metadata"] = {
                    "escalation_level": level,
                    "delay_minutes": delay,
                    "role": role,
                }
                notifications.append(log_entry)

        # Store escalation state
        self._escalation_state[incident_id_str] = notifications

        return {
            "incident_id": incident_id,
            "severity": severity,
            "plan_name": plan["plan_name"],
            "notifications_queued": len(notifications),
            "notifications": notifications,
        }

    def get_escalation_status(self, incident_id: uuid.UUID) -> dict[str, Any]:
        """Get the escalation status for an incident.

        Args:
            incident_id: The incident UUID.

        Returns:
            Dict with incident_id, total, sent, pending, failed, notifications.
        """
        incident_id_str = str(incident_id)
        notifications = self._escalation_state.get(incident_id_str, [])

        sent = sum(1 for n in notifications if n.get("status") == "sent")
        pending = sum(1 for n in notifications if n.get("status") == "pending")
        failed = sum(1 for n in notifications if n.get("status") == "failed")

        return {
            "incident_id": incident_id,
            "total_notifications": len(notifications),
            "sent": sent,
            "pending": pending,
            "failed": failed,
            "notifications": notifications,
        }
