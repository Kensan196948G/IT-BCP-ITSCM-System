"""API routes for Recovery Procedure management."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.models import RecoveryProcedure
from apps.schemas import (
    RecoveryProcedureCreate,
    RecoveryProcedureResponse,
    RecoveryProcedureUpdate,
)
from database import get_db

router = APIRouter(prefix="/api/procedures", tags=["recovery-procedures"])


@router.get("", response_model=list[RecoveryProcedureResponse])
async def list_procedures(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[RecoveryProcedure]:
    """Get all recovery procedure records with pagination."""
    return await crud.get_all_procedures(db, skip=skip, limit=limit)


@router.post("", response_model=RecoveryProcedureResponse, status_code=201)
async def create_procedure(
    payload: RecoveryProcedureCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new recovery procedure record."""
    return await crud.create_procedure(db, payload.model_dump())


@router.get("/{procedure_id}", response_model=RecoveryProcedureResponse)
async def get_procedure(
    procedure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Get a single recovery procedure record."""
    obj = await crud.get_procedure(db, procedure_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return obj


@router.put("/{procedure_id}", response_model=RecoveryProcedureResponse)
async def update_procedure(
    procedure_id: uuid.UUID,
    payload: RecoveryProcedureUpdate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Update a recovery procedure record."""
    obj = await crud.update_procedure(db, procedure_id, payload.model_dump(exclude_unset=True))
    if obj is None:
        raise HTTPException(status_code=404, detail="Procedure not found")
    return obj


@router.delete("/{procedure_id}", status_code=204)
async def delete_procedure(
    procedure_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a recovery procedure record."""
    deleted = await crud.delete_procedure(db, procedure_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Procedure not found")
