"""API routes for IT System BCP management."""

import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.cache import TTL_SYSTEM_LIST, get_cached, invalidate_pattern, set_cached
from apps.schemas import ITSystemBCPCreate, ITSystemBCPResponse, ITSystemBCPUpdate
from database import get_db

router = APIRouter(prefix="/api/systems", tags=["systems"])

_CACHE_NS = "systems:list"


@router.get("", response_model=list[ITSystemBCPResponse])
async def list_systems(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get all IT system BCP records with pagination."""
    cache_key = f"{_CACHE_NS}:{skip}:{limit}"
    cached = await get_cached(cache_key)
    if cached is not None:
        return cached
    result = await crud.get_all_systems(db, skip=skip, limit=limit)
    await set_cached(cache_key, result, TTL_SYSTEM_LIST)
    return result


@router.post("", response_model=ITSystemBCPResponse, status_code=201)
async def create_system(
    payload: ITSystemBCPCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new IT system BCP record."""
    obj = await crud.create_system(db, payload.model_dump())
    await invalidate_pattern(f"{_CACHE_NS}:*")
    return obj


@router.get("/{system_id}", response_model=ITSystemBCPResponse)
async def get_system(
    system_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Get a single IT system BCP record."""
    obj = await crud.get_system(db, system_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="System not found")
    return obj


@router.put("/{system_id}", response_model=ITSystemBCPResponse)
async def update_system(
    system_id: uuid.UUID,
    payload: ITSystemBCPUpdate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Update an IT system BCP record."""
    obj = await crud.update_system(db, system_id, payload.model_dump(exclude_unset=True))
    if obj is None:
        raise HTTPException(status_code=404, detail="System not found")
    await invalidate_pattern(f"{_CACHE_NS}:*")
    return obj


@router.delete("/{system_id}", status_code=204)
async def delete_system(
    system_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an IT system BCP record."""
    deleted = await crud.delete_system(db, system_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="System not found")
    await invalidate_pattern(f"{_CACHE_NS}:*")


_SYSTEM_CSV_FIELDS = [
    "id",
    "system_name",
    "system_type",
    "criticality",
    "rto_target_hours",
    "rpo_target_hours",
    "mtpd_hours",
    "fallback_system",
    "primary_owner",
    "vendor_name",
    "last_dr_test",
    "last_test_rto",
    "is_active",
    "created_at",
    "updated_at",
]


@router.get("/export/csv")
async def export_systems_csv(
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export all IT system BCP records as CSV."""
    records = await crud.get_all_systems(db, skip=0, limit=10000)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_SYSTEM_CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for rec in records:
        row = {f: getattr(rec, f, None) for f in _SYSTEM_CSV_FIELDS}
        writer.writerow(row)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=systems.csv"},
    )
