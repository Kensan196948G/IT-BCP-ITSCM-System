"use client";

import { useEffect, useState, useCallback } from "react";

// ---- Types ----

interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: string | null;
  user_role: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  status: string;
}

// ---- Mock data ----

const MOCK_LOGS: AuditLogEntry[] = [
  {
    id: "a1",
    timestamp: new Date().toISOString(),
    user_id: "admin1",
    user_role: "admin",
    action: "login",
    resource_type: "auth",
    resource_id: null,
    details: { method: "password" },
    ip_address: "192.168.1.10",
    user_agent: null,
    status: "success",
  },
  {
    id: "a2",
    timestamp: new Date(Date.now() - 60000).toISOString(),
    user_id: "operator1",
    user_role: "operator",
    action: "create",
    resource_type: "incident",
    resource_id: "BCP-2026-001",
    details: { title: "DC power failure" },
    ip_address: "192.168.1.20",
    user_agent: null,
    status: "success",
  },
  {
    id: "a3",
    timestamp: new Date(Date.now() - 120000).toISOString(),
    user_id: "viewer1",
    user_role: "viewer",
    action: "read",
    resource_type: "system",
    resource_id: "Core Banking",
    details: null,
    ip_address: "192.168.1.30",
    user_agent: null,
    status: "success",
  },
  {
    id: "a4",
    timestamp: new Date(Date.now() - 180000).toISOString(),
    user_id: "operator1",
    user_role: "operator",
    action: "update",
    resource_type: "incident",
    resource_id: "BCP-2026-001",
    details: { field: "status", value: "recovering" },
    ip_address: "192.168.1.20",
    user_agent: null,
    status: "success",
  },
  {
    id: "a5",
    timestamp: new Date(Date.now() - 240000).toISOString(),
    user_id: "unknown",
    user_role: null,
    action: "login",
    resource_type: "auth",
    resource_id: null,
    details: { reason: "invalid credentials" },
    ip_address: "10.0.0.50",
    user_agent: null,
    status: "failure",
  },
  {
    id: "a6",
    timestamp: new Date(Date.now() - 300000).toISOString(),
    user_id: "viewer1",
    user_role: "viewer",
    action: "delete",
    resource_type: "system",
    resource_id: "Legacy DB",
    details: null,
    ip_address: "192.168.1.30",
    user_agent: null,
    status: "denied",
  },
  {
    id: "a7",
    timestamp: new Date(Date.now() - 360000).toISOString(),
    user_id: "admin1",
    user_role: "admin",
    action: "escalation",
    resource_type: "incident",
    resource_id: "BCP-2026-001",
    details: { level: 3, target: "CISO" },
    ip_address: "192.168.1.10",
    user_agent: null,
    status: "success",
  },
  {
    id: "a8",
    timestamp: new Date(Date.now() - 420000).toISOString(),
    user_id: "auditor1",
    user_role: "auditor",
    action: "export",
    resource_type: "report",
    resource_id: "RPT-004",
    details: { format: "json" },
    ip_address: "192.168.1.40",
    user_agent: null,
    status: "success",
  },
];

const ACTION_OPTIONS = [
  "all",
  "create",
  "read",
  "update",
  "delete",
  "login",
  "logout",
  "escalation",
  "export",
];

// ---- Helpers ----

function statusBadge(status: string) {
  const map: Record<string, string> = {
    success: "bg-green-100 text-green-700",
    failure: "bg-red-100 text-red-700",
    denied: "bg-orange-100 text-orange-700",
  };
  const cls = map[status] ?? "bg-gray-100 text-gray-700";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${cls}`}>
      {status}
    </span>
  );
}

function formatTimestamp(iso: string) {
  try {
    return new Date(iso).toLocaleString("ja-JP", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}

// ---- Component ----

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [actionFilter, setActionFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (actionFilter !== "all") params.set("action", actionFilter);
      const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const resp = await fetch(`${base}/api/audit/logs?${params.toString()}`);
      if (!resp.ok) throw new Error("API error");
      const data: AuditLogEntry[] = await resp.json();
      setLogs(data.length > 0 ? data : MOCK_LOGS);
    } catch {
      // fallback to mock
      const filtered =
        actionFilter === "all"
          ? MOCK_LOGS
          : MOCK_LOGS.filter((l) => l.action === actionFilter);
      setLogs(filtered);
    } finally {
      setLoading(false);
    }
  }, [actionFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleExport = async () => {
    try {
      const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const resp = await fetch(`${base}/api/audit/logs/export`);
      if (!resp.ok) throw new Error("Export failed");
      const data = await resp.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // fallback: export mock
      const blob = new Blob([JSON.stringify({ logs: MOCK_LOGS }, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit-logs-mock-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-800">
          監査ログ
        </h2>
        <button
          onClick={handleExport}
          className="rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 transition-colors"
        >
          エクスポート (JSON)
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium text-slate-600">
          アクション:
        </label>
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
        >
          {ACTION_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt === "all" ? "全て" : opt}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="py-12 text-center text-slate-400">読み込み中...</div>
      ) : logs.length === 0 ? (
        <div className="py-12 text-center text-slate-400">
          監査ログはありません
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                <th className="px-4 py-3">日時</th>
                <th className="px-4 py-3">ユーザー</th>
                <th className="px-4 py-3">ロール</th>
                <th className="px-4 py-3">アクション</th>
                <th className="px-4 py-3">リソース</th>
                <th className="px-4 py-3">リソースID</th>
                <th className="px-4 py-3">ステータス</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                  <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                    {formatTimestamp(log.timestamp)}
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-800">
                    {log.user_id ?? "-"}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {log.user_role ?? "-"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {log.resource_type}
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {log.resource_id ?? "-"}
                  </td>
                  <td className="px-4 py-3">{statusBadge(log.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
