"""API routes for active incident management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.escalation_engine import EscalationEngine
from apps.incident_commander import (
    generate_situation_report,
    get_command_dashboard,
)
from apps.rto_tracker import RTOTracker
from apps.schemas import (
    ActiveIncidentCreate,
    ActiveIncidentResponse,
    ActiveIncidentUpdate,
    EscalationPlanResponse,
    EscalationStatusResponse,
    EscalationTriggerRequest,
    EscalationTriggerResponse,
    IncidentCommandDashboard,
    IncidentTaskCreate,
    IncidentTaskResponse,
    IncidentTaskUpdate,
    NotificationLogResponse,
    NotificationSendRequest,
    RTOStatusResponse,
    SituationReportCreate,
    SituationReportResponse,
)
from apps.notification_service import NotificationService
from database import get_db

_escalation_engine = EscalationEngine()

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("", response_model=list[ActiveIncidentResponse])
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get all active incident records with pagination."""
    return await crud.get_all_incidents(db, skip=skip, limit=limit)


@router.post("", response_model=ActiveIncidentResponse, status_code=201)
async def create_incident(
    payload: ActiveIncidentCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new active incident record."""
    return await crud.create_incident(db, payload.model_dump())


@router.get("/{incident_id}", response_model=ActiveIncidentResponse)
async def get_incident(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Get a single active incident record."""
    obj = await crud.get_incident(db, incident_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return obj


@router.put("/{incident_id}", response_model=ActiveIncidentResponse)
async def update_incident(
    incident_id: uuid.UUID,
    payload: ActiveIncidentUpdate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Update an active incident record."""
    obj = await crud.update_incident(db, incident_id, payload.model_dump(exclude_unset=True))
    if obj is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return obj


@router.get("/{incident_id}/rto-dashboard", response_model=list[RTOStatusResponse])
async def incident_rto_dashboard(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get RTO dashboard for a specific incident's affected systems."""
    incident = await crud.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    affected_names = incident.affected_systems or []
    if not affected_names:
        return []

    all_systems = await crud.get_all_systems(db)
    results: list[dict] = []
    for system in all_systems:
        if system.system_name in affected_names:
            tracker = RTOTracker(
                rto_target_hours=system.rto_target_hours,
                occurred_at=incident.occurred_at,
                resolved_at=incident.resolved_at,
                status=incident.status,
            )
            status_info = tracker.calculate_status()
            status_info["system_name"] = system.system_name
            results.append(status_info)

    return results


# ---------------------------------------------------------------------------
# Command Dashboard
# ---------------------------------------------------------------------------


@router.get(
    "/{incident_id}/command-dashboard",
    response_model=IncidentCommandDashboard,
)
async def command_dashboard(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Get the full command dashboard (war room) for an incident."""
    result = await get_command_dashboard(db, incident_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return result


# ---------------------------------------------------------------------------
# Incident Tasks
# ---------------------------------------------------------------------------


@router.post(
    "/{incident_id}/tasks",
    response_model=IncidentTaskResponse,
    status_code=201,
)
async def create_task(
    incident_id: uuid.UUID,
    payload: IncidentTaskCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new task for an incident."""
    incident = await crud.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    data = payload.model_dump()
    data["incident_id"] = incident_id
    return await crud.create_incident_task(db, data)


@router.get(
    "/{incident_id}/tasks",
    response_model=list[IncidentTaskResponse],
)
async def list_tasks(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get all tasks for an incident."""
    incident = await crud.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return await crud.get_incident_tasks_by_incident(db, incident_id)


@router.put(
    "/{incident_id}/tasks/{task_id}",
    response_model=IncidentTaskResponse,
)
async def update_task(
    incident_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: IncidentTaskUpdate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Update a task for an incident."""
    incident = await crud.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    obj = await crud.update_incident_task(db, task_id, payload.model_dump(exclude_unset=True))
    if obj is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return obj


# ---------------------------------------------------------------------------
# Situation Reports
# ---------------------------------------------------------------------------


@router.post(
    "/{incident_id}/situation-reports",
    response_model=SituationReportResponse,
    status_code=201,
)
async def create_situation_report_endpoint(
    incident_id: uuid.UUID,
    payload: SituationReportCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new situation report for an incident."""
    incident = await crud.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    data = payload.model_dump()
    data["incident_id"] = incident_id
    return await crud.create_situation_report(db, data)


@router.get(
    "/{incident_id}/situation-reports",
    response_model=list[SituationReportResponse],
)
async def list_situation_reports(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get all situation reports for an incident."""
    incident = await crud.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return await crud.get_situation_reports_by_incident(db, incident_id)


@router.post(
    "/{incident_id}/situation-reports/auto-generate",
    response_model=SituationReportResponse,
    status_code=201,
)
async def auto_generate_situation_report(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Auto-generate a situation report for an incident."""
    report_data = await generate_situation_report(db, incident_id)
    if report_data is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return await crud.create_situation_report(db, report_data)


# ---------------------------------------------------------------------------
# Escalation endpoints
# ---------------------------------------------------------------------------


@router.get("/escalation/plan/{severity}", response_model=EscalationPlanResponse)
async def get_escalation_plan(severity: str) -> dict:
    """Get the escalation plan for a given severity (p1, p2, p3)."""
    plan = _escalation_engine.get_escalation_plan(severity)
    if not plan["levels"]:
        raise HTTPException(status_code=404, detail=f"No escalation plan for severity '{severity}'")
    return plan


@router.post("/escalation/trigger", response_model=EscalationTriggerResponse, status_code=201)
async def trigger_escalation(payload: EscalationTriggerRequest) -> dict:
    """Trigger an escalation for an incident (dry-run mode; no real notifications sent)."""
    contacts = [c.model_dump() for c in payload.contacts]
    result = _escalation_engine.trigger_escalation(
        incident_id=payload.incident_id,
        severity=payload.severity,
        contacts=contacts,
    )
    return result


@router.get("/escalation/status/{incident_id}", response_model=EscalationStatusResponse)
async def get_escalation_status(incident_id: uuid.UUID) -> dict:
    """Get the escalation notification status for an incident."""
    return _escalation_engine.get_escalation_status(incident_id)


# ---------------------------------------------------------------------------
# Notification endpoints
# ---------------------------------------------------------------------------


@router.post("/notifications/send", response_model=NotificationLogResponse, status_code=201)
async def send_notification(payload: NotificationSendRequest) -> dict:
    """Send a manual notification (dry-run; logged but not actually delivered)."""
    svc = NotificationService()
    log_entry = svc.send_notification(
        notification_type=payload.notification_type,
        recipient=payload.recipient,
        subject=payload.subject,
        body=payload.body,
        incident_id=payload.incident_id,
    )
    return log_entry
