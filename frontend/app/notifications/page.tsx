"use client";

import { useEffect, useState, useCallback } from "react";
import type {
  NotificationLog,
  EscalationPlan,
  EscalationLevel,
} from "../../lib/types";
import { notifications as notificationsApi, escalation } from "../../lib/api";

// ---- Mock data for fallback ----

const MOCK_PLANS: Record<string, EscalationPlan> = {
  p1: {
    severity: "p1",
    plan_name: "P1 Full BCP Activation",
    levels: [
      { level: 1, role: "対応チーム", delay_minutes: 0, channels: ["teams"] },
      {
        level: 2,
        role: "IT部門長",
        delay_minutes: 5,
        channels: ["teams", "email"],
      },
      {
        level: 3,
        role: "経営層（CISO/CEO）",
        delay_minutes: 15,
        channels: ["email"],
      },
      {
        level: 4,
        role: "全部門長",
        delay_minutes: 30,
        channels: ["teams", "email"],
      },
    ],
  },
  p2: {
    severity: "p2",
    plan_name: "P2 Partial BCP Activation",
    levels: [
      { level: 1, role: "対応チーム", delay_minutes: 0, channels: ["teams"] },
      {
        level: 2,
        role: "IT部門長",
        delay_minutes: 15,
        channels: ["teams", "email"],
      },
    ],
  },
};

const MOCK_LOGS: NotificationLog[] = [
  {
    id: "mock-1",
    notification_type: "teams",
    recipient: "teams-channel",
    subject: "[BCP Escalation L1] P1 Full BCP Activation",
    body: "Escalation Level 1: 対応チーム",
    status: "sent",
    sent_at: "2026-03-27T10:00:00Z",
    created_at: "2026-03-27T10:00:00Z",
  },
  {
    id: "mock-2",
    notification_type: "email",
    recipient: "manager@example.com",
    subject: "[BCP Escalation L2] P1 Full BCP Activation",
    body: "Escalation Level 2: IT部門長",
    status: "sent",
    sent_at: "2026-03-27T10:05:00Z",
    created_at: "2026-03-27T10:05:00Z",
  },
  {
    id: "mock-3",
    notification_type: "email",
    recipient: "ciso@example.com",
    subject: "[BCP Escalation L3] P1 Full BCP Activation",
    body: "Escalation Level 3: 経営層",
    status: "pending",
    created_at: "2026-03-27T10:15:00Z",
  },
  {
    id: "mock-4",
    notification_type: "sms",
    recipient: "+81-90-0000-0000",
    subject: "Emergency Alert",
    body: "SMS notification failed",
    status: "failed",
    error_message: "SMS gateway timeout",
    created_at: "2026-03-27T10:20:00Z",
  },
];

// ---- Helper components ----

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    sent: "bg-green-100 text-green-800",
    pending: "bg-yellow-100 text-yellow-800",
    failed: "bg-red-100 text-red-800",
  };
  const cls = colors[status] || "bg-gray-100 text-gray-800";
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

function ChannelBadge({ channel }: { channel: string }) {
  const colors: Record<string, string> = {
    teams: "bg-purple-100 text-purple-800",
    email: "bg-blue-100 text-blue-800",
    sms: "bg-orange-100 text-orange-800",
  };
  const cls = colors[channel] || "bg-gray-100 text-gray-800";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {channel}
    </span>
  );
}

function EscalationTimeline({ levels }: { levels: EscalationLevel[] }) {
  return (
    <div className="relative ml-4 border-l-2 border-blue-300 pl-6">
      {levels.map((lv) => (
        <div key={lv.level} className="relative mb-6 last:mb-0">
          <div className="absolute -left-[31px] top-0 flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
            {lv.level}
          </div>
          <div className="rounded-lg border bg-white p-3 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-800">{lv.role}</span>
              <span className="text-sm text-gray-500">
                +{lv.delay_minutes}min
              </span>
            </div>
            <div className="mt-1 flex gap-1">
              {lv.channels.map((ch) => (
                <ChannelBadge key={ch} channel={ch} />
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---- Main page ----

export default function NotificationsPage() {
  const [logs, setLogs] = useState<NotificationLog[]>(MOCK_LOGS);
  const [plans, setPlans] = useState<Record<string, EscalationPlan>>(MOCK_PLANS);
  const [selectedPlan, setSelectedPlan] = useState<string>("p1");
  const [loading, setLoading] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);
  const [triggerSeverity, setTriggerSeverity] = useState<string>("p1");
  const [triggerResult, setTriggerResult] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [logsData, planP1, planP2] = await Promise.all([
        notificationsApi.logs(),
        escalation.plan("p1"),
        escalation.plan("p2"),
      ]);
      setLogs(logsData.length > 0 ? logsData : MOCK_LOGS);
      setPlans({
        p1: planP1,
        p2: planP2,
      });
    } catch {
      // fallback to mock data
      setLogs(MOCK_LOGS);
      setPlans(MOCK_PLANS);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleTriggerEscalation = async () => {
    setShowConfirm(false);
    try {
      const result = await escalation.trigger({
        incident_id: "00000000-0000-0000-0000-000000000000",
        severity: triggerSeverity,
        contacts: [],
      });
      setTriggerResult(
        `Escalation triggered: ${result.plan_name} - ${result.notifications_queued} notifications queued`
      );
      // Refresh logs
      await fetchData();
    } catch {
      setTriggerResult("Escalation trigger failed (API unavailable - dry run mode)");
    }
    setTimeout(() => setTriggerResult(null), 5000);
  };

  const currentPlan = plans[selectedPlan] || MOCK_PLANS[selectedPlan];

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900">
        通知管理・エスカレーション
      </h1>

      {/* Alert banner */}
      {triggerResult && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
          {triggerResult}
        </div>
      )}

      {/* Escalation Plans */}
      <section className="rounded-lg border bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-gray-800">
          エスカレーション計画
        </h2>
        <div className="mb-4 flex gap-2">
          {Object.keys(plans).map((sev) => (
            <button
              key={sev}
              onClick={() => setSelectedPlan(sev)}
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                selectedPlan === sev
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {sev.toUpperCase()} - {plans[sev]?.plan_name || sev}
            </button>
          ))}
        </div>
        {currentPlan && (
          <EscalationTimeline levels={currentPlan.levels} />
        )}
      </section>

      {/* Escalation Trigger */}
      <section className="rounded-lg border bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-gray-800">
          エスカレーション発動
        </h2>
        <div className="flex items-center gap-4">
          <select
            value={triggerSeverity}
            onChange={(e) => setTriggerSeverity(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="p1">P1 - Full BCP</option>
            <option value="p2">P2 - Partial BCP</option>
            <option value="p3">P3 - Monitoring</option>
          </select>
          <button
            onClick={() => setShowConfirm(true)}
            className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
          >
            エスカレーション発動
          </button>
        </div>
        {showConfirm && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="mb-3 text-sm text-red-800">
              {triggerSeverity.toUpperCase()}{" "}
              エスカレーションを発動しますか？関係者に通知が送信されます。
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleTriggerEscalation}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                確認・発動
              </button>
              <button
                onClick={() => setShowConfirm(false)}
                className="rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
              >
                キャンセル
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Notification Logs */}
      <section className="rounded-lg border bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-gray-800">
          通知ログ
        </h2>
        {loading ? (
          <p className="text-sm text-gray-500">読み込み中...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase text-gray-500">
                  <th className="px-4 py-3">日時</th>
                  <th className="px-4 py-3">チャネル</th>
                  <th className="px-4 py-3">宛先</th>
                  <th className="px-4 py-3">件名</th>
                  <th className="px-4 py-3">ステータス</th>
                  <th className="px-4 py-3">エラー</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b hover:bg-gray-50">
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                      {new Date(log.created_at).toLocaleString("ja-JP")}
                    </td>
                    <td className="px-4 py-3">
                      <ChannelBadge channel={log.notification_type} />
                    </td>
                    <td className="max-w-[200px] truncate px-4 py-3 text-gray-700">
                      {log.recipient}
                    </td>
                    <td className="max-w-[300px] truncate px-4 py-3 text-gray-800">
                      {log.subject}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={log.status} />
                    </td>
                    <td className="max-w-[200px] truncate px-4 py-3 text-red-600">
                      {log.error_message || "-"}
                    </td>
                  </tr>
                ))}
                {logs.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-4 py-8 text-center text-gray-400"
                    >
                      通知ログがありません
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
