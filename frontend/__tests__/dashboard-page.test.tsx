/**
 * Tests for app/page.tsx — DashboardPage component.
 *
 * Covers:
 *  - Loading state: spinner + loading text while useDashboard fetches
 *  - Error/offline mode: mock data shown, offline badge displayed
 *  - Success state: API data merged with mock, metrics displayed
 *  - Business logic: exercise result badge colors (success=green, other=yellow)
 *  - Active incidents: "none" message vs incident list
 */
import { render, screen } from "@testing-library/react";
import React from "react";
import DashboardPage from "../app/page";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseDashboard = jest.fn();
jest.mock("../lib/hooks", () => ({
  useDashboard: () => mockUseDashboard(),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function setLoading() {
  mockUseDashboard.mockReturnValue({ data: null, loading: true, error: null });
}

function setError() {
  mockUseDashboard.mockReturnValue({
    data: null,
    loading: false,
    error: new Error("API unreachable"),
  });
}

function setSuccess(overrides = {}) {
  mockUseDashboard.mockReturnValue({
    data: {
      readiness_score: 95,
      total_systems: 30,
      rto_achievement_rate: 99,
      rpo_achievement_rate: 97,
      active_incidents: 0,
      recent_exercises: [],
      active_incident_list: [],
      next_exercise: null,
      ...overrides,
    },
    loading: false,
    error: null,
  });
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Loading state ─────────────────────────────────────────────────────────────

describe("DashboardPage loading state", () => {
  it("shows loading spinner and text while fetching", () => {
    setLoading();
    render(<DashboardPage />);

    expect(screen.getByText(/データを読み込んでいます/i)).toBeInTheDocument();
    // Spinner is rendered as a div with animate-spin
    expect(document.querySelector(".animate-spin")).not.toBeNull();
  });

  it("does not render dashboard content while loading", () => {
    setLoading();
    render(<DashboardPage />);

    expect(screen.queryByText("ダッシュボード")).not.toBeInTheDocument();
  });
});

// ── Error / offline mode ──────────────────────────────────────────────────────

describe("DashboardPage error / offline mode", () => {
  it("shows offline mode badge on API error", () => {
    setError();
    render(<DashboardPage />);

    expect(screen.getByText(/オフラインモード/i)).toBeInTheDocument();
  });

  it("still renders dashboard content using mock data on error", () => {
    setError();
    render(<DashboardPage />);

    // Mock data readiness_score is 78
    expect(screen.getByText("78")).toBeInTheDocument();
    expect(screen.getByText("ダッシュボード")).toBeInTheDocument();
  });

  it("shows mock RTO achievement rate on error", () => {
    setError();
    render(<DashboardPage />);

    // Mock data has rto_achievement_rate: 87
    expect(screen.getByText("87%")).toBeInTheDocument();
  });
});

// ── Success state ─────────────────────────────────────────────────────────────

describe("DashboardPage success state", () => {
  it("shows API readiness score", () => {
    setSuccess({ readiness_score: 95 });
    render(<DashboardPage />);

    expect(screen.getByText("95")).toBeInTheDocument();
  });

  it("shows RTO and RPO achievement rates", () => {
    setSuccess({ rto_achievement_rate: 99, rpo_achievement_rate: 97 });
    render(<DashboardPage />);

    expect(screen.getByText("99%")).toBeInTheDocument();
    expect(screen.getByText("97%")).toBeInTheDocument();
  });

  it("shows total systems count", () => {
    setSuccess({ total_systems: 30 });
    render(<DashboardPage />);

    expect(screen.getAllByText(/30システム/)).toHaveLength(2); // RTO + RPO cards
  });

  it("shows next exercise info when provided", () => {
    setSuccess({
      next_exercise: {
        title: "全社BCP訓練",
        date: "2026-05-01",
        type: "フルスケール",
      },
    });
    render(<DashboardPage />);

    expect(screen.getByText("全社BCP訓練")).toBeInTheDocument();
    expect(screen.getByText("2026-05-01")).toBeInTheDocument();
    expect(screen.getByText("フルスケール")).toBeInTheDocument();
  });

  it("does not show next exercise section when null", () => {
    setSuccess({ next_exercise: null });
    render(<DashboardPage />);

    expect(screen.queryByText("次回訓練予定")).not.toBeInTheDocument();
  });
});

// ── Exercise result badge colors ──────────────────────────────────────────────

describe("DashboardPage exercise result badge colors", () => {
  it("renders green badge for successful exercises", () => {
    setSuccess({
      recent_exercises: [
        { id: "EX-001", title: "フェイルオーバー訓練", date: "2026-03-15", result: "成功" },
      ],
    });
    render(<DashboardPage />);

    const badge = screen.getByText("成功");
    expect(badge.className).toContain("bg-green-100");
    expect(badge.className).toContain("text-green-700");
  });

  it("renders yellow badge for exercises with issues", () => {
    setSuccess({
      recent_exercises: [
        { id: "EX-002", title: "DR切替訓練", date: "2026-03-01", result: "一部課題あり" },
      ],
    });
    render(<DashboardPage />);

    const badge = screen.getByText("一部課題あり");
    expect(badge.className).toContain("bg-yellow-100");
    expect(badge.className).toContain("text-yellow-700");
  });

  it("renders exercise table with ID, title, date, result columns", () => {
    setSuccess({
      recent_exercises: [
        { id: "EX-2026-001", title: "基幹系訓練", date: "2026-03-15", result: "成功" },
      ],
    });
    render(<DashboardPage />);

    expect(screen.getByText("EX-2026-001")).toBeInTheDocument();
    expect(screen.getByText("基幹系訓練")).toBeInTheDocument();
    expect(screen.getByText("2026-03-15")).toBeInTheDocument();
  });
});

// ── Active incidents ──────────────────────────────────────────────────────────

describe("DashboardPage active incidents", () => {
  it("shows 'インシデントなし' when no active incidents", () => {
    setSuccess({ active_incident_list: [] });
    render(<DashboardPage />);

    expect(screen.getByText("インシデントなし")).toBeInTheDocument();
  });

  it("renders active incident titles when present", () => {
    setSuccess({
      active_incident_list: [
        { id: "INC-001", title: "基幹システム障害", severity: "high" },
        { id: "INC-002", title: "ネットワーク遅延", severity: "medium" },
      ],
    });
    render(<DashboardPage />);

    expect(screen.getByText("基幹システム障害")).toBeInTheDocument();
    expect(screen.getByText("ネットワーク遅延")).toBeInTheDocument();
    expect(screen.queryByText("インシデントなし")).not.toBeInTheDocument();
  });
});
