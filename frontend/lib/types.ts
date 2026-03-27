// IT-BCP-ITSCM-System 型定義
// バックエンドPydanticスキーマに対応

export interface ITSystemBCP {
  id: string;
  system_name: string;
  system_type: string;       // onprem / cloud / hybrid / saas
  criticality: string;       // tier1 / tier2 / tier3 / tier4
  rto_target_hours: number;
  rpo_target_hours: number;
  mtpd_hours?: number;
  fallback_system?: string;
  fallback_procedure?: string;
  depends_on?: string[];
  supports?: string[];
  primary_owner_id?: string;
  secondary_owner_id?: string;
  vendor_contact_id?: string;
  last_dr_test?: string;
  last_test_rto?: number;
  created_at?: string;
}

export interface BCPExercise {
  id: string;
  exercise_id: string;
  title: string;
  exercise_type: string;     // tabletop / functional / full_scale
  scenario_id?: string;
  scheduled_date: string;
  actual_date?: string;
  duration_hours?: number;
  participants?: string[];
  facilitator_id?: string;
  status: string;            // planned / in_progress / completed
  overall_result?: string;   // pass / partial_pass / fail
  systems_tested?: SystemTestResult[];
  findings?: Finding[];
  improvements?: Improvement[];
  lessons_learned?: string;
  created_at?: string;
}

export interface SystemTestResult {
  system_name: string;
  rto_target: number;
  rto_actual: number;
  achieved: boolean;
}

export interface Finding {
  id: string;
  description: string;
  severity: string;
}

export interface Improvement {
  id: string;
  description: string;
  status: string;
  due_date?: string;
}

export interface ActiveIncident {
  id: string;
  incident_id: string;
  title: string;
  scenario_type: string;     // earthquake / ransomware / dc_failure / etc
  severity: string;          // p1 / p2 / p3
  occurred_at: string;
  detected_at: string;
  declared_at?: string;
  incident_commander_id?: string;
  status: string;            // active / recovering / resolved
  situation_report?: string;
  affected_systems?: string[];
  affected_users?: number;
  estimated_impact?: string;
  recovery_tasks?: RecoveryTask[];
  rto_status?: RTOStatus[];
  resolved_at?: string;
  actual_rto_hours?: number;
  created_at?: string;
}

export interface RecoveryTask {
  id: string;
  description: string;
  status: string;
  assignee?: string;
}

export interface RTOStatus {
  system_name: string;
  status: string;            // on_track / at_risk / overdue / recovered / not_started
  color: string;
  elapsed_hours: number;
  remaining_hours?: number;
  rto_target: number;
  overdue_hours?: number;
  actual_rto?: number;
  achieved?: boolean;
}

export interface DashboardReadiness {
  readiness_score: number;
  total_systems: number;
  rto_achievement_rate: number;
  rpo_achievement_rate: number;
  active_incidents: number;
  recent_exercises: DashboardExercise[];
  active_incident_list: DashboardIncident[];
  next_exercise?: DashboardNextExercise;
}

export interface DashboardExercise {
  id: string;
  title: string;
  date: string;
  result: string;
}

export interface DashboardIncident {
  id: string;
  title: string;
  severity: string;
}

export interface DashboardNextExercise {
  title: string;
  date: string;
  type: string;
}

export interface RTOOverview {
  systems: RTOMonitorSystem[];
}

export interface RTOMonitorSystem {
  name: string;
  rto_target_minutes: number;
  elapsed_minutes: number;
  status: string;            // on_track / at_risk / overdue / recovered / not_started
}

export interface RecoveryProcedure {
  id: string;
  procedure_id: string;
  system_name: string;
  scenario_type: string;
  title: string;
  version: string;
  priority_order: number;
  pre_requisites?: string;
  procedure_steps: { step: number; description: string; duration_minutes?: number }[];
  estimated_time_hours?: number;
  responsible_team?: string;
  last_reviewed?: string;
  review_cycle_months: number;
  status: string;             // active / draft / archived
  created_at?: string;
  updated_at?: string;
}

export interface EmergencyContact {
  id: string;
  name: string;
  role: string;
  department?: string;
  phone_primary?: string;
  phone_secondary?: string;
  email?: string;
  teams_id?: string;
  escalation_level: number;
  escalation_group: string;
  notification_channels?: string[];
  is_active: boolean;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface VendorContact {
  id: string;
  vendor_name: string;
  service_name: string;
  contract_id?: string;
  support_level?: string;    // premier / standard / basic
  phone_primary?: string;
  phone_emergency?: string;
  email_support?: string;
  sla_response_hours?: number;
  sla_resolution_hours?: number;
  contract_expiry?: string;
  notes?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// ---- BIA ----

export interface BIAAssessment {
  id: string;
  assessment_id: string;
  system_name: string;
  assessment_date: string;
  assessor?: string;
  business_processes: string[];
  financial_impact_per_hour?: number;
  financial_impact_per_day?: number;
  max_tolerable_downtime_hours?: number;
  regulatory_risks?: string[];
  reputation_impact?: string;    // none / low / medium / high / critical
  operational_impact?: string;   // none / low / medium / high / critical
  recommended_rto_hours?: number;
  recommended_rpo_hours?: number;
  risk_score?: number;           // 1-100
  mitigation_measures?: string[];
  status: string;                // draft / reviewed / approved
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface BIASummary {
  total_assessments: number;
  average_risk_score?: number;
  max_risk_score?: number;
  highest_risk_system?: string;
  impact_distribution: Record<string, number>;
  average_financial_impact_per_day?: number;
  status_distribution: Record<string, number>;
}

export interface RiskMatrixEntry {
  impact_level: number;      // 1-5
  likelihood_level: number;  // 1-5
  system_name: string;
  risk_score: number;
}

export interface RiskMatrixData {
  entries: RiskMatrixEntry[];
  matrix: number[][];         // 5x5
}

// API response wrapper
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiListResponse<T> {
  data: T[];
  total?: number;
  page?: number;
  page_size?: number;
}

// API error
export interface ApiError {
  message: string;
  status: number;
  detail?: string;
}
