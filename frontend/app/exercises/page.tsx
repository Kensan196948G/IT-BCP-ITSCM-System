const mockExercises = [
  { id: "EX-2026-001", title: "基幹系フェイルオーバー訓練", type: "フェイルオーバー", date: "2026-03-15", status: "completed", result: "成功" },
  { id: "EX-2026-002", title: "DR切替訓練", type: "DR切替", date: "2026-03-01", status: "completed", result: "一部課題あり" },
  { id: "EX-2026-003", title: "全社BCP訓練", type: "フルスケール", date: "2026-04-10", status: "planned", result: "-" },
  { id: "EX-2026-004", title: "ネットワーク障害対応訓練", type: "卓上訓練", date: "2026-04-25", status: "planned", result: "-" },
  { id: "EX-2026-005", title: "クラウド移行切替テスト", type: "フェイルオーバー", date: "2026-03-20", status: "in_progress", result: "-" },
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

export default function ExercisesPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">訓練管理</h2>

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
            {mockExercises.map((ex) => (
              <tr key={ex.id} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-xs text-slate-600">{ex.id}</td>
                <td className="px-4 py-3 font-medium text-slate-800">{ex.title}</td>
                <td className="px-4 py-3 text-slate-600">{ex.type}</td>
                <td className="px-4 py-3 text-slate-600">{ex.date}</td>
                <td className="px-4 py-3">
                  <span className={`rounded px-2 py-0.5 text-xs font-semibold ${statusBadge[ex.status]}`}>
                    {statusLabel[ex.status]}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{ex.result}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
