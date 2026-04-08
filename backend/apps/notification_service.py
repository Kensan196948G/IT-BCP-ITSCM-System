"""Notification service for sending Teams, Email, and SMS notifications."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Unified notification service with dry_run support."""

    def __init__(self, dry_run: bool | None = None):
        self.dry_run = dry_run if dry_run is not None else settings.NOTIFICATION_DRY_RUN
        self._logs: list[dict[str, Any]] = []

    @property
    def logs(self) -> list[dict[str, Any]]:
        """Return all notification logs."""
        return list(self._logs)

    def send_teams_webhook(
        self,
        webhook_url: str,
        title: str,
        body: str,
        color: str = "0076D7",
    ) -> dict[str, Any]:
        """Send a Teams Adaptive Card via webhook.

        Returns a dict with status and optional error_message.
        """
        if self.dry_run:
            logger.info("[DRY_RUN] Teams webhook: %s -> %s", title, webhook_url)
            return {"status": "sent", "error_message": None}

        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": title,
                                "weight": "Bolder",
                                "size": "Medium",
                                "color": "Attention" if color.lower() in ("ff0000", "red") else "Default",
                            },
                            {
                                "type": "TextBlock",
                                "text": body,
                                "wrap": True,
                            },
                        ],
                    },
                }
            ],
        }
        try:
            resp = httpx.post(webhook_url, json=payload, timeout=10.0)
            resp.raise_for_status()
            return {"status": "sent", "error_message": None}
        except Exception as exc:
            error_msg = str(exc)
            logger.error("Teams webhook failed: %s", error_msg)
            return {"status": "failed", "error_message": error_msg}

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> dict[str, Any]:
        """Send an email via SMTP.

        Returns a dict with status and optional error_message.
        """
        if self.dry_run:
            logger.info("[DRY_RUN] Email: %s -> %s", subject, to)
            return {"status": "sent", "error_message": None}

        try:
            import smtplib
            from email.mime.text import MIMEText

            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM
            msg["To"] = to

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USER:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return {"status": "sent", "error_message": None}
        except Exception as exc:
            error_msg = str(exc)
            logger.error("Email send failed: %s", error_msg)
            return {"status": "failed", "error_message": error_msg}

    def send_notification(
        self,
        notification_type: str,
        recipient: str,
        subject: str,
        body: str,
        incident_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Send a notification and record it in the internal log.

        Args:
            notification_type: 'teams', 'email', or 'sms'
            recipient: webhook URL, email address, or phone number
            subject: notification subject
            body: notification body
            incident_id: optional linked incident UUID

        Returns:
            A notification log dict.
        """
        now = datetime.now(timezone.utc)
        log_entry = {
            "id": uuid.uuid4(),
            "incident_id": incident_id,
            "notification_type": notification_type,
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "status": "pending",
            "sent_at": None,
            "error_message": None,
            "metadata": None,
            "created_at": now,
        }

        if notification_type == "teams":
            webhook_url = recipient if recipient.startswith("http") else settings.TEAMS_WEBHOOK_URL
            result = self.send_teams_webhook(webhook_url, subject, body)
        elif notification_type == "email":
            result = self.send_email(recipient, subject, body)
        elif notification_type == "sms":
            if self.dry_run:
                logger.info("[DRY_RUN] SMS: %s -> %s", subject, recipient)
                result = {"status": "sent", "error_message": None}
            else:
                result = {"status": "failed", "error_message": "SMS not configured"}
        else:
            result = {"status": "failed", "error_message": f"Unknown type: {notification_type}"}

        log_entry["status"] = result["status"]
        log_entry["error_message"] = result.get("error_message")
        if result["status"] == "sent":
            log_entry["sent_at"] = now

        self._logs.append(log_entry)
        return log_entry
