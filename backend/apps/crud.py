"""CRUD operations for all models."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.models import (
    ActiveIncident,
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


async def create_system(db: AsyncSession, data: dict) -> ITSystemBCP:
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


async def update_system(db: AsyncSession, system_id: uuid.UUID, data: dict) -> ITSystemBCP | None:
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


async def create_procedure(db: AsyncSession, data: dict) -> RecoveryProcedure:
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


async def update_procedure(db: AsyncSession, procedure_id: uuid.UUID, data: dict) -> RecoveryProcedure | None:
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


async def create_emergency_contact(db: AsyncSession, data: dict) -> EmergencyContact:
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


async def update_emergency_contact(db: AsyncSession, contact_id: uuid.UUID, data: dict) -> EmergencyContact | None:
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


async def create_vendor_contact(db: AsyncSession, data: dict) -> VendorContact:
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


async def update_vendor_contact(db: AsyncSession, contact_id: uuid.UUID, data: dict) -> VendorContact | None:
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


async def create_exercise(db: AsyncSession, data: dict) -> BCPExercise:
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


async def update_exercise(db: AsyncSession, exercise_id: uuid.UUID, data: dict) -> BCPExercise | None:
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


async def create_incident(db: AsyncSession, data: dict) -> ActiveIncident:
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


async def update_incident(db: AsyncSession, incident_id: uuid.UUID, data: dict) -> ActiveIncident | None:
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


async def create_bia_assessment(db: AsyncSession, data: dict) -> BIAAssessment:
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


async def update_bia_assessment(db: AsyncSession, assessment_id: uuid.UUID, data: dict) -> BIAAssessment | None:
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


async def create_scenario(db: AsyncSession, data: dict) -> BCPScenario:
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


async def update_scenario(db: AsyncSession, scenario_id: uuid.UUID, data: dict) -> BCPScenario | None:
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


async def create_rto_record(db: AsyncSession, data: dict) -> ExerciseRTORecord:
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


async def create_incident_task(db: AsyncSession, data: dict) -> IncidentTask:
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


async def update_incident_task(db: AsyncSession, task_id: uuid.UUID, data: dict) -> IncidentTask | None:
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


async def create_situation_report(db: AsyncSession, data: dict) -> SituationReport:
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
