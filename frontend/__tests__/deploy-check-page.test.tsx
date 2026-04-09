/**
 * Tests for app/deploy-check/page.tsx — DeployCheckPage component.
 *
 * Covers:
 *  - Page heading and version badge
 *  - Page links section (14 navigation links)
 *  - API test table rendering
 *  - Re-test button
 *  - Fetch success → OK badge, Fetch failure → NG badge
 */
import { render, screen, waitFor, act } from "@testing-library/react";
import React from "react";
import DeployCheckPage from "../app/deploy-check/page";

// Mock next/link
jest.mock("next/link", () => {
  const MockLink = ({ href, children, className }: {
    href: string; children: React.ReactNode; className?: string;
  }) => <a href={href} className={className}>{children}</a>;
  MockLink.displayName = "MockLink";
  return MockLink;
});

beforeEach(() => {
  jest.clearAllMocks();
});

describe("DeployCheckPage", () => {
  it("renders page heading and version badge", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("no server"));
    await act(async () => { render(<DeployCheckPage />); });

    expect(screen.getByText("デプロイ確認")).toBeInTheDocument();
    expect(screen.getByText(/v0\.1\.0/)).toBeInTheDocument();
  });

  it("renders all page navigation links", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("no server"));
    await act(async () => { render(<DeployCheckPage />); });

    expect(screen.getByText("ダッシュボード")).toBeInTheDocument();
    expect(screen.getByText("BCP計画")).toBeInTheDocument();
    expect(screen.getByText("復旧手順書")).toBeInTheDocument();
    expect(screen.getByText("連絡網")).toBeInTheDocument();
    expect(screen.getByText("訓練管理")).toBeInTheDocument();
    expect(screen.getByText("RTOモニタ")).toBeInTheDocument();
    expect(screen.getByText("システム状態")).toBeInTheDocument();
  });

  it("renders API test section heading", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("no server"));
    await act(async () => { render(<DeployCheckPage />); });

    expect(screen.getByText("API接続テスト")).toBeInTheDocument();
  });

  it("shows NG badges when all API calls fail", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("no server"));
    await act(async () => { render(<DeployCheckPage />); });

    await waitFor(() => {
      const ngBadges = screen.getAllByText("NG");
      expect(ngBadges.length).toBe(14); // all 14 endpoints fail
    });
  });

  it("shows OK badge when an API call succeeds", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
    } as Response);

    await act(async () => { render(<DeployCheckPage />); });

    await waitFor(() => {
      const okBadges = screen.getAllByText("OK");
      expect(okBadges.length).toBe(14);
    });
  });

  it("renders re-test button", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("no server"));
    await act(async () => { render(<DeployCheckPage />); });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /再テスト/ })).toBeInTheDocument();
    });
  });

  it("displays endpoint count summary", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("no server"));
    await act(async () => { render(<DeployCheckPage />); });

    await waitFor(() => {
      expect(screen.getByText(/全14件/)).toBeInTheDocument();
    });
  });
});
