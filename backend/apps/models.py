"""SQLAlchemy ORM models for IT-BCP-ITSCM-System."""

import uuid
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
