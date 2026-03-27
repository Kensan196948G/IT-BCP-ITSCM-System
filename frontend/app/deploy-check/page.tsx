"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

// ---------------------------------------------------------------------------
// Page link list
// ---------------------------------------------------------------------------

const pages = [
  { href: "/", label: "ダッシュボード" },
  { href: "/plans", label: "BCP計画" },
  { href: "/procedures", label: "復旧手順書" },
  { href: "/contacts", label: "連絡網" },
  { href: "/bia", label: "BIA分析" },
  { href: "/exercises", label: "訓練管理" },
  { href: "/scenarios", label: "シナリオ" },
  { href: "/incidents", label: "インシデント" },
  { href: "/notifications", label: "通知管理" },
  { href: "/rto-monitor", label: "RTOモニタ" },
  { href: "/reports", label: "レポート" },
  { href: "/runbook", label: "運用ランブック" },
  { href: "/system-status", label: "システム状態" },
  { href: "/settings", label: "設定" },
];

// ---------------------------------------------------------------------------
// API endpoints to test
// ---------------------------------------------------------------------------

const apiEndpoints = [
  { path: "/api/health", label: "ヘルスチェック" },
  { path: "/api/dashboard/readiness", label: "準備状況ダッシュボード" },
  { path: "/api/systems/", label: "システム一覧" },
  { path: "/api/exercises/", label: "訓練一覧" },
  { path: "/api/incidents/", label: "インシデント一覧" },
  { path: "/api/contacts/", label: "連絡先一覧" },
  { path: "/api/procedures/", label: "復旧手順一覧" },
  { path: "/api/bia/risk-matrix", label: "BIAリスクマトリクス" },
  { path: "/api/scenarios/", label: "シナリオ一覧" },
  { path: "/api/monitoring/health/live", label: "Liveness Probe" },
  { path: "/api/runbook/deployment-checklist", label: "デプロイチェックリスト" },
  { path: "/api/runbook/rollback-procedure", label: "ロールバック手順" },
  { path: "/api/runbook/dr-failover", label: "DRフェイルオーバー" },
  { path: "/api/runbook/incident-playbook/earthquake", label: "インシデントPB(地震)" },
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface EndpointStatus {
  path: string;
  label: string;
  status: "pending" | "ok" | "error";
  code?: number;
  latencyMs?: number;
}

export default function DeployCheckPage() {
  const [results, setResults] = useState<EndpointStatus[]>(
    apiEndpoints.map((ep) => ({ ...ep, status: "pending" })),
  );
  const [testing, setTesting] = useState(false);

  const runTests = async () => {
    setTesting(true);
    const updated: EndpointStatus[] = [];

    for (const ep of apiEndpoints) {
      const start = performance.now();
      try {
        const res = await fetch(`${API_BASE}${ep.path}`, { signal: AbortSignal.timeout(5000) });
        updated.push({
          ...ep,
          status: res.ok ? "ok" : "error",
          code: res.status,
          latencyMs: Math.round(performance.now() - start),
        });
      } catch {
        updated.push({
          ...ep,
          status: "error",
          latencyMs: Math.round(performance.now() - start),
        });
      }
    }
    setResults(updated);
    setTesting(false);
  };

  useEffect(() => {
    runTests();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const okCount = results.filter((r) => r.status === "ok").length;
  const errCount = results.filter((r) => r.status === "error").length;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-800">デプロイ確認</h2>
        <span className="rounded bg-slate-200 px-3 py-1 text-sm font-mono text-slate-600">
          v0.1.0 | Phase 4
        </span>
      </div>

      {/* Page Links */}
      <section>
        <h3 className="mb-3 text-lg font-semibold text-slate-700">全ページ一覧</h3>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {pages.map((p) => (
            <Link
              key={p.href}
              href={p.href}
              className="rounded-md border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-50"
            >
              {p.label}
            </Link>
          ))}
        </div>
      </section>

      {/* API Tests */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-700">API接続テスト</h3>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-500">
              OK: {okCount} / NG: {errCount} / 全{results.length}件
            </span>
            <button
              onClick={runTests}
              disabled={testing}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
            >
              {testing ? "テスト中..." : "再テスト"}
            </button>
          </div>
        </div>
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr>
                <th className="px-4 py-2 font-medium text-slate-600">エンドポイント</th>
                <th className="px-4 py-2 font-medium text-slate-600">説明</th>
                <th className="px-4 py-2 font-medium text-slate-600">状態</th>
                <th className="px-4 py-2 font-medium text-slate-600">コード</th>
                <th className="px-4 py-2 font-medium text-slate-600">レイテンシ</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.path} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-2 font-mono text-xs text-slate-700">{r.path}</td>
                  <td className="px-4 py-2 text-slate-600">{r.label}</td>
                  <td className="px-4 py-2">
                    {r.status === "pending" && (
                      <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">待機</span>
                    )}
                    {r.status === "ok" && (
                      <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">OK</span>
                    )}
                    {r.status === "error" && (
                      <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">NG</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-xs text-slate-500">{r.code ?? "-"}</td>
                  <td className="px-4 py-2 text-xs text-slate-500">{r.latencyMs != null ? `${r.latencyMs}ms` : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
