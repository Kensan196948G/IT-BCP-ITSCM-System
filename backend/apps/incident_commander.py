"""Incident command support logic for the war room dashboard."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.models import ActiveIncident
from apps.rto_tracker import RTOTracker
from apps.schemas import (
    ActiveIncidentResponse,
    IncidentCommandDashboard,
    IncidentTaskResponse,
    RTOStatusResponse,
    SituationReportResponse,
    TaskStatistics,
)


async def get_task_statistics(db: AsyncSession, incident_id: uuid.UUID) -> TaskStatistics:
    """Calculate task statistics for an incident."""
    tasks = await crud.get_incident_tasks_by_incident(db, incident_id)
    total = len(tasks)
    if total == 0:
        return TaskStatistics()

    pending = sum(1 for t in tasks if t.status == "pending")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    completed = sum(1 for t in tasks if t.status == "completed")
    blocked = sum(1 for t in tasks if t.status == "blocked")
    completion_rate = round((completed / total) * 100, 1) if total > 0 else 0.0

    return TaskStatistics(
        total=total,
        pending=pending,
        in_progress=in_progress,
        completed=completed,
        blocked=blocked,
        completion_rate=completion_rate,
    )


async def _get_rto_statuses(db: AsyncSession, incident: ActiveIncident) -> list[dict]:
    """Get RTO statuses for an incident's affected systems."""
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


async def get_command_dashboard(db: AsyncSession, incident_id: uuid.UUID) -> IncidentCommandDashboard | None:
    """Build the full command dashboard for an incident.

    Returns None if the incident is not found.
    """
    incident = await crud.get_incident(db, incident_id)
    if incident is None:
        return None

    # Tasks
    tasks = await crud.get_incident_tasks_by_incident(db, incident_id)
    task_stats = await get_task_statistics(db, incident_id)

    # Situation reports
    reports = await crud.get_situation_reports_by_incident(db, incident_id)
    latest_report = reports[-1] if reports else None

    # RTO statuses
    rto_statuses = await _get_rto_statuses(db, incident)

    return IncidentCommandDashboard(
        incident=ActiveIncidentResponse.model_validate(incident),
        tasks=[IncidentTaskResponse.model_validate(t) for t in tasks],
        task_statistics=task_stats,
        latest_report=(SituationReportResponse.model_validate(latest_report) if latest_report else None),
        reports_count=len(reports),
        rto_statuses=[RTOStatusResponse(**s) for s in rto_statuses],
    )


async def generate_situation_report(db: AsyncSession, incident_id: uuid.UUID) -> dict | None:
    """Auto-generate a situation report for an incident.

    Returns None if the incident is not found.
    Returns a dict suitable for creating a SituationReport.
    """
    incident = await crud.get_incident(db, incident_id)
    if incident is None:
        return None

    now = datetime.now(timezone.utc)

    # Task stats
    tasks = await crud.get_incident_tasks_by_incident(db, incident_id)
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "completed")
    blocked_tasks = sum(1 for t in tasks if t.status == "blocked")
    completion_pct = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0.0

    tasks_summary = {
        "total": total_tasks,
        "completed": completed_tasks,
        "blocked": blocked_tasks,
        "completion_rate": completion_pct,
    }

    # Systems status
    rto_statuses = await _get_rto_statuses(db, incident)
    systems_status: dict[str, str] = {}
    for s in rto_statuses:
        systems_status[s["system_name"]] = s["status"]

    # Determine next actions
    next_actions: list[str] = []
    if blocked_tasks > 0:
        next_actions.append(f"Resolve {blocked_tasks} blocked task(s)")
    pending_tasks = [t for t in tasks if t.status == "pending"]
    if pending_tasks:
        next_actions.append(f"Start {len(pending_tasks)} pending task(s)")
    overdue_systems = [s for s in rto_statuses if s["status"] == "overdue"]
    if overdue_systems:
        names = ", ".join(s["system_name"] for s in overdue_systems)
        next_actions.append(f"Escalate overdue systems: {names}")
    if not next_actions:
        next_actions.append("Continue monitoring recovery progress")

    # Elapsed time
    elapsed_hours = 0.0
    if incident.occurred_at:
        elapsed_hours = round((now - incident.occurred_at).total_seconds() / 3600.0, 1)

    # Summary
    summary = (
        f"Incident '{incident.title}' - {elapsed_hours}h elapsed. "
        f"Task completion: {completion_pct}% ({completed_tasks}/{total_tasks}). "
        f"Affected systems: {len(rto_statuses)}."
    )

    # Determine next report number
    existing_reports = await crud.get_situation_reports_by_incident(db, incident_id)
    next_number = len(existing_reports) + 1

    return {
        "incident_id": incident_id,
        "report_number": next_number,
        "report_time": now,
        "reporter": "auto-generated",
        "summary": summary,
        "systems_status": systems_status,
        "tasks_summary": tasks_summary,
        "next_actions": next_actions,
        "escalation_status": incident.status,
        "audience": "internal",
    }
