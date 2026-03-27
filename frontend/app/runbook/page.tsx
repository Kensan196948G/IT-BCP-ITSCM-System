"use client";

import { useEffect, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChecklistItem {
  id: number;
  category: string;
  item: string;
  required: boolean;
}

interface Step {
  step: number;
  action: string;
  description: string;
  responsible?: string;
  estimated_minutes?: number;
}

interface PlaybookStep {
  step: number;
  action: string;
  description: string;
}

// ---------------------------------------------------------------------------
// Mock Data (fallback)
// ---------------------------------------------------------------------------

const mockChecklist: ChecklistItem[] = [
  { id: 1, category: "テスト", item: "全ユニットテストがパスしていること", required: true },
  { id: 2, category: "テスト", item: "E2Eテストがパスしていること", required: true },
  { id: 3, category: "品質", item: "Lintチェックが通過していること", required: true },
  { id: 4, category: "品質", item: "フロントエンドビルドが成功していること", required: true },
  { id: 5, category: "セキュリティ", item: "セキュリティスキャンが完了していること", required: true },
  { id: 6, category: "セキュリティ", item: "シークレット漏洩チェックが完了していること", required: true },
  { id: 7, category: "データベース", item: "DBマイグレーションが確認済みであること", required: true },
  { id: 8, category: "データベース", item: "DBバックアップが取得済みであること", required: true },
  { id: 9, category: "インフラ", item: "Terraformプランがレビュー済みであること", required: true },
  { id: 10, category: "インフラ", item: "ロールバック手順が準備されていること", required: true },
  { id: 11, category: "承認", item: "変更管理チケットが承認済みであること", required: true },
  { id: 12, category: "承認", item: "関係者への事前通知が完了していること", required: false },
];

const mockRollback: Step[] = [
  { step: 1, action: "異常検知・ロールバック判断", description: "異常を検知しロールバック実施を判断", responsible: "インシデントコマンダー", estimated_minutes: 5 },
  { step: 2, action: "関係者への通知", description: "ロールバック開始を通知", responsible: "運用チーム", estimated_minutes: 3 },
  { step: 3, action: "トラフィック遮断", description: "メンテナンスページへ切替", responsible: "インフラチーム", estimated_minutes: 2 },
  { step: 4, action: "コンテナイメージの切り戻し", description: "前バージョンに変更してデプロイ", responsible: "インフラチーム", estimated_minutes: 10 },
  { step: 5, action: "DBマイグレーションのロールバック", description: "DBマイグレーションを逆方向に実行", responsible: "DBAチーム", estimated_minutes: 15 },
  { step: 6, action: "動作確認", description: "ヘルスチェック・主要機能の動作確認", responsible: "QAチーム", estimated_minutes: 10 },
  { step: 7, action: "トラフィック復旧", description: "本番アプリケーションにルーティング復旧", responsible: "インフラチーム", estimated_minutes: 2 },
  { step: 8, action: "事後報告・原因分析", description: "RCAチケットを作成", responsible: "運用チーム", estimated_minutes: 30 },
];

const mockDrFailover: Step[] = [
  { step: 1, action: "災害発生の確認", description: "プライマリリージョンの障害確認", responsible: "インシデントコマンダー", estimated_minutes: 10 },
  { step: 2, action: "DR発動宣言", description: "経営層にDR発動を宣言", responsible: "CIO/CISO", estimated_minutes: 5 },
  { step: 3, action: "DRサイトの状態確認", description: "西日本リージョンの状態確認", responsible: "インフラチーム", estimated_minutes: 10 },
  { step: 4, action: "DBフェイルオーバー実行", description: "リードレプリカを昇格", responsible: "DBAチーム", estimated_minutes: 15 },
  { step: 5, action: "アプリケーションスケールアップ", description: "レプリカ数を本番相当に増加", responsible: "インフラチーム", estimated_minutes: 10 },
  { step: 6, action: "DNS/Front Door切替", description: "オリジンを西日本に切替", responsible: "インフラチーム", estimated_minutes: 5 },
  { step: 7, action: "接続テスト・動作確認", description: "主要エンドポイントのアクセス確認", responsible: "QAチーム", estimated_minutes: 15 },
  { step: 8, action: "外部連携の切替確認", description: "外部API接続先の確認", responsible: "アプリチーム", estimated_minutes: 10 },
  { step: 9, action: "ユーザーへの通知", description: "サービス復旧通知", responsible: "広報/CS", estimated_minutes: 5 },
  { step: 10, action: "監視強化・状況報告", description: "監視強化とフェイルバック計画策定", responsible: "運用チーム", estimated_minutes: 30 },
];

const mockPlaybooks: Record<string, { title: string; steps: PlaybookStep[] }> = {
  earthquake: {
    title: "地震発生時インシデント対応プレイブック",
    steps: [
      { step: 1, action: "安全確認", description: "全従業員の安全確認を実施" },
      { step: 2, action: "被害状況の把握", description: "データセンター・オフィスの被害確認" },
      { step: 3, action: "インシデント宣言", description: "BCPインシデントを宣言" },
      { step: 4, action: "システム影響範囲の特定", description: "影響ITシステムの一覧作成" },
      { step: 5, action: "DRサイト切替判断", description: "DR切替の要否を判断" },
      { step: 6, action: "復旧作業の実施", description: "Tier1システムから順次復旧" },
      { step: 7, action: "復旧確認・事後対応", description: "事後レビューを実施" },
    ],
  },
  ransomware: {
    title: "ランサムウェア感染時インシデント対応プレイブック",
    steps: [
      { step: 1, action: "検知・初動対応", description: "感染端末をネットワークから隔離" },
      { step: 2, action: "感染範囲の特定", description: "EDR/SIEMログを分析" },
      { step: 3, action: "インシデント宣言・エスカレーション", description: "CSIRT・外部業者に連絡" },
      { step: 4, action: "証拠保全", description: "メモリダンプ・ディスクイメージ取得" },
      { step: 5, action: "封じ込め", description: "感染経路を遮断" },
      { step: 6, action: "クリーンバックアップからの復旧", description: "クリーンな環境へリストア" },
      { step: 7, action: "システム検証", description: "マルウェアスキャン・整合性チェック" },
      { step: 8, action: "再発防止・事後報告", description: "根本原因分析と再発防止策" },
    ],
  },
  dc_failure: {
    title: "データセンター障害時インシデント対応プレイブック",
    steps: [
      { step: 1, action: "障害検知・初期評価", description: "障害検知と影響範囲評価" },
      { step: 2, action: "インシデント宣言", description: "War Room開設" },
      { step: 3, action: "復旧見込みの確認", description: "DC事業者から復旧見込み取得" },
      { step: 4, action: "DRフェイルオーバー実行", description: "DRフェイルオーバー手順実行" },
      { step: 5, action: "サービス復旧確認", description: "DRサイトでのサービス稼働確認" },
      { step: 6, action: "フェイルバック計画・事後対応", description: "フェイルバック計画策定" },
    ],
  },
};

// ---------------------------------------------------------------------------
// API fetch helpers
// ---------------------------------------------------------------------------

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

// ---------------------------------------------------------------------------
// Tab type
// ---------------------------------------------------------------------------

type TabKey = "checklist" | "rollback" | "dr" | "incident";

const tabs: { key: TabKey; label: string }[] = [
  { key: "checklist", label: "デプロイチェックリスト" },
  { key: "rollback", label: "ロールバック手順" },
  { key: "dr", label: "DRフェイルオーバー" },
  { key: "incident", label: "インシデント対応" },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function RunbookPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("checklist");
  const [checklist, setChecklist] = useState<ChecklistItem[]>(mockChecklist);
  const [checked, setChecked] = useState<Record<number, boolean>>({});
  const [rollbackSteps, setRollbackSteps] = useState<Step[]>(mockRollback);
  const [drSteps, setDrSteps] = useState<Step[]>(mockDrFailover);
  const [scenario, setScenario] = useState<string>("earthquake");
  const [playbook, setPlaybook] = useState(mockPlaybooks["earthquake"]);

  useEffect(() => {
    fetchJson<{ items: ChecklistItem[] }>("/api/runbook/deployment-checklist", { items: mockChecklist }).then((d) =>
      setChecklist(d.items),
    );
    fetchJson<{ steps: Step[] }>("/api/runbook/rollback-procedure", { steps: mockRollback }).then((d) =>
      setRollbackSteps(d.steps),
    );
    fetchJson<{ steps: Step[] }>("/api/runbook/dr-failover", { steps: mockDrFailover }).then((d) =>
      setDrSteps(d.steps),
    );
  }, []);

  useEffect(() => {
    fetchJson<{ title: string; steps: PlaybookStep[] }>(
      `/api/runbook/incident-playbook/${scenario}`,
      mockPlaybooks[scenario] || mockPlaybooks["earthquake"],
    ).then(setPlaybook);
  }, [scenario]);

  const toggleCheck = (id: number) => {
    setChecked((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const completedCount = Object.values(checked).filter(Boolean).length;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">運用ランブック</h2>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg bg-slate-200 p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === t.key ? "bg-white text-blue-700 shadow" : "text-slate-600 hover:text-slate-800"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Deployment Checklist */}
      {activeTab === "checklist" && (
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-700">デプロイ前チェックリスト</h3>
            <span className="rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-700">
              {completedCount} / {checklist.length} 完了
            </span>
          </div>
          <div className="space-y-2">
            {checklist.map((item) => (
              <label
                key={item.id}
                className={`flex cursor-pointer items-center gap-3 rounded-md border p-3 transition-colors ${
                  checked[item.id] ? "border-green-300 bg-green-50" : "border-slate-200 hover:bg-slate-50"
                }`}
              >
                <input
                  type="checkbox"
                  checked={!!checked[item.id]}
                  onChange={() => toggleCheck(item.id)}
                  className="h-5 w-5 rounded border-slate-300 text-green-600"
                />
                <div className="flex-1">
                  <span className={`text-sm ${checked[item.id] ? "text-slate-400 line-through" : "text-slate-700"}`}>
                    {item.item}
                  </span>
                  <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                    {item.category}
                  </span>
                </div>
                {item.required && (
                  <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-600">必須</span>
                )}
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Rollback Procedure */}
      {activeTab === "rollback" && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-slate-700">ロールバック手順</h3>
          {rollbackSteps.map((s) => (
            <div key={s.step} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="flex items-start gap-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  {s.step}
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-slate-800">{s.action}</h4>
                  <p className="mt-1 text-sm text-slate-600">{s.description}</p>
                  <div className="mt-2 flex gap-3 text-xs text-slate-500">
                    <span>担当: {s.responsible}</span>
                    <span>想定: {s.estimated_minutes}分</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* DR Failover Timeline */}
      {activeTab === "dr" && (
        <div className="space-y-0">
          <h3 className="mb-4 text-lg font-semibold text-slate-700">DRフェイルオーバー手順</h3>
          <div className="relative ml-4 border-l-2 border-blue-300 pl-6">
            {drSteps.map((s, idx) => (
              <div key={s.step} className={`relative pb-8 ${idx === drSteps.length - 1 ? "pb-0" : ""}`}>
                <div className="absolute -left-[31px] top-0 h-4 w-4 rounded-full border-2 border-blue-500 bg-white" />
                <div className="rounded-lg border border-slate-200 bg-white p-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-slate-800">
                      Step {s.step}: {s.action}
                    </h4>
                    <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
                      {s.estimated_minutes}分
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{s.description}</p>
                  <p className="mt-1 text-xs text-slate-400">担当: {s.responsible}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Incident Response Playbook */}
      {activeTab === "incident" && (
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <h3 className="text-lg font-semibold text-slate-700">インシデント対応プレイブック</h3>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="earthquake">地震</option>
              <option value="ransomware">ランサムウェア</option>
              <option value="dc_failure">データセンター障害</option>
            </select>
          </div>
          {playbook && (
            <div className="rounded-lg border border-slate-200 bg-white p-6">
              <h4 className="mb-4 text-base font-bold text-slate-800">{playbook.title}</h4>
              <div className="space-y-3">
                {playbook.steps.map((s) => (
                  <div key={s.step} className="flex items-start gap-3 rounded-md border border-slate-100 bg-slate-50 p-3">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-orange-500 text-xs font-bold text-white">
                      {s.step}
                    </div>
                    <div>
                      <p className="font-medium text-slate-700">{s.action}</p>
                      <p className="text-sm text-slate-500">{s.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
