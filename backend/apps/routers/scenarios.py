"""API routes for BCP scenario management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.models import BCPScenario
from apps.schemas import BCPScenarioCreate, BCPScenarioResponse, BCPScenarioUpdate
from database import get_db

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=list[BCPScenarioResponse])
async def list_scenarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[BCPScenario]:
    """Get all BCP scenario records with pagination."""
    return await crud.get_all_scenarios(db, skip=skip, limit=limit)


@router.post("", response_model=BCPScenarioResponse, status_code=201)
async def create_scenario(
    payload: BCPScenarioCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new BCP scenario record."""
    return await crud.create_scenario(db, payload.model_dump())


@router.get("/{scenario_id}", response_model=BCPScenarioResponse)
async def get_scenario(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Get a single BCP scenario record."""
    obj = await crud.get_scenario(db, scenario_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return obj


@router.put("/{scenario_id}", response_model=BCPScenarioResponse)
async def update_scenario(
    scenario_id: uuid.UUID,
    payload: BCPScenarioUpdate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Update a BCP scenario record."""
    obj = await crud.update_scenario(db, scenario_id, payload.model_dump(exclude_unset=True))
    if obj is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return obj


@router.delete("/{scenario_id}", status_code=204)
async def delete_scenario(
    scenario_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a BCP scenario record."""
    deleted = await crud.delete_scenario(db, scenario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scenario not found")
