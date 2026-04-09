"use client";

import { incidents } from "../../lib/api";
import { useOfflineSync } from "../../lib/use-offline-sync";
import type { ActiveIncident } from "../../lib/types";

const severityBadge: Record<string, string> = {
  p1: "bg-red-100 text-red-700",
  p2: "bg-orange-100 text-orange-700",
  p3: "bg-yellow-100 text-yellow-700",
  P1: "bg-red-100 text-red-700",
  P2: "bg-orange-100 text-orange-700",
  P3: "bg-yellow-100 text-yellow-700",
};

const severityLabel: Record<string, string> = {
  p1: "P1",
  p2: "P2",
  p3: "P3",
  P1: "P1",
  P2: "P2",
  P3: "P3",
};

const statusLabel: Record<string, string> = {
  active: "対応中",
  recovering: "監視中",
  resolved: "解決済",
};

function elapsedTime(occurredAt: string): string {
  const now = new Date();
  const diffMs = now.getTime() - new Date(occurredAt).getTime();
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
  const { data, loading, error, isOnline, lastSyncTime } = useOfflineSync<ActiveIncident[]>(
    "incidents",
    () => incidents.list(),
  );

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

  const offlineLabel = isOnline
    ? "APIエラー — 再試行してください"
    : lastSyncTime
      ? `オフライン（最終同期: ${new Date(lastSyncTime).toLocaleString("ja-JP")}）`
      : "オフライン（キャッシュなし）";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-800">インシデント管理</h2>
        {error && (
          <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-700">
            {offlineLabel}
          </span>
        )}
      </div>

      {error && !data ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-sm text-red-600">
          インシデントデータを取得できませんでした。ネットワーク接続を確認してください。
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">タイトル</th>
                <th className="px-4 py-3 font-medium">重要度</th>
                <th className="px-4 py-3 font-medium">経過時間</th>
                <th className="px-4 py-3 font-medium">ステータス</th>
                <th className="px-4 py-3 font-medium">影響システム</th>
              </tr>
            </thead>
            <tbody>
              {data && data.length > 0 ? (
                data.map((inc) => (
                  <tr key={inc.id} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono text-xs text-slate-600">{inc.incident_id}</td>
                    <td className="px-4 py-3 font-medium text-slate-800">{inc.title}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded px-2 py-0.5 text-xs font-semibold ${severityBadge[inc.severity] || "bg-slate-100 text-slate-500"}`}>
                        {severityLabel[inc.severity] || inc.severity}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{elapsedTime(inc.occurred_at)}</td>
                    <td className="px-4 py-3 text-slate-600">{statusLabel[inc.status] || inc.status}</td>
                    <td className="px-4 py-3 text-slate-600">
                      {inc.affected_systems ? inc.affected_systems.join(", ") : "-"}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-sm text-slate-400">
                    アクティブなインシデントはありません
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
