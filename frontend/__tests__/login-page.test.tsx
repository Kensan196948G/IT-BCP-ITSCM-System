/**
 * Tests for app/login/page.tsx — LoginPage component.
 *
 * Covers:
 *  - Initial render (form fields, role selector)
 *  - Validation: empty userId shows error
 *  - Successful API login → calls auth.login() and navigates to "/"
 *  - API failure fallback → mock token, still navigates to "/"
 *  - Loading state during submission
 */
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import React from "react";
import LoginPage from "../app/login/page";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

const mockLogin = jest.fn();
jest.mock("../lib/auth-context", () => ({
  useAuth: () => ({ login: mockLogin }),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function mockFetchSuccess(token = "api-token-xyz") {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: jest.fn().mockResolvedValue({ access_token: token }),
  } as unknown as Response);
}

function mockFetchFailure() {
  global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Render ────────────────────────────────────────────────────────────────────

describe("LoginPage rendering", () => {
  it("renders the login form with all required elements", () => {
    render(<LoginPage />);

    expect(screen.getByPlaceholderText(/admin1/i)).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toBeInTheDocument(); // role selector
    expect(screen.getByRole("button", { name: /ログイン/i })).toBeInTheDocument();
    expect(screen.getByText(/IT-BCP-ITSCM-System/i)).toBeInTheDocument();
  });

  it("shows all four role options", () => {
    render(<LoginPage />);

    const select = screen.getByRole("combobox");
    const options = Array.from((select as HTMLSelectElement).options).map(
      (o) => o.value
    );
    expect(options).toEqual(["admin", "operator", "viewer", "auditor"]);
  });

  it("defaults role to operator", () => {
    render(<LoginPage />);

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("operator");
  });
});

// ── Validation ────────────────────────────────────────────────────────────────

describe("LoginPage validation", () => {
  it("shows error when userId is empty on submit", async () => {
    render(<LoginPage />);

    fireEvent.click(screen.getByRole("button", { name: /ログイン/i }));

    await waitFor(() =>
      expect(screen.getByText(/ユーザーIDを入力してください/i)).toBeInTheDocument()
    );
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it("does not submit when userId is only whitespace", async () => {
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText(/admin1/i), {
      target: { value: "   " },
    });
    fireEvent.click(screen.getByRole("button", { name: /ログイン/i }));

    await waitFor(() =>
      expect(screen.getByText(/ユーザーIDを入力してください/i)).toBeInTheDocument()
    );
    expect(mockLogin).not.toHaveBeenCalled();
  });
});

// ── API login ─────────────────────────────────────────────────────────────────

describe("LoginPage API login", () => {
  it("calls login() with API token and navigates to '/' on success", async () => {
    mockFetchSuccess("server-token-abc");
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText(/admin1/i), {
      target: { value: "user1" },
    });
    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "admin" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /ログイン/i }));
    });

    await waitFor(() => expect(mockLogin).toHaveBeenCalledTimes(1));
    const [token, user] = mockLogin.mock.calls[0] as [string, { user_id: string; role: string; permissions: string[] }];
    expect(token).toBe("server-token-abc");
    expect(user.user_id).toBe("user1");
    expect(user.role).toBe("admin");
    expect(user.permissions).toContain("manage_users");

    expect(mockPush).toHaveBeenCalledWith("/");
  });
});

// ── Mock token fallback ───────────────────────────────────────────────────────

describe("LoginPage mock token fallback", () => {
  it("uses mock token when API is unreachable and still navigates to '/'", async () => {
    mockFetchFailure();
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText(/admin1/i), {
      target: { value: "fallbackUser" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /ログイン/i }));
    });

    await waitFor(() => expect(mockLogin).toHaveBeenCalledTimes(1));
    const [token, user] = mockLogin.mock.calls[0] as [string, { user_id: string; role: string }];
    expect(token).toMatch(/^mock_fallbackUser_operator_/);
    expect(user.user_id).toBe("fallbackUser");
    expect(user.role).toBe("operator"); // default role

    expect(mockPush).toHaveBeenCalledWith("/");
  });

  it("uses role-specific permissions in mock token fallback", async () => {
    mockFetchFailure();
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText(/admin1/i), {
      target: { value: "viewer1" },
    });
    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "viewer" },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /ログイン/i }));
    });

    await waitFor(() => expect(mockLogin).toHaveBeenCalledTimes(1));
    const [, user] = mockLogin.mock.calls[0] as [string, { permissions: string[] }];
    expect(user.permissions).toEqual(["read"]);
  });
});

// ── Loading state ─────────────────────────────────────────────────────────────

describe("LoginPage loading state", () => {
  it("disables button and shows loading text while submitting", async () => {
    // Slow API call that won't resolve during the check
    global.fetch = jest.fn().mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({
        ok: true,
        json: () => Promise.resolve({ access_token: "t" }),
      } as unknown as Response), 5000))
    );

    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText(/admin1/i), {
      target: { value: "user1" },
    });

    fireEvent.click(screen.getByRole("button", { name: /ログイン/i }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /認証中/i })).toBeDisabled()
    );
  });
});
