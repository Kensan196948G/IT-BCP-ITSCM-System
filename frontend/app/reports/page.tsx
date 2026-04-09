"use client";

import { useState, useEffect } from "react";
import { dashboard } from "../../lib/api";
import type {
  ReadinessReport,
  RTOComplianceReport,
  ExerciseTrendReport,
  ISO20000Report,
} from "../../lib/types";

// ---- Tab definitions ----

const tabs = [
  { id: "readiness", label: "BCPレディネス" },
  { id: "compliance", label: "RTO/RPOコンプライアンス" },
  { id: "trends", label: "訓練トレンド" },
  { id: "iso20000", label: "ISO20000準拠" },
] as const;

type TabId = (typeof tabs)[number]["id"];

// ---- Helper components ----

function ScoreBadge({ score, label }: { score: number; label: string }) {
  const color =
    score >= 80
      ? "text-green-700 bg-green-50 border-green-200"
      : score >= 60
        ? "text-yellow-700 bg-yellow-50 border-yellow-200"
        : "text-red-700 bg-red-50 border-red-200";
  return (
    <div className={`rounded-xl border p-6 text-center ${color}`}>
      <p className="text-4xl font-bold">{score}%</p>
      <p className="mt-1 text-sm">{label}</p>
    </div>
  );
}

// ---- Tab content ----

function ReadinessTab({ data }: { data: ReadinessReport }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <ScoreBadge score={data.overall_score} label="総合レディネススコア" />
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
          <p className="text-4xl font-bold text-slate-800">{data.tested_systems}/{data.total_systems}</p>
          <p className="mt-1 text-sm text-slate-500">テスト済みシステム</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
          <p className="text-4xl font-bold text-slate-800">{data.rto_met_systems}</p>
          <p className="mt-1 text-sm text-slate-500">RTO目標達成</p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-3">
          <h3 className="font-semibold text-slate-800">システム別準備状況</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">システム名</th>
                <th className="px-4 py-3">RTO目標</th>
                <th className="px-4 py-3">直近テスト実績</th>
                <th className="px-4 py-3">達成</th>
                <th className="px-4 py-3">テスト済</th>
                <th className="px-4 py-3">代替手段</th>
                <th className="px-4 py-3">スコア</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.system_readiness.map((s) => (
                <tr key={s.system_name} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium">{s.system_name}</td>
                  <td className="px-4 py-3">{s.rto_target_hours}h</td>
                  <td className="px-4 py-3">{s.last_test_rto_hours != null ? `${s.last_test_rto_hours}h` : "-"}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded px-2 py-0.5 text-xs font-semibold ${s.rto_achieved ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                      {s.rto_achieved ? "達成" : "未達"}
                    </span>
                  </td>
                  <td className="px-4 py-3">{s.tested ? "済" : "未"}</td>
                  <td className="px-4 py-3">{s.has_fallback ? "あり" : "なし"}</td>
                  <td className="px-4 py-3 font-semibold">{s.readiness_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {data.recommendations.length > 0 && (
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <h3 className="mb-2 font-semibold text-yellow-800">改善推奨事項</h3>
          <ul className="list-inside list-disc space-y-1 text-sm text-yellow-700">
            {data.recommendations.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ComplianceTab({ data }: { data: RTOComplianceReport }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <ScoreBadge score={data.compliance_rate} label="RTO達成率" />
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
          <p className="text-4xl font-bold text-slate-800">{data.compliant_systems}/{data.total_systems}</p>
          <p className="mt-1 text-sm text-slate-500">準拠システム</p>
        </div>
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-4xl font-bold text-red-700">{data.overdue_systems.length}</p>
          <p className="mt-1 text-sm text-red-600">超過システム</p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-3">
          <h3 className="font-semibold text-slate-800">システム別RTO目標 vs 実績</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">システム名</th>
                <th className="px-4 py-3">RTO目標(h)</th>
                <th className="px-4 py-3">実績(h)</th>
                <th className="px-4 py-3">差異(h)</th>
                <th className="px-4 py-3">準拠</th>
                <th className="px-4 py-3">トレンド</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.system_compliance.map((s) => (
                <tr key={s.system_name} className={`hover:bg-slate-50 ${!s.compliant ? "bg-red-50" : ""}`}>
                  <td className="px-4 py-3 font-medium">{s.system_name}</td>
                  <td className="px-4 py-3">{s.rto_target_hours}</td>
                  <td className="px-4 py-3">{s.rto_actual_hours ?? "-"}</td>
                  <td className="px-4 py-3">{s.deviation_hours != null ? s.deviation_hours : "-"}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded px-2 py-0.5 text-xs font-semibold ${s.compliant ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                      {s.compliant ? "準拠" : "超過"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={s.trend === "improving" ? "text-green-600" : s.trend === "deteriorating" ? "text-red-600" : "text-slate-400"}>
                      {s.trend === "improving" ? "改善" : s.trend === "deteriorating" ? "悪化" : "-"}
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

function TrendsTab({ data }: { data: ExerciseTrendReport }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
          <p className="text-4xl font-bold text-blue-700">{data.total_exercises}</p>
          <p className="mt-1 text-sm text-slate-500">総訓練回数</p>
        </div>
        <ScoreBadge score={data.improvement_completion_rate} label="改善アクション実施率" />
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
          <p className="text-4xl font-bold text-slate-800">{data.completed_improvements}/{data.total_improvements}</p>
          <p className="mt-1 text-sm text-slate-500">改善完了/総数</p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-3">
          <h3 className="font-semibold text-slate-800">年度別訓練実績</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">年度</th>
                <th className="px-4 py-3">実施回数</th>
                <th className="px-4 py-3">完了</th>
                <th className="px-4 py-3">合格</th>
                <th className="px-4 py-3">達成率</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.yearly_trends.map((t) => (
                <tr key={t.year} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium">{t.year}</td>
                  <td className="px-4 py-3">{t.exercise_count}</td>
                  <td className="px-4 py-3">{t.completed}</td>
                  <td className="px-4 py-3">{t.pass_count}</td>
                  <td className="px-4 py-3">
                    <span className={`font-semibold ${t.achievement_rate >= 80 ? "text-green-600" : t.achievement_rate >= 50 ? "text-yellow-600" : "text-red-600"}`}>
                      {t.achievement_rate}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {Object.keys(data.common_issues).length > 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold text-slate-800">頻出課題カテゴリ</h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.common_issues).map(([cat, count]) => (
              <span key={cat} className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-700">
                {cat}: {count}件
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ISO20000Tab({ data }: { data: ISO20000Report }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <ScoreBadge score={data.compliance_rate} label="ISO20000 ITSCM準拠率" />
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
          <p className="text-4xl font-bold text-slate-800">{data.compliant_items}/{data.total_items}</p>
          <p className="mt-1 text-sm text-slate-500">準拠項目</p>
        </div>
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-4xl font-bold text-red-700">{data.non_compliant_items.length}</p>
          <p className="mt-1 text-sm text-red-600">未対応項目</p>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-3">
          <h3 className="font-semibold text-slate-800">ITSCM要件チェックリスト</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">要件</th>
                <th className="px-4 py-3">カテゴリ</th>
                <th className="px-4 py-3">準拠</th>
                <th className="px-4 py-3">根拠</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.checklist_results.map((item) => (
                <tr key={item.id} className={`hover:bg-slate-50 ${!item.compliant ? "bg-red-50" : ""}`}>
                  <td className="px-4 py-3 font-mono text-xs">{item.id}</td>
                  <td className="px-4 py-3">{item.requirement}</td>
                  <td className="px-4 py-3">{item.category}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded px-2 py-0.5 text-xs font-semibold ${item.compliant ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                      {item.compliant ? "準拠" : "未対応"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">{item.evidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {data.next_audit_actions.length > 0 && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <h3 className="mb-2 font-semibold text-red-800">次回監査対応事項</h3>
          <ul className="list-inside list-disc space-y-1 text-sm text-red-700">
            {data.next_audit_actions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ---- Main page ----

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("readiness");
  const [readiness, setReadiness] = useState<ReadinessReport | null>(null);
  const [compliance, setCompliance] = useState<RTOComplianceReport | null>(null);
  const [trends, setTrends] = useState<ExerciseTrendReport | null>(null);
  const [iso, setIso] = useState<ISO20000Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setFetchError(null);

    const fetchers: Record<TabId, () => Promise<void>> = {
      readiness: async () => {
        try {
          const data = await dashboard.reports.readiness();
          setReadiness(data);
        } catch {
          setReadiness(null);
          setFetchError("BCPレディネスレポートを取得できませんでした");
        }
      },
      compliance: async () => {
        try {
          const data = await dashboard.reports.rtoCompliance();
          setCompliance(data);
        } catch {
          setCompliance(null);
          setFetchError("RTO/RPOコンプライアンスレポートを取得できませんでした");
        }
      },
      trends: async () => {
        try {
          const data = await dashboard.reports.exerciseTrends();
          setTrends(data);
        } catch {
          setTrends(null);
          setFetchError("訓練トレンドレポートを取得できませんでした");
        }
      },
      iso20000: async () => {
        try {
          const data = await dashboard.reports.iso20000();
          setIso(data);
        } catch {
          setIso(null);
          setFetchError("ISO20000準拠レポートを取得できませんでした");
        }
      },
    };

    fetchers[activeTab]().finally(() => setLoading(false));
  }, [activeTab]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-800">レポート</h2>
        {fetchError && (
          <span className="rounded bg-red-100 px-2 py-1 text-xs text-red-700">
            {fetchError}
          </span>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg bg-slate-100 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-800"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
            <p className="text-sm text-slate-500">レポートを生成しています...</p>
          </div>
        </div>
      ) : fetchError && (
        (activeTab === "readiness" && !readiness) ||
        (activeTab === "compliance" && !compliance) ||
        (activeTab === "trends" && !trends) ||
        (activeTab === "iso20000" && !iso)
      ) ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-8 text-center">
          <p className="text-sm font-medium text-red-700">{fetchError}</p>
          <p className="mt-1 text-xs text-red-500">ネットワーク接続を確認し、再度お試しください。</p>
        </div>
      ) : (
        <>
          {activeTab === "readiness" && readiness && <ReadinessTab data={readiness} />}
          {activeTab === "compliance" && compliance && <ComplianceTab data={compliance} />}
          {activeTab === "trends" && trends && <TrendsTab data={trends} />}
          {activeTab === "iso20000" && iso && <ISO20000Tab data={iso} />}
        </>
      )}
    </div>
  );
}
