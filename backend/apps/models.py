"""SQLAlchemy ORM models for IT-BCP-ITSCM-System."""

import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ITSystemBCP(Base):
    """IT systems BCP registration table."""

    __tablename__ = "it_systems_bcp"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    system_type: Mapped[str] = mapped_column(String(30), nullable=False)  # onprem/cloud/hybrid
    criticality: Mapped[str] = mapped_column(String(20), nullable=False)  # tier1/tier2/tier3/tier4
    rto_target_hours: Mapped[float] = mapped_column(Float, nullable=False)
    rpo_target_hours: Mapped[float] = mapped_column(Float, nullable=False)
    mtpd_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    fallback_system: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fallback_procedure: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vendor_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_dr_test: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    last_test_rto: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RecoveryProcedure(Base):
    """Recovery procedure documents table."""

    __tablename__ = "recovery_procedures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    procedure_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    system_name: Mapped[str] = mapped_column(String(100), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    priority_order: Mapped[int] = mapped_column(Integer, nullable=False)
    pre_requisites: Mapped[str | None] = mapped_column(Text, nullable=True)
    procedure_steps: Mapped[list] = mapped_column(JSON, nullable=False)
    estimated_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    responsible_team: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_reviewed: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    review_cycle_months: Mapped[int] = mapped_column(Integer, default=12)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EmergencyContact(Base):
    """Emergency contact list table."""

    __tablename__ = "emergency_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone_primary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone_secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    teams_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    escalation_level: Mapped[int] = mapped_column(Integer, nullable=False)
    escalation_group: Mapped[str] = mapped_column(String(50), nullable=False)
    notification_channels: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VendorContact(Base):
    """Vendor contact information table."""

    __tablename__ = "vendor_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    service_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contract_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    support_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone_primary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone_emergency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email_support: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sla_response_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    sla_resolution_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    contract_expiry: Mapped[date_type | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BCPExercise(Base):
    """BCP exercise / drill records table."""

    __tablename__ = "bcp_exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g. EX-2026-001
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    exercise_type: Mapped[str] = mapped_column(String(30), nullable=False)  # tabletop/functional/full_scale
    scenario_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    facilitator: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planned")  # planned/in_progress/completed/cancelled
    overall_result: Mapped[str | None] = mapped_column(String(20), nullable=True)  # pass/partial_pass/fail
    findings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    improvements: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ActiveIncident(Base):
    """Active BCP incident tracking table."""

    __tablename__ = "active_incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # e.g. BCP-2026-001
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    scenario_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # earthquake/ransomware/dc_failure/cloud_outage/pandemic/supplier_failure/local_failure
    severity: Mapped[str] = mapped_column(String(10), nullable=False)  # p1/p2/p3
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    declared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    incident_commander: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/recovering/resolved/closed
    situation_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_systems: Mapped[list | None] = mapped_column(JSON, nullable=True)  # list of system names
    affected_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_rto_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
