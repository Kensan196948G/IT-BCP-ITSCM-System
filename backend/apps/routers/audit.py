"""Audit log API router."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.schemas import AuditLogExportResponse, AuditLogResponse
from database import get_db

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _model_to_dict(log: Any) -> dict[str, Any]:
    """Convert an AuditLog ORM model to a response dict."""
    return {
        "id": str(log.id),
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "user_id": log.user_id,
        "user_role": log.user_role,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "details": log.details,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "status": log.status,
    }


@router.get("/logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    resource_type: str | None = Query(None),
    action: str | None = Query(None),
    user_id: str | None = Query(None),
) -> list[dict[str, Any]]:
    """Return audit logs from database with optional filters."""
    logs = await crud.get_audit_logs(
        db,
        limit=limit,
        resource_type=resource_type,
        action=action,
        user_id=user_id,
    )
    return [_model_to_dict(log) for log in logs]


@router.get("/logs/export", response_model=AuditLogExportResponse)
async def export_audit_logs(
    db: AsyncSession = Depends(get_db),
    fmt: str = Query("json", alias="format"),
) -> dict[str, Any]:
    """Export all audit logs for ISO20000 compliance auditing."""
    logs = await crud.get_audit_logs(db, limit=10000)
    return {
        "format": fmt,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(logs),
        "standard": "ISO20000-ITSCM",
        "logs": [_model_to_dict(log) for log in logs],
    }


@router.get(
    "/logs/incident/{incident_id}",
    response_model=list[AuditLogResponse],
)
async def get_incident_audit_logs(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return audit logs related to a specific incident."""
    logs = await crud.get_audit_logs_by_incident(db, incident_id)
    return [_model_to_dict(log) for log in logs]
