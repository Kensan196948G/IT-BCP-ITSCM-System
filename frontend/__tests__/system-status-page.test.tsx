/**
 * Tests for app/system-status/page.tsx — SystemStatusPage component.
 *
 * Covers:
 *  - Initial render with mock data (loading state)
 *  - Component health display (Backend API, Database, Redis, Frontend)
 *  - Metrics display (requests, error rate, avg response, active incidents)
 *  - System resources (CPU, Memory, Disk with progress bars)
 *  - Uptime display via formatUptime (days/hours/minutes)
 *  - Fetch success: API data replaces mock data
 *  - Fetch failure: falls back to mock data gracefully
 */
import { render, screen, waitFor, act } from "@testing-library/react";
import React from "react";
import SystemStatusPage from "../app/system-status/page";

// ── Helpers ───────────────────────────────────────────────────────────────────

function mockFetchSuccess(data: Record<string, unknown>) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: jest.fn().mockResolvedValue(data),
  } as unknown as Response);
}

function mockFetchFailure() {
  global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));
}

const apiData = {
  status: "ready",
  checks: [
    { name: "database", status: "healthy", latency_ms: 2.1 },
    { name: "redis", status: "healthy", latency_ms: 0.8 },
  ],
  metrics: {
    request_count: 5000,
    error_count: 10,
    error_rate: 0.002,
    average_duration_seconds: 0.03,
    uptime_seconds: 172800, // 2 days
    active_incidents: 1,
  },
  system: {
    cpu_usage_percent: 65.0,
    memory_usage_percent: 75.0,
    disk_usage_percent: 45.0,
  },
};

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

// ── Initial render (loading + mock data) ────────────────────────────────────

describe("SystemStatusPage initial render", () => {
  it("shows loading text on initial render", () => {
    mockFetchSuccess(apiData);
    render(<SystemStatusPage />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders page heading", () => {
    mockFetchSuccess(apiData);
    render(<SystemStatusPage />);

    expect(screen.getByText("System Status")).toBeInTheDocument();
  });

  it("renders mock data components before fetch completes", () => {
    // Use a fetch that never resolves during this test
    global.fetch = jest.fn().mockImplementation(() => new Promise(() => {}));
    render(<SystemStatusPage />);

    // Mock data has database + redis checks, plus Backend API + Frontend
    expect(screen.getByText("Backend API")).toBeInTheDocument();
    expect(screen.getByText("Database")).toBeInTheDocument();
    expect(screen.getByText("Redis")).toBeInTheDocument();
    expect(screen.getByText("Frontend")).toBeInTheDocument();
  });
});

// ── Fetch success ───────────────────────────────────────────────────────────

describe("SystemStatusPage fetch success", () => {
  it("displays API data after successful fetch", async () => {
    mockFetchSuccess(apiData);

    await act(async () => {
      render(<SystemStatusPage />);
    });

    // metrics.request_count = 5000 → "5,000"
    await waitFor(() => expect(screen.getByText("5,000")).toBeInTheDocument());
    // error_rate 0.002 * 100 = 0.20%
    expect(screen.getByText("0.20%")).toBeInTheDocument();
    // avg response 0.03 * 1000 = 30.0ms
    expect(screen.getByText("30.0ms")).toBeInTheDocument();
    // active incidents = 1
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("displays uptime in days+hours+minutes format", async () => {
    mockFetchSuccess(apiData);

    await act(async () => {
      render(<SystemStatusPage />);
    });

    // 172800s = 2 days 0h 0m → "2d 0h 0m"
    await waitFor(() => expect(screen.getByText("2d 0h 0m")).toBeInTheDocument());
  });

  it("displays system resource percentages", async () => {
    mockFetchSuccess(apiData);

    await act(async () => {
      render(<SystemStatusPage />);
    });

    await waitFor(() => expect(screen.getByText("65%")).toBeInTheDocument());
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("45%")).toBeInTheDocument();
  });

  it("removes loading text after fetch completes", async () => {
    mockFetchSuccess(apiData);

    await act(async () => {
      render(<SystemStatusPage />);
    });

    await waitFor(() => expect(screen.queryByText("Loading...")).not.toBeInTheDocument());
  });
});

// ── Fetch failure (mock data fallback) ──────────────────────────────────────

describe("SystemStatusPage fetch failure", () => {
  it("falls back to mock data when fetch fails", async () => {
    mockFetchFailure();

    await act(async () => {
      render(<SystemStatusPage />);
    });

    // Mock data has request_count: 1024 → "1,024"
    await waitFor(() => expect(screen.getByText("1,024")).toBeInTheDocument());
    // Mock uptime: 86400s = 1d 0h 0m
    expect(screen.getByText("1d 0h 0m")).toBeInTheDocument();
  });

  it("still shows all four component health items on failure", async () => {
    mockFetchFailure();

    await act(async () => {
      render(<SystemStatusPage />);
    });

    await waitFor(() => expect(screen.queryByText("Loading...")).not.toBeInTheDocument());
    expect(screen.getByText("Backend API")).toBeInTheDocument();
    expect(screen.getByText("Database")).toBeInTheDocument();
    expect(screen.getByText("Redis")).toBeInTheDocument();
    expect(screen.getByText("Frontend")).toBeInTheDocument();
  });
});

// ── Component health status indicators ──────────────────────────────────────

describe("SystemStatusPage component health", () => {
  it("shows 'Operational' for healthy components", async () => {
    mockFetchSuccess(apiData);

    await act(async () => {
      render(<SystemStatusPage />);
    });

    await waitFor(() => expect(screen.queryByText("Loading...")).not.toBeInTheDocument());

    // All components are healthy in apiData → all show "Operational"
    const operationalTexts = screen.getAllByText("Operational");
    expect(operationalTexts.length).toBe(4); // Backend API, Database, Redis, Frontend
  });

  it("shows 'Down' for unhealthy components", async () => {
    const unhealthyData = {
      ...apiData,
      status: "degraded",
      checks: [
        { name: "database", status: "unhealthy", latency_ms: 5000 },
        { name: "redis", status: "healthy", latency_ms: 0.5 },
      ],
    };
    mockFetchSuccess(unhealthyData);

    await act(async () => {
      render(<SystemStatusPage />);
    });

    // Flush pending promises so fetch result applies
    await act(async () => { await Promise.resolve(); });

    await waitFor(() => {
      // Backend API is "degraded" (not "ready") → Down
      // Database is "unhealthy" → Down
      const downTexts = screen.getAllByText("Down");
      expect(downTexts.length).toBe(2);
    });
  });
});

// ── formatUptime edge cases ─────────────────────────────────────────────────

describe("SystemStatusPage formatUptime", () => {
  it("shows hours+minutes when uptime < 1 day", async () => {
    const shortUptime = { ...apiData, metrics: { ...apiData.metrics, uptime_seconds: 3661 } };
    mockFetchSuccess(shortUptime);

    await act(async () => {
      render(<SystemStatusPage />);
    });

    // 3661s = 1h 1m
    await waitFor(() => expect(screen.getByText("1h 1m")).toBeInTheDocument());
  });

  it("shows only minutes when uptime < 1 hour", async () => {
    const tinyUptime = { ...apiData, metrics: { ...apiData.metrics, uptime_seconds: 300 } };
    mockFetchSuccess(tinyUptime);

    await act(async () => {
      render(<SystemStatusPage />);
    });

    // 300s = 5m
    await waitFor(() => expect(screen.getByText("5m")).toBeInTheDocument());
  });
});

// ── Metrics sections ────────────────────────────────────────────────────────

describe("SystemStatusPage section headings", () => {
  it("renders all four section headings", async () => {
    mockFetchSuccess(apiData);

    await act(async () => {
      render(<SystemStatusPage />);
    });

    expect(screen.getByText("Component Health")).toBeInTheDocument();
    expect(screen.getByText("Metrics")).toBeInTheDocument();
    expect(screen.getByText("System Resources")).toBeInTheDocument();
    expect(screen.getByText("Uptime")).toBeInTheDocument();
  });
});
