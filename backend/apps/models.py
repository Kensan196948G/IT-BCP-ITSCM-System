"""SQLAlchemy ORM models for IT-BCP-ITSCM-System."""

import uuid
from datetime import date as date_type
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
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
    procedure_steps: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
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
    notification_channels: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
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
    findings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    improvements: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BIAAssessment(Base):
    """Business Impact Analysis assessment table."""

    __tablename__ = "bia_assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    system_name: Mapped[str] = mapped_column(String(100), nullable=False)
    assessment_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    assessor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    business_processes: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    financial_impact_per_hour: Mapped[float | None] = mapped_column(Float, nullable=True)
    financial_impact_per_day: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_tolerable_downtime_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    regulatory_risks: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    reputation_impact: Mapped[str | None] = mapped_column(String(20), nullable=True)
    operational_impact: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recommended_rto_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_rpo_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mitigation_measures: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scenario_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bcp_scenarios.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BCPScenario(Base):
    """BCP scenario templates for tabletop exercises."""

    __tablename__ = "bcp_scenarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    initial_inject: Mapped[str] = mapped_column(Text, nullable=False)
    injects: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    affected_systems: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    expected_duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ExerciseRTORecord(Base):
    """RTO achievement records per exercise per system."""

    __tablename__ = "exercise_rto_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("bcp_exercises.id"), nullable=False)
    system_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rto_target_hours: Mapped[float] = mapped_column(Float, nullable=False)
    rto_actual_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    achieved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    recorded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


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
    affected_systems: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)  # list of system names
    affected_users: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_rto_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IncidentTask(Base):
    """Tasks assigned during an active incident."""

    __tablename__ = "incident_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # References active_incidents.id (no FK constraint)
    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    task_title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_team: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # critical/high/medium/low
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/in_progress/completed/blocked
    target_system: Mapped[str | None] = mapped_column(String(100), nullable=True)
    due_hours: Mapped[float | None] = mapped_column(Float, nullable=True)  # deadline: N hours from occurrence
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NotificationLog(Base):
    """Notification log records for tracking all sent notifications."""

    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    notification_type: Mapped[str] = mapped_column(String(30), nullable=False)  # teams/email/sms
    recipient: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/sent/failed
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    """Audit log for tracking all user actions (ISO20000 compliance)."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="success")


class SituationReport(Base):
    """Situation reports for an active incident."""

    __tablename__ = "situation_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # References active_incidents.id (no FK constraint)
    incident_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    report_number: Mapped[int] = mapped_column(Integer, nullable=False)
    report_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reporter: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    systems_status: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    tasks_summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    next_actions: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    escalation_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    audience: Mapped[str] = mapped_column(String(50), default="internal")  # internal/management/executive/external
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
