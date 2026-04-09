/**
 * Tests for app/incidents/page.tsx — IncidentsPage component.
 *
 * Covers:
 *  - Loading state: spinner shown while useOfflineSync fetches
 *  - Error without data: full-page error banner
 *  - Success state: incidents table rendered with correct data
 *  - elapsedTime: < 24h shows "X時間Y分", >= 24h shows "X日Y時間"
 *  - severityBadge: P1 → red, P2 → orange, P3 → yellow (both cases)
 *  - statusLabel: active/recovering/resolved → Japanese labels
 *  - offlineLabel: isOnline / offline+cache / offline+noCache
 *  - Empty data: "アクティブなインシデントはありません"
 */
import { render, screen } from "@testing-library/react";
import React from "react";
import IncidentsPage from "../app/incidents/page";
import type { ActiveIncident } from "../lib/types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseOfflineSync = jest.fn();
jest.mock("../lib/use-offline-sync", () => ({
  useOfflineSync: (...args: unknown[]) => mockUseOfflineSync(...args),
}));

jest.mock("../lib/api", () => ({
  incidents: { list: jest.fn() },
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

type SyncResult = {
  data: ActiveIncident[] | null;
  loading: boolean;
  error: Error | null;
  isOnline: boolean;
  lastSyncTime: number | null;
};

function setSyncState(overrides: Partial<SyncResult> = {}) {
  mockUseOfflineSync.mockReturnValue({
    data: null,
    loading: false,
    error: null,
    isOnline: true,
    lastSyncTime: null,
    ...overrides,
  });
}

function makeIncident(
  overrides: Partial<ActiveIncident> = {}
): ActiveIncident {
  return {
    id: "INC-001",
    incident_id: "INC-2026-001",
    title: "テストインシデント",
    severity: "p1",
    status: "active",
    occurred_at: new Date().toISOString(),
    affected_systems: ["システムA"],
    ...overrides,
  } as ActiveIncident;
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Loading state ─────────────────────────────────────────────────────────────

describe("IncidentsPage loading state", () => {
  it("shows loading spinner and text while fetching", () => {
    setSyncState({ loading: true });
    render(<IncidentsPage />);

    expect(screen.getByText(/データを読み込んでいます/i)).toBeInTheDocument();
    expect(document.querySelector(".animate-spin")).not.toBeNull();
  });

  it("does not render the incidents table while loading", () => {
    setSyncState({ loading: true });
    render(<IncidentsPage />);

    expect(screen.queryByText("インシデント管理")).not.toBeInTheDocument();
  });
});

// ── Error without data ────────────────────────────────────────────────────────

describe("IncidentsPage error without data", () => {
  it("shows error banner when API fails and no cached data", () => {
    setSyncState({ error: new Error("Network error"), data: null });
    render(<IncidentsPage />);

    expect(
      screen.getByText(/インシデントデータを取得できませんでした/)
    ).toBeInTheDocument();
  });
});

// ── Success state ─────────────────────────────────────────────────────────────

describe("IncidentsPage success state", () => {
  it("renders the page heading", () => {
    setSyncState({ data: [] });
    render(<IncidentsPage />);

    expect(screen.getByText("インシデント管理")).toBeInTheDocument();
  });

  it("shows 'アクティブなインシデントはありません' when data is empty", () => {
    setSyncState({ data: [] });
    render(<IncidentsPage />);

    expect(
      screen.getByText("アクティブなインシデントはありません")
    ).toBeInTheDocument();
  });

  it("renders incident title and ID in the table", () => {
    setSyncState({
      data: [
        makeIncident({
          incident_id: "INC-2026-007",
          title: "基幹システム障害",
        }),
      ],
    });
    render(<IncidentsPage />);

    expect(screen.getByText("INC-2026-007")).toBeInTheDocument();
    expect(screen.getByText("基幹システム障害")).toBeInTheDocument();
  });

  it("renders affected_systems joined by comma", () => {
    setSyncState({
      data: [
        makeIncident({
          affected_systems: ["システムA", "システムB"],
        }),
      ],
    });
    render(<IncidentsPage />);

    expect(screen.getByText("システムA, システムB")).toBeInTheDocument();
  });

  it("shows '-' when affected_systems is absent", () => {
    setSyncState({
      data: [makeIncident({ affected_systems: undefined })],
    });
    render(<IncidentsPage />);

    expect(screen.getByText("-")).toBeInTheDocument();
  });
});

// ── elapsedTime function ──────────────────────────────────────────────────────

describe("IncidentsPage elapsedTime display", () => {
  beforeAll(() => {
    // Fix "now" to 2026-04-09T12:00:00Z
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2026-04-09T12:00:00Z"));
  });

  afterAll(() => {
    jest.useRealTimers();
  });

  it("shows 'X時間Y分' for incidents less than 24 hours ago", () => {
    // occurred 2h 30m ago
    setSyncState({
      data: [makeIncident({ occurred_at: "2026-04-09T09:30:00Z" })],
    });
    render(<IncidentsPage />);

    expect(screen.getByText("2時間30分")).toBeInTheDocument();
  });

  it("shows 'X日Y時間' for incidents 24 hours or more ago", () => {
    // occurred 49h ago → 2 days 1 hour
    setSyncState({
      data: [makeIncident({ occurred_at: "2026-04-07T11:00:00Z" })],
    });
    render(<IncidentsPage />);

    expect(screen.getByText("2日1時間")).toBeInTheDocument();
  });

  it("shows '1日0時間' for exactly 24 hours ago", () => {
    setSyncState({
      data: [makeIncident({ occurred_at: "2026-04-08T12:00:00Z" })],
    });
    render(<IncidentsPage />);

    expect(screen.getByText("1日0時間")).toBeInTheDocument();
  });
});

// ── Severity badge colors ─────────────────────────────────────────────────────

describe("IncidentsPage severity badge colors", () => {
  const cases: Array<[string, string, string]> = [
    ["p1", "bg-red-100", "text-red-700"],
    ["P1", "bg-red-100", "text-red-700"],
    ["p2", "bg-orange-100", "text-orange-700"],
    ["P2", "bg-orange-100", "text-orange-700"],
    ["p3", "bg-yellow-100", "text-yellow-700"],
    ["P3", "bg-yellow-100", "text-yellow-700"],
  ];

  test.each(cases)(
    "severity '%s' renders with %s and %s",
    (severity, bgClass, textClass) => {
      setSyncState({ data: [makeIncident({ severity })] });
      render(<IncidentsPage />);

      // Find the badge by its displayed text (P1/P2/P3)
      const badge = screen.getByText(severity.toUpperCase());
      expect(badge.className).toContain(bgClass);
      expect(badge.className).toContain(textClass);
    }
  );
});

// ── Status label mapping ──────────────────────────────────────────────────────

describe("IncidentsPage status labels", () => {
  const cases: Array<[string, string]> = [
    ["active", "対応中"],
    ["recovering", "監視中"],
    ["resolved", "解決済"],
  ];

  test.each(cases)(
    "status '%s' displays '%s'",
    (status, expectedLabel) => {
      setSyncState({ data: [makeIncident({ status })] });
      render(<IncidentsPage />);

      expect(screen.getByText(expectedLabel)).toBeInTheDocument();
    }
  );
});

// ── Offline label logic ───────────────────────────────────────────────────────

describe("IncidentsPage offline label", () => {
  it("shows 'APIエラー' badge when online but error occurs", () => {
    setSyncState({
      error: new Error("500"),
      data: [makeIncident()],
      isOnline: true,
    });
    render(<IncidentsPage />);

    expect(screen.getByText(/APIエラー/)).toBeInTheDocument();
  });

  it("shows offline + lastSyncTime label when offline with cache", () => {
    const syncTime = new Date("2026-04-09T10:00:00").getTime();
    setSyncState({
      error: new Error("offline"),
      data: [makeIncident()],
      isOnline: false,
      lastSyncTime: syncTime,
    });
    render(<IncidentsPage />);

    expect(screen.getByText(/オフライン（最終同期:/)).toBeInTheDocument();
  });

  it("shows 'オフライン（キャッシュなし）' when offline with no cache", () => {
    setSyncState({
      error: new Error("offline"),
      data: [makeIncident()],
      isOnline: false,
      lastSyncTime: null,
    });
    render(<IncidentsPage />);

    expect(
      screen.getByText("オフライン（キャッシュなし）")
    ).toBeInTheDocument();
  });

  it("does not show error badge when no error", () => {
    setSyncState({ data: [], error: null });
    render(<IncidentsPage />);

    expect(screen.queryByText(/APIエラー/)).not.toBeInTheDocument();
    expect(screen.queryByText(/オフライン/)).not.toBeInTheDocument();
  });
});
