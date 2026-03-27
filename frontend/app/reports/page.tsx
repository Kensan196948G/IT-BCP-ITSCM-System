"use client";

import { useState, useEffect } from "react";
import { dashboard } from "../../lib/api";
import type {
  ReadinessReport,
  RTOComplianceReport,
  ExerciseTrendReport,
  ISO20000Report,
} from "../../lib/types";

// ---- Mock data for fallback ----

const mockReadiness: ReadinessReport = {
  report_id: "RPT-001",
  report_type: "BCP Readiness Report",
  generated_at: new Date().toISOString(),
  overall_score: 72.5,
  total_systems: 6,
  tested_systems: 4,
  rto_met_systems: 3,
  system_readiness: [
    { system_name: "Core Banking", rto_target_hours: 4, rpo_target_hours: 1, last_test_rto_hours: 3.5, rto_achieved: true, tested: true, has_fallback: true, readiness_score: 100 },
    { system_name: "Email System", rto_target_hours: 2, rpo_target_hours: 0.5, last_test_rto_hours: 1.8, rto_achieved: true, tested: true, has_fallback: true, readiness_score: 100 },
    { system_name: "CRM", rto_target_hours: 8, rpo_target_hours: 4, last_test_rto_hours: 10, rto_achieved: false, tested: true, has_fallback: false, readiness_score: 40 },
    { system_name: "HR System", rto_target_hours: 24, rpo_target_hours: 8, last_test_rto_hours: 20, rto_achieved: true, tested: true, has_fallback: false, readiness_score: 80 },
    { system_name: "File Server", rto_target_hours: 2, rpo_target_hours: 1, rto_achieved: false, tested: false, has_fallback: true, readiness_score: 20 },
    { system_name: "Wiki", rto_target_hours: 48, rpo_target_hours: 24, rto_achieved: false, tested: false, has_fallback: false, readiness_score: 0 },
  ],
  untested_systems: ["File Server", "Wiki"],
  recommendations: [
    "2件のシステムが未テストです。DR試験を計画してください。",
    "一部システムのRTO目標が未達成です。復旧手順の見直しを推奨します。",
  ],
};

const mockCompliance: RTOComplianceReport = {
  report_id: "RPT-002",
  report_type: "RTO/RPO Compliance Report",
  generated_at: new Date().toISOString(),
  compliance_rate: 75.0,
  total_systems: 4,
  compliant_systems: 3,
  system_compliance: [
    { system_name: "Core Banking", rto_target_hours: 4, rto_actual_hours: 3.5, deviation_hours: -0.5, compliant: true, trend: "improving" },
    { system_name: "Email System", rto_target_hours: 2, rto_actual_hours: 1.8, deviation_hours: -0.2, compliant: true, trend: "improving" },
    { system_name: "CRM", rto_target_hours: 8, rto_actual_hours: 10, deviation_hours: 2, compliant: false, trend: "deteriorating" },
    { system_name: "HR System", rto_target_hours: 24, rto_actual_hours: 20, deviation_hours: -4, compliant: true, trend: "improving" },
  ],
  overdue_systems: ["CRM"],
};

const mockTrend: ExerciseTrendReport = {
  report_id: "RPT-003",
  report_type: "Exercise Trend Report",
  generated_at: new Date().toISOString(),
  total_exercises: 8,
  yearly_trends: [
    { year: 2024, exercise_count: 2, completed: 2, pass_count: 1, achievement_rate: 50.0 },
    { year: 2025, exercise_count: 3, completed: 3, pass_count: 2, achievement_rate: 66.7 },
    { year: 2026, exercise_count: 3, completed: 2, pass_count: 2, achievement_rate: 100.0 },
  ],
  common_issues: { "network": 3, "procedure": 2, "communication": 1 },
  total_improvements: 12,
  completed_improvements: 8,
  improvement_completion_rate: 66.7,
};

const mockISO: ISO20000Report = {
  report_id: "RPT-004",
  report_type: "ISO20000 ITSCM Compliance Report",
  generated_at: new Date().toISOString(),
  compliance_rate: 75.0,
  total_items: 8,
  compliant_items: 6,
  checklist_results: [
    { id: "ITSCM-001", requirement: "ITサービス継続計画が文書化されていること", category: "計画", compliant: true, evidence: "6件のシステムが登録済み" },
    { id: "ITSCM-002", requirement: "RTO/RPO目標が全対象システムに設定されていること", category: "目標設定", compliant: true, evidence: "6/6件設定済み" },
    { id: "ITSCM-003", requirement: "年1回以上のBCP訓練が実施されていること", category: "訓練", compliant: true, evidence: "2回の訓練完了" },
    { id: "ITSCM-004", requirement: "復旧手順が文書化・レビューされていること", category: "手順", compliant: true, evidence: "訓練記録あり" },
    { id: "ITSCM-005", requirement: "BIA（ビジネスインパクト分析）が実施されていること", category: "分析", compliant: true, evidence: "システム登録済み" },
    { id: "ITSCM-006", requirement: "緊急連絡体制が整備されていること", category: "連絡体制", compliant: true, evidence: "システム体制登録済み" },
    { id: "ITSCM-007", requirement: "DR試験結果に基づく改善が実施されていること", category: "継続改善", compliant: false, evidence: "0件テスト済み" },
    { id: "ITSCM-008", requirement: "代替手段・フォールバックが定義されていること", category: "代替手段", compliant: false, evidence: "0/6件定義済み" },
  ],
  non_compliant_items: [
    { id: "ITSCM-007", requirement: "DR試験結果に基づく改善が実施されていること", category: "継続改善", compliant: false, evidence: "0件テスト済み" },
    { id: "ITSCM-008", requirement: "代替手段・フォールバックが定義されていること", category: "代替手段", compliant: false, evidence: "0/6件定義済み" },
  ],
  next_audit_actions: [
    "[ITSCM-007] DR試験結果に基づく改善が実施されていること - 対応が必要です",
    "[ITSCM-008] 代替手段・フォールバックが定義されていること - 対応が必要です",
  ],
};

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
  const [usingMock, setUsingMock] = useState(false);

  useEffect(() => {
    setLoading(true);
    setUsingMock(false);

    const fetchers: Record<TabId, () => Promise<void>> = {
      readiness: async () => {
        try {
          const data = await dashboard.reports.readiness();
          setReadiness(data);
        } catch {
          setReadiness(mockReadiness);
          setUsingMock(true);
        }
      },
      compliance: async () => {
        try {
          const data = await dashboard.reports.rtoCompliance();
          setCompliance(data);
        } catch {
          setCompliance(mockCompliance);
          setUsingMock(true);
        }
      },
      trends: async () => {
        try {
          const data = await dashboard.reports.exerciseTrends();
          setTrends(data);
        } catch {
          setTrends(mockTrend);
          setUsingMock(true);
        }
      },
      iso20000: async () => {
        try {
          const data = await dashboard.reports.iso20000();
          setIso(data);
        } catch {
          setIso(mockISO);
          setUsingMock(true);
        }
      },
    };

    fetchers[activeTab]().finally(() => setLoading(false));
  }, [activeTab]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-800">レポート</h2>
        {usingMock && (
          <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-700">
            オフラインモード（モックデータ表示中）
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
