"use client";

import { useState } from "react";
import { useExercises } from "../../lib/hooks";
import { exercises as exercisesApi } from "../../lib/api";
import type { BCPExercise, ExerciseReport, ExerciseRTORecord } from "../../lib/types";

const mockExercises: BCPExercise[] = [
  { id: "1", exercise_id: "EX-2026-001", title: "基幹系フェイルオーバー訓練", exercise_type: "フェイルオーバー", scheduled_date: "2026-03-15", status: "completed", overall_result: "pass" },
  { id: "2", exercise_id: "EX-2026-002", title: "DR切替訓練", exercise_type: "DR切替", scheduled_date: "2026-03-01", status: "completed", overall_result: "partial_pass" },
  { id: "3", exercise_id: "EX-2026-003", title: "全社BCP訓練", exercise_type: "フルスケール", scheduled_date: "2026-04-10", status: "planned" },
  { id: "4", exercise_id: "EX-2026-004", title: "ネットワーク障害対応訓練", exercise_type: "卓上訓練", scheduled_date: "2026-04-25", status: "planned" },
  { id: "5", exercise_id: "EX-2026-005", title: "クラウド移行切替テスト", exercise_type: "フェイルオーバー", scheduled_date: "2026-03-20", status: "in_progress" },
];

const statusBadge: Record<string, string> = {
  planned: "bg-blue-100 text-blue-700",
  in_progress: "bg-orange-100 text-orange-700",
  completed: "bg-green-100 text-green-700",
};

const statusLabel: Record<string, string> = {
  planned: "予定",
  in_progress: "実施中",
  completed: "完了",
};

const resultLabel: Record<string, string> = {
  pass: "成功",
  partial_pass: "一部課題あり",
  fail: "失敗",
};

const resultBadge: Record<string, string> = {
  pass: "bg-green-100 text-green-700",
  partial_pass: "bg-yellow-100 text-yellow-700",
  fail: "bg-red-100 text-red-700",
};

export default function ExercisesPage() {
  const { data, loading, error, refetch } = useExercises();
  const [selectedReport, setSelectedReport] = useState<ExerciseReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // API失敗時はモックデータにフォールバック
  const exerciseList = error || !data ? mockExercises : data;

  const handleStart = async (id: string) => {
    setActionLoading(id);
    try {
      await exercisesApi.start(id);
      refetch();
    } catch {
      // silently handle
    } finally {
      setActionLoading(null);
    }
  };

  const handleComplete = async (id: string) => {
    setActionLoading(id);
    try {
      await exercisesApi.complete(id);
      refetch();
    } catch {
      // silently handle
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewReport = async (id: string) => {
    setReportLoading(true);
    try {
      const report = await exercisesApi.report(id);
      setSelectedReport(report);
    } catch {
      setSelectedReport(null);
    } finally {
      setReportLoading(false);
    }
  };

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
        <h2 className="text-2xl font-bold text-slate-800">訓練管理</h2>
        {error && (
          <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-700">
            オフラインモード（モックデータ表示中）
          </span>
        )}
      </div>

      {/* Exercise List */}
      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
              <th className="px-4 py-3 font-medium">ID</th>
              <th className="px-4 py-3 font-medium">タイトル</th>
              <th className="px-4 py-3 font-medium">種別</th>
              <th className="px-4 py-3 font-medium">予定日</th>
              <th className="px-4 py-3 font-medium">ステータス</th>
              <th className="px-4 py-3 font-medium">結果</th>
              <th className="px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            {exerciseList.map((ex) => (
              <tr key={ex.id} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-xs text-slate-600">{ex.exercise_id}</td>
                <td className="px-4 py-3 font-medium text-slate-800">{ex.title}</td>
                <td className="px-4 py-3 text-slate-600">{ex.exercise_type}</td>
                <td className="px-4 py-3 text-slate-600">{ex.scheduled_date}</td>
                <td className="px-4 py-3">
                  <span className={`rounded px-2 py-0.5 text-xs font-semibold ${statusBadge[ex.status] || "bg-slate-100 text-slate-500"}`}>
                    {statusLabel[ex.status] || ex.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {ex.overall_result ? (
                    <span className={`rounded px-2 py-0.5 text-xs font-semibold ${resultBadge[ex.overall_result] || "bg-slate-100 text-slate-500"}`}>
                      {resultLabel[ex.overall_result] || ex.overall_result}
                    </span>
                  ) : "-"}
                </td>
                <td className="px-4 py-3 space-x-2">
                  {ex.status === "planned" && (
                    <button
                      onClick={() => handleStart(ex.id)}
                      disabled={actionLoading === ex.id}
                      className="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      開始
                    </button>
                  )}
                  {ex.status === "in_progress" && (
                    <button
                      onClick={() => handleComplete(ex.id)}
                      disabled={actionLoading === ex.id}
                      className="rounded bg-green-600 px-3 py-1 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      完了
                    </button>
                  )}
                  {ex.status === "completed" && (
                    <button
                      onClick={() => handleViewReport(ex.id)}
                      className="rounded bg-slate-600 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700"
                    >
                      レポート
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Report Panel */}
      {reportLoading && (
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
            <span className="text-sm text-slate-500">レポートを読み込んでいます...</span>
          </div>
        </div>
      )}

      {selectedReport && !reportLoading && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-800">訓練レポート: {selectedReport.exercise.title}</h3>
            <button onClick={() => setSelectedReport(null)} className="text-sm text-slate-500 hover:text-slate-700">閉じる</button>
          </div>

          {/* RTO Achievement Summary */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
              <p className="text-2xl font-bold text-blue-600">{selectedReport.total_systems_tested}</p>
              <p className="text-xs text-slate-500">テスト対象システム</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
              <p className="text-2xl font-bold text-green-600">{selectedReport.systems_achieved}</p>
              <p className="text-xs text-slate-500">RTO達成</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
              <p className="text-2xl font-bold text-red-600">{selectedReport.systems_failed}</p>
              <p className="text-xs text-slate-500">RTO未達</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
              <p className="text-2xl font-bold text-slate-800">
                {selectedReport.rto_achievement_rate != null ? `${selectedReport.rto_achievement_rate.toFixed(1)}%` : "-"}
              </p>
              <p className="text-xs text-slate-500">RTO達成率</p>
            </div>
          </div>

          {/* RTO Achievement Chart-style display */}
          {selectedReport.rto_records.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h4 className="mb-3 text-sm font-semibold text-slate-700">RTO記録</h4>
              <div className="space-y-3">
                {selectedReport.rto_records.map((rec) => {
                  const target = rec.rto_target_hours;
                  const actual = rec.rto_actual_hours ?? 0;
                  const pct = Math.min((actual / target) * 100, 150);
                  const barColor = rec.achieved ? "bg-green-500" : "bg-red-500";
                  return (
                    <div key={rec.id}>
                      <div className="mb-1 flex items-center justify-between text-xs">
                        <span className="font-medium text-slate-700">{rec.system_name}</span>
                        <span className="text-slate-500">
                          {rec.rto_actual_hours != null ? `${rec.rto_actual_hours}h` : "-"} / {target}h
                        </span>
                      </div>
                      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
                        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${Math.min(pct, 100)}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Findings & Recommendations */}
          {selectedReport.findings.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h4 className="mb-2 text-sm font-semibold text-slate-700">所見</h4>
              <ul className="list-inside list-disc space-y-1 text-sm text-slate-600">
                {selectedReport.findings.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}

          {selectedReport.recommendations.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <h4 className="mb-2 text-sm font-semibold text-slate-700">改善提案</h4>
              <ul className="list-inside list-disc space-y-1 text-sm text-slate-600">
                {selectedReport.recommendations.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
