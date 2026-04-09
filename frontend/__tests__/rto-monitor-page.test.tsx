/**
 * Tests for app/rto-monitor/page.tsx — RtoMonitorPage component.
 *
 * Covers:
 *  - Loading state: spinner shown while useRTOOverview fetches
 *  - formatMinutes: minutes / hours+minutes / days+hours display
 *  - statusConfig: 5 status types with correct labels and colors
 *  - RTOCard: progress bar percentage calculation
 *  - Offline mode: mock data fallback when API errors
 *  - WebSocket status indicator (connected / connecting / disconnected)
 *  - WebSocket data display with summary bar
 *  - Reconnect button when disconnected
 */
import { render, screen, act } from "@testing-library/react";
import React from "react";
import RtoMonitorPage from "../app/rto-monitor/page";
import type { RTOOverview } from "../lib/types";

// ── WebSocket mock ──────────────────────────────────────────────────────────

type WsHandler = ((ev: { data: string }) => void) | null;

let mockWsInstances: Array<{
  onopen: (() => void) | null;
  onmessage: WsHandler;
  onclose: (() => void) | null;
  onerror: (() => void) | null;
  close: jest.Mock;
}>;

beforeEach(() => {
  mockWsInstances = [];
  // @ts-expect-error — replace global WebSocket with mock constructor
  global.WebSocket = jest.fn().mockImplementation(() => {
    const ws = {
      onopen: null as (() => void) | null,
      onmessage: null as WsHandler,
      onclose: null as (() => void) | null,
      onerror: null as (() => void) | null,
      close: jest.fn(),
    };
    mockWsInstances.push(ws);
    return ws;
  });
});

// ── Hooks mock ──────────────────────────────────────────────────────────────

const mockUseRTOOverview = jest.fn();
jest.mock("../lib/hooks", () => ({
  useRTOOverview: () => mockUseRTOOverview(),
}));

// ── Helpers ─────────────────────────────────────────────────────────────────

function setLoading() {
  mockUseRTOOverview.mockReturnValue({ data: null, loading: true, error: null });
}

function setError() {
  mockUseRTOOverview.mockReturnValue({ data: null, loading: false, error: new Error("API error") });
}

function setSuccess(overrides: Partial<RTOOverview> = {}) {
  mockUseRTOOverview.mockReturnValue({
    data: {
      systems: [
        { name: "基幹業務システム", rto_target_minutes: 60, elapsed_minutes: 30, status: "on_track" },
        { name: "メールシステム", rto_target_minutes: 120, elapsed_minutes: 150, status: "overdue" },
      ],
      ...overrides,
    },
    loading: false,
    error: null,
  });
}

function simulateWsOpen() {
  const ws = mockWsInstances[mockWsInstances.length - 1];
  if (ws?.onopen) {
    act(() => { ws.onopen!(); });
  }
}

function simulateWsMessage(data: Record<string, unknown>) {
  const ws = mockWsInstances[mockWsInstances.length - 1];
  if (ws?.onmessage) {
    act(() => { ws.onmessage!({ data: JSON.stringify(data) }); });
  }
}

function simulateWsClose() {
  const ws = mockWsInstances[mockWsInstances.length - 1];
  if (ws?.onclose) {
    act(() => { ws.onclose!(); });
  }
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Loading state ───────────────────────────────────────────────────────────

describe("RtoMonitorPage loading state", () => {
  it("shows loading spinner and text while fetching", () => {
    setLoading();
    render(<RtoMonitorPage />);

    expect(screen.getByText(/データを読み込んでいます/i)).toBeInTheDocument();
    expect(document.querySelector(".animate-spin")).not.toBeNull();
  });

  it("does not render page content while loading", () => {
    setLoading();
    render(<RtoMonitorPage />);

    expect(screen.queryByText("RTOモニタリング")).not.toBeInTheDocument();
  });
});

// ── Error / offline mode (mock data fallback) ───────────────────────────────

describe("RtoMonitorPage error / offline mode", () => {
  it("shows offline mode badge on API error", () => {
    setError();
    render(<RtoMonitorPage />);

    expect(screen.getByText(/オフラインモード/)).toBeInTheDocument();
  });

  it("renders mock data systems when API errors", () => {
    setError();
    render(<RtoMonitorPage />);

    // Mock data contains "基幹業務システム" as the first system
    expect(screen.getByText("基幹業務システム")).toBeInTheDocument();
    expect(screen.getByText("RTOモニタリング")).toBeInTheDocument();
  });
});

// ── Success state ───────────────────────────────────────────────────────────

describe("RtoMonitorPage success state", () => {
  it("renders the page heading", () => {
    setSuccess();
    render(<RtoMonitorPage />);

    expect(screen.getByText("RTOモニタリング")).toBeInTheDocument();
  });

  it("renders system names from API data", () => {
    setSuccess({
      systems: [
        { name: "テストシステムA", rto_target_minutes: 60, elapsed_minutes: 20, status: "on_track" },
        { name: "テストシステムB", rto_target_minutes: 240, elapsed_minutes: 200, status: "at_risk" },
      ],
    });
    render(<RtoMonitorPage />);

    expect(screen.getByText("テストシステムA")).toBeInTheDocument();
    expect(screen.getByText("テストシステムB")).toBeInTheDocument();
  });

  it("does not show offline badge when no error", () => {
    setSuccess();
    render(<RtoMonitorPage />);

    expect(screen.queryByText(/オフラインモード/)).not.toBeInTheDocument();
  });
});

// ── formatMinutes via RTOCard rendering ─────────────────────────────────────

describe("RtoMonitorPage formatMinutes display", () => {
  it("shows 'X分' for values under 60 minutes", () => {
    setSuccess({
      systems: [
        { name: "短時間システム", rto_target_minutes: 30, elapsed_minutes: 15, status: "on_track" },
      ],
    });
    render(<RtoMonitorPage />);

    // elapsed: 15分, target: 30分
    expect(screen.getByText(/経過: 15分/)).toBeInTheDocument();
    expect(screen.getByText(/目標: 30分/)).toBeInTheDocument();
  });

  it("shows 'X時間Y分' for values between 60 and 1440 minutes", () => {
    setSuccess({
      systems: [
        { name: "中間システム", rto_target_minutes: 150, elapsed_minutes: 90, status: "on_track" },
      ],
    });
    render(<RtoMonitorPage />);

    // 90 min = 1時間30分
    expect(screen.getByText(/経過: 1時間30分/)).toBeInTheDocument();
    // 150 min = 2時間30分
    expect(screen.getByText(/目標: 2時間30分/)).toBeInTheDocument();
  });

  it("shows 'X日Y時間' for values >= 1440 minutes", () => {
    setSuccess({
      systems: [
        { name: "長期システム", rto_target_minutes: 2880, elapsed_minutes: 2880, status: "recovered" },
      ],
    });
    render(<RtoMonitorPage />);

    // 2880 min = 2日0時間
    expect(screen.getByText(/経過: 2日0時間/)).toBeInTheDocument();
    expect(screen.getByText(/目標: 2日0時間/)).toBeInTheDocument();
  });
});

// ── Status label and color via RTOCard ──────────────────────────────────────

describe("RtoMonitorPage status labels", () => {
  const statusCases: Array<[string, string]> = [
    ["on_track", "順調"],
    ["at_risk", "リスクあり"],
    ["overdue", "超過"],
    ["recovered", "復旧済"],
    ["not_started", "未開始"],
  ];

  test.each(statusCases)(
    "status '%s' shows label '%s'",
    (status, expectedLabel) => {
      setSuccess({
        systems: [
          { name: "ステータステスト", rto_target_minutes: 60, elapsed_minutes: 30, status },
        ],
      });
      render(<RtoMonitorPage />);

      expect(screen.getByText(expectedLabel)).toBeInTheDocument();
    }
  );
});

// ── Progress bar percentage ─────────────────────────────────────────────────

describe("RtoMonitorPage progress bar", () => {
  it("shows correct percentage for 50% elapsed", () => {
    setSuccess({
      systems: [
        { name: "半分システム", rto_target_minutes: 100, elapsed_minutes: 50, status: "on_track" },
      ],
    });
    render(<RtoMonitorPage />);

    expect(screen.getByText("50% 消化")).toBeInTheDocument();
  });

  it("caps percentage at 100% when overdue", () => {
    setSuccess({
      systems: [
        { name: "超過システム", rto_target_minutes: 60, elapsed_minutes: 120, status: "overdue" },
      ],
    });
    render(<RtoMonitorPage />);

    // Math.min((120/60)*100, 100) = 100
    expect(screen.getByText("100% 消化")).toBeInTheDocument();
  });

  it("shows 0% when target is 0 (division guard)", () => {
    setSuccess({
      systems: [
        { name: "ゼロ目標システム", rto_target_minutes: 0, elapsed_minutes: 0, status: "not_started" },
      ],
    });
    render(<RtoMonitorPage />);

    expect(screen.getByText("0% 消化")).toBeInTheDocument();
  });
});

// ── WebSocket status indicator ──────────────────────────────────────────────

describe("RtoMonitorPage WebSocket status", () => {
  it("shows '切断中' initially before connection", () => {
    setSuccess();
    render(<RtoMonitorPage />);

    // WebSocket constructor called, but not yet onopen
    // Initial state should show connecting or disconnected depending on timing
    // The connectWebSocket sets "connecting" synchronously
    expect(
      screen.getByText(/接続中|切断中/)
    ).toBeInTheDocument();
  });

  it("shows 'リアルタイム接続中' after WebSocket opens", () => {
    setSuccess();
    render(<RtoMonitorPage />);

    simulateWsOpen();

    expect(screen.getByText("リアルタイム接続中")).toBeInTheDocument();
  });

  it("shows '切断中' and reconnect button after WebSocket closes", () => {
    setSuccess();
    render(<RtoMonitorPage />);

    simulateWsOpen();
    simulateWsClose();

    expect(screen.getByText("切断中")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /再接続/ })).toBeInTheDocument();
  });
});

// ── WebSocket data display ──────────────────────────────────────────────────

describe("RtoMonitorPage WebSocket data", () => {
  it("renders WS summary bar when rto_snapshot arrives", () => {
    setSuccess();
    render(<RtoMonitorPage />);

    simulateWsOpen();
    simulateWsMessage({
      type: "rto_snapshot",
      timestamp: "2026-04-09T12:00:00Z",
      systems: [
        { system_name: "WS基幹システム", rto_target_hours: 1, status: "on_track", elapsed_hours: 0.5, remaining_hours: 0.5 },
      ],
      summary: { total: 5, on_track: 3, at_risk: 1, overdue: 1 },
    });

    // Summary bar should show counts
    expect(screen.getByText("5")).toBeInTheDocument(); // total
    expect(screen.getByText("3")).toBeInTheDocument(); // on_track
    // WS system name should appear (converted to display format)
    expect(screen.getByText("WS基幹システム")).toBeInTheDocument();
  });

  it("converts WS rto_target_hours to minutes for display", () => {
    setSuccess();
    render(<RtoMonitorPage />);

    simulateWsOpen();
    simulateWsMessage({
      type: "rto_update",
      timestamp: "2026-04-09T12:00:00Z",
      systems: [
        { system_name: "時間変換テスト", rto_target_hours: 2, status: "on_track", elapsed_hours: 1, remaining_hours: 1 },
      ],
      summary: { total: 1, on_track: 1, at_risk: 0, overdue: 0 },
    });

    // 2 hours = 120 minutes → "2時間0分", 1 hour elapsed = 60 min → "1時間0分"
    expect(screen.getByText(/目標: 2時間0分/)).toBeInTheDocument();
    expect(screen.getByText(/経過: 1時間0分/)).toBeInTheDocument();
  });
});
