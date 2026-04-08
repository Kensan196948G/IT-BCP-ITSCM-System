"""API routes for BIA (Business Impact Analysis) management."""

import csv
import io
import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.bia_calculator import get_bia_summary, get_risk_matrix
from apps.cache import TTL_BIA, get_cached, set_cached
from apps.schemas import (
    BIAAssessmentCreate,
    BIAAssessmentResponse,
    BIAAssessmentUpdate,
    BIASummaryResponse,
    CSVImportResponse,
    RiskMatrixResponse,
)
from database import get_db

router = APIRouter(prefix="/api/bia", tags=["bia"])

_CACHE_BIA_SUMMARY = "bia:summary"
_CACHE_BIA_RISK_MATRIX = "bia:risk-matrix"


@router.get("", response_model=list[BIAAssessmentResponse])
async def list_bia_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[Any]:
    """Get all BIA assessment records with pagination."""
    return await crud.get_all_bia_assessments(db, skip=skip, limit=limit)


@router.post("", response_model=BIAAssessmentResponse, status_code=201)
async def create_bia_assessment(
    payload: BIAAssessmentCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new BIA assessment record."""
    return await crud.create_bia_assessment(db, payload.model_dump())


@router.get("/summary", response_model=BIASummaryResponse)
async def bia_summary(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get aggregated BIA summary statistics."""
    cached = await get_cached(_CACHE_BIA_SUMMARY)
    if cached is not None:
        return cached

    assessments = await crud.get_all_bia_assessments(db, skip=0, limit=1000)
    result = get_bia_summary(assessments)
    await set_cached(_CACHE_BIA_SUMMARY, result, TTL_BIA)
    return result


@router.get("/risk-matrix", response_model=RiskMatrixResponse)
async def bia_risk_matrix(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get risk matrix data for all assessments."""
    cached = await get_cached(_CACHE_BIA_RISK_MATRIX)
    if cached is not None:
        return cached

    assessments = await crud.get_all_bia_assessments(db, skip=0, limit=1000)
    result = get_risk_matrix(assessments)
    await set_cached(_CACHE_BIA_RISK_MATRIX, result, TTL_BIA)
    return result


@router.get("/{assessment_id}", response_model=BIAAssessmentResponse)
async def get_bia_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Get a single BIA assessment record."""
    obj = await crud.get_bia_assessment(db, assessment_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="BIA assessment not found")
    return obj


@router.put("/{assessment_id}", response_model=BIAAssessmentResponse)
async def update_bia_assessment(
    assessment_id: uuid.UUID,
    payload: BIAAssessmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Update a BIA assessment record."""
    obj = await crud.update_bia_assessment(db, assessment_id, payload.model_dump(exclude_unset=True))
    if obj is None:
        raise HTTPException(status_code=404, detail="BIA assessment not found")
    return obj


@router.delete("/{assessment_id}", status_code=204)
async def delete_bia_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a BIA assessment record."""
    deleted = await crud.delete_bia_assessment(db, assessment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="BIA assessment not found")


_BIA_CSV_FIELDS = [
    "id",
    "assessment_id",
    "system_name",
    "assessment_date",
    "assessor",
    "financial_impact_per_hour",
    "financial_impact_per_day",
    "max_tolerable_downtime_hours",
    "reputation_impact",
    "operational_impact",
    "recommended_rto_hours",
    "recommended_rpo_hours",
    "risk_score",
    "status",
    "notes",
    "created_at",
    "updated_at",
]


_BIA_IMPORT_SCALAR_FIELDS = [
    "assessment_id",
    "system_name",
    "assessment_date",
    "assessor",
    "financial_impact_per_hour",
    "financial_impact_per_day",
    "max_tolerable_downtime_hours",
    "reputation_impact",
    "operational_impact",
    "recommended_rto_hours",
    "recommended_rpo_hours",
    "risk_score",
    "status",
    "notes",
]
_BIA_FLOAT_FIELDS = {
    "financial_impact_per_hour",
    "financial_impact_per_day",
    "max_tolerable_downtime_hours",
    "recommended_rto_hours",
    "recommended_rpo_hours",
}
_BIA_INT_FIELDS = {"risk_score"}
_BIA_JSON_FIELDS = {"business_processes", "regulatory_risks", "mitigation_measures"}
_BIA_OPTIONAL_SCALAR = {
    "assessor",
    "financial_impact_per_hour",
    "financial_impact_per_day",
    "max_tolerable_downtime_hours",
    "reputation_impact",
    "operational_impact",
    "recommended_rto_hours",
    "recommended_rpo_hours",
    "risk_score",
    "notes",
}


def _coerce_bia_row(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce CSV string values to correct Python types for BIAAssessmentCreate."""
    result: dict[str, Any] = {}
    for field in _BIA_IMPORT_SCALAR_FIELDS:
        raw = row.get(field, "").strip() if row.get(field) is not None else ""
        if raw == "" and field in _BIA_OPTIONAL_SCALAR:
            result[field] = None
            continue
        if field in _BIA_FLOAT_FIELDS:
            result[field] = float(raw) if raw else None
        elif field in _BIA_INT_FIELDS:
            result[field] = int(raw) if raw else None
        else:
            result[field] = raw if raw else None
    # JSON-encoded list fields (business_processes, regulatory_risks, mitigation_measures)
    for field in _BIA_JSON_FIELDS:
        raw = row.get(field, "").strip() if row.get(field) is not None else ""
        if raw:
            try:
                result[field] = json.loads(raw)
            except json.JSONDecodeError:
                # Treat as single-element list if not valid JSON
                result[field] = [raw]
        else:
            result[field] = [] if field == "business_processes" else None
    return result


@router.post("/import/csv", response_model=CSVImportResponse, status_code=201)
async def import_bia_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Bulk-import BIA assessment records from a CSV file.

    The CSV must include a header row with at minimum:
    assessment_id, system_name, assessment_date.
    List fields (business_processes, regulatory_risks, mitigation_measures)
    should be JSON-encoded arrays. Extra columns are ignored.
    """
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    skipped = 0
    errors: list[dict[str, Any]] = []

    for row_num, row in enumerate(reader, start=2):
        try:
            raw_data = _coerce_bia_row(row)
            # Exclude None values so Pydantic applies field defaults (e.g. status="draft")
            data = {k: v for k, v in raw_data.items() if v is not None}
            payload = BIAAssessmentCreate(**data)
            await crud.create_bia_assessment(db, payload.model_dump())
            imported += 1
        except (ValidationError, ValueError, TypeError) as exc:
            errors.append({"row": row_num, "error": str(exc)})
            skipped += 1

    return {
        "total_rows": imported + skipped,
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }


@router.get("/export/csv")
async def export_bia_csv(
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export all BIA assessment records as CSV."""
    records = await crud.get_all_bia_assessments(db, skip=0, limit=10000)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_BIA_CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for rec in records:
        row = {f: getattr(rec, f, None) for f in _BIA_CSV_FIELDS}
        writer.writerow(row)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bia_assessments.csv"},
    )
