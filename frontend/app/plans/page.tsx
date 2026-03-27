const mockPlans = [
  { name: "基幹業務システム", type: "オンプレミス", tier: "tier1", rto: "1時間", rpo: "15分", lastTest: "2026-03-15" },
  { name: "メールシステム", type: "SaaS", tier: "tier1", rto: "30分", rpo: "0分", lastTest: "2026-03-10" },
  { name: "顧客管理CRM", type: "クラウド", tier: "tier2", rto: "4時間", rpo: "1時間", lastTest: "2026-02-20" },
  { name: "経費精算システム", type: "SaaS", tier: "tier3", rto: "24時間", rpo: "4時間", lastTest: "2026-01-15" },
  { name: "社内Wiki", type: "クラウド", tier: "tier3", rto: "48時間", rpo: "24時間", lastTest: "2025-12-01" },
  { name: "会議室予約", type: "SaaS", tier: "tier4", rto: "72時間", rpo: "48時間", lastTest: "2025-11-20" },
  { name: "人事給与システム", type: "オンプレミス", tier: "tier2", rto: "4時間", rpo: "30分", lastTest: "2026-03-05" },
  { name: "ファイルサーバ", type: "オンプレミス", tier: "tier2", rto: "2時間", rpo: "15分", lastTest: "2026-02-28" },
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

export default function PlansPage() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">BCP計画管理</h2>

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
            {mockPlans.map((plan) => (
              <tr key={plan.name} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-800">{plan.name}</td>
                <td className="px-4 py-3 text-slate-600">{plan.type}</td>
                <td className="px-4 py-3">
                  <span className={`rounded px-2 py-0.5 text-xs font-semibold ${tierBadge[plan.tier]}`}>
                    {tierLabel[plan.tier]}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{plan.rto}</td>
                <td className="px-4 py-3 text-slate-600">{plan.rpo}</td>
                <td className="px-4 py-3 text-slate-600">{plan.lastTest}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
