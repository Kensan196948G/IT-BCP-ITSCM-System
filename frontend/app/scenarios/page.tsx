"use client";

import { useScenarios } from "../../lib/hooks";
import type { BCPScenario } from "../../lib/types";

const mockScenarios: BCPScenario[] = [
  {
    id: "1",
    scenario_id: "SCN-001",
    title: "データセンター電源喪失",
    scenario_type: "dc_failure",
    description: "主要データセンターの電源が完全に失われるシナリオ。バックアップ電源も30分後に停止。",
    initial_inject: "午前9時、主要DCで停電が発生。UPSへ切替完了。",
    injects: [
      { offset_minutes: 0, title: "停電発生", description: "主電源喪失", expected_actions: ["UPS確認", "発電機起動"] },
      { offset_minutes: 30, title: "発電機故障", description: "バックアップ発電機が起動せず", expected_actions: ["ベンダー連絡", "DRサイト切替判断"] },
    ],
    affected_systems: ["基幹システム", "メールシステム", "ファイルサーバ"],
    expected_duration_hours: 4.0,
    difficulty: "hard",
    is_active: true,
  },
  {
    id: "2",
    scenario_id: "SCN-002",
    title: "ランサムウェア攻撃",
    scenario_type: "ransomware",
    description: "社内ネットワークにランサムウェアが侵入し、複数システムが暗号化されるシナリオ。",
    initial_inject: "セキュリティ監視でランサムウェアの挙動を検知。3台のサーバで暗号化が進行中。",
    injects: [
      { offset_minutes: 0, title: "検知", description: "EDRがランサムウェア検知", expected_actions: ["ネットワーク隔離", "CSIRT招集"] },
      { offset_minutes: 15, title: "拡散", description: "追加5台で暗号化確認", expected_actions: ["被害範囲特定", "バックアップ状態確認"] },
    ],
    affected_systems: ["Active Directory", "ファイルサーバ", "業務システム"],
    expected_duration_hours: 6.0,
    difficulty: "hard",
    is_active: true,
  },
  {
    id: "3",
    scenario_id: "SCN-003",
    title: "クラウドサービス障害",
    scenario_type: "cloud_outage",
    description: "主要クラウドプロバイダーのリージョン障害。SaaSサービス全停止。",
    initial_inject: "クラウドプロバイダーからリージョン障害の通知を受信。",
    injects: [
      { offset_minutes: 0, title: "障害通知", description: "リージョン全体停止", expected_actions: ["影響範囲確認", "代替手段検討"] },
    ],
    affected_systems: ["SaaS業務アプリ", "クラウドストレージ"],
    expected_duration_hours: 3.0,
    difficulty: "medium",
    is_active: true,
  },
  {
    id: "4",
    scenario_id: "SCN-004",
    title: "大規模地震発生",
    scenario_type: "earthquake",
    description: "震度6強の地震が発生。本社ビルおよびDCに物理的被害。",
    initial_inject: "午前10時、震度6強の地震が発生。本社ビル内で停電・通信障害。",
    injects: [
      { offset_minutes: 0, title: "地震発生", description: "震度6強、本社被災", expected_actions: ["安否確認", "被害状況把握"] },
      { offset_minutes: 60, title: "余震発生", description: "震度4の余震", expected_actions: ["二次災害防止", "復旧判断"] },
    ],
    affected_systems: ["全社システム"],
    expected_duration_hours: 8.0,
    difficulty: "hard",
    is_active: true,
  },
  {
    id: "5",
    scenario_id: "SCN-005",
    title: "パンデミック対応訓練",
    scenario_type: "pandemic",
    description: "新型感染症の流行により出社率が30%以下に低下。リモートワーク体制への完全移行。",
    initial_inject: "感染拡大により政府が緊急事態宣言。出社制限が発令。",
    injects: [
      { offset_minutes: 0, title: "緊急事態宣言", description: "出社率30%以下に制限", expected_actions: ["リモートワーク体制確認", "VPN容量確認"] },
    ],
    affected_systems: ["VPN", "リモートアクセス基盤"],
    expected_duration_hours: 2.0,
    difficulty: "easy",
    is_active: true,
  },
];

const difficultyBadge: Record<string, string> = {
  easy: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  hard: "bg-red-100 text-red-700",
};

const difficultyLabel: Record<string, string> = {
  easy: "易",
  medium: "中",
  hard: "難",
};

const scenarioTypeLabel: Record<string, string> = {
  earthquake: "地震",
  ransomware: "ランサムウェア",
  dc_failure: "DC障害",
  cloud_outage: "クラウド障害",
  pandemic: "パンデミック",
  supplier_failure: "サプライヤー障害",
};

export default function ScenariosPage() {
  const { data, loading, error } = useScenarios();

  const scenarioList = error || !data ? mockScenarios : data;

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
        <h2 className="text-2xl font-bold text-slate-800">シナリオ管理</h2>
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
              <th className="px-4 py-3 font-medium">タイプ</th>
              <th className="px-4 py-3 font-medium">難易度</th>
              <th className="px-4 py-3 font-medium">影響システム</th>
              <th className="px-4 py-3 font-medium">所要時間</th>
              <th className="px-4 py-3 font-medium">インジェクション数</th>
            </tr>
          </thead>
          <tbody>
            {scenarioList.map((scn) => (
              <tr key={scn.id} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-xs text-slate-600">{scn.scenario_id}</td>
                <td className="px-4 py-3 font-medium text-slate-800">{scn.title}</td>
                <td className="px-4 py-3 text-slate-600">
                  {scenarioTypeLabel[scn.scenario_type] || scn.scenario_type}
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded px-2 py-0.5 text-xs font-semibold ${difficultyBadge[scn.difficulty] || "bg-slate-100 text-slate-500"}`}>
                    {difficultyLabel[scn.difficulty] || scn.difficulty}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {scn.affected_systems ? (
                    <div className="flex flex-wrap gap-1">
                      {scn.affected_systems.slice(0, 3).map((sys) => (
                        <span key={sys} className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                          {sys}
                        </span>
                      ))}
                      {scn.affected_systems.length > 3 && (
                        <span className="text-xs text-slate-400">+{scn.affected_systems.length - 3}</span>
                      )}
                    </div>
                  ) : "-"}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {scn.expected_duration_hours ? `${scn.expected_duration_hours}h` : "-"}
                </td>
                <td className="px-4 py-3 text-center text-slate-600">
                  {scn.injects.length}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
