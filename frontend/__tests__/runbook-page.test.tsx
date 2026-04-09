/**
 * Tests for app/runbook/page.tsx — RunbookPage component.
 *
 * Covers:
 *  - Default render: page heading and tab buttons displayed
 *  - Tab navigation: clicking tabs switches content panels
 *  - Checklist tab: items rendered with categories, required badges, checkbox toggle
 *  - Rollback tab: steps with action, description, responsible, estimated_minutes
 *  - DR Failover tab: timeline steps rendered
 *  - Incident tab: scenario select, playbook steps rendered
 *  - API fetch: falls back to mock data on fetch failure
 *  - Completion counter: updates when checkboxes toggled
 *  - Active tab styling
 */
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import React from "react";
import RunbookPage from "../app/runbook/page";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockFetch = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  // By default, fetch rejects so the component uses built-in mock data
  mockFetch.mockRejectedValue(new Error("Network error"));
  global.fetch = mockFetch;
});

afterAll(() => {
  jest.restoreAllMocks();
});

// Helper to render and flush effects
async function renderPage() {
  let result: ReturnType<typeof render>;
  await act(async () => {
    result = render(<RunbookPage />);
  });
  return result!;
}

// ── Default render ───────────────────────────────────────────────────────────

describe("RunbookPage default render", () => {
  it("renders the page heading", async () => {
    await renderPage();
    expect(screen.getByText("運用ランブック")).toBeInTheDocument();
  });

  it("renders all four tab buttons", async () => {
    await renderPage();
    expect(screen.getByText("デプロイチェックリスト")).toBeInTheDocument();
    expect(screen.getByText("ロールバック手順")).toBeInTheDocument();
    expect(screen.getByText("DRフェイルオーバー")).toBeInTheDocument();
    expect(screen.getByText("インシデント対応")).toBeInTheDocument();
  });

  it("shows checklist tab as active by default", async () => {
    await renderPage();
    expect(screen.getByText("デプロイ前チェックリスト")).toBeInTheDocument();
  });
});

// ── Tab navigation ───────────────────────────────────────────────────────────

describe("RunbookPage tab navigation", () => {
  it("clicking 'ロールバック手順' tab shows rollback content", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "ロールバック手順" }));
    // Tab button and h3 heading share same text, so use getAllByText
    const matches = screen.getAllByText("ロールバック手順");
    expect(matches.length).toBe(2); // button + heading
  });

  const tabCases: Array<[string, string]> = [
    ["DRフェイルオーバー", "DRフェイルオーバー手順"],
    ["インシデント対応", "インシデント対応プレイブック"],
    ["デプロイチェックリスト", "デプロイ前チェックリスト"],
  ];

  test.each(tabCases)(
    "clicking '%s' tab shows content with heading '%s'",
    async (tabLabel, contentHeading) => {
      await renderPage();
      fireEvent.click(screen.getByRole("button", { name: tabLabel }));
      expect(screen.getByText(contentHeading)).toBeInTheDocument();
    }
  );

  it("hides checklist content when switching to rollback tab", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "ロールバック手順" }));
    expect(screen.queryByText("デプロイ前チェックリスト")).not.toBeInTheDocument();
  });
});

// ── Checklist tab ────────────────────────────────────────────────────────────

describe("RunbookPage checklist tab", () => {
  it("renders mock checklist items", async () => {
    await renderPage();
    expect(screen.getByText("全ユニットテストがパスしていること")).toBeInTheDocument();
    expect(screen.getByText("E2Eテストがパスしていること")).toBeInTheDocument();
    expect(screen.getByText("ロールバック手順が準備されていること")).toBeInTheDocument();
    expect(screen.getByText("関係者への事前通知が完了していること")).toBeInTheDocument();
  });

  it("renders category badges for checklist items", async () => {
    await renderPage();
    expect(screen.getAllByText("テスト").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("品質").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("セキュリティ").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("データベース").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("インフラ").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("承認").length).toBeGreaterThanOrEqual(1);
  });

  it("renders required badges for required items", async () => {
    await renderPage();
    // 11 of 12 items are required
    const requiredBadges = screen.getAllByText("必須");
    expect(requiredBadges.length).toBe(11);
  });

  it("shows initial completion count as 0 / 12", async () => {
    await renderPage();
    expect(screen.getByText("0 / 12 完了")).toBeInTheDocument();
  });

  it("updates completion count when checkbox is toggled", async () => {
    await renderPage();
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    expect(screen.getByText("1 / 12 完了")).toBeInTheDocument();
  });

  it("decrements completion count when checkbox is unchecked", async () => {
    await renderPage();
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    expect(screen.getByText("1 / 12 完了")).toBeInTheDocument();
    fireEvent.click(checkboxes[0]);
    expect(screen.getByText("0 / 12 完了")).toBeInTheDocument();
  });

  it("toggles multiple checkboxes independently", async () => {
    await renderPage();
    const checkboxes = screen.getAllByRole("checkbox");
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);
    fireEvent.click(checkboxes[2]);
    expect(screen.getByText("3 / 12 完了")).toBeInTheDocument();
  });
});

// ── Rollback tab ─────────────────────────────────────────────────────────────

describe("RunbookPage rollback tab", () => {
  it("renders rollback step actions", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "ロールバック手順" }));
    expect(screen.getByText("異常検知・ロールバック判断")).toBeInTheDocument();
    expect(screen.getByText("コンテナイメージの切り戻し")).toBeInTheDocument();
    expect(screen.getByText("事後報告・原因分析")).toBeInTheDocument();
  });

  it("renders responsible labels", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "ロールバック手順" }));
    expect(screen.getByText("担当: インシデントコマンダー")).toBeInTheDocument();
    expect(screen.getByText("担当: DBAチーム")).toBeInTheDocument();
  });

  it("renders estimated minutes", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "ロールバック手順" }));
    expect(screen.getByText("想定: 5分")).toBeInTheDocument();
    expect(screen.getByText("想定: 30分")).toBeInTheDocument();
  });
});

// ── DR Failover tab ──────────────────────────────────────────────────────────

describe("RunbookPage DR failover tab", () => {
  it("renders DR step actions with step numbers", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "DRフェイルオーバー" }));
    expect(screen.getByText(/Step 1: 災害発生の確認/)).toBeInTheDocument();
    expect(screen.getByText(/Step 4: DBフェイルオーバー実行/)).toBeInTheDocument();
    expect(screen.getByText(/Step 10: 監視強化・状況報告/)).toBeInTheDocument();
  });

  it("renders estimated minutes badges", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "DRフェイルオーバー" }));
    // Multiple steps have 10分 and 15分
    expect(screen.getAllByText("10分").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("15分").length).toBeGreaterThanOrEqual(1);
  });

  it("renders responsible labels for DR steps", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "DRフェイルオーバー" }));
    expect(screen.getByText("担当: CIO/CISO")).toBeInTheDocument();
    expect(screen.getByText("担当: 広報/CS")).toBeInTheDocument();
  });
});

// ── Incident tab ─────────────────────────────────────────────────────────────

describe("RunbookPage incident tab", () => {
  it("renders earthquake playbook by default", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "インシデント対応" }));
    expect(screen.getByText("地震発生時インシデント対応プレイブック")).toBeInTheDocument();
    expect(screen.getByText("安全確認")).toBeInTheDocument();
    expect(screen.getByText("復旧確認・事後対応")).toBeInTheDocument();
  });

  it("renders scenario selector with three options", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "インシデント対応" }));
    const select = screen.getByRole("combobox");
    expect(select).toBeInTheDocument();
    const options = select.querySelectorAll("option");
    expect(options).toHaveLength(3);
    expect(options[0]).toHaveTextContent("地震");
    expect(options[1]).toHaveTextContent("ランサムウェア");
    expect(options[2]).toHaveTextContent("データセンター障害");
  });

  it("switches to ransomware playbook when selected", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "インシデント対応" }));
    const select = screen.getByRole("combobox");

    await act(async () => {
      fireEvent.change(select, { target: { value: "ransomware" } });
    });

    await waitFor(() => {
      expect(screen.getByText("ランサムウェア感染時インシデント対応プレイブック")).toBeInTheDocument();
    });
    expect(screen.getByText("検知・初動対応")).toBeInTheDocument();
    expect(screen.getByText("証拠保全")).toBeInTheDocument();
  });

  it("switches to dc_failure playbook when selected", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "インシデント対応" }));
    const select = screen.getByRole("combobox");

    await act(async () => {
      fireEvent.change(select, { target: { value: "dc_failure" } });
    });

    await waitFor(() => {
      expect(screen.getByText("データセンター障害時インシデント対応プレイブック")).toBeInTheDocument();
    });
    expect(screen.getByText("障害検知・初期評価")).toBeInTheDocument();
  });
});

// ── API fetch behavior ───────────────────────────────────────────────────────

describe("RunbookPage API fetch behavior", () => {
  it("calls fetch for checklist, rollback, and DR on mount", async () => {
    await renderPage();
    const urls = mockFetch.mock.calls.map((c: unknown[]) => c[0] as string);
    expect(urls).toContain("/api/runbook/deployment-checklist");
    expect(urls).toContain("/api/runbook/rollback-procedure");
    expect(urls).toContain("/api/runbook/dr-failover");
  });

  it("calls fetch for incident playbook on mount", async () => {
    await renderPage();
    const urls = mockFetch.mock.calls.map((c: unknown[]) => c[0] as string);
    expect(urls).toContain("/api/runbook/incident-playbook/earthquake");
  });

  it("falls back to mock data when fetch returns non-ok status", async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 500 });
    await renderPage();
    // Mock data still renders
    expect(screen.getByText("全ユニットテストがパスしていること")).toBeInTheDocument();
  });
});

// ── Active tab styling ───────────────────────────────────────────────────────

describe("RunbookPage active tab styling", () => {
  it("applies active styling to the selected tab", async () => {
    await renderPage();
    const checklistTab = screen.getByRole("button", { name: "デプロイチェックリスト" });
    expect(checklistTab.className).toContain("bg-white");
    expect(checklistTab.className).toContain("text-blue-700");
  });

  it("applies inactive styling to non-selected tabs", async () => {
    await renderPage();
    const rollbackTab = screen.getByRole("button", { name: "ロールバック手順" });
    expect(rollbackTab.className).toContain("text-slate-600");
    expect(rollbackTab.className).not.toContain("text-blue-700");
  });

  it("moves active styling when tab is clicked", async () => {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "ロールバック手順" }));

    const rollbackTab = screen.getByRole("button", { name: "ロールバック手順" });
    expect(rollbackTab.className).toContain("bg-white");
    expect(rollbackTab.className).toContain("text-blue-700");

    const checklistTab = screen.getByRole("button", { name: "デプロイチェックリスト" });
    expect(checklistTab.className).toContain("text-slate-600");
  });
});
