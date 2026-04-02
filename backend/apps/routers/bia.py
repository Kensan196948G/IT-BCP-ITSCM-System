"""API routes for BIA (Business Impact Analysis) management."""

import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.bia_calculator import get_bia_summary, get_risk_matrix
from apps.cache import TTL_BIA, get_cached, set_cached
from apps.schemas import (
    BIAAssessmentCreate,
    BIAAssessmentResponse,
    BIAAssessmentUpdate,
    BIASummaryResponse,
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
) -> list:
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
) -> dict:
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
) -> dict:
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
