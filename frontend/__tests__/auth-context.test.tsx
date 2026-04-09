/**
 * Tests for AuthProvider context and useAuth hook.
 */
import { render, screen, act, waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import React from "react";
import { AuthProvider, useAuth, type User } from "../lib/auth-context";

const TEST_USER: User = {
  user_id: "u1",
  role: "admin",
  permissions: ["read", "write"],
};

const TOKEN = "test-token-abc";

// Wrapper to supply AuthProvider in renderHook
function wrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

beforeEach(() => {
  localStorage.clear();
});

// ─── Initial state ─────────────────────────────────────────────────────────────

describe("AuthProvider initial state", () => {
  it("starts unauthenticated with no user", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.currentUser).toBeNull());
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("restores session from localStorage on mount", async () => {
    localStorage.setItem("bcp_access_token", TOKEN);
    localStorage.setItem("bcp_current_user", JSON.stringify(TEST_USER));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() =>
      expect(result.current.currentUser).toEqual(TEST_USER)
    );
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("stays unauthenticated when only token is stored (no user)", async () => {
    localStorage.setItem("bcp_access_token", TOKEN);
    // bcp_current_user intentionally absent

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.currentUser).toBeNull());
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("stays unauthenticated when only user is stored (no token)", async () => {
    localStorage.setItem("bcp_current_user", JSON.stringify(TEST_USER));
    // bcp_access_token intentionally absent

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.currentUser).toBeNull());
    expect(result.current.isAuthenticated).toBe(false);
  });
});

// ─── login() ──────────────────────────────────────────────────────────────────

describe("login()", () => {
  it("sets currentUser and isAuthenticated=true", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(false));

    act(() => {
      result.current.login(TOKEN, TEST_USER);
    });

    expect(result.current.currentUser).toEqual(TEST_USER);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("persists token and user to localStorage", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(false));

    act(() => {
      result.current.login(TOKEN, TEST_USER);
    });

    expect(localStorage.getItem("bcp_access_token")).toBe(TOKEN);
    expect(JSON.parse(localStorage.getItem("bcp_current_user")!)).toEqual(
      TEST_USER
    );
  });
});

// ─── logout() ─────────────────────────────────────────────────────────────────

describe("logout()", () => {
  it("clears currentUser and sets isAuthenticated=false", async () => {
    localStorage.setItem("bcp_access_token", TOKEN);
    localStorage.setItem("bcp_current_user", JSON.stringify(TEST_USER));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => {
      result.current.logout();
    });

    expect(result.current.currentUser).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("removes token and user from localStorage", async () => {
    localStorage.setItem("bcp_access_token", TOKEN);
    localStorage.setItem("bcp_current_user", JSON.stringify(TEST_USER));

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    act(() => {
      result.current.logout();
    });

    expect(localStorage.getItem("bcp_access_token")).toBeNull();
    expect(localStorage.getItem("bcp_current_user")).toBeNull();
  });
});

// ─── useAuth outside provider ─────────────────────────────────────────────────

describe("useAuth outside AuthProvider", () => {
  it("returns default context values", () => {
    // renderHook without wrapper — uses the default context value
    const { result } = renderHook(() => useAuth());

    expect(result.current.currentUser).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(typeof result.current.login).toBe("function");
    expect(typeof result.current.logout).toBe("function");
  });
});

// ─── AuthProvider renders children ────────────────────────────────────────────

describe("AuthProvider rendering", () => {
  it("renders children after loading", async () => {
    render(
      <AuthProvider>
        <span data-testid="child">hello</span>
      </AuthProvider>
    );

    await waitFor(() =>
      expect(screen.getByTestId("child")).toBeInTheDocument()
    );
  });
});
