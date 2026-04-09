/**
 * Tests for app/reports/page.tsx — ReportsPage component.
 *
 * Covers:
 *  - Loading state: spinner shown while fetching report data
 *  - Error state: error message displayed when API call fails
 *  - Readiness tab: score badges, system readiness table, recommendations
 *  - Compliance tab: compliance rate, system compliance table, overdue systems
 *  - Trends tab: exercise counts, yearly trends table, common issues
 *  - ISO20000 tab: compliance rate, checklist table, audit actions
 *  - Tab switching: clicking tabs triggers different API calls
 *  - ScoreBadge color thresholds: green/yellow/red based on score
 */
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import React from "react";
import ReportsPage from "../app/reports/page";
import type {
  ReadinessReport,
  RTOComplianceReport,
  ExerciseTrendReport,
  ISO20000Report,
} from "../lib/types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockReadiness = jest.fn();
const mockRtoCompliance = jest.fn();
const mockExerciseTrends = jest.fn();
const mockIso20000 = jest.fn();

jest.mock("../lib/api", () => ({
  dashboard: {
    reports: {
      readiness: (...args: unknown[]) => mockReadiness(...args),
      rtoCompliance: (...args: unknown[]) => mockRtoCompliance(...args),
      exerciseTrends: (...args: unknown[]) => mockExerciseTrends(...args),
      iso20000: (...args: unknown[]) => mockIso20000(...args),
    },
  },
}));

// ── Test data factories ──────────────────────────────────────────────────────

function makeReadinessReport(overrides: Partial<ReadinessReport> = {}): ReadinessReport {
  return {
    report_id: "r-1",
    report_type: "readiness",
    generated_at: "2026-04-09T00:00:00Z",
    overall_score: 85,
    total_systems: 10,
    tested_systems: 8,
    rto_met_systems: 7,
    system_readiness: [
      {
        system_name: "基幹システム",
        rto_target_hours: 2,
        rpo_target_hours: 1,
        last_test_rto_hours: 1.5,
        rto_achieved: true,
        tested: true,
        has_fallback: true,
        readiness_score: 90,
      },
      {
        system_name: "メールシステム",
        rto_target_hours: 4,
        rpo_target_hours: 2,
        last_test_rto_hours: undefined,
        rto_achieved: false,
        tested: false,
        has_fallback: false,
        readiness_score: 30,
      },
    ],
    untested_systems: ["メールシステム"],
    recommendations: ["メールシステムのテストを早急に実施してください"],
    ...overrides,
  };
}

function makeComplianceReport(overrides: Partial<RTOComplianceReport> = {}): RTOComplianceReport {
  return {
    report_id: "r-2",
    report_type: "rto_compliance",
    generated_at: "2026-04-09T00:00:00Z",
    compliance_rate: 70,
    total_systems: 10,
    compliant_systems: 7,
    system_compliance: [
      {
        system_name: "基幹システム",
        rto_target_hours: 2,
        rto_actual_hours: 1.5,
        deviation_hours: -0.5,
        compliant: true,
        trend: "improving",
      },
      {
        system_name: "会計システム",
        rto_target_hours: 4,
        rto_actual_hours: 6,
        deviation_hours: 2,
        compliant: false,
        trend: "deteriorating",
      },
    ],
    overdue_systems: ["会計システム"],
    ...overrides,
  };
}

function makeTrendsReport(overrides: Partial<ExerciseTrendReport> = {}): ExerciseTrendReport {
  return {
    report_id: "r-3",
    report_type: "exercise_trends",
    generated_at: "2026-04-09T00:00:00Z",
    total_exercises: 25,
    yearly_trends: [
      { year: 2025, exercise_count: 12, completed: 10, pass_count: 8, achievement_rate: 80 },
      { year: 2026, exercise_count: 13, completed: 11, pass_count: 9, achievement_rate: 82 },
    ],
    common_issues: { "手順不備": 5, "連絡遅延": 3 },
    total_improvements: 20,
    completed_improvements: 15,
    improvement_completion_rate: 75,
    ...overrides,
  };
}

function makeISO20000Report(overrides: Partial<ISO20000Report> = {}): ISO20000Report {
  return {
    report_id: "r-4",
    report_type: "iso20000",
    generated_at: "2026-04-09T00:00:00Z",
    compliance_rate: 90,
    total_items: 20,
    compliant_items: 18,
    checklist_results: [
      {
        id: "ITSCM-001",
        requirement: "BCPの策定と維持",
        category: "計画",
        compliant: true,
        evidence: "BCP文書が最新版で存在",
      },
      {
        id: "ITSCM-002",
        requirement: "定期的な訓練の実施",
        category: "実施",
        compliant: false,
        evidence: "直近6ヶ月の訓練記録なし",
      },
    ],
    non_compliant_items: [
      {
        id: "ITSCM-002",
        requirement: "定期的な訓練の実施",
        category: "実施",
        compliant: false,
        evidence: "直近6ヶ月の訓練記録なし",
      },
    ],
    next_audit_actions: ["訓練計画を策定し、四半期ごとに実施すること"],
    ...overrides,
  };
}

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Set readiness API to resolve with data. Loading state is managed by the component. */
function setReadinessSuccess(data?: ReadinessReport) {
  mockReadiness.mockResolvedValue(data ?? makeReadinessReport());
}

function setReadinessError() {
  mockReadiness.mockRejectedValue(new Error("API error"));
}

/** Never-resolving promise to keep component in loading state */
function setReadinessLoading() {
  mockReadiness.mockReturnValue(new Promise(() => {}));
}

function setComplianceSuccess(data?: RTOComplianceReport) {
  mockRtoCompliance.mockResolvedValue(data ?? makeComplianceReport());
}

function setComplianceError() {
  mockRtoCompliance.mockRejectedValue(new Error("API error"));
}

function setTrendsSuccess(data?: ExerciseTrendReport) {
  mockExerciseTrends.mockResolvedValue(data ?? makeTrendsReport());
}

function setTrendsError() {
  mockExerciseTrends.mockRejectedValue(new Error("API error"));
}

function setISO20000Success(data?: ISO20000Report) {
  mockIso20000.mockResolvedValue(data ?? makeISO20000Report());
}

function setISO20000Error() {
  mockIso20000.mockRejectedValue(new Error("API error"));
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Loading state ────────────────────────────────────────────────────────────

describe("ReportsPage loading state", () => {
  it("shows loading spinner and text while fetching", () => {
    setReadinessLoading();
    render(<ReportsPage />);

    expect(screen.getByText("レポートを生成しています...")).toBeInTheDocument();
    expect(document.querySelector(".animate-spin")).not.toBeNull();
  });

  it("shows the page heading even while loading", () => {
    setReadinessLoading();
    render(<ReportsPage />);

    expect(screen.getByText("レポート")).toBeInTheDocument();
  });

  it("renders all tab buttons while loading", () => {
    setReadinessLoading();
    render(<ReportsPage />);

    expect(screen.getByText("BCPレディネス")).toBeInTheDocument();
    expect(screen.getByText("RTO/RPOコンプライアンス")).toBeInTheDocument();
    expect(screen.getByText("訓練トレンド")).toBeInTheDocument();
    expect(screen.getByText("ISO20000準拠")).toBeInTheDocument();
  });
});

// ── Error state ──────────────────────────────────────────────────────────────

describe("ReportsPage error state", () => {
  it("shows error message when readiness API fails", async () => {
    setReadinessError();
    render(<ReportsPage />);

    // Error text appears in both header badge and body error panel
    await waitFor(() => {
      expect(screen.getAllByText("BCPレディネスレポートを取得できませんでした")).toHaveLength(2);
    });
    expect(screen.getByText("ネットワーク接続を確認し、再度お試しください。")).toBeInTheDocument();
  });

  it("shows error message when compliance API fails", async () => {
    setReadinessSuccess();
    setComplianceError();
    render(<ReportsPage />);
    await waitFor(() => {
      expect(screen.getByText("総合レディネススコア")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText("RTO/RPOコンプライアンス"));
    });

    // Error text appears in both header badge and body error panel
    await waitFor(() => {
      expect(screen.getAllByText("RTO/RPOコンプライアンスレポートを取得できませんでした")).toHaveLength(2);
    });
  });

  it("shows error badge in header area as a span element", async () => {
    setReadinessError();
    render(<ReportsPage />);

    await waitFor(() => {
      const badges = screen.getAllByText("BCPレディネスレポートを取得できませんでした");
      // The header badge is a <span>
      const headerBadge = badges.find((el) => el.tagName === "SPAN");
      expect(headerBadge).toBeDefined();
      expect(headerBadge?.className).toContain("bg-red-100");
    });
  });
});

// ── Readiness tab (default) ──────────────────────────────────────────────────

describe("ReportsPage readiness tab", () => {
  it("renders overall score badge", async () => {
    setReadinessSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("85%")).toBeInTheDocument();
    });
    expect(screen.getByText("総合レディネススコア")).toBeInTheDocument();
  });

  it("renders tested systems count", async () => {
    setReadinessSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("8/10")).toBeInTheDocument();
    });
    expect(screen.getByText("テスト済みシステム")).toBeInTheDocument();
  });

  it("renders RTO met systems count", async () => {
    setReadinessSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("7")).toBeInTheDocument();
    });
    expect(screen.getByText("RTO目標達成")).toBeInTheDocument();
  });

  it("renders system readiness table rows", async () => {
    setReadinessSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("基幹システム")).toBeInTheDocument();
    });
    expect(screen.getByText("メールシステム")).toBeInTheDocument();
  });

  it("shows RTO achieved/not achieved badges", async () => {
    setReadinessSuccess();
    render(<ReportsPage />);

    // "達成" appears in both the table header <th> and the badge <span>
    await waitFor(() => {
      const elements = screen.getAllByText("達成");
      expect(elements.length).toBeGreaterThanOrEqual(2); // th + badge
    });
    expect(screen.getByText("未達")).toBeInTheDocument();
  });

  it("shows tested status", async () => {
    setReadinessSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("済")).toBeInTheDocument();
    });
    expect(screen.getByText("未")).toBeInTheDocument();
  });

  it("shows fallback status", async () => {
    setReadinessSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("あり")).toBeInTheDocument();
    });
    expect(screen.getByText("なし")).toBeInTheDocument();
  });

  it("shows last test RTO or dash for untested systems", async () => {
    setReadinessSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("1.5h")).toBeInTheDocument();
    });
    // Untested system shows "-"
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("renders recommendations section", async () => {
    setReadinessSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("改善推奨事項")).toBeInTheDocument();
    });
    expect(screen.getByText("メールシステムのテストを早急に実施してください")).toBeInTheDocument();
  });

  it("does not render recommendations when empty", async () => {
    setReadinessSuccess(makeReadinessReport({ recommendations: [] }));
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("85%")).toBeInTheDocument();
    });
    expect(screen.queryByText("改善推奨事項")).not.toBeInTheDocument();
  });
});

// ── Compliance tab ───────────────────────────────────────────────────────────

describe("ReportsPage compliance tab", () => {
  beforeEach(() => {
    setReadinessSuccess();
    setComplianceSuccess();
  });

  async function switchToCompliance() {
    render(<ReportsPage />);
    await waitFor(() => {
      expect(screen.getByText("総合レディネススコア")).toBeInTheDocument();
    });
    await act(async () => {
      fireEvent.click(screen.getByText("RTO/RPOコンプライアンス"));
    });
  }

  it("renders compliance rate badge", async () => {
    await switchToCompliance();

    await waitFor(() => {
      expect(screen.getByText("70%")).toBeInTheDocument();
    });
    expect(screen.getByText("RTO達成率")).toBeInTheDocument();
  });

  it("renders compliant systems count", async () => {
    await switchToCompliance();

    await waitFor(() => {
      expect(screen.getByText("7/10")).toBeInTheDocument();
    });
    expect(screen.getByText("準拠システム")).toBeInTheDocument();
  });

  it("renders overdue systems count", async () => {
    await switchToCompliance();

    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument();
    });
    expect(screen.getByText("超過システム")).toBeInTheDocument();
  });

  it("renders system compliance table with trend labels", async () => {
    await switchToCompliance();

    await waitFor(() => {
      expect(screen.getByText("基幹システム")).toBeInTheDocument();
    });
    expect(screen.getByText("会計システム")).toBeInTheDocument();
    expect(screen.getByText("改善")).toBeInTheDocument();
    expect(screen.getByText("悪化")).toBeInTheDocument();
  });

  it("shows compliant/non-compliant badges", async () => {
    await switchToCompliance();

    await waitFor(() => {
      // "準拠" appears in table header and as a badge; use getAllByText
      const badges = screen.getAllByText("準拠");
      expect(badges.length).toBeGreaterThanOrEqual(2); // th + badge
    });
    expect(screen.getByText("超過")).toBeInTheDocument();
  });
});

// ── Trends tab ───────────────────────────────────────────────────────────────

describe("ReportsPage trends tab", () => {
  beforeEach(() => {
    setReadinessSuccess();
    setTrendsSuccess();
  });

  async function switchToTrends() {
    render(<ReportsPage />);
    await waitFor(() => {
      expect(screen.getByText("総合レディネススコア")).toBeInTheDocument();
    });
    await act(async () => {
      fireEvent.click(screen.getByText("訓練トレンド"));
    });
  }

  it("renders total exercises count", async () => {
    await switchToTrends();

    await waitFor(() => {
      expect(screen.getByText("25")).toBeInTheDocument();
    });
    expect(screen.getByText("総訓練回数")).toBeInTheDocument();
  });

  it("renders improvement completion rate", async () => {
    await switchToTrends();

    await waitFor(() => {
      expect(screen.getByText("75%")).toBeInTheDocument();
    });
    expect(screen.getByText("改善アクション実施率")).toBeInTheDocument();
  });

  it("renders improvement counts", async () => {
    await switchToTrends();

    await waitFor(() => {
      expect(screen.getByText("15/20")).toBeInTheDocument();
    });
    expect(screen.getByText("改善完了/総数")).toBeInTheDocument();
  });

  it("renders yearly trends table", async () => {
    await switchToTrends();

    await waitFor(() => {
      expect(screen.getByText("2025")).toBeInTheDocument();
    });
    expect(screen.getByText("2026")).toBeInTheDocument();
  });

  it("renders common issues section", async () => {
    await switchToTrends();

    await waitFor(() => {
      expect(screen.getByText("頻出課題カテゴリ")).toBeInTheDocument();
    });
    expect(screen.getByText("手順不備: 5件")).toBeInTheDocument();
    expect(screen.getByText("連絡遅延: 3件")).toBeInTheDocument();
  });

  it("does not render common issues when empty", async () => {
    setTrendsSuccess(makeTrendsReport({ common_issues: {} }));
    await switchToTrends();

    await waitFor(() => {
      expect(screen.getByText("25")).toBeInTheDocument();
    });
    expect(screen.queryByText("頻出課題カテゴリ")).not.toBeInTheDocument();
  });
});

// ── ISO20000 tab ─────────────────────────────────────────────────────────────

describe("ReportsPage ISO20000 tab", () => {
  beforeEach(() => {
    setReadinessSuccess();
    setISO20000Success();
  });

  async function switchToISO20000() {
    render(<ReportsPage />);
    await waitFor(() => {
      expect(screen.getByText("総合レディネススコア")).toBeInTheDocument();
    });
    await act(async () => {
      fireEvent.click(screen.getByText("ISO20000準拠"));
    });
  }

  it("renders ISO compliance rate badge", async () => {
    await switchToISO20000();

    await waitFor(() => {
      expect(screen.getByText("90%")).toBeInTheDocument();
    });
    expect(screen.getByText("ISO20000 ITSCM準拠率")).toBeInTheDocument();
  });

  it("renders compliant items count", async () => {
    await switchToISO20000();

    await waitFor(() => {
      expect(screen.getByText("18/20")).toBeInTheDocument();
    });
    expect(screen.getByText("準拠項目")).toBeInTheDocument();
  });

  it("renders non-compliant items count", async () => {
    await switchToISO20000();

    await waitFor(() => {
      expect(screen.getByText("未対応項目")).toBeInTheDocument();
    });
  });

  it("renders checklist table", async () => {
    await switchToISO20000();

    await waitFor(() => {
      expect(screen.getByText("ITSCM-001")).toBeInTheDocument();
    });
    expect(screen.getByText("ITSCM-002")).toBeInTheDocument();
    expect(screen.getByText("BCPの策定と維持")).toBeInTheDocument();
    expect(screen.getByText("定期的な訓練の実施")).toBeInTheDocument();
  });

  it("shows compliant/non-compliant badges in checklist", async () => {
    await switchToISO20000();

    await waitFor(() => {
      // "準拠" for compliant item, "未対応" for non-compliant
      expect(screen.getByText("未対応")).toBeInTheDocument();
    });
  });

  it("renders next audit actions", async () => {
    await switchToISO20000();

    await waitFor(() => {
      expect(screen.getByText("次回監査対応事項")).toBeInTheDocument();
    });
    expect(screen.getByText("訓練計画を策定し、四半期ごとに実施すること")).toBeInTheDocument();
  });

  it("does not render audit actions when empty", async () => {
    setISO20000Success(makeISO20000Report({ next_audit_actions: [] }));
    await switchToISO20000();

    await waitFor(() => {
      expect(screen.getByText("90%")).toBeInTheDocument();
    });
    expect(screen.queryByText("次回監査対応事項")).not.toBeInTheDocument();
  });
});

// ── Tab switching ────────────────────────────────────────────────────────────

describe("ReportsPage tab switching", () => {
  it("calls readiness API on initial render", async () => {
    setReadinessSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(mockReadiness).toHaveBeenCalledTimes(1);
    });
  });

  it("calls rtoCompliance API when switching to compliance tab", async () => {
    setReadinessSuccess();
    setComplianceSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("総合レディネススコア")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText("RTO/RPOコンプライアンス"));
    });

    await waitFor(() => {
      expect(mockRtoCompliance).toHaveBeenCalledTimes(1);
    });
  });

  it("calls exerciseTrends API when switching to trends tab", async () => {
    setReadinessSuccess();
    setTrendsSuccess();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("総合レディネススコア")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText("訓練トレンド"));
    });

    await waitFor(() => {
      expect(mockExerciseTrends).toHaveBeenCalledTimes(1);
    });
  });

  it("calls iso20000 API when switching to ISO20000 tab", async () => {
    setReadinessSuccess();
    setISO20000Success();
    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("総合レディネススコア")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText("ISO20000準拠"));
    });

    await waitFor(() => {
      expect(mockIso20000).toHaveBeenCalledTimes(1);
    });
  });
});

// ── ScoreBadge color thresholds ──────────────────────────────────────────────

describe("ReportsPage ScoreBadge color thresholds", () => {
  const cases: Array<[number, string]> = [
    [85, "bg-green-50"],   // >= 80: green
    [80, "bg-green-50"],   // exactly 80: green
    [75, "bg-yellow-50"],  // >= 60 and < 80: yellow
    [60, "bg-yellow-50"],  // exactly 60: yellow
    [45, "bg-red-50"],     // < 60: red
  ];

  test.each(cases)(
    "score %d renders with class '%s'",
    async (score, expectedClass) => {
      setReadinessSuccess(makeReadinessReport({ overall_score: score }));
      render(<ReportsPage />);

      await waitFor(() => {
        expect(screen.getByText(`${score}%`)).toBeInTheDocument();
      });

      const badge = screen.getByText(`${score}%`).closest("div");
      expect(badge?.className).toContain(expectedClass);
    }
  );
});

// ── Achievement rate color in trends table ───────────────────────────────────

describe("ReportsPage achievement rate colors", () => {
  const cases: Array<[number, string]> = [
    [80, "text-green-600"],   // >= 80
    [50, "text-yellow-600"],  // >= 50 and < 80
    [30, "text-red-600"],     // < 50
  ];

  test.each(cases)(
    "achievement rate %d renders with class '%s'",
    async (rate, expectedClass) => {
      setReadinessSuccess();
      setTrendsSuccess(
        makeTrendsReport({
          yearly_trends: [
            { year: 2026, exercise_count: 10, completed: 8, pass_count: 6, achievement_rate: rate },
          ],
        })
      );

      render(<ReportsPage />);
      await waitFor(() => {
        expect(screen.getByText("総合レディネススコア")).toBeInTheDocument();
      });

      await act(async () => {
        fireEvent.click(screen.getByText("訓練トレンド"));
      });

      await waitFor(() => {
        const rateEl = screen.getByText(`${rate}%`);
        expect(rateEl.className).toContain(expectedClass);
      });
    }
  );
});
