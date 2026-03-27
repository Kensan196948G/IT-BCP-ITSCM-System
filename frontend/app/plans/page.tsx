"use client";

import { useSystems } from "../../lib/hooks";
import type { ITSystemBCP } from "../../lib/types";

const mockPlans: ITSystemBCP[] = [
  { id: "1", system_name: "基幹業務システム", system_type: "オンプレミス", criticality: "tier1", rto_target_hours: 1, rpo_target_hours: 0.25, last_dr_test: "2026-03-15" },
  { id: "2", system_name: "メールシステム", system_type: "SaaS", criticality: "tier1", rto_target_hours: 0.5, rpo_target_hours: 0, last_dr_test: "2026-03-10" },
  { id: "3", system_name: "顧客管理CRM", system_type: "クラウド", criticality: "tier2", rto_target_hours: 4, rpo_target_hours: 1, last_dr_test: "2026-02-20" },
  { id: "4", system_name: "経費精算システム", system_type: "SaaS", criticality: "tier3", rto_target_hours: 24, rpo_target_hours: 4, last_dr_test: "2026-01-15" },
  { id: "5", system_name: "社内Wiki", system_type: "クラウド", criticality: "tier3", rto_target_hours: 48, rpo_target_hours: 24, last_dr_test: "2025-12-01" },
  { id: "6", system_name: "会議室予約", system_type: "SaaS", criticality: "tier4", rto_target_hours: 72, rpo_target_hours: 48, last_dr_test: "2025-11-20" },
  { id: "7", system_name: "人事給与システム", system_type: "オンプレミス", criticality: "tier2", rto_target_hours: 4, rpo_target_hours: 0.5, last_dr_test: "2026-03-05" },
  { id: "8", system_name: "ファイルサーバ", system_type: "オンプレミス", criticality: "tier2", rto_target_hours: 2, rpo_target_hours: 0.25, last_dr_test: "2026-02-28" },
];

const tierBadge: Record<string, string> = {
  tier1: "bg-red-100 text-red-700",
  tier2: "bg-orange-100 text-orange-700",
  tier3: "bg-yellow-100 text-yellow-700",
  tier4: "bg-slate-100 text-slate-500",
};

const tierLabel: Record<string, string> = {
  tier1: "Tier 1",
  tier2: "Tier 2",
  tier3: "Tier 3",
  tier4: "Tier 4",
};

function formatHours(hours: number): string {
  if (hours < 1) return `${Math.round(hours * 60)}分`;
  if (hours >= 24) return `${Math.round(hours)}時間`;
  return `${hours}時間`;
}

export default function PlansPage() {
  const { data, loading, error } = useSystems();

  // API失敗時はモックデータにフォールバック
  const plans = error || !data ? mockPlans : data;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          <p className="text-sm text-slate-500">データを読み込んでいます...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-800">BCP計画管理</h2>
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
              <th className="px-4 py-3 font-medium">システム名</th>
              <th className="px-4 py-3 font-medium">種別</th>
              <th className="px-4 py-3 font-medium">重要度</th>
              <th className="px-4 py-3 font-medium">RTO目標</th>
              <th className="px-4 py-3 font-medium">RPO目標</th>
              <th className="px-4 py-3 font-medium">最終テスト日</th>
            </tr>
          </thead>
          <tbody>
            {plans.map((plan) => (
              <tr key={plan.id} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-800">{plan.system_name}</td>
                <td className="px-4 py-3 text-slate-600">{plan.system_type}</td>
                <td className="px-4 py-3">
                  <span className={`rounded px-2 py-0.5 text-xs font-semibold ${tierBadge[plan.criticality] || "bg-slate-100 text-slate-500"}`}>
                    {tierLabel[plan.criticality] || plan.criticality}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{formatHours(plan.rto_target_hours)}</td>
                <td className="px-4 py-3 text-slate-600">{formatHours(plan.rpo_target_hours)}</td>
                <td className="px-4 py-3 text-slate-600">{plan.last_dr_test || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
