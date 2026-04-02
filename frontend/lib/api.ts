import type {
  ITSystemBCP,
  BCPExercise,
  ActiveIncident,
  DashboardReadiness,
  RTOOverview,
  RTOStatus,
  RecoveryProcedure,
  EmergencyContact,
  VendorContact,
  BIAAssessment,
  BIASummary,
  RiskMatrixData,
  BCPScenario,
  ExerciseRTORecord,
  ExerciseReport,
  IncidentTask,
  SituationReport,
  IncidentCommandDashboard,
  ReadinessReport,
  RTOComplianceReport,
  ExerciseTrendReport,
  ISO20000Report,
  NotificationLog,
  EscalationPlan,
  EscalationStatus,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json",
  };

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    let detail: string | undefined;
    try {
      const errorBody = await response.json();
      detail = errorBody.detail || errorBody.message;
    } catch {
      // ignore parse error
    }
    throw new ApiError(
      `API Error: ${response.status} ${response.statusText}`,
      response.status,
      detail
    );
  }

  return response.json() as Promise<T>;
}

// Systems API
export const systems = {
  list: () => fetchAPI<ITSystemBCP[]>("/api/systems"),

  get: (id: string) => fetchAPI<ITSystemBCP>(`/api/systems/${id}`),

  create: (data: Omit<ITSystemBCP, "id" | "created_at">) =>
    fetchAPI<ITSystemBCP>("/api/systems", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<ITSystemBCP>) =>
    fetchAPI<ITSystemBCP>(`/api/systems/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchAPI<void>(`/api/systems/${id}`, {
      method: "DELETE",
    }),
};

// Exercises API
export const exercises = {
  list: () => fetchAPI<BCPExercise[]>("/api/exercises"),

  get: (id: string) => fetchAPI<BCPExercise>(`/api/exercises/${id}`),

  create: (data: Omit<BCPExercise, "id" | "created_at">) =>
    fetchAPI<BCPExercise>("/api/exercises", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<BCPExercise>) =>
    fetchAPI<BCPExercise>(`/api/exercises/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  start: (id: string) =>
    fetchAPI<BCPExercise>(`/api/exercises/${id}/start`, {
      method: "POST",
    }),

  inject: (id: string, inject_index: number) =>
    fetchAPI<Record<string, unknown>>(`/api/exercises/${id}/inject`, {
      method: "POST",
      body: JSON.stringify({ inject_index }),
    }),

  recordRto: (id: string, data: { system_name: string; rto_target_hours: number; rto_actual_hours?: number; recorded_by?: string; notes?: string }) =>
    fetchAPI<ExerciseRTORecord>(`/api/exercises/${id}/rto-record`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  complete: (id: string) =>
    fetchAPI<BCPExercise>(`/api/exercises/${id}/complete`, {
      method: "POST",
    }),

  report: (id: string) =>
    fetchAPI<ExerciseReport>(`/api/exercises/${id}/report`),
};

// Incidents API
export const incidents = {
  list: () => fetchAPI<ActiveIncident[]>("/api/incidents"),

  get: (id: string) => fetchAPI<ActiveIncident>(`/api/incidents/${id}`),

  create: (data: Omit<ActiveIncident, "id" | "created_at">) =>
    fetchAPI<ActiveIncident>("/api/incidents", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<ActiveIncident>) =>
    fetchAPI<ActiveIncident>(`/api/incidents/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  rtoDashboard: (incidentId: string) =>
    fetchAPI<RTOStatus[]>(`/api/incidents/${incidentId}/rto-status`),

  commandDashboard: (incidentId: string) =>
    fetchAPI<IncidentCommandDashboard>(
      `/api/incidents/${incidentId}/command-dashboard`
    ),

  createTask: (
    incidentId: string,
    data: Omit<IncidentTask, "id" | "incident_id" | "created_at" | "updated_at">
  ) =>
    fetchAPI<IncidentTask>(`/api/incidents/${incidentId}/tasks`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listTasks: (incidentId: string) =>
    fetchAPI<IncidentTask[]>(`/api/incidents/${incidentId}/tasks`),

  updateTask: (incidentId: string, taskId: string, data: Partial<IncidentTask>) =>
    fetchAPI<IncidentTask>(`/api/incidents/${incidentId}/tasks/${taskId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  createReport: (
    incidentId: string,
    data: Omit<SituationReport, "id" | "incident_id" | "created_at">
  ) =>
    fetchAPI<SituationReport>(
      `/api/incidents/${incidentId}/situation-reports`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    ),

  listReports: (incidentId: string) =>
    fetchAPI<SituationReport[]>(
      `/api/incidents/${incidentId}/situation-reports`
    ),

  autoGenerateReport: (incidentId: string) =>
    fetchAPI<SituationReport>(
      `/api/incidents/${incidentId}/situation-reports/auto-generate`,
      { method: "POST" }
    ),
};

// Dashboard API
export const dashboard = {
  readiness: () =>
    fetchAPI<DashboardReadiness>("/api/dashboard/readiness"),

  rtoOverview: async (): Promise<RTOOverview> => {
    // Backend returns RTOStatusResponse[] (array with hours units).
    // Transform to RTOOverview { systems: RTOMonitorSystem[] } (minutes units).
    type RawItem = {
      system_name: string;
      status: string;
      elapsed_hours: number | null;
      rto_target: number;
    };
    const list = await fetchAPI<RawItem[]>("/api/dashboard/rto-overview");
    return {
      systems: list.map((s) => ({
        name: s.system_name,
        rto_target_minutes: s.rto_target * 60,
        elapsed_minutes: (s.elapsed_hours ?? 0) * 60,
        status: s.status,
      })),
    };
  },

  reports: {
    readiness: () =>
      fetchAPI<ReadinessReport>("/api/dashboard/reports/readiness"),

    rtoCompliance: () =>
      fetchAPI<RTOComplianceReport>("/api/dashboard/reports/rto-compliance"),

    exerciseTrends: () =>
      fetchAPI<ExerciseTrendReport>("/api/dashboard/reports/exercise-trends"),

    iso20000: () =>
      fetchAPI<ISO20000Report>("/api/dashboard/reports/iso20000"),
  },
};

// Procedures API
export const procedures = {
  list: () => fetchAPI<RecoveryProcedure[]>("/api/procedures"),

  get: (id: string) => fetchAPI<RecoveryProcedure>(`/api/procedures/${id}`),

  create: (data: Omit<RecoveryProcedure, "id" | "created_at" | "updated_at">) =>
    fetchAPI<RecoveryProcedure>("/api/procedures", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<RecoveryProcedure>) =>
    fetchAPI<RecoveryProcedure>(`/api/procedures/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchAPI<void>(`/api/procedures/${id}`, {
      method: "DELETE",
    }),
};

// Contacts API
export const contacts = {
  emergency: {
    list: () => fetchAPI<EmergencyContact[]>("/api/contacts/emergency"),

    get: (id: string) =>
      fetchAPI<EmergencyContact>(`/api/contacts/emergency/${id}`),

    create: (data: Omit<EmergencyContact, "id" | "created_at" | "updated_at">) =>
      fetchAPI<EmergencyContact>("/api/contacts/emergency", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  vendors: {
    list: () => fetchAPI<VendorContact[]>("/api/contacts/vendors"),

    get: (id: string) =>
      fetchAPI<VendorContact>(`/api/contacts/vendors/${id}`),

    create: (data: Omit<VendorContact, "id" | "created_at" | "updated_at">) =>
      fetchAPI<VendorContact>("/api/contacts/vendors", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
};

// BIA API
export const biaApi = {
  list: () => fetchAPI<BIAAssessment[]>("/api/bia"),

  get: (id: string) => fetchAPI<BIAAssessment>(`/api/bia/${id}`),

  create: (data: Omit<BIAAssessment, "id" | "created_at" | "updated_at">) =>
    fetchAPI<BIAAssessment>("/api/bia", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<BIAAssessment>) =>
    fetchAPI<BIAAssessment>(`/api/bia/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchAPI<void>(`/api/bia/${id}`, {
      method: "DELETE",
    }),

  summary: () => fetchAPI<BIASummary>("/api/bia/summary"),

  riskMatrix: () => fetchAPI<RiskMatrixData>("/api/bia/risk-matrix"),
};

// Scenarios API
export const scenariosApi = {
  list: () => fetchAPI<BCPScenario[]>("/api/scenarios"),

  get: (id: string) => fetchAPI<BCPScenario>(`/api/scenarios/${id}`),

  create: (data: Omit<BCPScenario, "id" | "created_at" | "updated_at">) =>
    fetchAPI<BCPScenario>("/api/scenarios", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// Notifications API
export const notifications = {
  send: (data: {
    notification_type: string;
    recipient: string;
    subject: string;
    body: string;
    incident_id?: string;
  }) =>
    fetchAPI<NotificationLog>("/api/notifications/send", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  logs: () => fetchAPI<NotificationLog[]>("/api/notifications/logs"),

  logsByIncident: (incidentId: string) =>
    fetchAPI<NotificationLog[]>(`/api/notifications/logs/${incidentId}`),
};

// Escalation API
export const escalation = {
  trigger: (data: {
    incident_id: string;
    severity: string;
    contacts?: { role: string; name: string; email?: string; teams_id?: string }[];
  }) =>
    fetchAPI<{
      incident_id: string;
      severity: string;
      plan_name: string;
      notifications_queued: number;
      notifications: NotificationLog[];
    }>("/api/escalation/trigger", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  plan: (severity: string) =>
    fetchAPI<EscalationPlan>(`/api/escalation/plan/${severity}`),

  status: (incidentId: string) =>
    fetchAPI<EscalationStatus>(`/api/escalation/status/${incidentId}`),
};

export { fetchAPI };
