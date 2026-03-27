"use client";

import { useExercises } from "../../lib/hooks";
import type { BCPExercise } from "../../lib/types";

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

export default function ExercisesPage() {
  const { data, loading, error } = useExercises();

  // API失敗時はモックデータにフォールバック
  const exerciseList = error || !data ? mockExercises : data;

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
                <td className="px-4 py-3 text-slate-600">
                  {ex.overall_result ? (resultLabel[ex.overall_result] || ex.overall_result) : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
