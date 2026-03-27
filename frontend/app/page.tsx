const mockDashboard = {
  readinessScore: 78,
  totalSystems: 24,
  rtoAchievementRate: 87,
  rpoAchievementRate: 92,
  recentExercises: [
    { id: "EX-2026-001", title: "基幹系フェイルオーバー訓練", date: "2026-03-15", result: "成功" },
    { id: "EX-2026-002", title: "DR切替訓練", date: "2026-03-01", result: "一部課題あり" },
  ],
  activeIncidents: [] as { id: string; title: string; severity: string }[],
  nextExercise: { title: "全社BCP訓練", date: "2026-04-10", type: "フルスケール" },
};

export default function DashboardPage() {
  const d = mockDashboard;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">ダッシュボード</h2>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* Readiness Score */}
        <div className="col-span-1 flex flex-col items-center rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:col-span-2 lg:col-span-1">
          <span className="text-sm font-medium text-slate-500">BCPレディネススコア</span>
          <div className="relative my-4 flex h-32 w-32 items-center justify-center rounded-full border-8 border-blue-500">
            <span className="text-4xl font-extrabold text-blue-700">{d.readinessScore}</span>
          </div>
          <span className="text-xs text-slate-400">/ 100</span>
        </div>

        {/* RTO Card */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <span className="text-sm font-medium text-slate-500">RTO達成率</span>
          <p className="mt-2 text-3xl font-bold text-green-600">{d.rtoAchievementRate}%</p>
          <p className="mt-1 text-xs text-slate-400">対象: {d.totalSystems}システム</p>
        </div>

        {/* RPO Card */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <span className="text-sm font-medium text-slate-500">RPO達成率</span>
          <p className="mt-2 text-3xl font-bold text-green-600">{d.rpoAchievementRate}%</p>
          <p className="mt-1 text-xs text-slate-400">対象: {d.totalSystems}システム</p>
        </div>

        {/* Next Exercise */}
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <span className="text-sm font-medium text-slate-500">次回訓練予定</span>
          <p className="mt-2 text-lg font-semibold text-slate-800">{d.nextExercise.title}</p>
          <p className="mt-1 text-sm text-slate-500">{d.nextExercise.date}</p>
          <span className="mt-2 inline-block rounded bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
            {d.nextExercise.type}
          </span>
        </div>
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
            {d.recentExercises.map((ex) => (
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
        {d.activeIncidents.length === 0 ? (
          <p className="text-sm text-slate-400">インシデントなし</p>
        ) : (
          <ul>
            {d.activeIncidents.map((inc) => (
              <li key={inc.id}>{inc.title}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
