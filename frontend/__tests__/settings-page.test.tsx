/**
 * Tests for app/settings/page.tsx — SettingsPage placeholder.
 */
import { render, screen } from "@testing-library/react";
import React from "react";
import SettingsPage from "../app/settings/page";

describe("SettingsPage", () => {
  it("renders page heading", () => {
    render(<SettingsPage />);
    expect(screen.getByText("設定")).toBeInTheDocument();
  });

  it("shows placeholder message", () => {
    render(<SettingsPage />);
    expect(screen.getByText(/設定ページは今後実装予定/)).toBeInTheDocument();
  });
});
