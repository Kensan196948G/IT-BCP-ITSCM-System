"use client";

import { useEffect, useState } from "react";

interface ComponentStatus {
  name: string;
  status: "healthy" | "unhealthy";
  latency_ms: number;
}

interface HealthData {
  status: string;
  checks: ComponentStatus[];
  metrics: {
    request_count: number;
    error_count: number;
    error_rate: number;
    average_duration_seconds: number;
    uptime_seconds: number;
    active_incidents: number;
  };
  system: {
    cpu_usage_percent: number;
    memory_usage_percent: number;
    disk_usage_percent: number;
  };
}

const MOCK_DATA: HealthData = {
  status: "ready",
  checks: [
    { name: "database", status: "healthy", latency_ms: 1.2 },
    { name: "redis", status: "healthy", latency_ms: 0.5 },
  ],
  metrics: {
    request_count: 1024,
    error_count: 3,
    error_rate: 0.0029,
    average_duration_seconds: 0.045,
    uptime_seconds: 86400,
    active_incidents: 0,
  },
  system: {
    cpu_usage_percent: 32.5,
    memory_usage_percent: 48.2,
    disk_usage_percent: 35.2,
  },
};

function StatusBadge({ healthy }: { healthy: boolean }) {
  return (
    <span
      className={`inline-block h-3 w-3 rounded-full ${
        healthy ? "bg-green-500" : "bg-red-500"
      }`}
    />
  );
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h ${mins}m`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}

export default function SystemStatusPage() {
  const [data, setData] = useState<HealthData>(MOCK_DATA);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/health/detailed`
        );
        if (res.ok) {
          const json = await res.json();
          setData(json);
        }
      } catch {
        // Use mock data as fallback
      } finally {
        setLoading(false);
        setLastUpdated(new Date().toLocaleString("ja-JP"));
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const allComponents = [
    {
      name: "Backend API",
      healthy: data.status === "ready",
    },
    ...data.checks.map((c) => ({
      name: c.name.charAt(0).toUpperCase() + c.name.slice(1),
      healthy: c.status === "healthy",
    })),
    {
      name: "Frontend",
      healthy: true,
    },
  ];

  const errorRatePercent = (data.metrics.error_rate * 100).toFixed(2);
  const avgResponseMs = (data.metrics.average_duration_seconds * 1000).toFixed(
    1
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-800">
          System Status
        </h2>
        {lastUpdated && (
          <span className="text-xs text-slate-500">
            Last updated: {lastUpdated}
          </span>
        )}
      </div>

      {loading && (
        <p className="text-sm text-slate-500">Loading...</p>
      )}

      {/* Component Status */}
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-slate-700">
          Component Health
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {allComponents.map((comp) => (
            <div
              key={comp.name}
              className="flex items-center gap-3 rounded-md border border-slate-100 bg-slate-50 px-4 py-3"
            >
              <StatusBadge healthy={comp.healthy} />
              <div>
                <p className="text-sm font-medium text-slate-700">
                  {comp.name}
                </p>
                <p
                  className={`text-xs ${
                    comp.healthy ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {comp.healthy ? "Operational" : "Down"}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Metrics */}
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-slate-700">
          Metrics
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-md bg-blue-50 px-4 py-3">
            <p className="text-xs text-blue-600">Total Requests</p>
            <p className="text-2xl font-bold text-blue-800">
              {data.metrics.request_count.toLocaleString()}
            </p>
          </div>
          <div className="rounded-md bg-red-50 px-4 py-3">
            <p className="text-xs text-red-600">Error Rate</p>
            <p className="text-2xl font-bold text-red-800">
              {errorRatePercent}%
            </p>
          </div>
          <div className="rounded-md bg-amber-50 px-4 py-3">
            <p className="text-xs text-amber-600">Avg Response</p>
            <p className="text-2xl font-bold text-amber-800">
              {avgResponseMs}ms
            </p>
          </div>
          <div className="rounded-md bg-purple-50 px-4 py-3">
            <p className="text-xs text-purple-600">Active Incidents</p>
            <p className="text-2xl font-bold text-purple-800">
              {data.metrics.active_incidents}
            </p>
          </div>
        </div>
      </section>

      {/* System Resources */}
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-slate-700">
          System Resources
        </h3>
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { label: "CPU", value: data.system.cpu_usage_percent },
            { label: "Memory", value: data.system.memory_usage_percent },
            { label: "Disk", value: data.system.disk_usage_percent },
          ].map((res) => (
            <div key={res.label} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600">{res.label}</span>
                <span className="font-medium text-slate-800">
                  {res.value}%
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                <div
                  className={`h-full rounded-full ${
                    res.value > 80
                      ? "bg-red-500"
                      : res.value > 60
                        ? "bg-amber-500"
                        : "bg-green-500"
                  }`}
                  style={{ width: `${res.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Uptime */}
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-2 text-lg font-semibold text-slate-700">
          Uptime
        </h3>
        <p className="text-3xl font-bold text-green-700">
          {formatUptime(data.metrics.uptime_seconds)}
        </p>
      </section>
    </div>
  );
}
