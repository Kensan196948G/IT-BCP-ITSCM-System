/**
 * Tests for app/notifications/page.tsx — NotificationsPage component.
 *
 * Covers:
 *  - Loading state: "読み込み中..." shown while fetching
 *  - Success state: notification logs table rendered after fetch
 *  - Fallback on API error: mock data used when API fails
 *  - Status badges: sent/pending/failed labels and colors
 *  - Channel badges: teams/email/sms labels and colors
 *  - Escalation plan tabs: P1/P2 plan buttons and timeline
 *  - Escalation trigger: confirmation dialog and API call
 *  - Table headers and section headings
 */
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import React from "react";
import NotificationsPage from "../app/notifications/page";
import type { NotificationLog, EscalationPlan } from "../lib/types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockLogs = jest.fn();
const mockPlan = jest.fn();
const mockTrigger = jest.fn();

jest.mock("../lib/api", () => ({
  notifications: {
    logs: (...args: unknown[]) => mockLogs(...args),
  },
  escalation: {
    plan: (...args: unknown[]) => mockPlan(...args),
    trigger: (...args: unknown[]) => mockTrigger(...args),
  },
}));

// ── Test data ────────────────────────────────────────────────────────────────

const SAMPLE_LOGS: NotificationLog[] = [
  {
    id: "log-1",
    notification_type: "teams",
    recipient: "teams-channel",
    subject: "[BCP] Alert L1",
    body: "Level 1 alert",
    status: "sent",
    sent_at: "2026-03-27T10:00:00Z",
    created_at: "2026-03-27T10:00:00Z",
  },
  {
    id: "log-2",
    notification_type: "email",
    recipient: "admin@example.com",
    subject: "[BCP] Alert L2",
    body: "Level 2 alert",
    status: "pending",
    created_at: "2026-03-27T10:05:00Z",
  },
  {
    id: "log-3",
    notification_type: "sms",
    recipient: "+81-90-0000-0000",
    subject: "Emergency",
    body: "SMS failed",
    status: "failed",
    error_message: "Gateway timeout",
    created_at: "2026-03-27T10:10:00Z",
  },
];

const SAMPLE_PLAN_P1: EscalationPlan = {
  severity: "p1",
  plan_name: "P1 Full BCP Activation",
  levels: [
    { level: 1, role: "対応チーム", delay_minutes: 0, channels: ["teams"] },
    { level: 2, role: "IT部門長", delay_minutes: 5, channels: ["teams", "email"] },
  ],
};

const SAMPLE_PLAN_P2: EscalationPlan = {
  severity: "p2",
  plan_name: "P2 Partial BCP Activation",
  levels: [
    { level: 1, role: "対応チーム", delay_minutes: 0, channels: ["teams"] },
  ],
};

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Configure API mocks to return successfully */
function setSuccess(logs: NotificationLog[] = SAMPLE_LOGS) {
  mockLogs.mockResolvedValue(logs);
  mockPlan.mockImplementation((severity: string) => {
    if (severity === "p1") return Promise.resolve(SAMPLE_PLAN_P1);
    if (severity === "p2") return Promise.resolve(SAMPLE_PLAN_P2);
    return Promise.reject(new Error("Unknown severity"));
  });
}

/** Configure API mocks to reject */
function setError() {
  mockLogs.mockRejectedValue(new Error("Network error"));
  mockPlan.mockRejectedValue(new Error("Network error"));
}

/** Configure API to return empty logs (component falls back to mock data) */
function setEmpty() {
  mockLogs.mockResolvedValue([]);
  mockPlan.mockImplementation((severity: string) => {
    if (severity === "p1") return Promise.resolve(SAMPLE_PLAN_P1);
    if (severity === "p2") return Promise.resolve(SAMPLE_PLAN_P2);
    return Promise.reject(new Error("Unknown severity"));
  });
}

/** Configure API to never resolve (stay in loading state) */
function setLoading() {
  mockLogs.mockReturnValue(new Promise(() => {}));
  mockPlan.mockReturnValue(new Promise(() => {}));
}

/** Render the page and wait for async effects to settle */
async function renderPage() {
  let result: ReturnType<typeof render>;
  await act(async () => {
    result = render(<NotificationsPage />);
  });
  return result!;
}

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

// ── Loading state ─────────────────────────────────────────────────────────────

describe("NotificationsPage loading state", () => {
  it("shows loading text while fetching", () => {
    setLoading();
    render(<NotificationsPage />);

    expect(screen.getByText("読み込み中...")).toBeInTheDocument();
  });

  it("does not render the log table while loading", () => {
    setLoading();
    render(<NotificationsPage />);

    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });
});

// ── Success state ─────────────────────────────────────────────────────────────

describe("NotificationsPage success state", () => {
  it("renders the page heading", async () => {
    setSuccess();
    await renderPage();

    expect(screen.getByText("通知管理・エスカレーション")).toBeInTheDocument();
  });

  it("renders notification log subjects after fetch", async () => {
    setSuccess();
    await renderPage();

    expect(screen.getByText("[BCP] Alert L1")).toBeInTheDocument();
    expect(screen.getByText("[BCP] Alert L2")).toBeInTheDocument();
    expect(screen.getByText("Emergency")).toBeInTheDocument();
  });

  it("renders recipients", async () => {
    setSuccess();
    await renderPage();

    expect(screen.getByText("teams-channel")).toBeInTheDocument();
    expect(screen.getByText("admin@example.com")).toBeInTheDocument();
    expect(screen.getByText("+81-90-0000-0000")).toBeInTheDocument();
  });

  it("renders error message for failed notifications", async () => {
    setSuccess();
    await renderPage();

    expect(screen.getByText("Gateway timeout")).toBeInTheDocument();
  });

  it("shows '-' for logs without error messages", async () => {
    setSuccess([SAMPLE_LOGS[0]]);
    await renderPage();

    expect(screen.getByText("-")).toBeInTheDocument();
  });
});

// ── Fallback on API error ────────────────────────────────────────────────────

describe("NotificationsPage API error fallback", () => {
  it("renders mock data when API fails", async () => {
    setError();
    await renderPage();

    // Falls back to internal MOCK_LOGS
    expect(screen.getByText("[BCP Escalation L1] P1 Full BCP Activation")).toBeInTheDocument();
    expect(screen.getByText("[BCP Escalation L2] P1 Full BCP Activation")).toBeInTheDocument();
  });

  it("still renders page heading on error", async () => {
    setError();
    await renderPage();

    expect(screen.getByText("通知管理・エスカレーション")).toBeInTheDocument();
  });
});

// ── Status badges ─────────────────────────────────────────────────────────────

describe("NotificationsPage status badges", () => {
  const cases: Array<[string, string]> = [
    ["sent", "bg-green-100"],
    ["pending", "bg-yellow-100"],
    ["failed", "bg-red-100"],
  ];

  test.each(cases)(
    "status '%s' badge has class '%s'",
    async (status, bgClass) => {
      setSuccess([
        {
          id: `badge-${status}`,
          notification_type: "email",
          recipient: "test@example.com",
          subject: `Test ${status}`,
          body: "body",
          status,
          created_at: "2026-03-27T10:00:00Z",
        },
      ]);
      await renderPage();

      const badge = screen.getByText(status);
      expect(badge.className).toContain(bgClass);
    }
  );
});

// ── Channel badges ────────────────────────────────────────────────────────────

describe("NotificationsPage channel badges", () => {
  const cases: Array<[string, string]> = [
    ["teams", "bg-purple-100"],
    ["email", "bg-blue-100"],
    ["sms", "bg-orange-100"],
  ];

  test.each(cases)(
    "channel '%s' badge has class '%s'",
    async (channel, bgClass) => {
      setSuccess([
        {
          id: `ch-${channel}`,
          notification_type: channel,
          recipient: "test",
          subject: "Test",
          body: "body",
          status: "sent",
          created_at: "2026-03-27T10:00:00Z",
        },
      ]);
      await renderPage();

      // Channel badge in log table row
      const badges = screen.getAllByText(channel);
      const tableBadge = badges.find((el) => el.className.includes(bgClass));
      expect(tableBadge).toBeDefined();
    }
  );
});

// ── Escalation plan tabs ─────────────────────────────────────────────────────

describe("NotificationsPage escalation plan tabs", () => {
  it("renders plan buttons for P1 and P2", async () => {
    setSuccess();
    await renderPage();

    expect(screen.getByText(/P1 - P1 Full BCP Activation/)).toBeInTheDocument();
    expect(screen.getByText(/P2 - P2 Partial BCP Activation/)).toBeInTheDocument();
  });

  it("shows escalation timeline roles for selected plan", async () => {
    setSuccess();
    await renderPage();

    // Default selection is P1
    expect(screen.getByText("対応チーム")).toBeInTheDocument();
    expect(screen.getByText("IT部門長")).toBeInTheDocument();
  });

  it("switches plan when clicking P2 tab", async () => {
    setSuccess();
    await renderPage();

    const p2Button = screen.getByText(/P2 - P2 Partial BCP Activation/);
    fireEvent.click(p2Button);

    // P2 has only level 1: 対応チーム
    expect(screen.getByText("対応チーム")).toBeInTheDocument();
    // IT部門長 should not be visible in P2
    expect(screen.queryByText("IT部門長")).not.toBeInTheDocument();
  });

  it("displays delay minutes in timeline", async () => {
    setSuccess();
    await renderPage();

    expect(screen.getByText("+0min")).toBeInTheDocument();
    expect(screen.getByText("+5min")).toBeInTheDocument();
  });
});

// ── Escalation trigger ───────────────────────────────────────────────────────

describe("NotificationsPage escalation trigger", () => {
  it("shows trigger button", async () => {
    setSuccess();
    await renderPage();

    expect(screen.getByRole("button", { name: "エスカレーション発動" })).toBeInTheDocument();
  });

  it("shows confirmation dialog when trigger button clicked", async () => {
    setSuccess();
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "エスカレーション発動" }));

    expect(screen.getByText(/エスカレーションを発動しますか/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "確認・発動" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "キャンセル" })).toBeInTheDocument();
  });

  it("hides confirmation dialog when cancel clicked", async () => {
    setSuccess();
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "エスカレーション発動" }));
    expect(screen.getByText(/エスカレーションを発動しますか/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "キャンセル" }));
    expect(screen.queryByText(/エスカレーションを発動しますか/)).not.toBeInTheDocument();
  });

  it("calls escalation.trigger on confirm and shows result", async () => {
    setSuccess();
    mockTrigger.mockResolvedValue({
      incident_id: "test-id",
      severity: "p1",
      plan_name: "P1 Full BCP Activation",
      notifications_queued: 4,
      notifications: [],
    });
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "エスカレーション発動" }));

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "確認・発動" }));
    });

    await waitFor(() => {
      expect(mockTrigger).toHaveBeenCalledWith({
        incident_id: "00000000-0000-0000-0000-000000000000",
        severity: "p1",
        contacts: [],
      });
    });

    expect(screen.getByText(/Escalation triggered.*4 notifications queued/)).toBeInTheDocument();
  });

  it("shows failure message when trigger API fails", async () => {
    setSuccess();
    mockTrigger.mockRejectedValue(new Error("API unavailable"));
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "エスカレーション発動" }));

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "確認・発動" }));
    });

    await waitFor(() => {
      expect(screen.getByText(/dry run mode/)).toBeInTheDocument();
    });
  });

  it("allows selecting severity before triggering", async () => {
    setSuccess();
    mockTrigger.mockResolvedValue({
      incident_id: "test-id",
      severity: "p2",
      plan_name: "P2 Partial BCP Activation",
      notifications_queued: 2,
      notifications: [],
    });
    await renderPage();

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "p2" } });

    fireEvent.click(screen.getByRole("button", { name: "エスカレーション発動" }));

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "確認・発動" }));
    });

    await waitFor(() => {
      expect(mockTrigger).toHaveBeenCalledWith(
        expect.objectContaining({ severity: "p2" })
      );
    });
  });

  it("clears trigger result after timeout", async () => {
    setSuccess();
    mockTrigger.mockResolvedValue({
      incident_id: "test-id",
      severity: "p1",
      plan_name: "P1 Full BCP Activation",
      notifications_queued: 4,
      notifications: [],
    });
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "エスカレーション発動" }));

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "確認・発動" }));
    });

    await waitFor(() => {
      expect(screen.getByText(/Escalation triggered/)).toBeInTheDocument();
    });

    // Advance past the 5s timeout
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    expect(screen.queryByText(/Escalation triggered/)).not.toBeInTheDocument();
  });
});

// ── Empty logs fallback ──────────────────────────────────────────────────────

describe("NotificationsPage empty logs", () => {
  it("falls back to mock data when API returns empty array", async () => {
    setEmpty();
    await renderPage();

    // Component does: logsData.length > 0 ? logsData : MOCK_LOGS
    // So empty response => falls back to built-in mock data
    expect(screen.getByText("[BCP Escalation L1] P1 Full BCP Activation")).toBeInTheDocument();
  });
});

// ── Table headers ────────────────────────────────────────────────────────────

describe("NotificationsPage table headers", () => {
  const headers = ["日時", "チャネル", "宛先", "件名", "ステータス", "エラー"];

  test.each(headers)("renders table header '%s'", async (header) => {
    setSuccess();
    await renderPage();

    expect(screen.getByText(header)).toBeInTheDocument();
  });
});

// ── Section headings ─────────────────────────────────────────────────────────

describe("NotificationsPage section headings", () => {
  it("renders 'エスカレーション計画' heading", async () => {
    setSuccess();
    await renderPage();
    expect(screen.getByText("エスカレーション計画")).toBeInTheDocument();
  });

  it("renders 'エスカレーション発動' heading", async () => {
    setSuccess();
    await renderPage();
    // Both h2 and button share this text; verify the heading exists
    const elements = screen.getAllByText("エスカレーション発動");
    const heading = elements.find((el) => el.tagName === "H2");
    expect(heading).toBeDefined();
  });

  it("renders '通知ログ' heading", async () => {
    setSuccess();
    await renderPage();
    expect(screen.getByText("通知ログ")).toBeInTheDocument();
  });
});

// ── Severity select options ──────────────────────────────────────────────────

describe("NotificationsPage severity select", () => {
  it("renders all severity options", async () => {
    setSuccess();
    await renderPage();

    expect(screen.getByText("P1 - Full BCP")).toBeInTheDocument();
    expect(screen.getByText("P2 - Partial BCP")).toBeInTheDocument();
    expect(screen.getByText("P3 - Monitoring")).toBeInTheDocument();
  });
});
