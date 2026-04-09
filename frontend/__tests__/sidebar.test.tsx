/**
 * Tests for app/components/Sidebar.tsx and app/components/AppShell.tsx.
 *
 * Sidebar covers:
 *  - Rendering: nav items, header title
 *  - Unauthenticated: no user info, no logout button
 *  - Authenticated: user_id + role label displayed, logout button visible
 *  - Role labels: admin/operator/viewer/auditor mapped to Japanese labels
 *  - Active link: current pathname gets highlighted style
 *  - Mobile hamburger: toggle open/close, overlay click closes sidebar
 *  - Logout: calls auth.logout() and navigates to /login
 *
 * AppShell covers:
 *  - Login page path: renders children only (no Sidebar)
 *  - Other paths: renders Sidebar + header + children
 */
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { Sidebar } from "../app/components/Sidebar";
import { AppShell } from "../app/components/AppShell";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockPush = jest.fn();
let mockPathname = "/";

jest.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
  useRouter: () => ({ push: mockPush }),
}));

// next/link renders as <a> in jsdom
jest.mock("next/link", () => {
  const MockLink = ({ href, children, onClick, className }: {
    href: string;
    children: React.ReactNode;
    onClick?: () => void;
    className?: string;
  }) => (
    <a href={href} onClick={onClick} className={className}>
      {children}
    </a>
  );
  MockLink.displayName = "MockLink";
  return MockLink;
});

const mockLogout = jest.fn();
let mockAuthState = {
  currentUser: null as { user_id: string; role: string; permissions: string[] } | null,
  isAuthenticated: false,
  logout: mockLogout,
  login: jest.fn(),
};

jest.mock("../lib/auth-context", () => ({
  useAuth: () => mockAuthState,
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function setUnauthenticated() {
  mockAuthState = {
    currentUser: null,
    isAuthenticated: false,
    logout: mockLogout,
    login: jest.fn(),
  };
}

function setAuthenticated(role = "operator") {
  mockAuthState = {
    currentUser: { user_id: "testuser", role, permissions: ["read"] },
    isAuthenticated: true,
    logout: mockLogout,
    login: jest.fn(),
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  mockPathname = "/";
  setUnauthenticated();
});

// ── Sidebar rendering ─────────────────────────────────────────────────────────

describe("Sidebar rendering", () => {
  it("renders the header title BCP-ITSCM", () => {
    render(<Sidebar />);
    expect(screen.getByText("BCP-ITSCM")).toBeInTheDocument();
  });

  it("renders all nav items", () => {
    render(<Sidebar />);
    expect(screen.getByText("ダッシュボード")).toBeInTheDocument();
    expect(screen.getByText("BCP計画")).toBeInTheDocument();
    expect(screen.getByText("インシデント")).toBeInTheDocument();
    expect(screen.getByText("設定")).toBeInTheDocument();
  });

  it("renders the mobile hamburger button", () => {
    render(<Sidebar />);
    expect(screen.getByRole("button", { name: /メニュー/i })).toBeInTheDocument();
  });
});

// ── Unauthenticated ───────────────────────────────────────────────────────────

describe("Sidebar unauthenticated state", () => {
  it("does not show user info when not authenticated", () => {
    setUnauthenticated();
    render(<Sidebar />);
    expect(screen.queryByText("testuser")).not.toBeInTheDocument();
  });

  it("does not show logout button when not authenticated", () => {
    setUnauthenticated();
    render(<Sidebar />);
    expect(screen.queryByRole("button", { name: /ログアウト/i })).not.toBeInTheDocument();
  });
});

// ── Authenticated ─────────────────────────────────────────────────────────────

describe("Sidebar authenticated state", () => {
  it("shows user_id when authenticated", () => {
    setAuthenticated("admin");
    render(<Sidebar />);
    expect(screen.getByText("testuser")).toBeInTheDocument();
  });

  it("shows logout button when authenticated", () => {
    setAuthenticated();
    render(<Sidebar />);
    expect(screen.getByRole("button", { name: /ログアウト/i })).toBeInTheDocument();
  });

  it("shows first character of user_id as avatar", () => {
    setAuthenticated();
    render(<Sidebar />);
    // "testuser" → "t" in avatar span
    expect(screen.getByText("t")).toBeInTheDocument();
  });
});

// ── Role labels ───────────────────────────────────────────────────────────────

describe("Sidebar role labels", () => {
  const cases: [string, string][] = [
    ["admin", "管理者"],
    ["operator", "運用担当"],
    ["viewer", "閲覧者"],
    ["auditor", "監査人"],
  ];

  test.each(cases)("role '%s' shows label '%s'", (role, label) => {
    setAuthenticated(role);
    render(<Sidebar />);
    expect(screen.getByText(label)).toBeInTheDocument();
  });
});

// ── Active link ───────────────────────────────────────────────────────────────

describe("Sidebar active link", () => {
  it("applies active style to the current pathname link", () => {
    mockPathname = "/plans";
    render(<Sidebar />);

    const planLink = screen.getByText("BCP計画").closest("a")!;
    expect(planLink.className).toContain("bg-blue-700");
    expect(planLink.className).toContain("font-semibold");
  });

  it("does not apply active style to non-current links", () => {
    mockPathname = "/plans";
    render(<Sidebar />);

    const dashLink = screen.getByText("ダッシュボード").closest("a")!;
    expect(dashLink.className).not.toContain("bg-blue-700");
  });
});

// ── Mobile hamburger ──────────────────────────────────────────────────────────

describe("Sidebar mobile hamburger", () => {
  it("clicking hamburger opens the mobile sidebar (translate-x-0)", () => {
    render(<Sidebar />);

    const nav = screen.getByRole("navigation");
    expect(nav.className).toContain("-translate-x-full");

    fireEvent.click(screen.getByRole("button", { name: /メニュー/i }));

    expect(nav.className).toContain("translate-x-0");
  });

  it("clicking hamburger again closes the sidebar", () => {
    render(<Sidebar />);

    const btn = screen.getByRole("button", { name: /メニュー/i });
    fireEvent.click(btn); // open
    fireEvent.click(btn); // close

    const nav = screen.getByRole("navigation");
    expect(nav.className).toContain("-translate-x-full");
  });

  it("clicking overlay closes the sidebar", () => {
    render(<Sidebar />);

    fireEvent.click(screen.getByRole("button", { name: /メニュー/i })); // open

    // overlay div appears when open
    const overlay = document.querySelector(".fixed.inset-0") as HTMLElement;
    expect(overlay).not.toBeNull();
    fireEvent.click(overlay);

    const nav = screen.getByRole("navigation");
    expect(nav.className).toContain("-translate-x-full");
  });
});

// ── Logout ────────────────────────────────────────────────────────────────────

describe("Sidebar logout", () => {
  it("calls logout() and navigates to /login on logout button click", () => {
    setAuthenticated();
    render(<Sidebar />);

    fireEvent.click(screen.getByRole("button", { name: /ログアウト/i }));

    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(mockPush).toHaveBeenCalledWith("/login");
  });
});

// ── AppShell ──────────────────────────────────────────────────────────────────

describe("AppShell", () => {
  it("renders children without Sidebar on /login page", () => {
    mockPathname = "/login";
    render(
      <AppShell>
        <span data-testid="content">login content</span>
      </AppShell>
    );

    expect(screen.getByTestId("content")).toBeInTheDocument();
    // Sidebar nav should not be rendered
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  });

  it("renders Sidebar and header on non-login pages", () => {
    mockPathname = "/";
    render(
      <AppShell>
        <span data-testid="content">dashboard content</span>
      </AppShell>
    );

    expect(screen.getByTestId("content")).toBeInTheDocument();
    expect(screen.getByRole("navigation")).toBeInTheDocument();
    expect(screen.getByText("IT-BCP-ITSCM-System")).toBeInTheDocument();
    expect(screen.getByText("稼働中")).toBeInTheDocument();
  });

  it("shows status badge '稼働中' in header", () => {
    mockPathname = "/plans";
    render(
      <AppShell>
        <div>plans</div>
      </AppShell>
    );

    expect(screen.getByText("稼働中")).toBeInTheDocument();
  });
});
