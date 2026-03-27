const mockIncidents = [
  {
    id: "INC-2026-042",
    title: "基幹DBレプリケーション遅延",
    severity: "P2",
    startedAt: "2026-03-27T06:30:00Z",
    status: "対応中",
    assignee: "インフラチーム",
  },
  {
    id: "INC-2026-041",
    title: "社外向けWebサーバ応答遅延",
    severity: "P3",
    startedAt: "2026-03-26T14:00:00Z",
    status: "監視中",
    assignee: "Webチーム",
  },
  {
    id: "INC-2026-039",
    title: "東日本DCネットワーク断",
    severity: "P1",
    startedAt: "2026-03-25T22:15:00Z",
    status: "対応中",
    assignee: "NWチーム",
  },
];

const severityBadge: Record<string, string> = {
  P1: "bg-red-100 text-red-700",
  P2: "bg-orange-100 text-orange-700",
  P3: "bg-yellow-100 text-yellow-700",
};

function elapsedTime(startedAt: string): string {
  const diffMs = new Date("2026-03-27T10:00:00Z").getTime() - new Date(startedAt).getTime();
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    const remHours = hours % 24;
    return `${days}日${remHours}時間`;
  }
  return `${hours}時間${minutes}分`;
}

export default function IncidentsPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">インシデント管理</h2>

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
              <th className="px-4 py-3 font-medium">ID</th>
              <th className="px-4 py-3 font-medium">タイトル</th>
              <th className="px-4 py-3 font-medium">重要度</th>
              <th className="px-4 py-3 font-medium">経過時間</th>
              <th className="px-4 py-3 font-medium">ステータス</th>
              <th className="px-4 py-3 font-medium">担当</th>
            </tr>
          </thead>
          <tbody>
            {mockIncidents.map((inc) => (
              <tr key={inc.id} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-xs text-slate-600">{inc.id}</td>
                <td className="px-4 py-3 font-medium text-slate-800">{inc.title}</td>
                <td className="px-4 py-3">
                  <span className={`rounded px-2 py-0.5 text-xs font-semibold ${severityBadge[inc.severity]}`}>
                    {inc.severity}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{elapsedTime(inc.startedAt)}</td>
                <td className="px-4 py-3 text-slate-600">{inc.status}</td>
                <td className="px-4 py-3 text-slate-600">{inc.assignee}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
