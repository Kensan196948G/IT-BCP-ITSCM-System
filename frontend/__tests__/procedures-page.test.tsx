/**
 * Tests for app/procedures/page.tsx — ProceduresPage component.
 *
 * Covers:
 *  - Loading state
 *  - Error/offline mode: mock data fallback
 *  - Success state: procedure table rendering
 *  - Status badges: active/draft/archived labels and colors
 *  - Scenario labels: dc_failure/ransomware/earthquake → Japanese labels
 *  - Version display, priority order, last_reviewed
 */
import { render, screen } from "@testing-library/react";
import React from "react";
import ProceduresPage from "../app/procedures/page";
import type { RecoveryProcedure } from "../lib/types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseProcedures = jest.fn();
jest.mock("../lib/hooks", () => ({
  useProcedures: () => mockUseProcedures(),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function setLoading() {
  mockUseProcedures.mockReturnValue({ data: null, loading: true, error: null });
}

function setError() {
  mockUseProcedures.mockReturnValue({ data: null, loading: false, error: new Error("API error") });
}

function setSuccess(procedures: RecoveryProcedure[]) {
  mockUseProcedures.mockReturnValue({ data: procedures, loading: false, error: null });
}

function makeProc(overrides: Partial<RecoveryProcedure> = {}): RecoveryProcedure {
  return {
    id: "1",
    procedure_id: "RP-2026-001",
    system_name: "テストシステム",
    scenario_type: "dc_failure",
    title: "テスト手順書",
    version: "1.0",
    priority_order: 1,
    procedure_steps: [],
    estimated_time_hours: 2.0,
    responsible_team: "テストチーム",
    last_reviewed: "2026-04-01",
    review_cycle_months: 6,
    status: "active",
    ...overrides,
  } as RecoveryProcedure;
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Loading state ─────────────────────────────────────────────────────────────

describe("ProceduresPage loading state", () => {
  it("shows loading spinner while fetching", () => {
    setLoading();
    render(<ProceduresPage />);

    expect(screen.getByText(/データを読み込んでいます/i)).toBeInTheDocument();
  });
});

// ── Error / offline mode ──────────────────────────────────────────────────────

describe("ProceduresPage error / offline mode", () => {
  it("shows offline mode badge on API error", () => {
    setError();
    render(<ProceduresPage />);

    expect(screen.getByText(/オフラインモード/)).toBeInTheDocument();
  });

  it("renders mock data when API errors", () => {
    setError();
    render(<ProceduresPage />);

    expect(screen.getByText("復旧手順書")).toBeInTheDocument();
    expect(screen.getByText("基幹システム")).toBeInTheDocument();
  });
});

// ── Success state ─────────────────────────────────────────────────────────────

describe("ProceduresPage success state", () => {
  it("renders procedure title, system name, and version", () => {
    setSuccess([makeProc({
      system_name: "メールシステム",
      title: "ランサムウェア復旧手順",
      version: "2.1",
    })]);
    render(<ProceduresPage />);

    expect(screen.getByText("メールシステム")).toBeInTheDocument();
    expect(screen.getByText("ランサムウェア復旧手順")).toBeInTheDocument();
    expect(screen.getByText("v2.1")).toBeInTheDocument();
  });

  it("renders priority order and last reviewed date", () => {
    setSuccess([makeProc({ priority_order: 3, last_reviewed: "2026-02-20" })]);
    render(<ProceduresPage />);

    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("2026-02-20")).toBeInTheDocument();
  });

  it("shows '-' when last_reviewed is absent", () => {
    setSuccess([makeProc({ last_reviewed: undefined })]);
    render(<ProceduresPage />);

    expect(screen.getByText("-")).toBeInTheDocument();
  });
});

// ── Status badges ─────────────────────────────────────────────────────────────

describe("ProceduresPage status badges", () => {
  const cases: Array<[string, string, string]> = [
    ["active", "有効", "bg-green-100"],
    ["draft", "下書き", "bg-yellow-100"],
    ["archived", "アーカイブ", "bg-slate-100"],
  ];

  test.each(cases)(
    "status '%s' shows label '%s' with class '%s'",
    (status, label, bgClass) => {
      setSuccess([makeProc({ status })]);
      render(<ProceduresPage />);

      const badge = screen.getByText(label);
      expect(badge.className).toContain(bgClass);
    }
  );
});

// ── Scenario labels ─────────────────────────────────────────────────────────

describe("ProceduresPage scenario labels", () => {
  const cases: Array<[string, string]> = [
    ["dc_failure", "DC障害"],
    ["ransomware", "ランサムウェア"],
    ["earthquake", "地震"],
    ["cloud_outage", "クラウド障害"],
    ["pandemic", "パンデミック"],
  ];

  test.each(cases)(
    "scenario '%s' displays '%s'",
    (scenario, expectedLabel) => {
      setSuccess([makeProc({ scenario_type: scenario })]);
      render(<ProceduresPage />);

      expect(screen.getByText(expectedLabel)).toBeInTheDocument();
    }
  );
});
