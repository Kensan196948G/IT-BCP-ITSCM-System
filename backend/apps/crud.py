"""CRUD operations for all models."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import desc

from apps.models import (
    ActiveIncident,
    AuditLog,
    BCPExercise,
    BCPScenario,
    BIAAssessment,
    EmergencyContact,
    ExerciseRTORecord,
    ITSystemBCP,
    IncidentTask,
    RecoveryProcedure,
    SituationReport,
    VendorContact,
)

# ---- ITSystemBCP CRUD ----


async def create_system(db: AsyncSession, data: dict[str, Any]) -> ITSystemBCP:
    """Create a new IT system BCP record."""
    obj = ITSystemBCP(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_system(db: AsyncSession, system_id: uuid.UUID) -> ITSystemBCP | None:
    """Get a single IT system BCP record by ID."""
    result = await db.execute(select(ITSystemBCP).where(ITSystemBCP.id == system_id))
    return result.scalar_one_or_none()


async def get_all_systems(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[ITSystemBCP]:
    """Get all IT system BCP records with pagination."""
    result = await db.execute(select(ITSystemBCP).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_system(db: AsyncSession, system_id: uuid.UUID, data: dict[str, Any]) -> ITSystemBCP | None:
    """Update an IT system BCP record."""
    obj = await get_system(db, system_id)
    if obj is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(obj, key, value)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_system(db: AsyncSession, system_id: uuid.UUID) -> bool:
    """Delete an IT system BCP record."""
    obj = await get_system(db, system_id)
    if obj is None:
        return False
    await db.delete(obj)
    await db.flush()
    return True


# ---- RecoveryProcedure CRUD ----


async def create_procedure(db: AsyncSession, data: dict[str, Any]) -> RecoveryProcedure:
    """Create a new recovery procedure record."""
    obj = RecoveryProcedure(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_procedure(db: AsyncSession, procedure_id: uuid.UUID) -> RecoveryProcedure | None:
    """Get a single recovery procedure record by ID."""
    result = await db.execute(select(RecoveryProcedure).where(RecoveryProcedure.id == procedure_id))
    return result.scalar_one_or_none()


async def get_all_procedures(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[RecoveryProcedure]:
    """Get all recovery procedure records with pagination."""
    result = await db.execute(select(RecoveryProcedure).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_procedure(db: AsyncSession, procedure_id: uuid.UUID, data: dict[str, Any]) -> RecoveryProcedure | None:
    """Update a recovery procedure record."""
    obj = await get_procedure(db, procedure_id)
    if obj is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(obj, key, value)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_procedure(db: AsyncSession, procedure_id: uuid.UUID) -> bool:
    """Delete a recovery procedure record."""
    obj = await get_procedure(db, procedure_id)
    if obj is None:
        return False
    await db.delete(obj)
    await db.flush()
    return True


# ---- EmergencyContact CRUD ----


async def create_emergency_contact(db: AsyncSession, data: dict[str, Any]) -> EmergencyContact:
    """Create a new emergency contact record."""
    obj = EmergencyContact(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_emergency_contact(db: AsyncSession, contact_id: uuid.UUID) -> EmergencyContact | None:
    """Get a single emergency contact record by ID."""
    result = await db.execute(select(EmergencyContact).where(EmergencyContact.id == contact_id))
    return result.scalar_one_or_none()


async def get_all_emergency_contacts(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[EmergencyContact]:
    """Get all emergency contact records with pagination."""
    result = await db.execute(select(EmergencyContact).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_emergency_contact(
    db: AsyncSession,
    contact_id: uuid.UUID,
    data: dict[str, Any],
) -> EmergencyContact | None:
    """Update an emergency contact record."""
    obj = await get_emergency_contact(db, contact_id)
    if obj is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(obj, key, value)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_emergency_contact(db: AsyncSession, contact_id: uuid.UUID) -> bool:
    """Delete an emergency contact record."""
    obj = await get_emergency_contact(db, contact_id)
    if obj is None:
        return False
    await db.delete(obj)
    await db.flush()
    return True


async def get_emergency_contacts_by_escalation_group(db: AsyncSession, group: str) -> list[EmergencyContact]:
    """Get emergency contacts filtered by escalation group."""
    result = await db.execute(select(EmergencyContact).where(EmergencyContact.escalation_group == group))
    return list(result.scalars().all())


# ---- VendorContact CRUD ----


async def create_vendor_contact(db: AsyncSession, data: dict[str, Any]) -> VendorContact:
    """Create a new vendor contact record."""
    obj = VendorContact(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_vendor_contact(db: AsyncSession, contact_id: uuid.UUID) -> VendorContact | None:
    """Get a single vendor contact record by ID."""
    result = await db.execute(select(VendorContact).where(VendorContact.id == contact_id))
    return result.scalar_one_or_none()


async def get_all_vendor_contacts(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[VendorContact]:
    """Get all vendor contact records with pagination."""
    result = await db.execute(select(VendorContact).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_vendor_contact(db: AsyncSession, contact_id: uuid.UUID, data: dict[str, Any]) -> VendorContact | None:
    """Update a vendor contact record."""
    obj = await get_vendor_contact(db, contact_id)
    if obj is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(obj, key, value)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_vendor_contact(db: AsyncSession, contact_id: uuid.UUID) -> bool:
    """Delete a vendor contact record."""
    obj = await get_vendor_contact(db, contact_id)
    if obj is None:
        return False
    await db.delete(obj)
    await db.flush()
    return True


# ---- BCPExercise CRUD ----


async def create_exercise(db: AsyncSession, data: dict[str, Any]) -> BCPExercise:
    """Create a new BCP exercise record."""
    obj = BCPExercise(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_exercise(db: AsyncSession, exercise_id: uuid.UUID) -> BCPExercise | None:
    """Get a single BCP exercise record by ID."""
    result = await db.execute(select(BCPExercise).where(BCPExercise.id == exercise_id))
    return result.scalar_one_or_none()


async def get_all_exercises(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[BCPExercise]:
    """Get all BCP exercise records with pagination."""
    result = await db.execute(select(BCPExercise).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_exercise(db: AsyncSession, exercise_id: uuid.UUID, data: dict[str, Any]) -> BCPExercise | None:
    """Update a BCP exercise record."""
    obj = await get_exercise(db, exercise_id)
    if obj is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(obj, key, value)
    await db.flush()
    await db.refresh(obj)
    return obj


# ---- ActiveIncident CRUD ----


async def create_incident(db: AsyncSession, data: dict[str, Any]) -> ActiveIncident:
    """Create a new active incident record."""
    obj = ActiveIncident(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_incident(db: AsyncSession, incident_id: uuid.UUID) -> ActiveIncident | None:
    """Get a single active incident record by ID."""
    result = await db.execute(select(ActiveIncident).where(ActiveIncident.id == incident_id))
    return result.scalar_one_or_none()


async def get_all_incidents(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[ActiveIncident]:
    """Get all active incident records with pagination."""
    result = await db.execute(select(ActiveIncident).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_incident(db: AsyncSession, incident_id: uuid.UUID, data: dict[str, Any]) -> ActiveIncident | None:
    """Update an active incident record."""
    obj = await get_incident(db, incident_id)
    if obj is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(obj, key, value)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_active_incidents(db: AsyncSession) -> list[ActiveIncident]:
    """Get all incidents with active or recovering status."""
    result = await db.execute(select(ActiveIncident).where(ActiveIncident.status.in_(["active", "recovering"])))
    return list(result.scalars().all())


# ---- BIAAssessment CRUD ----


async def create_bia_assessment(db: AsyncSession, data: dict[str, Any]) -> BIAAssessment:
    """Create a new BIA assessment record."""
    obj = BIAAssessment(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_bia_assessment(db: AsyncSession, assessment_id: uuid.UUID) -> BIAAssessment | None:
    """Get a single BIA assessment record by ID."""
    result = await db.execute(select(BIAAssessment).where(BIAAssessment.id == assessment_id))
    return result.scalar_one_or_none()


async def get_all_bia_assessments(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[BIAAssessment]:
    """Get all BIA assessment records with pagination."""
    result = await db.execute(select(BIAAssessment).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_bia_assessment(
    db: AsyncSession,
    assessment_id: uuid.UUID,
    data: dict[str, Any],
) -> BIAAssessment | None:
    """Update a BIA assessment record."""
    obj = await get_bia_assessment(db, assessment_id)
    if obj is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(obj, key, value)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_bia_assessment(db: AsyncSession, assessment_id: uuid.UUID) -> bool:
    """Delete a BIA assessment record."""
    obj = await get_bia_assessment(db, assessment_id)
    if obj is None:
        return False
    await db.delete(obj)
    await db.flush()
    return True


# ---- BCPScenario CRUD ----


async def create_scenario(db: AsyncSession, data: dict[str, Any]) -> BCPScenario:
    """Create a new BCP scenario record."""
    obj = BCPScenario(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_scenario(db: AsyncSession, scenario_id: uuid.UUID) -> BCPScenario | None:
    """Get a single BCP scenario record by ID."""
    result = await db.execute(select(BCPScenario).where(BCPScenario.id == scenario_id))
    return result.scalar_one_or_none()


async def get_all_scenarios(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[BCPScenario]:
    """Get all BCP scenario records with pagination."""
    result = await db.execute(select(BCPScenario).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_scenario(db: AsyncSession, scenario_id: uuid.UUID, data: dict[str, Any]) -> BCPScenario | None:
    """Update a BCP scenario record."""
    obj = await get_scenario(db, scenario_id)
    if obj is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(obj, key, value)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_scenario(db: AsyncSession, scenario_id: uuid.UUID) -> bool:
    """Delete a BCP scenario record."""
    obj = await get_scenario(db, scenario_id)
    if obj is None:
        return False
    await db.delete(obj)
    await db.flush()
    return True


# ---- ExerciseRTORecord CRUD ----


async def create_rto_record(db: AsyncSession, data: dict[str, Any]) -> ExerciseRTORecord:
    """Create a new exercise RTO record."""
    obj = ExerciseRTORecord(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_rto_records_by_exercise(db: AsyncSession, exercise_id: uuid.UUID) -> list[ExerciseRTORecord]:
    """Get all RTO records for a given exercise."""
    result = await db.execute(select(ExerciseRTORecord).where(ExerciseRTORecord.exercise_id == exercise_id))
    return list(result.scalars().all())


# ---- IncidentTask CRUD ----


async def create_incident_task(db: AsyncSession, data: dict[str, Any]) -> IncidentTask:
    """Create a new incident task record."""
    obj = IncidentTask(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_incident_task(db: AsyncSession, task_id: uuid.UUID) -> IncidentTask | None:
    """Get a single incident task by ID."""
    result = await db.execute(select(IncidentTask).where(IncidentTask.id == task_id))
    return result.scalar_one_or_none()


async def get_incident_tasks_by_incident(db: AsyncSession, incident_id: uuid.UUID) -> list[IncidentTask]:
    """Get all tasks for a given incident."""
    result = await db.execute(
        select(IncidentTask).where(IncidentTask.incident_id == incident_id).order_by(IncidentTask.created_at)
    )
    return list(result.scalars().all())


async def update_incident_task(db: AsyncSession, task_id: uuid.UUID, data: dict[str, Any]) -> IncidentTask | None:
    """Update an incident task record."""
    obj = await get_incident_task(db, task_id)
    if obj is None:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(obj, key, value)
    await db.flush()
    await db.refresh(obj)
    return obj


async def delete_incident_task(db: AsyncSession, task_id: uuid.UUID) -> bool:
    """Delete an incident task record."""
    obj = await get_incident_task(db, task_id)
    if obj is None:
        return False
    await db.delete(obj)
    await db.flush()
    return True


# ---- SituationReport CRUD ----


async def create_situation_report(db: AsyncSession, data: dict[str, Any]) -> SituationReport:
    """Create a new situation report record."""
    obj = SituationReport(**data)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


async def get_situation_report(db: AsyncSession, report_id: uuid.UUID) -> SituationReport | None:
    """Get a single situation report by ID."""
    result = await db.execute(select(SituationReport).where(SituationReport.id == report_id))
    return result.scalar_one_or_none()


async def get_situation_reports_by_incident(db: AsyncSession, incident_id: uuid.UUID) -> list[SituationReport]:
    """Get all situation reports for a given incident."""
    result = await db.execute(
        select(SituationReport)
        .where(SituationReport.incident_id == incident_id)
        .order_by(SituationReport.report_number)
    )
    return list(result.scalars().all())


# ---- AuditLog CRUD ----


async def create_audit_log(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    user_id: str | None = None,
    user_role: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    status: str = "success",
) -> AuditLog:
    """Persist an audit log entry to the database."""
    entry = AuditLog(
        user_id=user_id,
        user_role=user_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def get_audit_logs(
    db: AsyncSession,
    limit: int = 100,
    resource_type: str | None = None,
    action: str | None = None,
    user_id: str | None = None,
) -> list[AuditLog]:
    """Query audit logs from database with optional filters."""
    stmt = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    if resource_type is not None:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_audit_logs_by_incident(
    db: AsyncSession,
    incident_id: str,
) -> list[AuditLog]:
    """Query audit logs for a specific incident."""
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.resource_type == "incident",
            AuditLog.resource_id == incident_id,
        )
        .order_by(desc(AuditLog.timestamp))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_bcp_statistics(db: AsyncSession) -> dict[str, Any]:
    """Compute aggregate BCP/ITSCM statistics for the dashboard."""
    systems = await get_all_systems(db, limit=10000)
    incidents = await get_all_incidents(db, limit=10000)

    # Systems aggregation
    total_systems = len(systems)
    systems_by_criticality: dict[str, int] = {}
    rto_sum = 0.0
    rto_count = 0
    for s in systems:
        crit = getattr(s, "criticality", "unknown") or "unknown"
        systems_by_criticality[crit] = systems_by_criticality.get(crit, 0) + 1
        if s.rto_target_hours is not None:
            rto_sum += s.rto_target_hours
            rto_count += 1
    avg_rto = round(rto_sum / rto_count, 2) if rto_count > 0 else None

    # Incident aggregation
    active = sum(1 for i in incidents if i.status in ("active", "recovering"))
    resolved = sum(1 for i in incidents if i.status in ("resolved", "closed"))

    # MTTR: mean hours from occurred_at to resolved_at for resolved/closed incidents
    mttr_values: list[float] = []
    for i in incidents:
        if i.status in ("resolved", "closed") and i.occurred_at and i.resolved_at:
            delta_hours = (i.resolved_at - i.occurred_at).total_seconds() / 3600
            if delta_hours >= 0:
                mttr_values.append(delta_hours)
    mttr = round(sum(mttr_values) / len(mttr_values), 2) if mttr_values else None

    # RTO breach: incidents where actual recovery time > minimum RTO target of affected systems
    system_rto_map = {s.system_name: s.rto_target_hours for s in systems if s.rto_target_hours is not None}
    breach_count = 0
    for i in incidents:
        if i.status in ("resolved", "closed") and i.occurred_at and i.resolved_at and i.affected_systems:
            actual_hours = (i.resolved_at - i.occurred_at).total_seconds() / 3600
            rto_targets = [system_rto_map[sys] for sys in i.affected_systems if sys in system_rto_map]
            if rto_targets and actual_hours > min(rto_targets):
                breach_count += 1

    breach_rate = round(breach_count / resolved, 4) if resolved > 0 else None

    return {
        "total_systems": total_systems,
        "systems_by_criticality": systems_by_criticality,
        "avg_rto_target_hours": avg_rto,
        "total_incidents": len(incidents),
        "active_incidents": active,
        "resolved_incidents": resolved,
        "mttr_hours": mttr,
        "rto_breach_count": breach_count,
        "rto_breach_rate": breach_rate,
    }
