/**
 * Tests for api.ts — ApiError class, fetchAPI utility, and key API namespaces.
 */
import {
  ApiError,
  fetchAPI,
  systems,
  incidents,
  dashboard,
  escalation,
} from "../lib/api";

// Helper to build a minimal Response-like mock
function mockResponse(
  body: unknown,
  status = 200,
  statusText = "OK"
): Response {
  const json = jest.fn().mockResolvedValue(body);
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    json,
  } as unknown as Response;
}

beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.resetAllMocks();
});

// ─── ApiError ─────────────────────────────────────────────────────────────────

describe("ApiError", () => {
  it("stores status and inherits from Error", () => {
    const err = new ApiError("something went wrong", 404);
    expect(err).toBeInstanceOf(Error);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.message).toBe("something went wrong");
    expect(err.status).toBe(404);
    expect(err.name).toBe("ApiError");
  });

  it("stores optional detail", () => {
    const err = new ApiError("bad request", 400, "field required");
    expect(err.detail).toBe("field required");
  });

  it("detail is undefined when omitted", () => {
    const err = new ApiError("not found", 404);
    expect(err.detail).toBeUndefined();
  });
});

// ─── fetchAPI ─────────────────────────────────────────────────────────────────

describe("fetchAPI", () => {
  it("returns parsed JSON on success", async () => {
    const payload = { id: "1", name: "System A" };
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse(payload));

    const result = await fetchAPI<typeof payload>("/api/systems");
    expect(result).toEqual(payload);
  });

  it("sends Content-Type: application/json by default", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse({}));
    await fetchAPI("/api/systems");

    const [, config] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect((config.headers as Record<string, string>)["Content-Type"]).toBe(
      "application/json"
    );
  });

  it("merges caller-provided headers with defaults", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse({}));
    await fetchAPI("/api/systems", {
      headers: { Authorization: "Bearer token" },
    });

    const [, config] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];
    const headers = config.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");
    expect(headers["Authorization"]).toBe("Bearer token");
  });

  it("throws ApiError on HTTP error status", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockResponse({ detail: "Not found" }, 404, "Not Found")
    );

    await expect(fetchAPI("/api/systems/missing")).rejects.toThrow(ApiError);
    await expect(fetchAPI("/api/systems/missing")).rejects.toMatchObject({
      status: 404,
      detail: "Not found",
    });
  });

  it("falls back to message field when detail is absent", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockResponse({ message: "server error" }, 500, "Internal Server Error")
    );

    await expect(fetchAPI("/api/test")).rejects.toMatchObject({
      status: 500,
      detail: "server error",
    });
  });

  it("throws ApiError with undefined detail when error body is not JSON", async () => {
    const res = {
      ok: false,
      status: 502,
      statusText: "Bad Gateway",
      json: jest.fn().mockRejectedValue(new SyntaxError("not json")),
    } as unknown as Response;
    (global.fetch as jest.Mock).mockResolvedValue(res);

    const err = await fetchAPI("/api/test").catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(502);
    expect(err.detail).toBeUndefined();
  });
});

// ─── systems API ──────────────────────────────────────────────────────────────

describe("systems", () => {
  it("list() calls GET /api/systems", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse([]));
    await systems.list();

    const [url] = (global.fetch as jest.Mock).mock.calls[0] as [string];
    expect(url).toMatch(/\/api\/systems$/);
  });

  it("get() calls GET /api/systems/:id", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse({}));
    await systems.get("abc");

    const [url] = (global.fetch as jest.Mock).mock.calls[0] as [string];
    expect(url).toMatch(/\/api\/systems\/abc$/);
  });

  it("create() sends POST with JSON body", async () => {
    const body = { name: "New System", rto_target: 4 };
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse({ id: "new", ...body }));
    await systems.create(body as Parameters<typeof systems.create>[0]);

    const [url, config] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(url).toMatch(/\/api\/systems$/);
    expect(config.method).toBe("POST");
    expect(JSON.parse(config.body as string)).toMatchObject(body);
  });

  it("delete() sends DELETE to /api/systems/:id", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse(null));
    await systems.delete("xyz");

    const [url, config] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(url).toMatch(/\/api\/systems\/xyz$/);
    expect(config.method).toBe("DELETE");
  });
});

// ─── incidents API ────────────────────────────────────────────────────────────

describe("incidents", () => {
  it("list() calls GET /api/incidents", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse([]));
    await incidents.list();

    const [url] = (global.fetch as jest.Mock).mock.calls[0] as [string];
    expect(url).toMatch(/\/api\/incidents$/);
  });

  it("create() sends POST with correct body", async () => {
    const payload = { title: "DB outage", severity: "critical" };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockResponse({ id: "i1", ...payload })
    );
    await incidents.create(payload as Parameters<typeof incidents.create>[0]);

    const [, config] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(config.method).toBe("POST");
    expect(JSON.parse(config.body as string)).toMatchObject(payload);
  });

  it("rtoDashboard() calls GET /api/incidents/:id/rto-status", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse([]));
    await incidents.rtoDashboard("inc-1");

    const [url] = (global.fetch as jest.Mock).mock.calls[0] as [string];
    expect(url).toMatch(/\/api\/incidents\/inc-1\/rto-status$/);
  });
});

// ─── dashboard.rtoOverview ────────────────────────────────────────────────────

describe("dashboard.rtoOverview", () => {
  it("converts hours to minutes and maps fields correctly", async () => {
    const raw = [
      {
        system_name: "ERP",
        status: "normal",
        elapsed_hours: 2,
        rto_target: 4,
      },
      {
        system_name: "DB",
        status: "warning",
        elapsed_hours: null,
        rto_target: 1,
      },
    ];
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse(raw));

    const result = await dashboard.rtoOverview();

    expect(result.systems).toHaveLength(2);

    const erp = result.systems[0];
    expect(erp.name).toBe("ERP");
    expect(erp.elapsed_minutes).toBe(120); // 2 * 60
    expect(erp.rto_target_minutes).toBe(240); // 4 * 60
    expect(erp.status).toBe("normal");

    const db = result.systems[1];
    expect(db.name).toBe("DB");
    expect(db.elapsed_minutes).toBe(0); // null ?? 0, then * 60
    expect(db.rto_target_minutes).toBe(60); // 1 * 60
  });

  it("handles an empty list", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse([]));

    const result = await dashboard.rtoOverview();
    expect(result.systems).toHaveLength(0);
  });
});

// ─── escalation API ───────────────────────────────────────────────────────────

describe("escalation", () => {
  it("trigger() sends POST with incident data", async () => {
    const payload = { incident_id: "inc-1", severity: "critical" };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockResponse({
        incident_id: "inc-1",
        severity: "critical",
        plan_name: "Critical Plan",
        notifications_queued: 3,
        notifications: [],
      })
    );

    await escalation.trigger(payload);

    const [url, config] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(url).toMatch(/\/api\/escalation\/trigger$/);
    expect(config.method).toBe("POST");
    expect(JSON.parse(config.body as string)).toMatchObject(payload);
  });

  it("plan() calls GET /api/escalation/plan/:severity", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse({}));
    await escalation.plan("high");

    const [url] = (global.fetch as jest.Mock).mock.calls[0] as [string];
    expect(url).toMatch(/\/api\/escalation\/plan\/high$/);
  });

  it("status() calls GET /api/escalation/status/:incidentId", async () => {
    (global.fetch as jest.Mock).mockResolvedValue(mockResponse({}));
    await escalation.status("inc-99");

    const [url] = (global.fetch as jest.Mock).mock.calls[0] as [string];
    expect(url).toMatch(/\/api\/escalation\/status\/inc-99$/);
  });
});
