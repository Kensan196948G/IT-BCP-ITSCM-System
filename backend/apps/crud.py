"""CRUD operations for all models."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.models import ActiveIncident, BCPExercise, ITSystemBCP


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
