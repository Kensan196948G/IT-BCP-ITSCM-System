"""API routes for BCP exercise management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.schemas import BCPExerciseCreate, BCPExerciseResponse, BCPExerciseUpdate
from database import get_db

router = APIRouter(prefix="/api/exercises", tags=["exercises"])


@router.get("", response_model=list[BCPExerciseResponse])
async def list_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get all BCP exercise records with pagination."""
    return await crud.get_all_exercises(db, skip=skip, limit=limit)


@router.post("", response_model=BCPExerciseResponse, status_code=201)
async def create_exercise(
    payload: BCPExerciseCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new BCP exercise record."""
    return await crud.create_exercise(db, payload.model_dump())


@router.get("/{exercise_id}", response_model=BCPExerciseResponse)
async def get_exercise(
    exercise_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Get a single BCP exercise record."""
    obj = await crud.get_exercise(db, exercise_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return obj


@router.put("/{exercise_id}", response_model=BCPExerciseResponse)
async def update_exercise(
    exercise_id: uuid.UUID,
    payload: BCPExerciseUpdate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Update a BCP exercise record."""
    obj = await crud.update_exercise(db, exercise_id, payload.model_dump(exclude_unset=True))
    if obj is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return obj
