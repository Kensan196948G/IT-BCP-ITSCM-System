/**
 * Tests for app/exercises/page.tsx — ExercisesPage component.
 *
 * Covers:
 *  - Loading state: spinner shown while useExercises fetches
 *  - Error/offline mode: mock data fallback with badge
 *  - Success state: exercise list table rendered
 *  - Status badges: planned/in_progress/completed labels and colors
 *  - Result badges: pass/partial_pass/fail labels and colors
 *  - Action buttons: "開始" for planned, "完了" for in_progress, "レポート" for completed
 *  - handleStart / handleComplete: API calls triggered on button click
 *  - Report panel: renders RTO achievement data after "レポート" click
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import ExercisesPage from "../app/exercises/page";
import type { BCPExercise } from "../lib/types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseExercises = jest.fn();
jest.mock("../lib/hooks", () => ({
  useExercises: () => mockUseExercises(),
}));

const mockStart = jest.fn().mockResolvedValue({});
const mockComplete = jest.fn().mockResolvedValue({});
const mockReport = jest.fn();
jest.mock("../lib/api", () => ({
  exercises: {
    start: (...args: unknown[]) => mockStart(...args),
    complete: (...args: unknown[]) => mockComplete(...args),
    report: (...args: unknown[]) => mockReport(...args),
  },
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

const mockRefetch = jest.fn();

function setLoading() {
  mockUseExercises.mockReturnValue({ data: null, loading: true, error: null, refetch: mockRefetch });
}

function setError() {
  mockUseExercises.mockReturnValue({ data: null, loading: false, error: new Error("API error"), refetch: mockRefetch });
}

function setSuccess(exercises: BCPExercise[]) {
  mockUseExercises.mockReturnValue({ data: exercises, loading: false, error: null, refetch: mockRefetch });
}

function makeExercise(overrides: Partial<BCPExercise> = {}): BCPExercise {
  return {
    id: "1",
    exercise_id: "EX-2026-001",
    title: "テスト訓練",
    exercise_type: "フェイルオーバー",
    scheduled_date: "2026-04-10",
    status: "planned",
    ...overrides,
  } as BCPExercise;
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Loading state ─────────────────────────────────────────────────────────────

describe("ExercisesPage loading state", () => {
  it("shows loading spinner and text while fetching", () => {
    setLoading();
    render(<ExercisesPage />);

    expect(screen.getByText(/データを読み込んでいます/i)).toBeInTheDocument();
    expect(document.querySelector(".animate-spin")).not.toBeNull();
  });

  it("does not render page content while loading", () => {
    setLoading();
    render(<ExercisesPage />);

    expect(screen.queryByText("訓練管理")).not.toBeInTheDocument();
  });
});

// ── Error / offline mode ──────────────────────────────────────────────────────

describe("ExercisesPage error / offline mode", () => {
  it("shows offline mode badge on API error", () => {
    setError();
    render(<ExercisesPage />);

    expect(screen.getByText(/オフラインモード/)).toBeInTheDocument();
  });

  it("renders mock data when API errors", () => {
    setError();
    render(<ExercisesPage />);

    // Mock data first exercise
    expect(screen.getByText("基幹系フェイルオーバー訓練")).toBeInTheDocument();
    expect(screen.getByText("訓練管理")).toBeInTheDocument();
  });
});

// ── Success state ─────────────────────────────────────────────────────────────

describe("ExercisesPage success state", () => {
  it("renders the page heading", () => {
    setSuccess([makeExercise()]);
    render(<ExercisesPage />);

    expect(screen.getByText("訓練管理")).toBeInTheDocument();
  });

  it("renders exercise ID, title, type, and date", () => {
    setSuccess([
      makeExercise({
        exercise_id: "EX-2026-010",
        title: "ネットワーク障害訓練",
        exercise_type: "卓上訓練",
        scheduled_date: "2026-05-01",
      }),
    ]);
    render(<ExercisesPage />);

    expect(screen.getByText("EX-2026-010")).toBeInTheDocument();
    expect(screen.getByText("ネットワーク障害訓練")).toBeInTheDocument();
    expect(screen.getByText("卓上訓練")).toBeInTheDocument();
    expect(screen.getByText("2026-05-01")).toBeInTheDocument();
  });

  it("does not show offline badge when no error", () => {
    setSuccess([makeExercise()]);
    render(<ExercisesPage />);

    expect(screen.queryByText(/オフラインモード/)).not.toBeInTheDocument();
  });
});

// ── Status badges ─────────────────────────────────────────────────────────────

describe("ExercisesPage status badges", () => {
  const cases: Array<[string, string, string]> = [
    ["planned", "予定", "bg-blue-100"],
    ["in_progress", "実施中", "bg-orange-100"],
    ["completed", "完了", "bg-green-100"],
  ];

  test.each(cases)(
    "status '%s' shows label '%s' with class '%s'",
    (status, label, bgClass) => {
      setSuccess([makeExercise({ status })]);
      render(<ExercisesPage />);

      const badge = screen.getByText(label);
      expect(badge.className).toContain(bgClass);
    }
  );
});

// ── Result badges ─────────────────────────────────────────────────────────────

describe("ExercisesPage result badges", () => {
  const cases: Array<[string, string, string]> = [
    ["pass", "成功", "bg-green-100"],
    ["partial_pass", "一部課題あり", "bg-yellow-100"],
    ["fail", "失敗", "bg-red-100"],
  ];

  test.each(cases)(
    "result '%s' shows label '%s' with class '%s'",
    (result, label, bgClass) => {
      setSuccess([makeExercise({ status: "completed", overall_result: result })]);
      render(<ExercisesPage />);

      const badge = screen.getByText(label);
      expect(badge.className).toContain(bgClass);
    }
  );

  it("shows '-' when overall_result is absent", () => {
    setSuccess([makeExercise({ status: "planned", overall_result: undefined })]);
    render(<ExercisesPage />);

    expect(screen.getByText("-")).toBeInTheDocument();
  });
});

// ── Action buttons ────────────────────────────────────────────────────────────

describe("ExercisesPage action buttons", () => {
  it("shows '開始' button for planned exercises", () => {
    setSuccess([makeExercise({ status: "planned" })]);
    render(<ExercisesPage />);

    expect(screen.getByRole("button", { name: "開始" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "完了" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "レポート" })).not.toBeInTheDocument();
  });

  it("shows '完了' button for in_progress exercises", () => {
    setSuccess([makeExercise({ id: "2", status: "in_progress" })]);
    render(<ExercisesPage />);

    expect(screen.getByRole("button", { name: "完了" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "開始" })).not.toBeInTheDocument();
  });

  it("shows 'レポート' button for completed exercises", () => {
    setSuccess([makeExercise({ id: "3", status: "completed", overall_result: "pass" })]);
    render(<ExercisesPage />);

    expect(screen.getByRole("button", { name: "レポート" })).toBeInTheDocument();
  });
});

// ── API calls ─────────────────────────────────────────────────────────────────

describe("ExercisesPage API calls", () => {
  it("calls exercises.start() when '開始' is clicked", async () => {
    setSuccess([makeExercise({ id: "ex-1", status: "planned" })]);
    render(<ExercisesPage />);

    fireEvent.click(screen.getByRole("button", { name: "開始" }));

    await waitFor(() => expect(mockStart).toHaveBeenCalledWith("ex-1"));
    expect(mockRefetch).toHaveBeenCalled();
  });

  it("calls exercises.complete() when '完了' is clicked", async () => {
    setSuccess([makeExercise({ id: "ex-2", status: "in_progress" })]);
    render(<ExercisesPage />);

    fireEvent.click(screen.getByRole("button", { name: "完了" }));

    await waitFor(() => expect(mockComplete).toHaveBeenCalledWith("ex-2"));
    expect(mockRefetch).toHaveBeenCalled();
  });
});

// ── Report panel ──────────────────────────────────────────────────────────────

describe("ExercisesPage report panel", () => {
  it("shows report data after clicking 'レポート' button", async () => {
    mockReport.mockResolvedValue({
      exercise: makeExercise({ title: "報告対象訓練", status: "completed", overall_result: "pass" }),
      rto_records: [
        { id: "r1", exercise_id: "EX-2026-001", system_name: "基幹システム", rto_target_hours: 2, rto_actual_hours: 1.5, achieved: true, recorded_at: "2026-04-10" },
      ],
      rto_achievement_rate: 100.0,
      total_systems_tested: 3,
      systems_achieved: 3,
      systems_failed: 0,
      findings: ["復旧手順が正常に機能した"],
      recommendations: ["手順書の定期更新を推奨"],
    });

    setSuccess([makeExercise({ id: "3", status: "completed", overall_result: "pass" })]);
    render(<ExercisesPage />);

    fireEvent.click(screen.getByRole("button", { name: "レポート" }));

    await waitFor(() => expect(screen.getByText(/訓練レポート/)).toBeInTheDocument());

    // RTO achievement summary — "3" appears twice (total_systems_tested + systems_achieved)
    expect(screen.getAllByText("3")).toHaveLength(2);
    expect(screen.getByText("0")).toBeInTheDocument(); // systems_failed
    expect(screen.getByText("100.0%")).toBeInTheDocument(); // achievement rate

    // RTO records
    expect(screen.getByText("基幹システム")).toBeInTheDocument();

    // Findings & recommendations
    expect(screen.getByText("復旧手順が正常に機能した")).toBeInTheDocument();
    expect(screen.getByText("手順書の定期更新を推奨")).toBeInTheDocument();
  });

  it("closes report panel when '閉じる' is clicked", async () => {
    mockReport.mockResolvedValue({
      exercise: makeExercise({ title: "閉じるテスト", status: "completed" }),
      rto_records: [],
      rto_achievement_rate: null,
      total_systems_tested: 0,
      systems_achieved: 0,
      systems_failed: 0,
      findings: [],
      recommendations: [],
    });

    setSuccess([makeExercise({ id: "4", status: "completed", overall_result: "pass" })]);
    render(<ExercisesPage />);

    fireEvent.click(screen.getByRole("button", { name: "レポート" }));
    await waitFor(() => expect(screen.getByText(/訓練レポート/)).toBeInTheDocument());

    fireEvent.click(screen.getByText("閉じる"));

    expect(screen.queryByText(/訓練レポート/)).not.toBeInTheDocument();
  });
});
