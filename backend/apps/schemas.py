"""Pydantic schemas for request/response validation."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

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

    @field_validator("system_name")
    @classmethod
    def system_name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("system_name must not be blank")
        return v.strip()


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


# ---- RecoveryProcedure ----


class RecoveryProcedureCreate(BaseModel):
    """Schema for creating a new recovery procedure."""

    procedure_id: str = Field(..., max_length=20)
    system_name: str = Field(..., max_length=100)
    scenario_type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=300)
    version: str = Field("1.0", max_length=20)
    priority_order: int = Field(..., ge=1)
    pre_requisites: str | None = None
    procedure_steps: list = Field(...)
    estimated_time_hours: float | None = None
    responsible_team: str | None = Field(None, max_length=100)
    last_reviewed: date | None = None
    review_cycle_months: int = 12
    status: str = Field("active", pattern=r"^(active|draft|archived)$")

    @field_validator("procedure_id")
    @classmethod
    def procedure_id_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("procedure_id must not be blank")
        return v.strip()


class RecoveryProcedureUpdate(BaseModel):
    """Schema for updating a recovery procedure."""

    system_name: str | None = Field(None, max_length=100)
    scenario_type: str | None = Field(None, max_length=50)
    title: str | None = Field(None, max_length=300)
    version: str | None = Field(None, max_length=20)
    priority_order: int | None = Field(None, ge=1)
    pre_requisites: str | None = None
    procedure_steps: list | None = None
    estimated_time_hours: float | None = None
    responsible_team: str | None = Field(None, max_length=100)
    last_reviewed: date | None = None
    review_cycle_months: int | None = None
    status: str | None = Field(None, pattern=r"^(active|draft|archived)$")


class RecoveryProcedureResponse(BaseModel):
    """Schema for recovery procedure response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    procedure_id: str
    system_name: str
    scenario_type: str
    title: str
    version: str
    priority_order: int
    pre_requisites: str | None = None
    procedure_steps: list
    estimated_time_hours: float | None = None
    responsible_team: str | None = None
    last_reviewed: date | None = None
    review_cycle_months: int
    status: str
    created_at: datetime
    updated_at: datetime


# ---- EmergencyContact ----


class EmergencyContactCreate(BaseModel):
    """Schema for creating a new emergency contact."""

    name: str = Field(..., max_length=100)
    role: str = Field(..., max_length=100)
    department: str | None = Field(None, max_length=100)
    phone_primary: str | None = Field(None, max_length=20)
    phone_secondary: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=200)
    teams_id: str | None = Field(None, max_length=200)
    escalation_level: int = Field(..., ge=1)
    escalation_group: str = Field(..., max_length=50)
    notification_channels: list[str] | None = None
    is_active: bool = True
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class EmergencyContactUpdate(BaseModel):
    """Schema for updating an emergency contact."""

    name: str | None = Field(None, max_length=100)
    role: str | None = Field(None, max_length=100)
    department: str | None = Field(None, max_length=100)
    phone_primary: str | None = Field(None, max_length=20)
    phone_secondary: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=200)
    teams_id: str | None = Field(None, max_length=200)
    escalation_level: int | None = Field(None, ge=1)
    escalation_group: str | None = Field(None, max_length=50)
    notification_channels: list[str] | None = None
    is_active: bool | None = None
    notes: str | None = None


class EmergencyContactResponse(BaseModel):
    """Schema for emergency contact response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    role: str
    department: str | None = None
    phone_primary: str | None = None
    phone_secondary: str | None = None
    email: str | None = None
    teams_id: str | None = None
    escalation_level: int
    escalation_group: str
    notification_channels: list[str] | None = None
    is_active: bool
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


# ---- VendorContact ----


class VendorContactCreate(BaseModel):
    """Schema for creating a new vendor contact."""

    vendor_name: str = Field(..., max_length=200)
    service_name: str = Field(..., max_length=200)
    contract_id: str | None = Field(None, max_length=100)
    support_level: str | None = Field(None, pattern=r"^(premier|standard|basic)$")
    phone_primary: str | None = Field(None, max_length=20)
    phone_emergency: str | None = Field(None, max_length=20)
    email_support: str | None = Field(None, max_length=200)
    sla_response_hours: float | None = None
    sla_resolution_hours: float | None = None
    contract_expiry: date | None = None
    notes: str | None = None
    is_active: bool = True

    @field_validator("vendor_name")
    @classmethod
    def vendor_name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("vendor_name must not be blank")
        return v.strip()


class VendorContactUpdate(BaseModel):
    """Schema for updating a vendor contact."""

    vendor_name: str | None = Field(None, max_length=200)
    service_name: str | None = Field(None, max_length=200)
    contract_id: str | None = Field(None, max_length=100)
    support_level: str | None = Field(None, pattern=r"^(premier|standard|basic)$")
    phone_primary: str | None = Field(None, max_length=20)
    phone_emergency: str | None = Field(None, max_length=20)
    email_support: str | None = Field(None, max_length=200)
    sla_response_hours: float | None = None
    sla_resolution_hours: float | None = None
    contract_expiry: date | None = None
    notes: str | None = None
    is_active: bool | None = None


class VendorContactResponse(BaseModel):
    """Schema for vendor contact response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_name: str
    service_name: str
    contract_id: str | None = None
    support_level: str | None = None
    phone_primary: str | None = None
    phone_emergency: str | None = None
    email_support: str | None = None
    sla_response_hours: float | None = None
    sla_resolution_hours: float | None = None
    contract_expiry: date | None = None
    notes: str | None = None
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

    @field_validator("exercise_type")
    @classmethod
    def validate_exercise_type(cls, v: str) -> str:
        allowed = ("tabletop", "functional", "full_scale")
        if v not in allowed:
            raise ValueError(f"exercise_type must be one of {allowed}")
        return v


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

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = ("p1", "p2", "p3")
        if v not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return v


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


# ---- BIAAssessment ----


IMPACT_LEVELS = r"^(none|low|medium|high|critical)$"
BIA_STATUSES = r"^(draft|reviewed|approved)$"


class BIAAssessmentCreate(BaseModel):
    """Schema for creating a new BIA assessment."""

    assessment_id: str = Field(..., max_length=20)
    system_name: str = Field(..., max_length=100)
    assessment_date: date
    assessor: str | None = Field(None, max_length=100)
    business_processes: list = Field(...)
    financial_impact_per_hour: float | None = None
    financial_impact_per_day: float | None = None
    max_tolerable_downtime_hours: float | None = None
    regulatory_risks: list | None = None
    reputation_impact: str | None = Field(None, pattern=IMPACT_LEVELS)
    operational_impact: str | None = Field(None, pattern=IMPACT_LEVELS)
    recommended_rto_hours: float | None = None
    recommended_rpo_hours: float | None = None
    risk_score: int | None = Field(None, ge=1, le=100)
    mitigation_measures: list | None = None
    status: str = Field("draft", pattern=BIA_STATUSES)
    notes: str | None = None

    @field_validator("assessment_id")
    @classmethod
    def assessment_id_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("assessment_id must not be blank")
        return v.strip()


class BIAAssessmentUpdate(BaseModel):
    """Schema for updating a BIA assessment."""

    system_name: str | None = Field(None, max_length=100)
    assessment_date: date | None = None
    assessor: str | None = Field(None, max_length=100)
    business_processes: list | None = None
    financial_impact_per_hour: float | None = None
    financial_impact_per_day: float | None = None
    max_tolerable_downtime_hours: float | None = None
    regulatory_risks: list | None = None
    reputation_impact: str | None = Field(None, pattern=IMPACT_LEVELS)
    operational_impact: str | None = Field(None, pattern=IMPACT_LEVELS)
    recommended_rto_hours: float | None = None
    recommended_rpo_hours: float | None = None
    risk_score: int | None = Field(None, ge=1, le=100)
    mitigation_measures: list | None = None
    status: str | None = Field(None, pattern=BIA_STATUSES)
    notes: str | None = None


class BIAAssessmentResponse(BaseModel):
    """Schema for BIA assessment response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: str
    system_name: str
    assessment_date: date
    assessor: str | None = None
    business_processes: list
    financial_impact_per_hour: float | None = None
    financial_impact_per_day: float | None = None
    max_tolerable_downtime_hours: float | None = None
    regulatory_risks: list | None = None
    reputation_impact: str | None = None
    operational_impact: str | None = None
    recommended_rto_hours: float | None = None
    recommended_rpo_hours: float | None = None
    risk_score: int | None = None
    mitigation_measures: list | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class BIASummaryResponse(BaseModel):
    """Schema for BIA summary overview."""

    total_assessments: int
    average_risk_score: float | None = None
    max_risk_score: int | None = None
    highest_risk_system: str | None = None
    impact_distribution: dict = Field(default_factory=dict)
    average_financial_impact_per_day: float | None = None
    status_distribution: dict = Field(default_factory=dict)


class RiskMatrixEntry(BaseModel):
    """Single cell in the risk matrix."""

    impact_level: int  # 1-5
    likelihood_level: int  # 1-5
    system_name: str
    risk_score: int


class RiskMatrixResponse(BaseModel):
    """Schema for the risk matrix API response."""

    entries: list[RiskMatrixEntry]
    matrix: list[list[int]]  # 5x5 count matrix


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


# ---- BCPScenario ----


SCENARIO_TYPES = r"^(earthquake|ransomware|dc_failure|cloud_outage|pandemic|supplier_failure)$"
DIFFICULTY_LEVELS = r"^(easy|medium|hard)$"


class BCPScenarioCreate(BaseModel):
    """Schema for creating a new BCP scenario."""

    scenario_id: str = Field(..., max_length=20)
    title: str = Field(..., max_length=200)
    scenario_type: str = Field(
        ...,
        pattern=SCENARIO_TYPES,
    )
    description: str
    initial_inject: str
    injects: list = Field(...)
    affected_systems: list[str] | None = None
    expected_duration_hours: float | None = None
    difficulty: str = Field("medium", pattern=DIFFICULTY_LEVELS)
    is_active: bool = True

    @field_validator("scenario_id")
    @classmethod
    def scenario_id_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("scenario_id must not be blank")
        return v.strip()


class BCPScenarioUpdate(BaseModel):
    """Schema for updating a BCP scenario."""

    title: str | None = Field(None, max_length=200)
    scenario_type: str | None = Field(None, pattern=SCENARIO_TYPES)
    description: str | None = None
    initial_inject: str | None = None
    injects: list | None = None
    affected_systems: list[str] | None = None
    expected_duration_hours: float | None = None
    difficulty: str | None = Field(None, pattern=DIFFICULTY_LEVELS)
    is_active: bool | None = None


class BCPScenarioResponse(BaseModel):
    """Schema for BCP scenario response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scenario_id: str
    title: str
    scenario_type: str
    description: str
    initial_inject: str
    injects: list
    affected_systems: list[str] | None = None
    expected_duration_hours: float | None = None
    difficulty: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---- ExerciseRTORecord ----


class ExerciseRTORecordCreate(BaseModel):
    """Schema for creating an exercise RTO record."""

    system_name: str = Field(..., max_length=100)
    rto_target_hours: float = Field(..., gt=0)
    rto_actual_hours: float | None = None
    achieved: bool | None = None
    recorded_by: str | None = Field(None, max_length=100)
    notes: str | None = None


class ExerciseRTORecordResponse(BaseModel):
    """Schema for exercise RTO record response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    exercise_id: uuid.UUID
    system_name: str
    rto_target_hours: float
    rto_actual_hours: float | None = None
    achieved: bool | None = None
    recorded_at: datetime
    recorded_by: str | None = None
    notes: str | None = None


# ---- ExerciseReport ----


class ExerciseReportResponse(BaseModel):
    """Schema for exercise report with RTO records, findings, recommendations."""

    exercise: BCPExerciseResponse
    rto_records: list[ExerciseRTORecordResponse] = Field(default_factory=list)
    rto_achievement_rate: float | None = None
    total_systems_tested: int = 0
    systems_achieved: int = 0
    systems_failed: int = 0
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


# ---- Exercise Engine request schemas ----


class InjectRequest(BaseModel):
    """Schema for injecting a scenario step into an exercise."""

    inject_index: int = Field(..., ge=0)


# ---- IncidentTask ----

TASK_PRIORITIES = r"^(critical|high|medium|low)$"
TASK_STATUSES = r"^(pending|in_progress|completed|blocked)$"


class IncidentTaskCreate(BaseModel):
    """Schema for creating a new incident task."""

    task_title: str = Field(..., max_length=300)
    description: str | None = None
    assigned_to: str | None = Field(None, max_length=100)
    assigned_team: str | None = Field(None, max_length=100)
    priority: str = Field("medium", pattern=TASK_PRIORITIES)
    status: str = Field("pending", pattern=TASK_STATUSES)
    target_system: str | None = Field(None, max_length=100)
    due_hours: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None


class IncidentTaskUpdate(BaseModel):
    """Schema for updating an incident task."""

    task_title: str | None = Field(None, max_length=300)
    description: str | None = None
    assigned_to: str | None = Field(None, max_length=100)
    assigned_team: str | None = Field(None, max_length=100)
    priority: str | None = Field(None, pattern=TASK_PRIORITIES)
    status: str | None = Field(None, pattern=TASK_STATUSES)
    target_system: str | None = Field(None, max_length=100)
    due_hours: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None


class IncidentTaskResponse(BaseModel):
    """Schema for incident task response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    task_title: str
    description: str | None = None
    assigned_to: str | None = None
    assigned_team: str | None = None
    priority: str
    status: str
    target_system: str | None = None
    due_hours: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


# ---- SituationReport ----

AUDIENCE_TYPES = r"^(internal|management|executive|external)$"


class SituationReportCreate(BaseModel):
    """Schema for creating a new situation report."""

    report_number: int = Field(..., ge=1)
    report_time: datetime | None = None
    reporter: str | None = Field(None, max_length=100)
    summary: str
    systems_status: dict | None = None
    tasks_summary: dict | None = None
    next_actions: list | None = None
    escalation_status: str | None = Field(None, max_length=50)
    audience: str = Field("internal", pattern=AUDIENCE_TYPES)


class SituationReportResponse(BaseModel):
    """Schema for situation report response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    report_number: int
    report_time: datetime
    reporter: str | None = None
    summary: str
    systems_status: dict | None = None
    tasks_summary: dict | None = None
    next_actions: list | None = None
    escalation_status: str | None = None
    audience: str
    created_at: datetime


# ---- IncidentCommandDashboard ----


class TaskStatistics(BaseModel):
    """Task completion statistics."""

    total: int = 0
    pending: int = 0
    in_progress: int = 0
    completed: int = 0
    blocked: int = 0
    completion_rate: float = 0.0


class IncidentCommandDashboard(BaseModel):
    """Command dashboard data combining incident, tasks, reports, and RTO status."""

    incident: ActiveIncidentResponse
    tasks: list[IncidentTaskResponse] = Field(default_factory=list)
    task_statistics: TaskStatistics = Field(default_factory=TaskStatistics)
    latest_report: SituationReportResponse | None = None
    reports_count: int = 0
    rto_statuses: list[RTOStatusResponse] = Field(default_factory=list)


# ---- Report Responses ----


class SystemReadinessDetail(BaseModel):
    """Detail for a single system in the readiness report."""

    system_name: str
    rto_target_hours: float
    rpo_target_hours: float
    last_test_rto_hours: float | None = None
    rto_achieved: bool
    tested: bool
    has_fallback: bool
    readiness_score: float


class ReadinessReportResponse(BaseModel):
    """Schema for BCP Readiness Report (RPT-001)."""

    report_id: str
    report_type: str
    generated_at: str
    overall_score: float
    total_systems: int
    tested_systems: int
    rto_met_systems: int
    system_readiness: list[SystemReadinessDetail]
    untested_systems: list[str]
    recommendations: list[str]


class SystemComplianceDetail(BaseModel):
    """Detail for a single system in the compliance report."""

    system_name: str
    rto_target_hours: float
    rto_actual_hours: float | None = None
    deviation_hours: float | None = None
    compliant: bool
    trend: str


class RTOComplianceReportResponse(BaseModel):
    """Schema for RTO/RPO Compliance Report (RPT-002)."""

    report_id: str
    report_type: str
    generated_at: str
    compliance_rate: float
    total_systems: int
    compliant_systems: int
    system_compliance: list[SystemComplianceDetail]
    overdue_systems: list[str]


class YearlyTrendEntry(BaseModel):
    """Yearly exercise trend data."""

    year: int
    exercise_count: int
    completed: int
    pass_count: int
    achievement_rate: float = 0.0


class ExerciseTrendReportResponse(BaseModel):
    """Schema for Exercise Trend Report (RPT-003)."""

    report_id: str
    report_type: str
    generated_at: str
    total_exercises: int
    yearly_trends: list[YearlyTrendEntry]
    common_issues: dict = Field(default_factory=dict)
    total_improvements: int
    completed_improvements: int
    improvement_completion_rate: float


# ---- Notification / Escalation ----


class NotificationSendRequest(BaseModel):
    """Schema for sending a notification manually."""

    notification_type: str = Field(..., pattern=r"^(teams|email|sms)$")
    recipient: str = Field(..., max_length=200)
    subject: str = Field(..., max_length=300)
    body: str
    incident_id: uuid.UUID | None = None


class NotificationLogResponse(BaseModel):
    """Schema for notification log response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID | None = None
    notification_type: str
    recipient: str
    subject: str
    body: str
    status: str
    sent_at: datetime | None = None
    error_message: str | None = None
    metadata: dict | None = None
    created_at: datetime


class EscalationLevel(BaseModel):
    """A single escalation level definition."""

    level: int
    role: str
    delay_minutes: int
    channels: list[str]


class EscalationPlanResponse(BaseModel):
    """Schema for escalation plan response."""

    severity: str
    plan_name: str
    levels: list[EscalationLevel]


class EscalationContact(BaseModel):
    """Contact info for escalation trigger."""

    role: str
    name: str
    email: str | None = None
    teams_id: str | None = None


class EscalationTriggerRequest(BaseModel):
    """Schema for triggering an escalation."""

    incident_id: uuid.UUID
    severity: str = Field(..., pattern=r"^(p1|p2|p3)$")
    contacts: list[EscalationContact] = Field(default_factory=list)


class EscalationTriggerResponse(BaseModel):
    """Schema for escalation trigger response."""

    incident_id: uuid.UUID
    severity: str
    plan_name: str
    notifications_queued: int
    notifications: list[NotificationLogResponse]


class EscalationStatusResponse(BaseModel):
    """Schema for escalation status."""

    incident_id: uuid.UUID
    total_notifications: int
    sent: int
    pending: int
    failed: int
    notifications: list[NotificationLogResponse]


class ChecklistItemResult(BaseModel):
    """Result for a single ISO20000 checklist item."""

    id: str
    requirement: str
    category: str
    compliant: bool
    evidence: str


# ---- Auth / JWT ----


class LoginRequest(BaseModel):
    """Schema for login request (simplified)."""

    user_id: str = Field(..., max_length=100)
    password: str = Field("", max_length=200)
    role: str = Field("viewer", pattern=r"^(admin|operator|viewer|auditor)$")


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """Schema for current user info."""

    user_id: str
    role: str
    permissions: list[str]


# ---- AuditLog ----


class AuditLogResponse(BaseModel):
    """Schema for a single audit log entry."""

    id: str
    timestamp: str
    user_id: str | None = None
    user_role: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    status: str = "success"


class AuditLogExportResponse(BaseModel):
    """Schema for audit log export (ISO20000)."""

    format: str = "json"
    exported_at: str
    total_count: int
    standard: str = "ISO20000-ITSCM"
    logs: list[AuditLogResponse]


class ISO20000ReportResponse(BaseModel):
    """Schema for ISO20000 ITSCM Compliance Report (RPT-004)."""

    report_id: str
    report_type: str
    generated_at: str
    compliance_rate: float
    total_items: int
    compliant_items: int
    checklist_results: list[ChecklistItemResult]
    non_compliant_items: list[ChecklistItemResult]
    next_audit_actions: list[str]
