"""Notification and escalation API routes."""

import uuid

from fastapi import APIRouter

from apps.escalation_engine import EscalationEngine
from apps.notification_service import NotificationService
from apps.schemas import (
    EscalationPlanResponse,
    EscalationStatusResponse,
    EscalationTriggerRequest,
    EscalationTriggerResponse,
    NotificationLogResponse,
    NotificationSendRequest,
)

router = APIRouter(tags=["notifications"])

# Module-level service instances (singleton per process)
_notification_service = NotificationService()
_escalation_engine = EscalationEngine(notification_service=_notification_service)


def _log_to_response(log: dict) -> NotificationLogResponse:
    """Convert an internal log dict to a NotificationLogResponse."""
    return NotificationLogResponse(
        id=log["id"],
        incident_id=log.get("incident_id"),
        notification_type=log["notification_type"],
        recipient=log["recipient"],
        subject=log["subject"],
        body=log["body"],
        status=log["status"],
        sent_at=log.get("sent_at"),
        error_message=log.get("error_message"),
        metadata=log.get("metadata"),
        created_at=log["created_at"],
    )


# ---- Notification endpoints ----


@router.post("/api/notifications/send", response_model=NotificationLogResponse)
async def send_notification(req: NotificationSendRequest) -> NotificationLogResponse:
    """Send a notification manually."""
    log = _notification_service.send_notification(
        notification_type=req.notification_type,
        recipient=req.recipient,
        subject=req.subject,
        body=req.body,
        incident_id=req.incident_id,
    )
    return _log_to_response(log)


@router.get("/api/notifications/logs", response_model=list[NotificationLogResponse])
async def list_notification_logs() -> list[NotificationLogResponse]:
    """List all notification logs (most recent first)."""
    logs = _notification_service.logs
    return [_log_to_response(log) for log in reversed(logs)]


@router.get(
    "/api/notifications/logs/{incident_id}",
    response_model=list[NotificationLogResponse],
)
async def get_notification_logs_by_incident(
    incident_id: uuid.UUID,
) -> list[NotificationLogResponse]:
    """Get notification logs for a specific incident."""
    logs = [log for log in _notification_service.logs if log.get("incident_id") == incident_id]
    return [_log_to_response(log) for log in reversed(logs)]


# ---- Escalation endpoints ----


@router.post("/api/escalation/trigger", response_model=EscalationTriggerResponse)
async def trigger_escalation(
    req: EscalationTriggerRequest,
) -> EscalationTriggerResponse:
    """Trigger an escalation for an incident."""
    contacts_dicts = [c.model_dump() for c in req.contacts]
    result = _escalation_engine.trigger_escalation(
        incident_id=req.incident_id,
        severity=req.severity,
        contacts=contacts_dicts,
    )
    return EscalationTriggerResponse(
        incident_id=result["incident_id"],
        severity=result["severity"],
        plan_name=result["plan_name"],
        notifications_queued=result["notifications_queued"],
        notifications=[_log_to_response(n) for n in result["notifications"]],
    )


@router.get(
    "/api/escalation/plan/{severity}",
    response_model=EscalationPlanResponse,
)
async def get_escalation_plan(severity: str) -> EscalationPlanResponse:
    """Get the escalation plan for a given severity."""
    plan = _escalation_engine.get_escalation_plan(severity)
    return EscalationPlanResponse(**plan)


@router.get(
    "/api/escalation/status/{incident_id}",
    response_model=EscalationStatusResponse,
)
async def get_escalation_status(
    incident_id: uuid.UUID,
) -> EscalationStatusResponse:
    """Get the escalation status for an incident."""
    status = _escalation_engine.get_escalation_status(incident_id)
    return EscalationStatusResponse(
        incident_id=status["incident_id"],
        total_notifications=status["total_notifications"],
        sent=status["sent"],
        pending=status["pending"],
        failed=status["failed"],
        notifications=[_log_to_response(n) for n in status["notifications"]],
    )
