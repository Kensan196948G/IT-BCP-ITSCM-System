/**
 * Tests for app/plans/page.tsx — PlansPage component.
 *
 * Covers:
 *  - Loading state
 *  - Error/offline mode: mock data fallback
 *  - Success state: BCP plan table rendering
 *  - Tier badges: tier1/tier2/tier3/tier4 labels and colors
 *  - formatHours: minutes / hours / large hours display
 *  - Offline badge and syncing indicator
 */
import { render, screen } from "@testing-library/react";
import React from "react";
import PlansPage from "../app/plans/page";
import type { ITSystemBCP } from "../lib/types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseOfflineSync = jest.fn();
jest.mock("../lib/use-offline-sync", () => ({
  useOfflineSync: (...args: unknown[]) => mockUseOfflineSync(...args),
}));

jest.mock("../lib/api", () => ({
  systems: { list: jest.fn() },
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

type SyncResult = {
  data: ITSystemBCP[] | null;
  loading: boolean;
  error: Error | null;
  isOnline: boolean;
  lastSyncTime: string | null;
  isSyncing: boolean;
};

function setSyncState(overrides: Partial<SyncResult> = {}) {
  mockUseOfflineSync.mockReturnValue({
    data: null,
    loading: false,
    error: null,
    isOnline: true,
    lastSyncTime: null,
    isSyncing: false,
    ...overrides,
  });
}

function makePlan(overrides: Partial<ITSystemBCP> = {}): ITSystemBCP {
  return {
    id: "1",
    system_name: "テストシステム",
    system_type: "オンプレミス",
    criticality: "tier1",
    rto_target_hours: 1,
    rpo_target_hours: 0.25,
    last_dr_test: "2026-03-15",
    ...overrides,
  } as ITSystemBCP;
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Loading state ─────────────────────────────────────────────────────────────

describe("PlansPage loading state", () => {
  it("shows loading spinner while fetching", () => {
    setSyncState({ loading: true });
    render(<PlansPage />);

    expect(screen.getByText(/データを読み込んでいます/i)).toBeInTheDocument();
    expect(document.querySelector(".animate-spin")).not.toBeNull();
  });
});

// ── Error / offline mode ──────────────────────────────────────────────────────

describe("PlansPage error / offline mode", () => {
  it("shows offline mode badge on API error when online", () => {
    setSyncState({ error: new Error("API error"), isOnline: true });
    render(<PlansPage />);

    expect(screen.getByText(/オフラインモード/)).toBeInTheDocument();
  });

  it("renders mock data when API errors", () => {
    setSyncState({ error: new Error("API error") });
    render(<PlansPage />);

    expect(screen.getByText("基幹業務システム")).toBeInTheDocument();
    expect(screen.getByText("BCP計画管理")).toBeInTheDocument();
  });

  it("shows offline data badge when not online", () => {
    setSyncState({ isOnline: false, data: [makePlan()] });
    render(<PlansPage />);

    expect(screen.getByText("オフラインデータ使用中")).toBeInTheDocument();
  });

  it("shows syncing indicator when syncing", () => {
    setSyncState({ isSyncing: true, data: [makePlan()] });
    render(<PlansPage />);

    expect(screen.getByText("同期中...")).toBeInTheDocument();
  });
});

// ── Success state ─────────────────────────────────────────────────────────────

describe("PlansPage success state", () => {
  it("renders system name, type, and last DR test date", () => {
    setSyncState({
      data: [makePlan({
        system_name: "メールシステム",
        system_type: "SaaS",
        last_dr_test: "2026-04-01",
      })],
    });
    render(<PlansPage />);

    expect(screen.getByText("メールシステム")).toBeInTheDocument();
    expect(screen.getByText("SaaS")).toBeInTheDocument();
    expect(screen.getByText("2026-04-01")).toBeInTheDocument();
  });
});

// ── Tier badges ───────────────────────────────────────────────────────────────

describe("PlansPage tier badges", () => {
  const cases: Array<[string, string, string]> = [
    ["tier1", "Tier 1", "bg-red-100"],
    ["tier2", "Tier 2", "bg-orange-100"],
    ["tier3", "Tier 3", "bg-yellow-100"],
    ["tier4", "Tier 4", "bg-slate-100"],
  ];

  test.each(cases)(
    "criticality '%s' shows label '%s' with class '%s'",
    (criticality, label, bgClass) => {
      setSyncState({ data: [makePlan({ criticality })] });
      render(<PlansPage />);

      const badge = screen.getByText(label);
      expect(badge.className).toContain(bgClass);
    }
  );
});

// ── formatHours display ─────────────────────────────────────────────────────

describe("PlansPage formatHours display", () => {
  it("shows minutes for values < 1 hour (e.g., 0.25 → 15分)", () => {
    setSyncState({
      data: [makePlan({ rto_target_hours: 1, rpo_target_hours: 0.25 })],
    });
    render(<PlansPage />);

    expect(screen.getByText("15分")).toBeInTheDocument();
  });

  it("shows hours for normal values (e.g., 4 → 4時間)", () => {
    setSyncState({
      data: [makePlan({ rto_target_hours: 4, rpo_target_hours: 1 })],
    });
    render(<PlansPage />);

    expect(screen.getByText("4時間")).toBeInTheDocument();
  });

  it("shows hours for values >= 24 (e.g., 48 → 48時間)", () => {
    setSyncState({
      data: [makePlan({ rto_target_hours: 48, rpo_target_hours: 24 })],
    });
    render(<PlansPage />);

    expect(screen.getByText("48時間")).toBeInTheDocument();
    expect(screen.getByText("24時間")).toBeInTheDocument();
  });
});
