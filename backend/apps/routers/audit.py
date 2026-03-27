"""Audit log API router."""

from typing import Any

from fastapi import APIRouter, Query

from apps.audit_service import audit_service
from apps.schemas import AuditLogExportResponse, AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    resource_type: str | None = Query(None),
    action: str | None = Query(None),
    user_id: str | None = Query(None),
) -> list[dict[str, Any]]:
    """Return audit logs with optional filters."""
    return audit_service.get_logs(
        limit=limit,
        resource_type=resource_type,
        action=action,
        user_id=user_id,
    )


@router.get("/logs/export", response_model=AuditLogExportResponse)
async def export_audit_logs(
    fmt: str = Query("json", alias="format"),
) -> dict[str, Any]:
    """Export all audit logs for ISO20000 compliance auditing."""
    return audit_service.export_logs(fmt=fmt)


@router.get(
    "/logs/incident/{incident_id}",
    response_model=list[AuditLogResponse],
)
async def get_incident_audit_logs(
    incident_id: str,
) -> list[dict[str, Any]]:
    """Return audit logs related to a specific incident."""
    return audit_service.get_logs_by_incident(incident_id)
