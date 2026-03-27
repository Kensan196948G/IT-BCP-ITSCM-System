"""API routes for Emergency Contact and Vendor Contact management."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.schemas import (
    EmergencyContactCreate,
    EmergencyContactResponse,
    EmergencyContactUpdate,
    VendorContactCreate,
    VendorContactResponse,
    VendorContactUpdate,
)
from database import get_db

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


# ---- Emergency Contacts ----


@router.get("/emergency", response_model=list[EmergencyContactResponse])
async def list_emergency_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get all emergency contact records with pagination."""
    return await crud.get_all_emergency_contacts(db, skip=skip, limit=limit)


@router.post("/emergency", response_model=EmergencyContactResponse, status_code=201)
async def create_emergency_contact(
    payload: EmergencyContactCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new emergency contact record."""
    return await crud.create_emergency_contact(db, payload.model_dump())


@router.get("/emergency/escalation/{group}", response_model=list[EmergencyContactResponse])
async def get_emergency_contacts_by_escalation(
    group: str,
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get emergency contacts filtered by escalation group."""
    return await crud.get_emergency_contacts_by_escalation_group(db, group)


@router.get("/emergency/{contact_id}", response_model=EmergencyContactResponse)
async def get_emergency_contact(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Get a single emergency contact record."""
    obj = await crud.get_emergency_contact(db, contact_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Emergency contact not found")
    return obj


@router.put("/emergency/{contact_id}", response_model=EmergencyContactResponse)
async def update_emergency_contact(
    contact_id: uuid.UUID,
    payload: EmergencyContactUpdate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Update an emergency contact record."""
    obj = await crud.update_emergency_contact(db, contact_id, payload.model_dump(exclude_unset=True))
    if obj is None:
        raise HTTPException(status_code=404, detail="Emergency contact not found")
    return obj


@router.delete("/emergency/{contact_id}", status_code=204)
async def delete_emergency_contact(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an emergency contact record."""
    deleted = await crud.delete_emergency_contact(db, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Emergency contact not found")


# ---- Vendor Contacts ----


@router.get("/vendors", response_model=list[VendorContactResponse])
async def list_vendor_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get all vendor contact records with pagination."""
    return await crud.get_all_vendor_contacts(db, skip=skip, limit=limit)


@router.post("/vendors", response_model=VendorContactResponse, status_code=201)
async def create_vendor_contact(
    payload: VendorContactCreate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Create a new vendor contact record."""
    return await crud.create_vendor_contact(db, payload.model_dump())


@router.get("/vendors/{contact_id}", response_model=VendorContactResponse)
async def get_vendor_contact(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Get a single vendor contact record."""
    obj = await crud.get_vendor_contact(db, contact_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Vendor contact not found")
    return obj


@router.put("/vendors/{contact_id}", response_model=VendorContactResponse)
async def update_vendor_contact(
    contact_id: uuid.UUID,
    payload: VendorContactUpdate,
    db: AsyncSession = Depends(get_db),
) -> object:
    """Update a vendor contact record."""
    obj = await crud.update_vendor_contact(db, contact_id, payload.model_dump(exclude_unset=True))
    if obj is None:
        raise HTTPException(status_code=404, detail="Vendor contact not found")
    return obj


@router.delete("/vendors/{contact_id}", status_code=204)
async def delete_vendor_contact(
    contact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a vendor contact record."""
    deleted = await crud.delete_vendor_contact(db, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vendor contact not found")
