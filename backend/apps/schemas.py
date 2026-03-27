"""Pydantic schemas for request/response validation."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ---- ITSystemBCP ----


class ITSystemBCPCreate(BaseModel):
    """Schema for creating a new IT system BCP record."""

    system_name: str = Field(..., max_length=100)
    system_type: str = Field(..., pattern=r"^(onprem|cloud|hybrid)$")
    criticality: str = Field(..., pattern=r"^(tier1|tier2|tier3|tier4)$")
    rto_target_hours: float = Field(..., gt=0)
    rpo_target_hours: float = Field(..., gt=0)
    mtpd_hours: float | None = None
    fallback_system: str | None = Field(None, max_length=100)
    fallback_procedure: str | None = None
    primary_owner: str | None = Field(None, max_length=100)
    vendor_name: str | None = Field(None, max_length=100)
    last_dr_test: date | None = None
    last_test_rto: float | None = None
    is_active: bool = True


class ITSystemBCPUpdate(BaseModel):
    """Schema for updating an IT system BCP record."""

    system_name: str | None = Field(None, max_length=100)
    system_type: str | None = Field(None, pattern=r"^(onprem|cloud|hybrid)$")
    criticality: str | None = Field(None, pattern=r"^(tier1|tier2|tier3|tier4)$")
    rto_target_hours: float | None = Field(None, gt=0)
    rpo_target_hours: float | None = Field(None, gt=0)
    mtpd_hours: float | None = None
    fallback_system: str | None = Field(None, max_length=100)
    fallback_procedure: str | None = None
    primary_owner: str | None = Field(None, max_length=100)
    vendor_name: str | None = Field(None, max_length=100)
    last_dr_test: date | None = None
    last_test_rto: float | None = None
    is_active: bool | None = None


class ITSystemBCPResponse(BaseModel):
    """Schema for IT system BCP response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    system_name: str
    system_type: str
    criticality: str
    rto_target_hours: float
    rpo_target_hours: float
    mtpd_hours: float | None = None
    fallback_system: str | None = None
    fallback_procedure: str | None = None
    primary_owner: str | None = None
    vendor_name: str | None = None
    last_dr_test: date | None = None
    last_test_rto: float | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---- BCPExercise ----


class BCPExerciseCreate(BaseModel):
    """Schema for creating a new BCP exercise."""

    exercise_id: str = Field(..., max_length=20)
    title: str = Field(..., max_length=200)
    exercise_type: str = Field(..., pattern=r"^(tabletop|functional|full_scale)$")
    scenario_description: str | None = None
    scheduled_date: datetime
    actual_date: datetime | None = None
    duration_hours: float | None = None
    facilitator: str | None = Field(None, max_length=100)
    status: str = Field("planned", pattern=r"^(planned|in_progress|completed|cancelled)$")
    overall_result: str | None = Field(None, pattern=r"^(pass|partial_pass|fail)$")
    findings: dict | None = None
    improvements: dict | None = None
    lessons_learned: str | None = None


class BCPExerciseUpdate(BaseModel):
    """Schema for updating a BCP exercise."""

    title: str | None = Field(None, max_length=200)
    exercise_type: str | None = Field(None, pattern=r"^(tabletop|functional|full_scale)$")
    scenario_description: str | None = None
    scheduled_date: datetime | None = None
    actual_date: datetime | None = None
    duration_hours: float | None = None
    facilitator: str | None = Field(None, max_length=100)
    status: str | None = Field(None, pattern=r"^(planned|in_progress|completed|cancelled)$")
    overall_result: str | None = Field(None, pattern=r"^(pass|partial_pass|fail)$")
    findings: dict | None = None
    improvements: dict | None = None
    lessons_learned: str | None = None


class BCPExerciseResponse(BaseModel):
    """Schema for BCP exercise response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    exercise_id: str
    title: str
    exercise_type: str
    scenario_description: str | None = None
    scheduled_date: datetime
    actual_date: datetime | None = None
    duration_hours: float | None = None
    facilitator: str | None = None
    status: str
    overall_result: str | None = None
    findings: dict | None = None
    improvements: dict | None = None
    lessons_learned: str | None = None
    created_at: datetime
    updated_at: datetime


# ---- ActiveIncident ----


class ActiveIncidentCreate(BaseModel):
    """Schema for creating a new active incident."""

    incident_id: str = Field(..., max_length=20)
    title: str = Field(..., max_length=300)
    scenario_type: str = Field(
        ...,
        pattern=r"^(earthquake|ransomware|dc_failure|cloud_outage|pandemic|supplier_failure|local_failure)$",
    )
    severity: str = Field(..., pattern=r"^(p1|p2|p3)$")
    occurred_at: datetime
    detected_at: datetime
    declared_at: datetime | None = None
    incident_commander: str | None = Field(None, max_length=100)
    status: str = Field("active", pattern=r"^(active|recovering|resolved|closed)$")
    situation_report: str | None = None
    affected_systems: list[str] | None = None
    affected_users: int | None = None
    estimated_impact: str | None = None
    resolved_at: datetime | None = None
    actual_rto_hours: float | None = None


class ActiveIncidentUpdate(BaseModel):
    """Schema for updating an active incident."""

    title: str | None = Field(None, max_length=300)
    scenario_type: str | None = Field(
        None,
        pattern=r"^(earthquake|ransomware|dc_failure|cloud_outage|pandemic|supplier_failure|local_failure)$",
    )
    severity: str | None = Field(None, pattern=r"^(p1|p2|p3)$")
    occurred_at: datetime | None = None
    detected_at: datetime | None = None
    declared_at: datetime | None = None
    incident_commander: str | None = Field(None, max_length=100)
    status: str | None = Field(None, pattern=r"^(active|recovering|resolved|closed)$")
    situation_report: str | None = None
    affected_systems: list[str] | None = None
    affected_users: int | None = None
    estimated_impact: str | None = None
    resolved_at: datetime | None = None
    actual_rto_hours: float | None = None


class ActiveIncidentResponse(BaseModel):
    """Schema for active incident response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: str
    title: str
    scenario_type: str
    severity: str
    occurred_at: datetime
    detected_at: datetime
    declared_at: datetime | None = None
    incident_commander: str | None = None
    status: str
    situation_report: str | None = None
    affected_systems: list[str] | None = None
    affected_users: int | None = None
    estimated_impact: str | None = None
    resolved_at: datetime | None = None
    actual_rto_hours: float | None = None
    created_at: datetime
    updated_at: datetime


# ---- RTO / Dashboard ----


class RTOStatusResponse(BaseModel):
    """Schema for RTO status of a single system."""

    system_name: str
    status: str  # on_track/at_risk/overdue/recovered/not_started
    color: str
    elapsed_hours: float | None = None
    remaining_hours: float | None = None
    rto_target: float
    overdue_hours: float | None = None


class DashboardResponse(BaseModel):
    """Schema for the overall dashboard response."""

    total_systems: int
    active_incidents: int
    rto_statuses: list[RTOStatusResponse]
    readiness_score: float
    systems_on_track: int
    systems_at_risk: int
    systems_overdue: int
