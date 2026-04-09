/**
 * Tests for app/scenarios/page.tsx — ScenariosPage component.
 *
 * Covers:
 *  - Loading state
 *  - Error/offline mode: mock data fallback
 *  - Success state: scenario table rendering
 *  - Difficulty badges: easy/medium/hard labels and colors
 *  - Scenario type labels: dc_failure/ransomware/earthquake etc. → Japanese labels
 *  - Affected systems display, duration, inject count
 */
import { render, screen } from "@testing-library/react";
import React from "react";
import ScenariosPage from "../app/scenarios/page";
import type { BCPScenario } from "../lib/types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseScenarios = jest.fn();
jest.mock("../lib/hooks", () => ({
  useScenarios: () => mockUseScenarios(),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function setLoading() {
  mockUseScenarios.mockReturnValue({ data: null, loading: true, error: null });
}

function setError() {
  mockUseScenarios.mockReturnValue({ data: null, loading: false, error: new Error("API error") });
}

function setSuccess(scenarios: BCPScenario[]) {
  mockUseScenarios.mockReturnValue({ data: scenarios, loading: false, error: null });
}

function makeScenario(overrides: Partial<BCPScenario> = {}): BCPScenario {
  return {
    id: "1",
    scenario_id: "SCN-001",
    title: "テストシナリオ",
    scenario_type: "dc_failure",
    description: "テスト説明",
    initial_inject: "テスト初期インジェクト",
    injects: [
      { offset_minutes: 0, title: "初期", description: "初期イベント", expected_actions: ["確認"] },
    ],
    affected_systems: ["基幹システム"],
    expected_duration_hours: 4.0,
    difficulty: "medium",
    is_active: true,
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Loading state ─────────────────────────────────────────────────────────────

describe("ScenariosPage loading state", () => {
  it("shows loading spinner while fetching", () => {
    setLoading();
    render(<ScenariosPage />);

    expect(screen.getByText(/データを読み込んでいます/i)).toBeInTheDocument();
  });
});

// ── Error / offline mode ──────────────────────────────────────────────────────

describe("ScenariosPage error / offline mode", () => {
  it("shows offline mode badge on API error", () => {
    setError();
    render(<ScenariosPage />);

    expect(screen.getByText(/オフラインモード/)).toBeInTheDocument();
  });

  it("renders mock data when API errors", () => {
    setError();
    render(<ScenariosPage />);

    expect(screen.getByText("シナリオ管理")).toBeInTheDocument();
    expect(screen.getByText("データセンター電源喪失")).toBeInTheDocument();
  });
});

// ── Success state ─────────────────────────────────────────────────────────────

describe("ScenariosPage success state", () => {
  it("renders scenario ID, title, and duration", () => {
    setSuccess([makeScenario({
      scenario_id: "SCN-010",
      title: "テスト障害シナリオ",
      expected_duration_hours: 5.0,
    })]);
    render(<ScenariosPage />);

    expect(screen.getByText("SCN-010")).toBeInTheDocument();
    expect(screen.getByText("テスト障害シナリオ")).toBeInTheDocument();
    expect(screen.getByText("5h")).toBeInTheDocument();
  });

  it("renders inject count", () => {
    setSuccess([makeScenario({
      injects: [
        { offset_minutes: 0, title: "A", description: "a" },
        { offset_minutes: 15, title: "B", description: "b" },
        { offset_minutes: 30, title: "C", description: "c" },
      ],
    })]);
    render(<ScenariosPage />);

    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders affected systems as badges", () => {
    setSuccess([makeScenario({
      affected_systems: ["メールシステム", "ファイルサーバ"],
    })]);
    render(<ScenariosPage />);

    expect(screen.getByText("メールシステム")).toBeInTheDocument();
    expect(screen.getByText("ファイルサーバ")).toBeInTheDocument();
  });

  it("shows '+N' when affected_systems exceeds 3", () => {
    setSuccess([makeScenario({
      affected_systems: ["SysA", "SysB", "SysC", "SysD", "SysE"],
    })]);
    render(<ScenariosPage />);

    expect(screen.getByText("SysA")).toBeInTheDocument();
    expect(screen.getByText("SysB")).toBeInTheDocument();
    expect(screen.getByText("SysC")).toBeInTheDocument();
    expect(screen.getByText("+2")).toBeInTheDocument();
  });

  it("shows '-' when affected_systems is absent", () => {
    setSuccess([makeScenario({ affected_systems: undefined })]);
    render(<ScenariosPage />);

    const cells = screen.getAllByText("-");
    expect(cells.length).toBeGreaterThanOrEqual(1);
  });

  it("shows '-' when expected_duration_hours is absent", () => {
    setSuccess([makeScenario({ expected_duration_hours: undefined })]);
    render(<ScenariosPage />);

    const cells = screen.getAllByText("-");
    expect(cells.length).toBeGreaterThanOrEqual(1);
  });

  it("does not show offline badge on success", () => {
    setSuccess([makeScenario()]);
    render(<ScenariosPage />);

    expect(screen.queryByText(/オフラインモード/)).not.toBeInTheDocument();
  });
});

// ── Difficulty badges ─────────────────────────────────────────────────────────

describe("ScenariosPage difficulty badges", () => {
  const cases: Array<[string, string, string]> = [
    ["easy", "易", "bg-green-100"],
    ["medium", "中", "bg-yellow-100"],
    ["hard", "難", "bg-red-100"],
  ];

  test.each(cases)(
    "difficulty '%s' shows label '%s' with class '%s'",
    (difficulty, label, bgClass) => {
      setSuccess([makeScenario({ difficulty })]);
      render(<ScenariosPage />);

      const badge = screen.getByText(label);
      expect(badge.className).toContain(bgClass);
    }
  );
});

// ── Scenario type labels ──────────────────────────────────────────────────────

describe("ScenariosPage scenario type labels", () => {
  const cases: Array<[string, string]> = [
    ["dc_failure", "DC障害"],
    ["ransomware", "ランサムウェア"],
    ["earthquake", "地震"],
    ["cloud_outage", "クラウド障害"],
    ["pandemic", "パンデミック"],
    ["supplier_failure", "サプライヤー障害"],
  ];

  test.each(cases)(
    "scenario type '%s' displays '%s'",
    (scenarioType, expectedLabel) => {
      setSuccess([makeScenario({ scenario_type: scenarioType })]);
      render(<ScenariosPage />);

      expect(screen.getByText(expectedLabel)).toBeInTheDocument();
    }
  );

  it("falls back to raw type when label is not defined", () => {
    setSuccess([makeScenario({ scenario_type: "unknown_type" })]);
    render(<ScenariosPage />);

    expect(screen.getByText("unknown_type")).toBeInTheDocument();
  });
});
