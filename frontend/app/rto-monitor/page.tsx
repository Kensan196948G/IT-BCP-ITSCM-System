const mockRtoSystems = [
  { name: "基幹業務システム", rtoTarget: 60, elapsed: 0, status: "not_started" },
  { name: "メールシステム", rtoTarget: 30, elapsed: 25, status: "on_track" },
  { name: "顧客管理CRM", rtoTarget: 240, elapsed: 180, status: "at_risk" },
  { name: "人事給与システム", rtoTarget: 240, elapsed: 120, status: "on_track" },
  { name: "ファイルサーバ", rtoTarget: 120, elapsed: 150, status: "overdue" },
  { name: "社内Wiki", rtoTarget: 2880, elapsed: 2880, status: "recovered" },
];

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

export default function RtoMonitorPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">RTOモニタリング</h2>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {mockRtoSystems.map((sys) => {
          const cfg = statusConfig[sys.status];
          const pct = sys.rtoTarget > 0 ? Math.min((sys.elapsed / sys.rtoTarget) * 100, 100) : 0;

          return (
            <div
              key={sys.name}
              className={`rounded-lg border p-5 shadow-sm ${cfg.bg}`}
            >
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-semibold text-slate-800">{sys.name}</h3>
                <span className={`rounded px-2 py-0.5 text-xs font-semibold ${cfg.color}`}>
                  {cfg.label}
                </span>
              </div>

              <div className="mb-2 flex justify-between text-xs text-slate-500">
                <span>経過: {formatMinutes(sys.elapsed)}</span>
                <span>目標: {formatMinutes(sys.rtoTarget)}</span>
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
        })}
      </div>
    </div>
  );
}
