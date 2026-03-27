"""API routes for BIA (Business Impact Analysis) management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.bia_calculator import get_bia_summary, get_risk_matrix
from apps.schemas import (
    BIAAssessmentCreate,
    BIAAssessmentResponse,
    BIAAssessmentUpdate,
    BIASummaryResponse,
    RiskMatrixResponse,
)
from database import get_db

router = APIRouter(prefix="/api/bia", tags=["bia"])


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
    assessments = await crud.get_all_bia_assessments(db, skip=0, limit=1000)
    return get_bia_summary(assessments)


@router.get("/risk-matrix", response_model=RiskMatrixResponse)
async def bia_risk_matrix(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get risk matrix data for all assessments."""
    assessments = await crud.get_all_bia_assessments(db, skip=0, limit=1000)
    return get_risk_matrix(assessments)


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
