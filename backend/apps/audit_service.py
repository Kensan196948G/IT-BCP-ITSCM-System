"""Audit log service for IT-BCP-ITSCM-System.

Provides in-memory audit logging with filtering and export capabilities.
Designed to be easily extended to database persistence.
"""

import uuid
from datetime import datetime, timezone
from typing import Any


class AuditService:
    """Record and query audit log entries."""

    def __init__(self) -> None:
        self._logs: list[dict[str, Any]] = []

    def log(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        user_id: str | None = None,
        role: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        status: str = "success",
    ) -> dict[str, Any]:
        """Record an audit log entry and return it."""
        entry: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "user_role": role,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status": status,
        }
        self._logs.append(entry)
        return entry

    def get_logs(
        self,
        limit: int = 100,
        resource_type: str | None = None,
        action: str | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return audit logs with optional filtering."""
        results = list(self._logs)
        if resource_type is not None:
            results = [e for e in results if e["resource_type"] == resource_type]
        if action is not None:
            results = [e for e in results if e["action"] == action]
        if user_id is not None:
            results = [e for e in results if e["user_id"] == user_id]
        # Most recent first
        results.reverse()
        return results[:limit]

    def get_logs_by_incident(self, incident_id: str) -> list[dict[str, Any]]:
        """Return audit logs related to a specific incident."""
        results = [e for e in self._logs if e["resource_type"] == "incident" and e["resource_id"] == incident_id]
        results.reverse()
        return results

    def export_logs(self, fmt: str = "json") -> dict[str, Any]:
        """Export all audit logs with metadata (ISO20000 audit ready)."""
        logs = list(self._logs)
        logs.reverse()
        return {
            "format": fmt,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_count": len(logs),
            "standard": "ISO20000-ITSCM",
            "logs": logs,
        }


# Singleton instance
audit_service = AuditService()
