"use client";

import { useState } from "react";
import { useEmergencyContacts, useVendorContacts } from "../../lib/hooks";
import type { EmergencyContact, VendorContact } from "../../lib/types";

const mockEmergencyContacts: EmergencyContact[] = [
  {
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
  },
  {
    id: "2",
    name: "鈴木花子",
    role: "インフラ担当",
    department: "IT部門",
    phone_primary: "03-2345-6789",
    email: "suzuki@example.com",
    escalation_level: 1,
    escalation_group: "P1_FULL_BCP",
    notification_channels: ["teams", "sms", "phone"],
    is_active: true,
  },
  {
    id: "3",
    name: "佐藤一郎",
    role: "CISO",
    department: "セキュリティ部門",
    phone_primary: "03-3456-7890",
    email: "sato@example.com",
    escalation_level: 2,
    escalation_group: "P1_FULL_BCP",
    notification_channels: ["email", "phone"],
    is_active: true,
  },
  {
    id: "4",
    name: "山田次郎",
    role: "CTO",
    department: "経営企画",
    phone_primary: "03-4567-8901",
    email: "yamada@example.com",
    escalation_level: 3,
    escalation_group: "P1_FULL_BCP",
    notification_channels: ["phone"],
    is_active: true,
  },
];

const mockVendorContacts: VendorContact[] = [
  {
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
  },
  {
    id: "2",
    vendor_name: "AWS Japan",
    service_name: "AWS Enterprise Support",
    contract_id: "AWS-2026-001",
    support_level: "premier",
    phone_primary: "0120-000-002",
    email_support: "enterprise@aws.example.com",
    sla_response_hours: 0.25,
    sla_resolution_hours: 2,
    contract_expiry: "2027-06-30",
    is_active: true,
  },
  {
    id: "3",
    vendor_name: "NTTデータ",
    service_name: "基幹系保守サポート",
    contract_id: "NTT-2026-001",
    support_level: "standard",
    phone_primary: "0120-000-003",
    email_support: "support@nttdata.example.com",
    sla_response_hours: 2,
    sla_resolution_hours: 8,
    contract_expiry: "2026-12-31",
    is_active: true,
  },
];

const escalationLabel: Record<number, string> = {
  1: "Lv1 (即時)",
  2: "Lv2 (15分後)",
  3: "Lv3 (30分後)",
};

const supportBadge: Record<string, string> = {
  premier: "bg-purple-100 text-purple-700",
  standard: "bg-blue-100 text-blue-700",
  basic: "bg-slate-100 text-slate-600",
};

export default function ContactsPage() {
  const [activeTab, setActiveTab] = useState<"emergency" | "vendor">(
    "emergency"
  );

  const {
    data: emergencyData,
    loading: emergencyLoading,
    error: emergencyError,
  } = useEmergencyContacts();
  const {
    data: vendorData,
    loading: vendorLoading,
    error: vendorError,
  } = useVendorContacts();

  const emergencyList =
    emergencyError || !emergencyData
      ? mockEmergencyContacts
      : emergencyData;
  const vendorList =
    vendorError || !vendorData ? mockVendorContacts : vendorData;

  const loading =
    activeTab === "emergency" ? emergencyLoading : vendorLoading;
  const hasError =
    activeTab === "emergency" ? emergencyError : vendorError;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          <p className="text-sm text-slate-500">
            データを読み込んでいます...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-800">連絡網</h2>
        {hasError && (
          <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-700">
            オフラインモード（モックデータ表示中）
          </span>
        )}
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 rounded-lg border border-slate-200 bg-slate-100 p-1">
        <button
          onClick={() => setActiveTab("emergency")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "emergency"
              ? "bg-white text-slate-800 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          緊急連絡先
        </button>
        <button
          onClick={() => setActiveTab("vendor")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "vendor"
              ? "bg-white text-slate-800 shadow-sm"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          ベンダー連絡先
        </button>
      </div>

      {/* Emergency contacts table */}
      {activeTab === "emergency" && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
                <th className="px-4 py-3 font-medium">名前</th>
                <th className="px-4 py-3 font-medium">役割</th>
                <th className="px-4 py-3 font-medium">部門</th>
                <th className="px-4 py-3 font-medium">電話</th>
                <th className="px-4 py-3 font-medium">
                  エスカレーション
                </th>
                <th className="px-4 py-3 font-medium">通知チャネル</th>
              </tr>
            </thead>
            <tbody>
              {emergencyList.map((contact) => (
                <tr
                  key={contact.id}
                  className="border-b border-slate-50 hover:bg-slate-50"
                >
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {contact.name}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {contact.role}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {contact.department || "-"}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-600">
                    {contact.phone_primary || "-"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">
                      {escalationLabel[contact.escalation_level] ||
                        `Lv${contact.escalation_level}`}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {(contact.notification_channels || []).map((ch) => (
                        <span
                          key={ch}
                          className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600"
                        >
                          {ch}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Vendor contacts table */}
      {activeTab === "vendor" && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
                <th className="px-4 py-3 font-medium">ベンダー名</th>
                <th className="px-4 py-3 font-medium">サービス</th>
                <th className="px-4 py-3 font-medium">サポートレベル</th>
                <th className="px-4 py-3 font-medium">SLA応答</th>
                <th className="px-4 py-3 font-medium">SLA解決</th>
                <th className="px-4 py-3 font-medium">契約期限</th>
              </tr>
            </thead>
            <tbody>
              {vendorList.map((vendor) => (
                <tr
                  key={vendor.id}
                  className="border-b border-slate-50 hover:bg-slate-50"
                >
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {vendor.vendor_name}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {vendor.service_name}
                  </td>
                  <td className="px-4 py-3">
                    {vendor.support_level ? (
                      <span
                        className={`rounded px-2 py-0.5 text-xs font-semibold ${supportBadge[vendor.support_level] || "bg-slate-100 text-slate-500"}`}
                      >
                        {vendor.support_level}
                      </span>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {vendor.sla_response_hours != null
                      ? `${vendor.sla_response_hours}h`
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {vendor.sla_resolution_hours != null
                      ? `${vendor.sla_resolution_hours}h`
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {vendor.contract_expiry || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
