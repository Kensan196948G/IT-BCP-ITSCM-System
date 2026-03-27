"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { incidents } from "../../../lib/api";
import type {
  IncidentCommandDashboard,
  IncidentTask,
  SituationReport,
  RTOStatus,
} from "../../../lib/types";

// ---------------------------------------------------------------------------
// Mock data fallback
// ---------------------------------------------------------------------------

const mockDashboard: IncidentCommandDashboard = {
  incident: {
    id: "mock-1",
    incident_id: "BCP-2026-001",
    title: "DC Power Failure - East Region",
    scenario_type: "dc_failure",
    severity: "p1",
    occurred_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    detected_at: new Date(Date.now() - 2.9 * 60 * 60 * 1000).toISOString(),
    status: "active",
    affected_systems: ["Core Banking System", "File Server", "HR System"],
  },
  tasks: [
    {
      id: "t1",
      incident_id: "mock-1",
      task_title: "Activate backup power",
      priority: "critical",
      status: "completed",
      assigned_team: "Facilities",
    },
    {
      id: "t2",
      incident_id: "mock-1",
      task_title: "Failover core DB to DR site",
      priority: "critical",
      status: "in_progress",
      assigned_team: "Database",
      target_system: "Core Banking System",
    },
    {
      id: "t3",
      incident_id: "mock-1",
      task_title: "Notify affected business units",
      priority: "high",
      status: "pending",
      assigned_team: "Communications",
    },
    {
      id: "t4",
      incident_id: "mock-1",
      task_title: "Verify network connectivity",
      priority: "medium",
      status: "blocked",
      assigned_team: "Network",
      notes: "Waiting for power restoration",
    },
  ],
  task_statistics: {
    total: 4,
    pending: 1,
    in_progress: 1,
    completed: 1,
    blocked: 1,
    completion_rate: 25.0,
  },
  latest_report: {
    id: "r1",
    incident_id: "mock-1",
    report_number: 2,
    report_time: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    reporter: "Incident Commander",
    summary:
      "Backup power activated. DB failover in progress. Network team blocked by power dependency.",
    audience: "internal",
  },
  reports_count: 2,
  rto_statuses: [
    {
      system_name: "Core Banking System",
      status: "at_risk",
      color: "#eab308",
      elapsed_hours: 3.0,
      remaining_hours: 1.0,
      rto_target: 4.0,
    },
    {
      system_name: "File Server",
      status: "on_track",
      color: "#22c55e",
      elapsed_hours: 3.0,
      remaining_hours: 5.0,
      rto_target: 8.0,
    },
    {
      system_name: "HR System",
      status: "overdue",
      color: "#dc2626",
      elapsed_hours: 3.0,
      remaining_hours: 0,
      rto_target: 2.0,
      overdue_hours: 1.0,
    },
  ],
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const severityBadge: Record<string, string> = {
  p1: "bg-red-100 text-red-700 border-red-200",
  p2: "bg-orange-100 text-orange-700 border-orange-200",
  p3: "bg-yellow-100 text-yellow-700 border-yellow-200",
};

const severityLabel: Record<string, string> = {
  p1: "P1 - Critical",
  p2: "P2 - Major",
  p3: "P3 - Minor",
};

const statusLabel: Record<string, string> = {
  active: "Active",
  recovering: "Recovering",
  resolved: "Resolved",
  closed: "Closed",
};

const statusColor: Record<string, string> = {
  active: "bg-red-500",
  recovering: "bg-yellow-500",
  resolved: "bg-green-500",
  closed: "bg-slate-400",
};

const taskStatusColor: Record<string, string> = {
  pending: "bg-slate-100 border-slate-300",
  in_progress: "bg-blue-50 border-blue-300",
  completed: "bg-green-50 border-green-300",
  blocked: "bg-red-50 border-red-300",
};

const taskStatusLabel: Record<string, string> = {
  pending: "Pending",
  in_progress: "In Progress",
  completed: "Completed",
  blocked: "Blocked",
};

const priorityBadge: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-slate-100 text-slate-600",
};

function elapsedTime(occurredAt: string): string {
  const now = new Date();
  const diffMs = now.getTime() - new Date(occurredAt).getTime();
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    const remHours = hours % 24;
    return `${days}d ${remHours}h`;
  }
  return `${hours}h ${minutes}m`;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("ja-JP", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TaskColumn({
  title,
  tasks,
  statusKey,
  icon,
}: {
  title: string;
  tasks: IncidentTask[];
  statusKey: string;
  icon: string;
}) {
  const filtered = tasks.filter((t) => t.status === statusKey);
  return (
    <div className={`rounded-lg border p-3 ${taskStatusColor[statusKey] || "bg-white border-slate-200"}`}>
      <h4 className="mb-2 flex items-center gap-1 text-sm font-semibold text-slate-700">
        <span>{icon}</span> {title}
        <span className="ml-auto rounded-full bg-white px-2 py-0.5 text-xs font-medium text-slate-600 shadow-sm">
          {filtered.length}
        </span>
      </h4>
      <div className="space-y-2">
        {filtered.map((task) => (
          <div
            key={task.id}
            className="rounded border border-white/60 bg-white p-2 shadow-sm"
          >
            <p className="text-sm font-medium text-slate-800">
              {task.task_title}
            </p>
            <div className="mt-1 flex flex-wrap items-center gap-1">
              <span
                className={`rounded px-1.5 py-0.5 text-xs font-medium ${priorityBadge[task.priority] || "bg-slate-100"}`}
              >
                {task.priority}
              </span>
              {task.assigned_team && (
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                  {task.assigned_team}
                </span>
              )}
              {task.target_system && (
                <span className="rounded bg-purple-50 px-1.5 py-0.5 text-xs text-purple-600">
                  {task.target_system}
                </span>
              )}
            </div>
            {task.notes && (
              <p className="mt-1 text-xs text-slate-500">{task.notes}</p>
            )}
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="py-2 text-center text-xs text-slate-400">No tasks</p>
        )}
      </div>
    </div>
  );
}

function RTOProgressBar({ rto }: { rto: RTOStatus }) {
  const pct =
    rto.rto_target > 0
      ? Math.min(100, ((rto.elapsed_hours ?? 0) / rto.rto_target) * 100)
      : 0;
  return (
    <div className="flex items-center gap-3 rounded border border-slate-200 bg-white p-3">
      <div className="min-w-[140px]">
        <p className="text-sm font-medium text-slate-800">{rto.system_name}</p>
        <p className="text-xs text-slate-500">
          RTO: {rto.rto_target}h | Elapsed: {rto.elapsed_hours ?? 0}h
        </p>
      </div>
      <div className="flex-1">
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full transition-all"
            style={{
              width: `${Math.min(pct, 100)}%`,
              backgroundColor: rto.color,
            }}
          />
        </div>
      </div>
      <span
        className="rounded px-2 py-0.5 text-xs font-semibold"
        style={{
          backgroundColor: rto.color + "20",
          color: rto.color,
        }}
      >
        {rto.status.replace("_", " ")}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function IncidentCommandPage() {
  const params = useParams();
  const incidentId = params?.id as string;

  const [data, setData] = useState<IncidentCommandDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [generating, setGenerating] = useState(false);

  const fetchData = useCallback(() => {
    if (!incidentId) return;
    setLoading(true);
    incidents
      .commandDashboard(incidentId)
      .then((result) => {
        setData(result);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err : new Error(String(err)));
        setData(null);
      })
      .finally(() => setLoading(false));
  }, [incidentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const dashboard = error || !data ? mockDashboard : data;
  const inc = dashboard.incident;

  const handleAutoGenerate = () => {
    setGenerating(true);
    incidents
      .autoGenerateReport(incidentId)
      .then(() => fetchData())
      .catch(() => {
        /* fallback: ignore in mock mode */
      })
      .finally(() => setGenerating(false));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          <p className="text-sm text-slate-500">Loading command dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`inline-block h-3 w-3 rounded-full ${statusColor[inc.status] || "bg-slate-400"}`}
          />
          <h2 className="text-xl font-bold text-slate-800">{inc.title}</h2>
          <span
            className={`rounded border px-2 py-0.5 text-xs font-semibold ${severityBadge[inc.severity] || "bg-slate-100"}`}
          >
            {severityLabel[inc.severity] || inc.severity}
          </span>
          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
            {statusLabel[inc.status] || inc.status}
          </span>
          <span className="ml-auto text-sm font-medium text-slate-600">
            Elapsed: {elapsedTime(inc.occurred_at)}
          </span>
          {error && (
            <span className="rounded bg-yellow-100 px-2 py-1 text-xs text-yellow-700">
              Offline (mock data)
            </span>
          )}
        </div>
        <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-500">
          <span>ID: {inc.incident_id}</span>
          <span>Type: {inc.scenario_type}</span>
          <span>Detected: {formatTime(inc.detected_at)}</span>
          {inc.affected_systems && (
            <span>
              Systems: {inc.affected_systems.join(", ")}
            </span>
          )}
        </div>
      </div>

      {/* Task Statistics Bar */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-6">
        {[
          { label: "Total Tasks", value: dashboard.task_statistics.total, bg: "bg-slate-50" },
          { label: "Pending", value: dashboard.task_statistics.pending, bg: "bg-slate-50" },
          { label: "In Progress", value: dashboard.task_statistics.in_progress, bg: "bg-blue-50" },
          { label: "Completed", value: dashboard.task_statistics.completed, bg: "bg-green-50" },
          { label: "Blocked", value: dashboard.task_statistics.blocked, bg: "bg-red-50" },
          {
            label: "Completion",
            value: `${dashboard.task_statistics.completion_rate}%`,
            bg: "bg-indigo-50",
          },
        ].map((stat) => (
          <div
            key={stat.label}
            className={`rounded-lg border border-slate-200 ${stat.bg} p-3 text-center`}
          >
            <p className="text-lg font-bold text-slate-800">{stat.value}</p>
            <p className="text-xs text-slate-500">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Task Board (Kanban) */}
      <div>
        <h3 className="mb-3 text-lg font-semibold text-slate-800">
          Task Board
        </h3>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <TaskColumn title="Pending" tasks={dashboard.tasks} statusKey="pending" icon="&#9202;" />
          <TaskColumn
            title="In Progress"
            tasks={dashboard.tasks}
            statusKey="in_progress"
            icon="&#9881;"
          />
          <TaskColumn
            title="Completed"
            tasks={dashboard.tasks}
            statusKey="completed"
            icon="&#10004;"
          />
          <TaskColumn title="Blocked" tasks={dashboard.tasks} statusKey="blocked" icon="&#9940;" />
        </div>
      </div>

      {/* RTO Status */}
      {dashboard.rto_statuses.length > 0 && (
        <div>
          <h3 className="mb-3 text-lg font-semibold text-slate-800">
            RTO Status
          </h3>
          <div className="space-y-2">
            {dashboard.rto_statuses.map((rto) => (
              <RTOProgressBar key={rto.system_name} rto={rto} />
            ))}
          </div>
        </div>
      )}

      {/* Situation Reports Timeline */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800">
            Situation Reports ({dashboard.reports_count})
          </h3>
          <button
            onClick={handleAutoGenerate}
            disabled={generating}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {generating ? "Generating..." : "Auto Generate Report"}
          </button>
        </div>
        {dashboard.latest_report ? (
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span className="font-semibold text-slate-700">
                #{dashboard.latest_report.report_number}
              </span>
              <span>{formatTime(dashboard.latest_report.report_time)}</span>
              {dashboard.latest_report.reporter && (
                <span>by {dashboard.latest_report.reporter}</span>
              )}
              <span className="ml-auto rounded bg-slate-100 px-2 py-0.5 text-xs">
                {dashboard.latest_report.audience}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-700">
              {dashboard.latest_report.summary}
            </p>
            {dashboard.latest_report.next_actions &&
              dashboard.latest_report.next_actions.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-slate-600">
                    Next Actions:
                  </p>
                  <ul className="mt-1 list-inside list-disc text-xs text-slate-500">
                    {dashboard.latest_report.next_actions.map((action, i) => (
                      <li key={i}>{action}</li>
                    ))}
                  </ul>
                </div>
              )}
          </div>
        ) : (
          <p className="text-sm text-slate-400">
            No situation reports yet. Click &quot;Auto Generate Report&quot; to
            create one.
          </p>
        )}
      </div>
    </div>
  );
}
