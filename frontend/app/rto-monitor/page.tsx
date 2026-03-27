"use client";

import { useRTOOverview } from "../../lib/hooks";
import type { RTOMonitorSystem, RTOOverview } from "../../lib/types";

const mockRtoData: RTOOverview = {
  systems: [
    { name: "基幹業務システム", rto_target_minutes: 60, elapsed_minutes: 0, status: "not_started" },
    { name: "メールシステム", rto_target_minutes: 30, elapsed_minutes: 25, status: "on_track" },
    { name: "顧客管理CRM", rto_target_minutes: 240, elapsed_minutes: 180, status: "at_risk" },
    { name: "人事給与システム", rto_target_minutes: 240, elapsed_minutes: 120, status: "on_track" },
    { name: "ファイルサーバ", rto_target_minutes: 120, elapsed_minutes: 150, status: "overdue" },
    { name: "社内Wiki", rto_target_minutes: 2880, elapsed_minutes: 2880, status: "recovered" },
  ],
};

const statusConfig: Record<string, { label: string; color: string; bg: string; bar: string }> = {
  on_track: { label: "順調", color: "text-green-700", bg: "bg-green-50 border-green-200", bar: "bg-green-500" },
  at_risk: { label: "リスクあり", color: "text-yellow-700", bg: "bg-yellow-50 border-yellow-200", bar: "bg-yellow-500" },
  overdue: { label: "超過", color: "text-red-700", bg: "bg-red-50 border-red-200", bar: "bg-red-500" },
  recovered: { label: "復旧済", color: "text-blue-700", bg: "bg-blue-50 border-blue-200", bar: "bg-blue-500" },
  not_started: { label: "未開始", color: "text-slate-500", bg: "bg-slate-50 border-slate-200", bar: "bg-slate-400" },
};

function formatMinutes(min: number): string {
  if (min >= 1440) return `${Math.floor(min / 1440)}日${Math.floor((min % 1440) / 60)}時間`;
  if (min >= 60) return `${Math.floor(min / 60)}時間${min % 60}分`;
  return `${min}分`;
}

function RTOCard({ sys }: { sys: RTOMonitorSystem }) {
  const cfg = statusConfig[sys.status] || statusConfig.not_started;
  const pct = sys.rto_target_minutes > 0 ? Math.min((sys.elapsed_minutes / sys.rto_target_minutes) * 100, 100) : 0;

  return (
    <div className={`rounded-lg border p-5 shadow-sm ${cfg.bg}`}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-slate-800">{sys.name}</h3>
        <span className={`rounded px-2 py-0.5 text-xs font-semibold ${cfg.color}`}>
          {cfg.label}
        </span>
      </div>

      <div className="mb-2 flex justify-between text-xs text-slate-500">
        <span>経過: {formatMinutes(sys.elapsed_minutes)}</span>
        <span>目標: {formatMinutes(sys.rto_target_minutes)}</span>
      </div>

      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className={`h-full rounded-full transition-all ${cfg.bar}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <p className="mt-2 text-right text-xs text-slate-400">
        {Math.round(pct)}% 消化
      </p>
    </div>
  );
}

export default function RtoMonitorPage() {
  const { data, loading, error } = useRTOOverview();

  // API失敗時はモックデータにフォールバック
  const rtoData = error || !data ? mockRtoData : data;

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
        <h2 className="text-2xl font-bold text-slate-800">RTOモニタリング</h2>
        {error && (
          <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-700">
            オフラインモード（モックデータ表示中）
          </span>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {rtoData.systems.map((sys) => (
          <RTOCard key={sys.name} sys={sys} />
        ))}
      </div>
    </div>
  );
}
