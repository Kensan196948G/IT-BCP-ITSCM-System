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
} from "./types";

const API_BASE_URL =
  (typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_URL
    : process.env.NEXT_PUBLIC_API_URL) || "http://localhost:8000";

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
  list: () => fetchAPI<ITSystemBCP[]>("/api/v1/systems"),

  get: (id: string) => fetchAPI<ITSystemBCP>(`/api/v1/systems/${id}`),

  create: (data: Omit<ITSystemBCP, "id" | "created_at">) =>
    fetchAPI<ITSystemBCP>("/api/v1/systems", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<ITSystemBCP>) =>
    fetchAPI<ITSystemBCP>(`/api/v1/systems/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchAPI<void>(`/api/v1/systems/${id}`, {
      method: "DELETE",
    }),
};

// Exercises API
export const exercises = {
  list: () => fetchAPI<BCPExercise[]>("/api/v1/exercises"),

  get: (id: string) => fetchAPI<BCPExercise>(`/api/v1/exercises/${id}`),

  create: (data: Omit<BCPExercise, "id" | "created_at">) =>
    fetchAPI<BCPExercise>("/api/v1/exercises", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<BCPExercise>) =>
    fetchAPI<BCPExercise>(`/api/v1/exercises/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};

// Incidents API
export const incidents = {
  list: () => fetchAPI<ActiveIncident[]>("/api/v1/incidents"),

  get: (id: string) => fetchAPI<ActiveIncident>(`/api/v1/incidents/${id}`),

  create: (data: Omit<ActiveIncident, "id" | "created_at">) =>
    fetchAPI<ActiveIncident>("/api/v1/incidents", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<ActiveIncident>) =>
    fetchAPI<ActiveIncident>(`/api/v1/incidents/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  rtoDashboard: (incidentId: string) =>
    fetchAPI<RTOStatus[]>(`/api/v1/incidents/${incidentId}/rto-status`),
};

// Dashboard API
export const dashboard = {
  readiness: () =>
    fetchAPI<DashboardReadiness>("/api/v1/dashboard/readiness"),

  rtoOverview: () =>
    fetchAPI<RTOOverview>("/api/v1/dashboard/rto-overview"),
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

export { fetchAPI };
