"use client";

import { useBIAAssessments, useBIASummary, useBIARiskMatrix } from "../../lib/hooks";
import type { BIAAssessment, BIASummary, RiskMatrixData } from "../../lib/types";

// ---- Mock data for fallback ----

const mockAssessments: BIAAssessment[] = [
  {
    id: "1",
    assessment_id: "BIA-2026-001",
    system_name: "Core Banking System",
    assessment_date: "2026-03-15",
    assessor: "Risk Manager",
    business_processes: ["決済処理", "口座管理"],
    financial_impact_per_hour: 500,
    financial_impact_per_day: 12000,
    max_tolerable_downtime_hours: 24,
    reputation_impact: "high",
    operational_impact: "critical",
    recommended_rto_hours: 4,
    recommended_rpo_hours: 1,
    risk_score: 82,
    status: "approved",
  },
  {
    id: "2",
    assessment_id: "BIA-2026-002",
    system_name: "Email System",
    assessment_date: "2026-03-16",
    assessor: "IT Manager",
    business_processes: ["社内連絡", "外部連絡"],
    financial_impact_per_hour: 50,
    financial_impact_per_day: 1200,
    max_tolerable_downtime_hours: 72,
    reputation_impact: "medium",
    operational_impact: "medium",
    recommended_rto_hours: 8,
    recommended_rpo_hours: 4,
    risk_score: 45,
    status: "reviewed",
  },
  {
    id: "3",
    assessment_id: "BIA-2026-003",
    system_name: "HR Portal",
    assessment_date: "2026-03-17",
    assessor: "HR Director",
    business_processes: ["勤怠管理", "給与計算"],
    financial_impact_per_hour: 20,
    financial_impact_per_day: 480,
    max_tolerable_downtime_hours: 168,
    reputation_impact: "low",
    operational_impact: "low",
    recommended_rto_hours: 24,
    recommended_rpo_hours: 12,
    risk_score: 18,
    status: "draft",
  },
  {
    id: "4",
    assessment_id: "BIA-2026-004",
    system_name: "Trading Platform",
    assessment_date: "2026-03-18",
    assessor: "Risk Manager",
    business_processes: ["株式取引", "為替取引"],
    financial_impact_per_hour: 2000,
    financial_impact_per_day: 48000,
    max_tolerable_downtime_hours: 4,
    reputation_impact: "critical",
    operational_impact: "critical",
    recommended_rto_hours: 0.5,
    recommended_rpo_hours: 0,
    risk_score: 95,
    status: "approved",
  },
  {
    id: "5",
    assessment_id: "BIA-2026-005",
    system_name: "File Server",
    assessment_date: "2026-03-19",
    assessor: "IT Manager",
    business_processes: ["ファイル共有"],
    financial_impact_per_hour: 30,
    financial_impact_per_day: 720,
    max_tolerable_downtime_hours: 48,
    reputation_impact: "low",
    operational_impact: "medium",
    recommended_rto_hours: 12,
    recommended_rpo_hours: 4,
    risk_score: 32,
    status: "reviewed",
  },
];

const mockSummary: BIASummary = {
  total_assessments: 5,
  average_risk_score: 54.4,
  max_risk_score: 95,
  highest_risk_system: "Trading Platform",
  impact_distribution: { none: 0, low: 2, medium: 1, high: 1, critical: 1 },
  average_financial_impact_per_day: 12480,
  status_distribution: { draft: 1, reviewed: 2, approved: 2 },
};

const mockRiskMatrix: RiskMatrixData = {
  entries: mockAssessments
    .filter((a) => a.risk_score != null)
    .map((a) => ({
      impact_level: Math.ceil((a.risk_score ?? 1) / 20),
      likelihood_level: Math.ceil((a.risk_score ?? 1) / 25),
      system_name: a.system_name,
      risk_score: a.risk_score ?? 0,
    })),
  matrix: [
    [0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1],
    [0, 0, 0, 0, 1],
  ],
};

// ---- Helpers ----

function riskColor(score: number | undefined): string {
  if (score == null) return "bg-slate-200";
  if (score <= 25) return "bg-green-500";
  if (score <= 50) return "bg-yellow-400";
  if (score <= 75) return "bg-orange-500";
  return "bg-red-500";
}

function riskTextColor(score: number | undefined): string {
  if (score == null) return "text-slate-500";
  if (score <= 25) return "text-green-700";
  if (score <= 50) return "text-yellow-700";
  if (score <= 75) return "text-orange-700";
  return "text-red-700";
}

function riskBgLight(score: number | undefined): string {
  if (score == null) return "bg-slate-50";
  if (score <= 25) return "bg-green-50";
  if (score <= 50) return "bg-yellow-50";
  if (score <= 75) return "bg-orange-50";
  return "bg-red-50";
}

const statusLabel: Record<string, string> = {
  draft: "下書き",
  reviewed: "レビュー済",
  approved: "承認済",
};

const statusBadge: Record<string, string> = {
  draft: "bg-slate-100 text-slate-700",
  reviewed: "bg-blue-100 text-blue-700",
  approved: "bg-green-100 text-green-700",
};

const matrixCellColor = (count: number): string => {
  if (count === 0) return "bg-slate-100 text-slate-400";
  if (count === 1) return "bg-yellow-200 text-yellow-800";
  if (count <= 3) return "bg-orange-300 text-orange-900";
  return "bg-red-400 text-white";
};

// ---- Component ----

export default function BIAPage() {
  const { data: assessments, loading: loadA, error: errA } = useBIAAssessments();
  const { data: summary, error: errS } = useBIASummary();
  const { data: matrix, error: errM } = useBIARiskMatrix();

  const list = errA || !assessments ? mockAssessments : assessments;
  const sum = errS || !summary ? mockSummary : summary;
  const mat = errM || !matrix ? mockRiskMatrix : matrix;

  if (loadA) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          <p className="text-sm text-slate-500">BIAデータを読み込んでいます...</p>
        </div>
      </div>
    );
  }

  const impactLabels = ["", "Very Low", "Low", "Medium", "High", "Critical"];
  const likelihoodLabels = ["", "Rare", "Unlikely", "Possible", "Likely", "Almost Certain"];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-800">BIA分析 (ビジネスインパクト分析)</h2>
        <p className="mt-1 text-sm text-slate-500">
          各ITシステムの業務影響度を評価し、復旧優先度を決定します
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total risk score */}
        <div className={`rounded-lg border p-4 ${riskBgLight(sum.max_risk_score ?? undefined)}`}>
          <p className="text-xs font-medium text-slate-500">最高リスクスコア</p>
          <p className={`mt-1 text-3xl font-bold ${riskTextColor(sum.max_risk_score ?? undefined)}`}>
            {sum.max_risk_score ?? "-"}
            <span className="text-sm font-normal text-slate-400"> / 100</span>
          </p>
          <p className="mt-1 text-xs text-slate-500">{sum.highest_risk_system ?? "-"}</p>
        </div>

        {/* Average risk */}
        <div className="rounded-lg border bg-white p-4">
          <p className="text-xs font-medium text-slate-500">平均リスクスコア</p>
          <p className={`mt-1 text-3xl font-bold ${riskTextColor(sum.average_risk_score ? Math.round(sum.average_risk_score) : undefined)}`}>
            {sum.average_risk_score != null ? sum.average_risk_score.toFixed(1) : "-"}
          </p>
          <p className="mt-1 text-xs text-slate-500">全 {sum.total_assessments} システム</p>
        </div>

        {/* Financial impact */}
        <div className="rounded-lg border bg-white p-4">
          <p className="text-xs font-medium text-slate-500">平均財務影響 (日次)</p>
          <p className="mt-1 text-3xl font-bold text-slate-800">
            {sum.average_financial_impact_per_day != null
              ? `${sum.average_financial_impact_per_day.toLocaleString()}万`
              : "-"}
          </p>
          <p className="mt-1 text-xs text-slate-500">円/日</p>
        </div>

        {/* Status dist */}
        <div className="rounded-lg border bg-white p-4">
          <p className="text-xs font-medium text-slate-500">ステータス</p>
          <div className="mt-2 flex gap-2">
            {Object.entries(sum.status_distribution).map(([key, val]) => (
              <span key={key} className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusBadge[key] || "bg-slate-100 text-slate-700"}`}>
                {statusLabel[key] || key}: {val}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Risk Matrix */}
      <div className="rounded-lg border bg-white p-6">
        <h3 className="mb-4 text-lg font-semibold text-slate-700">リスクマトリクス</h3>
        <div className="overflow-x-auto">
          <table className="mx-auto border-collapse">
            <thead>
              <tr>
                <th className="w-24 p-1 text-xs text-slate-500"></th>
                {[1, 2, 3, 4, 5].map((l) => (
                  <th key={l} className="p-1 text-center text-xs text-slate-500 font-normal">
                    {likelihoodLabels[l]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[5, 4, 3, 2, 1].map((impact) => (
                <tr key={impact}>
                  <td className="p-1 text-right text-xs text-slate-500 font-normal pr-2">
                    {impactLabels[impact]}
                  </td>
                  {[1, 2, 3, 4, 5].map((likelihood) => {
                    const count = mat.matrix[impact - 1]?.[likelihood - 1] ?? 0;
                    return (
                      <td key={likelihood} className="p-1">
                        <div
                          className={`flex h-12 w-16 items-center justify-center rounded text-sm font-semibold ${matrixCellColor(count)}`}
                        >
                          {count > 0 ? count : ""}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-2 flex justify-center gap-4 text-xs text-slate-500">
            <span>Y: Impact</span>
            <span>X: Likelihood</span>
          </div>
        </div>
      </div>

      {/* Assessment Table */}
      <div className="rounded-lg border bg-white">
        <div className="border-b px-6 py-4">
          <h3 className="text-lg font-semibold text-slate-700">アセスメント一覧</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-6 py-3">システム名</th>
                <th className="px-6 py-3">リスクスコア</th>
                <th className="px-6 py-3">財務影響 (日)</th>
                <th className="px-6 py-3">推奨RTO</th>
                <th className="px-6 py-3">MTPD</th>
                <th className="px-6 py-3">ステータス</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {list.map((a) => (
                <tr key={a.id} className="hover:bg-slate-50">
                  <td className="px-6 py-3 font-medium text-slate-800">
                    {a.system_name}
                    <div className="text-xs text-slate-400">{a.assessment_id}</div>
                  </td>
                  <td className="px-6 py-3">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-bold ${riskTextColor(a.risk_score)}`}>
                        {a.risk_score ?? "-"}
                      </span>
                      <div className="h-2 w-20 overflow-hidden rounded-full bg-slate-200">
                        <div
                          className={`h-full rounded-full ${riskColor(a.risk_score)}`}
                          style={{ width: `${a.risk_score ?? 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-3 text-slate-700">
                    {a.financial_impact_per_day != null
                      ? `${a.financial_impact_per_day.toLocaleString()} 万円`
                      : "-"}
                  </td>
                  <td className="px-6 py-3 text-slate-700">
                    {a.recommended_rto_hours != null ? `${a.recommended_rto_hours}h` : "-"}
                  </td>
                  <td className="px-6 py-3 text-slate-700">
                    {a.max_tolerable_downtime_hours != null
                      ? `${a.max_tolerable_downtime_hours}h`
                      : "-"}
                  </td>
                  <td className="px-6 py-3">
                    <span
                      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        statusBadge[a.status] || "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {statusLabel[a.status] || a.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
