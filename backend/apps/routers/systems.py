"""API routes for IT System BCP management."""

import csv
import io
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.cache import TTL_SYSTEM_LIST, get_cached, invalidate_pattern, set_cached
from apps.schemas import CSVImportResponse, ITSystemBCPCreate, ITSystemBCPResponse, ITSystemBCPUpdate
from database import get_db

router = APIRouter(prefix="/api/systems", tags=["systems"])

_CACHE_NS = "systems:list"


@router.get("", response_model=list[ITSystemBCPResponse])
async def list_systems(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[Any]:
    """Get all IT system BCP records with pagination."""
    cache_key = f"{_CACHE_NS}:{skip}:{limit}"
    cached = await get_cached(cache_key)
    if cached is not None:
        return list(cached)
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


_SYSTEM_IMPORT_FIELDS = [
    "system_name",
    "system_type",
    "criticality",
    "rto_target_hours",
    "rpo_target_hours",
    "mtpd_hours",
    "fallback_system",
    "fallback_procedure",
    "primary_owner",
    "vendor_name",
    "last_dr_test",
    "last_test_rto",
    "is_active",
]

_SYSTEM_FLOAT_FIELDS = {"rto_target_hours", "rpo_target_hours", "mtpd_hours", "last_test_rto"}
_SYSTEM_BOOL_FIELDS = {"is_active"}
_SYSTEM_OPTIONAL_FIELDS = {
    "mtpd_hours",
    "fallback_system",
    "fallback_procedure",
    "primary_owner",
    "vendor_name",
    "last_dr_test",
    "last_test_rto",
}


def _coerce_system_row(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce CSV string values to correct Python types for ITSystemBCPCreate."""
    result: dict[str, Any] = {}
    for field in _SYSTEM_IMPORT_FIELDS:
        raw = row.get(field, "").strip() if row.get(field) is not None else ""
        if raw == "" and field in _SYSTEM_OPTIONAL_FIELDS:
            result[field] = None
            continue
        if field in _SYSTEM_FLOAT_FIELDS:
            result[field] = float(raw) if raw else None
        elif field in _SYSTEM_BOOL_FIELDS:
            result[field] = raw.lower() in ("true", "1", "yes")
        else:
            result[field] = raw if raw else None
    return result


@router.post("/import/csv", response_model=CSVImportResponse, status_code=201)
async def import_systems_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Bulk-import IT system BCP records from a CSV file.

    The CSV must include a header row with at minimum:
    system_name, system_type, criticality, rto_target_hours, rpo_target_hours.
    Extra columns are ignored; missing optional columns default to null.
    """
    content = await file.read()
    text = content.decode("utf-8-sig")  # strip BOM if present
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    skipped = 0
    errors: list[dict[str, Any]] = []

    for row_num, row in enumerate(reader, start=2):  # row 1 = header
        try:
            data = _coerce_system_row(row)
            payload = ITSystemBCPCreate(**data)
            await crud.create_system(db, payload.model_dump())
            imported += 1
        except (ValidationError, ValueError, TypeError) as exc:
            errors.append({"row": row_num, "error": str(exc)})
            skipped += 1

    if imported > 0:
        await invalidate_pattern(f"{_CACHE_NS}:*")

    return {
        "total_rows": imported + skipped,
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }
