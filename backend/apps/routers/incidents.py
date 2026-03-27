"""API routes for active incident management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.rto_tracker import RTOTracker
from apps.schemas import ActiveIncidentCreate, ActiveIncidentResponse, ActiveIncidentUpdate, RTOStatusResponse
from database import get_db

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
