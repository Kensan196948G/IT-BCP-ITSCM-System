/**
 * Tests for app/bia/page.tsx — BIAPage component.
 *
 * Covers:
 *  - Loading state
 *  - Error/offline mode: mock data fallback
 *  - Success state: summary cards, assessment table, risk matrix
 *  - Status badges: draft/reviewed/approved labels and colors
 *  - Risk score color helpers
 *  - Risk matrix cell rendering
 *  - Financial impact display
 */
import { render, screen } from "@testing-library/react";
import React from "react";
import BIAPage from "../app/bia/page";
import type { BIAAssessment, BIASummary, RiskMatrixData } from "../lib/types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseBIAAssessments = jest.fn();
const mockUseBIASummary = jest.fn();
const mockUseBIARiskMatrix = jest.fn();

jest.mock("../lib/hooks", () => ({
  useBIAAssessments: (...args: unknown[]) => mockUseBIAAssessments(...args),
  useBIASummary: (...args: unknown[]) => mockUseBIASummary(...args),
  useBIARiskMatrix: (...args: unknown[]) => mockUseBIARiskMatrix(...args),
}));

// ── Helpers ──────────────────────────────────────────────────────────────────

interface HookResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

function defaultHookResult<T>(overrides: Partial<HookResult<T>> = {}): HookResult<T> {
  return {
    data: null,
    loading: false,
    error: null,
    refetch: jest.fn(),
    ...overrides,
  };
}

function setLoading() {
  mockUseBIAAssessments.mockReturnValue(defaultHookResult({ loading: true }));
  mockUseBIASummary.mockReturnValue(defaultHookResult({ loading: true }));
  mockUseBIARiskMatrix.mockReturnValue(defaultHookResult({ loading: true }));
}

function setError() {
  const err = new Error("API error");
  mockUseBIAAssessments.mockReturnValue(defaultHookResult({ error: err }));
  mockUseBIASummary.mockReturnValue(defaultHookResult({ error: err }));
  mockUseBIARiskMatrix.mockReturnValue(defaultHookResult({ error: err }));
}

function setSuccess(
  assessments: BIAAssessment[],
  summary: BIASummary,
  matrix: RiskMatrixData,
) {
  mockUseBIAAssessments.mockReturnValue(defaultHookResult({ data: assessments }));
  mockUseBIASummary.mockReturnValue(defaultHookResult({ data: summary }));
  mockUseBIARiskMatrix.mockReturnValue(defaultHookResult({ data: matrix }));
}

function makeAssessment(overrides: Partial<BIAAssessment> = {}): BIAAssessment {
  return {
    id: "1",
    assessment_id: "BIA-2026-001",
    system_name: "Test System",
    assessment_date: "2026-03-15",
    assessor: "Tester",
    business_processes: ["Process A"],
    financial_impact_per_hour: 100,
    financial_impact_per_day: 2400,
    max_tolerable_downtime_hours: 24,
    reputation_impact: "medium",
    operational_impact: "medium",
    recommended_rto_hours: 4,
    recommended_rpo_hours: 1,
    risk_score: 50,
    status: "draft",
    ...overrides,
  };
}

function makeSummary(overrides: Partial<BIASummary> = {}): BIASummary {
  return {
    total_assessments: 1,
    average_risk_score: 50,
    max_risk_score: 50,
    highest_risk_system: "Test System",
    impact_distribution: { none: 0, low: 0, medium: 1, high: 0, critical: 0 },
    average_financial_impact_per_day: 2400,
    status_distribution: { draft: 1, reviewed: 0, approved: 0 },
    ...overrides,
  };
}

function makeMatrix(overrides: Partial<RiskMatrixData> = {}): RiskMatrixData {
  return {
    entries: [],
    matrix: [
      [0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0],
      [0, 0, 1, 0, 0],
      [0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0],
    ],
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Loading state ────────────────────────────────────────────────────────────

describe("BIAPage loading state", () => {
  it("shows loading spinner while fetching", () => {
    setLoading();
    render(<BIAPage />);

    expect(screen.getByText(/BIAデータを読み込んでいます/)).toBeInTheDocument();
    expect(document.querySelector(".animate-spin")).not.toBeNull();
  });
});

// ── Error / offline mode ─────────────────────────────────────────────────────

describe("BIAPage error / offline mode", () => {
  it("renders page header with mock data on API error", () => {
    setError();
    render(<BIAPage />);

    // Page header should still render
    expect(screen.getByText("BIA分析 (ビジネスインパクト分析)")).toBeInTheDocument();
  });

  it("renders fallback mock assessment data on error", () => {
    setError();
    render(<BIAPage />);

    // Mock data system names from the component
    expect(screen.getByText("Core Banking System")).toBeInTheDocument();
    // Trading Platform appears in both summary card and table
    expect(screen.getAllByText("Trading Platform").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Email System")).toBeInTheDocument();
  });

  it("renders fallback summary data on error", () => {
    setError();
    render(<BIAPage />);

    // Mock summary highest risk system (appears in summary card + table row)
    expect(screen.getAllByText("Trading Platform").length).toBe(2);
    // Mock summary max risk score is 95 (appears in summary card and table row)
    expect(screen.getAllByText("95").length).toBeGreaterThanOrEqual(1);
  });
});

// ── Success state ────────────────────────────────────────────────────────────

describe("BIAPage success state", () => {
  it("renders page header", () => {
    setSuccess([makeAssessment()], makeSummary(), makeMatrix());
    render(<BIAPage />);

    expect(screen.getByText("BIA分析 (ビジネスインパクト分析)")).toBeInTheDocument();
    expect(
      screen.getByText("各ITシステムの業務影響度を評価し、復旧優先度を決定します")
    ).toBeInTheDocument();
  });

  it("renders assessment table with system name and assessment ID", () => {
    setSuccess(
      [makeAssessment({ system_name: "重要システム", assessment_id: "BIA-2026-100" })],
      makeSummary(),
      makeMatrix(),
    );
    render(<BIAPage />);

    expect(screen.getByText("重要システム")).toBeInTheDocument();
    expect(screen.getByText("BIA-2026-100")).toBeInTheDocument();
  });

  it("renders table column headers", () => {
    setSuccess([makeAssessment()], makeSummary(), makeMatrix());
    render(<BIAPage />);

    expect(screen.getByText("システム名")).toBeInTheDocument();
    expect(screen.getByText("リスクスコア")).toBeInTheDocument();
    expect(screen.getByText("財務影響 (日)")).toBeInTheDocument();
    expect(screen.getByText("推奨RTO")).toBeInTheDocument();
    expect(screen.getByText("MTPD")).toBeInTheDocument();
    // "ステータス" appears in both the summary card and table header
    expect(screen.getAllByText("ステータス").length).toBeGreaterThanOrEqual(1);
  });

  it("renders RTO and MTPD values with 'h' suffix", () => {
    setSuccess(
      [makeAssessment({ recommended_rto_hours: 4, max_tolerable_downtime_hours: 24 })],
      makeSummary(),
      makeMatrix(),
    );
    render(<BIAPage />);

    expect(screen.getByText("4h")).toBeInTheDocument();
    expect(screen.getByText("24h")).toBeInTheDocument();
  });

  it("renders financial impact with locale formatting", () => {
    setSuccess(
      [makeAssessment({ financial_impact_per_day: 12000 })],
      makeSummary(),
      makeMatrix(),
    );
    render(<BIAPage />);

    expect(screen.getByText("12,000 万円")).toBeInTheDocument();
  });

  it("renders multiple assessments", () => {
    const assessments = [
      makeAssessment({ id: "1", system_name: "System A" }),
      makeAssessment({ id: "2", system_name: "System B" }),
    ];
    setSuccess(assessments, makeSummary({ total_assessments: 2 }), makeMatrix());
    render(<BIAPage />);

    expect(screen.getByText("System A")).toBeInTheDocument();
    expect(screen.getByText("System B")).toBeInTheDocument();
  });
});

// ── Summary cards ────────────────────────────────────────────────────────────

describe("BIAPage summary cards", () => {
  it("displays max risk score", () => {
    setSuccess(
      [makeAssessment()],
      makeSummary({ max_risk_score: 82 }),
      makeMatrix(),
    );
    render(<BIAPage />);

    expect(screen.getByText("82")).toBeInTheDocument();
    expect(screen.getByText("最高リスクスコア")).toBeInTheDocument();
  });

  it("displays highest risk system name", () => {
    setSuccess(
      [makeAssessment()],
      makeSummary({ highest_risk_system: "Core Banking" }),
      makeMatrix(),
    );
    render(<BIAPage />);

    expect(screen.getByText("Core Banking")).toBeInTheDocument();
  });

  it("displays average risk score with one decimal", () => {
    setSuccess(
      [makeAssessment()],
      makeSummary({ average_risk_score: 54.4 }),
      makeMatrix(),
    );
    render(<BIAPage />);

    expect(screen.getByText("54.4")).toBeInTheDocument();
    expect(screen.getByText("平均リスクスコア")).toBeInTheDocument();
  });

  it("displays total assessments count", () => {
    setSuccess(
      [makeAssessment()],
      makeSummary({ total_assessments: 5 }),
      makeMatrix(),
    );
    render(<BIAPage />);

    expect(screen.getByText("全 5 システム")).toBeInTheDocument();
  });

  it("displays average financial impact per day", () => {
    setSuccess(
      [makeAssessment()],
      makeSummary({ average_financial_impact_per_day: 12480 }),
      makeMatrix(),
    );
    render(<BIAPage />);

    expect(screen.getByText("12,480万")).toBeInTheDocument();
    expect(screen.getByText("平均財務影響 (日次)")).toBeInTheDocument();
  });
});

// ── Status badges ────────────────────────────────────────────────────────────

describe("BIAPage status badges", () => {
  const cases: Array<[string, string, string]> = [
    ["draft", "下書き", "bg-slate-100"],
    ["reviewed", "レビュー済", "bg-blue-100"],
    ["approved", "承認済", "bg-green-100"],
  ];

  test.each(cases)(
    "status '%s' shows label '%s' with class containing '%s'",
    (status, label, bgClass) => {
      setSuccess(
        [makeAssessment({ status })],
        makeSummary(),
        makeMatrix(),
      );
      render(<BIAPage />);

      // The status label appears both in the summary card area and in the table row.
      // We look for the table row badge specifically.
      const badges = screen.getAllByText(label);
      const tableBadge = badges.find(
        (el) => el.className.includes("rounded-full") && el.className.includes(bgClass)
      );
      expect(tableBadge).toBeDefined();
    }
  );
});

// ── Status distribution in summary card ──────────────────────────────────────

describe("BIAPage status distribution", () => {
  it("renders status distribution badges in summary card", () => {
    setSuccess(
      [makeAssessment()],
      makeSummary({ status_distribution: { draft: 1, reviewed: 2, approved: 3 } }),
      makeMatrix(),
    );
    render(<BIAPage />);

    // React renders "{label}: {val}" with text content joined
    expect(screen.getByText(/下書き.*1/)).toBeInTheDocument();
    expect(screen.getByText(/レビュー済.*2/)).toBeInTheDocument();
    expect(screen.getByText(/承認済.*3/)).toBeInTheDocument();
  });
});

// ── Risk matrix ──────────────────────────────────────────────────────────────

describe("BIAPage risk matrix", () => {
  it("renders risk matrix section header", () => {
    setSuccess([makeAssessment()], makeSummary(), makeMatrix());
    render(<BIAPage />);

    expect(screen.getByText("リスクマトリクス")).toBeInTheDocument();
  });

  it("renders matrix axis labels", () => {
    setSuccess([makeAssessment()], makeSummary(), makeMatrix());
    render(<BIAPage />);

    expect(screen.getByText("Y: Impact")).toBeInTheDocument();
    expect(screen.getByText("X: Likelihood")).toBeInTheDocument();
  });

  it("renders impact level labels", () => {
    setSuccess([makeAssessment()], makeSummary(), makeMatrix());
    render(<BIAPage />);

    expect(screen.getByText("Very Low")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Critical")).toBeInTheDocument();
  });

  it("renders likelihood level labels", () => {
    setSuccess([makeAssessment()], makeSummary(), makeMatrix());
    render(<BIAPage />);

    expect(screen.getByText("Rare")).toBeInTheDocument();
    expect(screen.getByText("Unlikely")).toBeInTheDocument();
    expect(screen.getByText("Possible")).toBeInTheDocument();
    expect(screen.getByText("Likely")).toBeInTheDocument();
    expect(screen.getByText("Almost Certain")).toBeInTheDocument();
  });

  it("renders assessment table section header", () => {
    setSuccess([makeAssessment()], makeSummary(), makeMatrix());
    render(<BIAPage />);

    expect(screen.getByText("アセスメント一覧")).toBeInTheDocument();
  });
});

// ── Risk score color mapping (parametric) ────────────────────────────────────

describe("BIAPage risk score colors", () => {
  const scoreCases: Array<[number, string]> = [
    [18, "text-green-700"],
    [45, "text-yellow-700"],
    [65, "text-orange-700"],
    [95, "text-red-700"],
  ];

  test.each(scoreCases)(
    "risk score %d renders with color class '%s'",
    (riskScore, expectedClass) => {
      setSuccess(
        [makeAssessment({ risk_score: riskScore })],
        makeSummary(),
        makeMatrix(),
      );
      render(<BIAPage />);

      const scoreEl = screen.getByText(String(riskScore));
      expect(scoreEl.className).toContain(expectedClass);
    }
  );
});
