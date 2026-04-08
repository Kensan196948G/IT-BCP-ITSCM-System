"""API routes for BCP exercise management."""

import csv
import io
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.cache import TTL_EXERCISE_LIST, get_cached, invalidate_pattern, set_cached
from apps.exercise_engine import ExerciseEngine
from apps.schemas import (
    BCPExerciseCreate,
    BCPExerciseResponse,
    BCPExerciseUpdate,
    ExerciseReportResponse,
    ExerciseRTORecordCreate,
    ExerciseRTORecordResponse,
    InjectRequest,
)
from database import get_db

router = APIRouter(prefix="/api/exercises", tags=["exercises"])

_CACHE_NS = "exercises:list"


@router.get("", response_model=list[BCPExerciseResponse])
async def list_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[Any]:
    """Get all BCP exercise records with pagination."""
    cache_key = f"{_CACHE_NS}:{skip}:{limit}"
    cached = await get_cached(cache_key)
    if cached is not None:
        return list(cached)
    result = await crud.get_all_exercises(db, skip=skip, limit=limit)
    await set_cached(cache_key, result, TTL_EXERCISE_LIST)
    return result


@router.post("", response_model=BCPExerciseResponse, status_code=201)
async def create_exercise(
    payload: BCPExerciseCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new BCP exercise record."""
    obj = await crud.create_exercise(db, payload.model_dump())
    await invalidate_pattern(f"{_CACHE_NS}:*")
    return obj


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
    await invalidate_pattern(f"{_CACHE_NS}:*")
    return obj


# ---------------------------------------------------------------------------
# Exercise Engine endpoints
# ---------------------------------------------------------------------------


@router.post("/{exercise_id}/start", response_model=BCPExerciseResponse)
async def start_exercise(
    exercise_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Start a planned exercise (set status to in_progress)."""
    engine = ExerciseEngine(db)
    try:
        return await engine.start_exercise(exercise_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{exercise_id}/inject")
async def inject_scenario(
    exercise_id: uuid.UUID,
    payload: InjectRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Inject a scenario step into a running exercise."""
    engine = ExerciseEngine(db)
    try:
        return await engine.inject_scenario(exercise_id, payload.inject_index)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post(
    "/{exercise_id}/rto-record",
    response_model=ExerciseRTORecordResponse,
    status_code=201,
)
async def record_rto(
    exercise_id: uuid.UUID,
    payload: ExerciseRTORecordCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Record an RTO measurement for a system in an exercise."""
    engine = ExerciseEngine(db)
    try:
        return await engine.record_rto(
            exercise_id=exercise_id,
            system_name=payload.system_name,
            rto_target_hours=payload.rto_target_hours,
            rto_actual_hours=payload.rto_actual_hours,
            recorded_by=payload.recorded_by,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{exercise_id}/complete", response_model=BCPExerciseResponse)
async def complete_exercise(
    exercise_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Complete an exercise and compute overall result."""
    engine = ExerciseEngine(db)
    try:
        return await engine.complete_exercise(exercise_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{exercise_id}/report", response_model=ExerciseReportResponse)
async def get_exercise_report(
    exercise_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate a comprehensive exercise report."""
    engine = ExerciseEngine(db)
    try:
        return await engine.generate_report(exercise_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


_EXERCISE_CSV_FIELDS = [
    "id",
    "exercise_id",
    "title",
    "exercise_type",
    "scenario_description",
    "scheduled_date",
    "actual_date",
    "duration_hours",
    "facilitator",
    "status",
    "overall_result",
    "lessons_learned",
    "created_at",
    "updated_at",
]


@router.get("/export/csv")
async def export_exercises_csv(
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export all BCP exercise records as CSV."""
    records = await crud.get_all_exercises(db, skip=0, limit=10000)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_EXERCISE_CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for rec in records:
        row = {f: getattr(rec, f, None) for f in _EXERCISE_CSV_FIELDS}
        writer.writerow(row)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=exercises.csv"},
    )
