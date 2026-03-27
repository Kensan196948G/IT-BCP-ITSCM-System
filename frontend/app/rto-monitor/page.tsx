"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRTOOverview } from "../../lib/hooks";
import type { RTOMonitorSystem, RTOOverview } from "../../lib/types";

const mockRtoData: RTOOverview = {
  systems: [
    { name: "基幹業務システム", rto_target_minutes: 60, elapsed_minutes: 0, status: "not_started" },
    { name: "メールシステム", rto_target_minutes: 30, elapsed_minutes: 25, status: "on_track" },
    { name: "顧客管理CRM", rto_target_minutes: 240, elapsed_minutes: 180, status: "at_risk" },
    { name: "人事給与システム", rto_target_minutes: 240, elapsed_minutes: 120, status: "on_track" },
    { name: "ファイルサーバ", rto_target_minutes: 120, elapsed_minutes: 150, status: "overdue" },
    { name: "社内Wiki", rto_target_minutes: 2880, elapsed_minutes: 2880, status: "recovered" },
  ],
};

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

function RTOCard({ sys }: { sys: RTOMonitorSystem }) {
  const cfg = statusConfig[sys.status] || statusConfig.not_started;
  const pct = sys.rto_target_minutes > 0 ? Math.min((sys.elapsed_minutes / sys.rto_target_minutes) * 100, 100) : 0;

  return (
    <div className={`rounded-lg border p-5 shadow-sm ${cfg.bg}`}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-slate-800">{sys.name}</h3>
        <span className={`rounded px-2 py-0.5 text-xs font-semibold ${cfg.color}`}>
          {cfg.label}
        </span>
      </div>

      <div className="mb-2 flex justify-between text-xs text-slate-500">
        <span>経過: {formatMinutes(sys.elapsed_minutes)}</span>
        <span>目標: {formatMinutes(sys.rto_target_minutes)}</span>
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
}

type WsStatus = "connecting" | "connected" | "disconnected";

interface WsRtoData {
  type: string;
  timestamp: string;
  systems: Array<{
    system_name: string;
    rto_target_hours: number;
    status: string;
    elapsed_hours: number;
    remaining_hours: number;
    overdue_hours?: number;
  }>;
  summary: {
    total: number;
    on_track: number;
    at_risk: number;
    overdue: number;
  };
}

export default function RtoMonitorPage() {
  const { data, loading, error } = useRTOOverview();
  const [wsStatus, setWsStatus] = useState<WsStatus>("disconnected");
  const [wsData, setWsData] = useState<WsRtoData | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connectWebSocket = useCallback(() => {
    try {
      const wsUrl =
        (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
          .replace("http://", "ws://")
          .replace("https://", "wss://") + "/ws/rto-dashboard";

      setWsStatus("connecting");
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus("connected");
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data) as WsRtoData;
          if (msg.type === "rto_snapshot" || msg.type === "rto_update") {
            setWsData(msg);
            setLastUpdate(new Date().toLocaleTimeString("ja-JP"));
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        setWsStatus("disconnected");
        wsRef.current = null;
      };

      ws.onerror = () => {
        setWsStatus("disconnected");
      };
    } catch {
      setWsStatus("disconnected");
    }
  }, []);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // Convert WS data to display format
  const wsDisplayData: RTOOverview | null = wsData
    ? {
        systems: wsData.systems.map((s) => ({
          name: s.system_name,
          rto_target_minutes: s.rto_target_hours * 60,
          elapsed_minutes: s.elapsed_hours * 60,
          status: s.status,
        })),
      }
    : null;

  // Use WS data if available, else API, else mock
  const rtoData = wsDisplayData || (error || !data ? mockRtoData : data);

  if (loading && !wsData) {
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
        <h2 className="text-2xl font-bold text-slate-800">RTOモニタリング</h2>
        <div className="flex items-center gap-3">
          {/* WebSocket status indicator */}
          <div className="flex items-center gap-2">
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full ${
                wsStatus === "connected"
                  ? "bg-green-500"
                  : wsStatus === "connecting"
                    ? "animate-pulse bg-yellow-500"
                    : "bg-red-400"
              }`}
            />
            <span className="text-xs text-slate-500">
              {wsStatus === "connected"
                ? "リアルタイム接続中"
                : wsStatus === "connecting"
                  ? "接続中..."
                  : "切断中"}
            </span>
          </div>

          {wsStatus === "disconnected" && (
            <button
              onClick={connectWebSocket}
              className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700"
            >
              再接続
            </button>
          )}

          {lastUpdate && (
            <span className="text-xs text-slate-400">
              最終更新: {lastUpdate}
            </span>
          )}

          {error && !wsData && (
            <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-700">
              オフラインモード（モックデータ表示中）
            </span>
          )}
        </div>
      </div>

      {/* WS summary bar */}
      {wsData && wsData.summary && (
        <div className="grid grid-cols-4 gap-3">
          <div className="rounded-lg border border-slate-200 bg-white p-3 text-center">
            <p className="text-2xl font-bold text-slate-800">{wsData.summary.total}</p>
            <p className="text-xs text-slate-500">総数</p>
          </div>
          <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-center">
            <p className="text-2xl font-bold text-green-700">{wsData.summary.on_track}</p>
            <p className="text-xs text-green-600">順調</p>
          </div>
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-center">
            <p className="text-2xl font-bold text-yellow-700">{wsData.summary.at_risk}</p>
            <p className="text-xs text-yellow-600">リスクあり</p>
          </div>
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-center">
            <p className="text-2xl font-bold text-red-700">{wsData.summary.overdue}</p>
            <p className="text-xs text-red-600">超過</p>
          </div>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {rtoData.systems.map((sys) => (
          <RTOCard key={sys.name} sys={sys} />
        ))}
      </div>
    </div>
  );
}
