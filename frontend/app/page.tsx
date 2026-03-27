"use client";

import { useDashboard } from "../lib/hooks";
import type { DashboardReadiness } from "../lib/types";

const mockDashboard: DashboardReadiness = {
  readiness_score: 78,
  total_systems: 24,
  rto_achievement_rate: 87,
  rpo_achievement_rate: 92,
  active_incidents: 0,
  recent_exercises: [
    { id: "EX-2026-001", title: "基幹系フェイルオーバー訓練", date: "2026-03-15", result: "成功" },
    { id: "EX-2026-002", title: "DR切替訓練", date: "2026-03-01", result: "一部課題あり" },
  ],
  active_incident_list: [],
  next_exercise: { title: "全社BCP訓練", date: "2026-04-10", type: "フルスケール" },
};

export default function DashboardPage() {
  const { data, loading, error } = useDashboard();

  // API失敗時はモックデータにフォールバック
  const d = error || !data ? mockDashboard : data;

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
        <h2 className="text-2xl font-bold text-slate-800">ダッシュボード</h2>
        {error && (
          <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-700">
            オフラインモード（モックデータ表示中）
          </span>
        )}
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* Readiness Score */}
        <div className="col-span-1 flex flex-col items-center rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:col-span-2 lg:col-span-1">
          <span className="text-sm font-medium text-slate-500">BCPレディネススコア</span>
          <div className="relative my-4 flex h-32 w-32 items-center justify-center rounded-full border-8 border-blue-500">
            <span className="text-4xl font-extrabold text-blue-700">{d.readiness_score}</span>
          </div>
          <span className="text-xs text-slate-400">/ 100</span>
        </div>

        {/* RTO Card */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <span className="text-sm font-medium text-slate-500">RTO達成率</span>
          <p className="mt-2 text-3xl font-bold text-green-600">{d.rto_achievement_rate}%</p>
          <p className="mt-1 text-xs text-slate-400">対象: {d.total_systems}システム</p>
        </div>

        {/* RPO Card */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <span className="text-sm font-medium text-slate-500">RPO達成率</span>
          <p className="mt-2 text-3xl font-bold text-green-600">{d.rpo_achievement_rate}%</p>
          <p className="mt-1 text-xs text-slate-400">対象: {d.total_systems}システム</p>
        </div>

        {/* Next Exercise */}
        {d.next_exercise && (
          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <span className="text-sm font-medium text-slate-500">次回訓練予定</span>
            <p className="mt-2 text-lg font-semibold text-slate-800">{d.next_exercise.title}</p>
            <p className="mt-1 text-sm text-slate-500">{d.next_exercise.date}</p>
            <span className="mt-2 inline-block rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
              {d.next_exercise.type}
            </span>
          </div>
        )}
      </div>

      {/* Recent Exercises */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-slate-700">最近の訓練結果</h3>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-slate-500">
              <th className="pb-2 font-medium">ID</th>
              <th className="pb-2 font-medium">タイトル</th>
              <th className="pb-2 font-medium">実施日</th>
              <th className="pb-2 font-medium">結果</th>
            </tr>
          </thead>
          <tbody>
            {d.recent_exercises.map((ex) => (
              <tr key={ex.id} className="border-b border-slate-50">
                <td className="py-2 font-mono text-xs">{ex.id}</td>
                <td className="py-2">{ex.title}</td>
                <td className="py-2">{ex.date}</td>
                <td className="py-2">
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-medium ${
                      ex.result === "成功"
                        ? "bg-green-100 text-green-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}
                  >
                    {ex.result}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Active Incidents */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-slate-700">アクティブインシデント</h3>
        {d.active_incident_list.length === 0 ? (
          <p className="text-sm text-slate-400">インシデントなし</p>
        ) : (
          <ul>
            {d.active_incident_list.map((inc) => (
              <li key={inc.id}>{inc.title}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
