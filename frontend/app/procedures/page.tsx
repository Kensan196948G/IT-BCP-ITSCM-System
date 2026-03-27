"use client";

import { useProcedures } from "../../lib/hooks";
import type { RecoveryProcedure } from "../../lib/types";

const mockProcedures: RecoveryProcedure[] = [
  {
    id: "1",
    procedure_id: "RP-2026-001",
    system_name: "基幹システム",
    scenario_type: "dc_failure",
    title: "DC障害時の基幹システム復旧手順",
    version: "2.1",
    priority_order: 1,
    procedure_steps: [
      { step: 1, description: "状況確認", duration_minutes: 10 },
      { step: 2, description: "フェイルオーバー実行", duration_minutes: 30 },
    ],
    estimated_time_hours: 2.0,
    responsible_team: "インフラチーム",
    last_reviewed: "2026-02-15",
    review_cycle_months: 6,
    status: "active",
  },
  {
    id: "2",
    procedure_id: "RP-2026-002",
    system_name: "メールシステム",
    scenario_type: "ransomware",
    title: "ランサムウェア感染時のメール復旧",
    version: "1.0",
    priority_order: 2,
    procedure_steps: [
      { step: 1, description: "ネットワーク隔離", duration_minutes: 5 },
    ],
    estimated_time_hours: 4.0,
    responsible_team: "セキュリティチーム",
    last_reviewed: "2026-01-10",
    review_cycle_months: 12,
    status: "active",
  },
  {
    id: "3",
    procedure_id: "RP-2026-003",
    system_name: "会計システム",
    scenario_type: "earthquake",
    title: "地震発生時の会計システム復旧",
    version: "0.9",
    priority_order: 3,
    procedure_steps: [],
    estimated_time_hours: 6.0,
    responsible_team: "業務チーム",
    review_cycle_months: 12,
    status: "draft",
  },
  {
    id: "4",
    procedure_id: "RP-2025-010",
    system_name: "旧CRMシステム",
    scenario_type: "dc_failure",
    title: "旧CRM復旧手順（廃止予定）",
    version: "3.0",
    priority_order: 10,
    procedure_steps: [],
    responsible_team: "業務チーム",
    last_reviewed: "2025-06-01",
    review_cycle_months: 12,
    status: "archived",
  },
];

const statusBadge: Record<string, string> = {
  active: "bg-green-100 text-green-700",
  draft: "bg-yellow-100 text-yellow-700",
  archived: "bg-slate-100 text-slate-500",
};

const statusLabel: Record<string, string> = {
  active: "有効",
  draft: "下書き",
  archived: "アーカイブ",
};

const scenarioLabel: Record<string, string> = {
  earthquake: "地震",
  ransomware: "ランサムウェア",
  dc_failure: "DC障害",
  cloud_outage: "クラウド障害",
  pandemic: "パンデミック",
  supplier_failure: "サプライヤ障害",
  local_failure: "局所障害",
};

export default function ProceduresPage() {
  const { data, loading, error } = useProcedures();

  const procedureList = error || !data ? mockProcedures : data;

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
        <h2 className="text-2xl font-bold text-slate-800">復旧手順書</h2>
        {error && (
          <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-700">
            オフラインモード（モックデータ表示中）
          </span>
        )}
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
              <th className="px-4 py-3 font-medium">対象システム</th>
              <th className="px-4 py-3 font-medium">シナリオ</th>
              <th className="px-4 py-3 font-medium">タイトル</th>
              <th className="px-4 py-3 font-medium text-center">
                優先順位
              </th>
              <th className="px-4 py-3 font-medium">バージョン</th>
              <th className="px-4 py-3 font-medium">最終レビュー</th>
              <th className="px-4 py-3 font-medium">ステータス</th>
            </tr>
          </thead>
          <tbody>
            {procedureList.map((proc) => (
              <tr
                key={proc.id}
                className="border-b border-slate-50 hover:bg-slate-50"
              >
                <td className="px-4 py-3 font-medium text-slate-800">
                  {proc.system_name}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {scenarioLabel[proc.scenario_type] || proc.scenario_type}
                </td>
                <td className="px-4 py-3 text-slate-800">{proc.title}</td>
                <td className="px-4 py-3 text-center font-mono text-slate-600">
                  {proc.priority_order}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-slate-600">
                  v{proc.version}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {proc.last_reviewed || "-"}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-semibold ${statusBadge[proc.status] || "bg-slate-100 text-slate-500"}`}
                  >
                    {statusLabel[proc.status] || proc.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
