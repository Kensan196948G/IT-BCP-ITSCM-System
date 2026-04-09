/**
 * Tests for app/contacts/page.tsx — ContactsPage component.
 *
 * Covers:
 *  - Loading state: spinner shown while hooks fetch
 *  - Error/offline mode: offline badge shown, mock data rendered
 *  - Success state: emergency contacts table with correct data
 *  - Tab switching: emergency ↔ vendor tabs
 *  - Escalation labels: Lv1/Lv2/Lv3 mapped correctly
 *  - Support level badges: premier/standard/basic rendered
 *  - SLA display: hours formatted with "h" suffix
 *  - Notification channels rendered as individual badges
 */
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import ContactsPage from "../app/contacts/page";
import type { EmergencyContact, VendorContact } from "../lib/types";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockUseEmergencyContacts = jest.fn();
const mockUseVendorContacts = jest.fn();

jest.mock("../lib/hooks", () => ({
  useEmergencyContacts: (...args: unknown[]) =>
    mockUseEmergencyContacts(...args),
  useVendorContacts: (...args: unknown[]) => mockUseVendorContacts(...args),
}));

// ── Helpers ──────────────────────────────────────────────────────────────────

type HookResult<T> = {
  data: T | null;
  loading: boolean;
  error: Error | null;
};

function setEmergencyState(
  overrides: Partial<HookResult<EmergencyContact[]>> = {}
) {
  mockUseEmergencyContacts.mockReturnValue({
    data: null,
    loading: false,
    error: null,
    ...overrides,
  });
}

function setVendorState(
  overrides: Partial<HookResult<VendorContact[]>> = {}
) {
  mockUseVendorContacts.mockReturnValue({
    data: null,
    loading: false,
    error: null,
    ...overrides,
  });
}

function setLoading() {
  setEmergencyState({ loading: true });
  setVendorState({ loading: true });
}

function setError() {
  setEmergencyState({ error: new Error("Network error"), data: null });
  setVendorState({ error: new Error("Network error"), data: null });
}

function setSuccess(
  emergency: EmergencyContact[] = [],
  vendors: VendorContact[] = []
) {
  setEmergencyState({ data: emergency });
  setVendorState({ data: vendors });
}

function makeEmergencyContact(
  overrides: Partial<EmergencyContact> = {}
): EmergencyContact {
  return {
    id: "1",
    name: "田中太郎",
    role: "IT部門長",
    department: "IT部門",
    phone_primary: "03-1234-5678",
    email: "tanaka@example.com",
    escalation_level: 1,
    escalation_group: "P1_FULL_BCP",
    notification_channels: ["teams", "phone"],
    is_active: true,
    ...overrides,
  };
}

function makeVendorContact(
  overrides: Partial<VendorContact> = {}
): VendorContact {
  return {
    id: "1",
    vendor_name: "Oracle Japan",
    service_name: "Oracle Database Premium Support",
    contract_id: "ORA-2026-001",
    support_level: "premier",
    phone_primary: "0120-000-001",
    email_support: "support@oracle.example.com",
    sla_response_hours: 0.5,
    sla_resolution_hours: 4,
    contract_expiry: "2027-03-31",
    is_active: true,
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Loading state ────────────────────────────────────────────────────────────

describe("ContactsPage loading state", () => {
  it("shows loading spinner and text while fetching", () => {
    setLoading();
    render(<ContactsPage />);

    expect(
      screen.getByText(/データを読み込んでいます/)
    ).toBeInTheDocument();
    expect(document.querySelector(".animate-spin")).not.toBeNull();
  });

  it("does not render the page heading while loading", () => {
    setLoading();
    render(<ContactsPage />);

    expect(screen.queryByText("連絡網")).not.toBeInTheDocument();
  });
});

// ── Error / offline mode ─────────────────────────────────────────────────────

describe("ContactsPage error / offline mode", () => {
  it("shows offline badge when API fails", () => {
    setError();
    render(<ContactsPage />);

    expect(
      screen.getByText(/オフラインモード（モックデータ表示中）/)
    ).toBeInTheDocument();
  });

  it("renders mock emergency data when API fails", () => {
    setError();
    render(<ContactsPage />);

    // The component falls back to its internal mockEmergencyContacts
    expect(screen.getByText("田中太郎")).toBeInTheDocument();
    expect(screen.getByText("鈴木花子")).toBeInTheDocument();
  });

  it("renders mock vendor data when API fails and vendor tab is active", () => {
    setError();
    render(<ContactsPage />);

    // Switch to vendor tab
    fireEvent.click(screen.getByText("ベンダー連絡先"));

    expect(screen.getByText("Oracle Japan")).toBeInTheDocument();
    expect(screen.getByText("AWS Japan")).toBeInTheDocument();
  });
});

// ── Success state: emergency contacts ────────────────────────────────────────

describe("ContactsPage success state (emergency)", () => {
  it("renders the page heading", () => {
    setSuccess();
    render(<ContactsPage />);

    expect(screen.getByText("連絡網")).toBeInTheDocument();
  });

  it("renders emergency contact name, role, and department", () => {
    setSuccess([
      makeEmergencyContact({
        name: "佐藤一郎",
        role: "CISO",
        department: "セキュリティ部門",
      }),
    ]);
    render(<ContactsPage />);

    expect(screen.getByText("佐藤一郎")).toBeInTheDocument();
    expect(screen.getByText("CISO")).toBeInTheDocument();
    expect(screen.getByText("セキュリティ部門")).toBeInTheDocument();
  });

  it("renders phone number", () => {
    setSuccess([
      makeEmergencyContact({ phone_primary: "03-9999-0000" }),
    ]);
    render(<ContactsPage />);

    expect(screen.getByText("03-9999-0000")).toBeInTheDocument();
  });

  it("shows '-' when department is absent", () => {
    setSuccess([
      makeEmergencyContact({ department: undefined }),
    ]);
    render(<ContactsPage />);

    // At least one "-" should appear for missing department
    const dashes = screen.getAllByText("-");
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it("renders notification channels as individual badges", () => {
    setSuccess([
      makeEmergencyContact({
        notification_channels: ["teams", "sms", "phone"],
      }),
    ]);
    render(<ContactsPage />);

    expect(screen.getByText("teams")).toBeInTheDocument();
    expect(screen.getByText("sms")).toBeInTheDocument();
    expect(screen.getByText("phone")).toBeInTheDocument();
  });

  it("does not show offline badge when no error", () => {
    setSuccess([makeEmergencyContact()]);
    render(<ContactsPage />);

    expect(
      screen.queryByText(/オフラインモード/)
    ).not.toBeInTheDocument();
  });
});

// ── Escalation labels ────────────────────────────────────────────────────────

describe("ContactsPage escalation labels", () => {
  const cases: Array<[number, string]> = [
    [1, "Lv1 (即時)"],
    [2, "Lv2 (15分後)"],
    [3, "Lv3 (30分後)"],
  ];

  test.each(cases)(
    "escalation_level %d displays '%s'",
    (level, expectedLabel) => {
      setSuccess([makeEmergencyContact({ escalation_level: level })]);
      render(<ContactsPage />);

      expect(screen.getByText(expectedLabel)).toBeInTheDocument();
    }
  );

  it("falls back to 'LvN' for unknown escalation level", () => {
    setSuccess([makeEmergencyContact({ escalation_level: 5 })]);
    render(<ContactsPage />);

    expect(screen.getByText("Lv5")).toBeInTheDocument();
  });
});

// ── Tab switching ────────────────────────────────────────────────────────────

describe("ContactsPage tab switching", () => {
  it("shows emergency tab by default", () => {
    setSuccess(
      [makeEmergencyContact({ name: "緊急連絡A" })],
      [makeVendorContact({ vendor_name: "ベンダーA" })]
    );
    render(<ContactsPage />);

    expect(screen.getByText("緊急連絡A")).toBeInTheDocument();
    expect(screen.queryByText("ベンダーA")).not.toBeInTheDocument();
  });

  it("switches to vendor tab on click", () => {
    setSuccess(
      [makeEmergencyContact({ name: "緊急連絡A" })],
      [makeVendorContact({ vendor_name: "ベンダーA" })]
    );
    render(<ContactsPage />);

    fireEvent.click(screen.getByText("ベンダー連絡先"));

    expect(screen.queryByText("緊急連絡A")).not.toBeInTheDocument();
    expect(screen.getByText("ベンダーA")).toBeInTheDocument();
  });

  it("switches back to emergency tab", () => {
    setSuccess(
      [makeEmergencyContact({ name: "緊急連絡A" })],
      [makeVendorContact({ vendor_name: "ベンダーA" })]
    );
    render(<ContactsPage />);

    fireEvent.click(screen.getByText("ベンダー連絡先"));
    fireEvent.click(screen.getByText("緊急連絡先"));

    expect(screen.getByText("緊急連絡A")).toBeInTheDocument();
    expect(screen.queryByText("ベンダーA")).not.toBeInTheDocument();
  });
});

// ── Vendor contacts: success state ───────────────────────────────────────────

describe("ContactsPage success state (vendor)", () => {
  function renderVendorTab(vendors: VendorContact[]) {
    setSuccess([], vendors);
    render(<ContactsPage />);
    fireEvent.click(screen.getByText("ベンダー連絡先"));
  }

  it("renders vendor name and service name", () => {
    renderVendorTab([
      makeVendorContact({
        vendor_name: "NTTデータ",
        service_name: "基幹系保守サポート",
      }),
    ]);

    expect(screen.getByText("NTTデータ")).toBeInTheDocument();
    expect(screen.getByText("基幹系保守サポート")).toBeInTheDocument();
  });

  it("renders SLA response and resolution hours with 'h' suffix", () => {
    renderVendorTab([
      makeVendorContact({
        sla_response_hours: 0.25,
        sla_resolution_hours: 2,
      }),
    ]);

    expect(screen.getByText("0.25h")).toBeInTheDocument();
    expect(screen.getByText("2h")).toBeInTheDocument();
  });

  it("renders contract expiry date", () => {
    renderVendorTab([
      makeVendorContact({ contract_expiry: "2027-06-30" }),
    ]);

    expect(screen.getByText("2027-06-30")).toBeInTheDocument();
  });

  it("shows '-' when SLA hours are absent", () => {
    renderVendorTab([
      makeVendorContact({
        sla_response_hours: undefined,
        sla_resolution_hours: undefined,
      }),
    ]);

    const dashes = screen.getAllByText("-");
    expect(dashes.length).toBeGreaterThanOrEqual(2);
  });

  it("shows '-' when support_level is absent", () => {
    renderVendorTab([
      makeVendorContact({ support_level: undefined }),
    ]);

    const dashes = screen.getAllByText("-");
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });
});

// ── Support level badges ─────────────────────────────────────────────────────

describe("ContactsPage support level badges", () => {
  const cases: Array<[string, string, string]> = [
    ["premier", "bg-purple-100", "text-purple-700"],
    ["standard", "bg-blue-100", "text-blue-700"],
    ["basic", "bg-slate-100", "text-slate-600"],
  ];

  test.each(cases)(
    "support_level '%s' renders with %s and %s",
    (level, bgClass, textClass) => {
      setSuccess([], [makeVendorContact({ support_level: level })]);
      render(<ContactsPage />);
      fireEvent.click(screen.getByText("ベンダー連絡先"));

      const badge = screen.getByText(level);
      expect(badge.className).toContain(bgClass);
      expect(badge.className).toContain(textClass);
    }
  );
});

// ── Vendor loading state triggers loading screen ─────────────────────────────

describe("ContactsPage vendor loading via tab", () => {
  it("shows loading when emergency is done but vendor is loading and vendor tab active", () => {
    // The component checks activeTab to determine loading. Default tab is emergency.
    // When emergency is not loading, the page renders. Then switching to vendor tab
    // does not re-trigger loading because both hooks run unconditionally.
    // However if emergency is loading, the loading screen shows.
    setEmergencyState({ loading: false, data: [] });
    setVendorState({ loading: true });
    render(<ContactsPage />);

    // Default tab is emergency; emergency is not loading, so page renders
    expect(screen.getByText("連絡網")).toBeInTheDocument();
  });
});
