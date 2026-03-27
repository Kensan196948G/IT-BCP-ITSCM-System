"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth, type User } from "../../lib/auth-context";

const ROLES = ["admin", "operator", "viewer", "auditor"] as const;

const ROLE_LABELS: Record<string, string> = {
  admin: "管理者 (Admin)",
  operator: "運用担当 (Operator)",
  viewer: "閲覧者 (Viewer)",
  auditor: "監査人 (Auditor)",
};

const ROLE_PERMISSIONS: Record<string, string[]> = {
  admin: ["read", "create", "update", "delete", "manage_users", "report", "audit_log"],
  operator: ["read", "create", "update", "report"],
  viewer: ["read"],
  auditor: ["read", "report", "audit_log"],
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState<string>("operator");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!userId.trim()) {
      setError("ユーザーIDを入力してください");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, password: "test", role }),
      });

      if (res.ok) {
        const data = await res.json();
        const user: User = {
          user_id: userId,
          role,
          permissions: ROLE_PERMISSIONS[role] ?? ["read"],
        };
        login(data.access_token, user);
        router.push("/");
        return;
      }
    } catch {
      // API unreachable -- fall through to mock token
    }

    // Mock token fallback
    const mockToken = `mock_${userId}_${role}_${Date.now()}`;
    const user: User = {
      user_id: userId,
      role,
      permissions: ROLE_PERMISSIONS[role] ?? ["read"],
    };
    login(mockToken, user);
    setLoading(false);
    router.push("/");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-900 via-blue-800 to-slate-900">
      {/* Subtle grid overlay */}
      <div className="pointer-events-none absolute inset-0 opacity-10 bg-[linear-gradient(rgba(255,255,255,.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.05)_1px,transparent_1px)] bg-[size:40px_40px]" />

      <div className="relative z-10 w-full max-w-md px-4">
        {/* Logo / Title card */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-white/10 backdrop-blur">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              className="h-9 w-9 text-blue-300"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751A11.959 11.959 0 0 0 12 2.714Z"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            IT-BCP-ITSCM-System
          </h1>
          <p className="mt-1 text-sm text-blue-300">
            IT事業継続管理システム
          </p>
        </div>

        {/* Login form */}
        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur"
        >
          <h2 className="mb-6 text-lg font-semibold text-white">
            ログイン
          </h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-500/20 px-4 py-2 text-sm text-red-200">
              {error}
            </div>
          )}

          <label className="mb-1 block text-sm font-medium text-blue-200">
            ユーザーID
          </label>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="例: admin1"
            className="mb-4 w-full rounded-lg border border-white/20 bg-white/10 px-4 py-2.5 text-white placeholder-blue-300/50 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30"
          />

          <label className="mb-1 block text-sm font-medium text-blue-200">
            ロール
          </label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="mb-6 w-full rounded-lg border border-white/20 bg-white/10 px-4 py-2.5 text-white outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30"
          >
            {ROLES.map((r) => (
              <option key={r} value={r} className="bg-blue-900 text-white">
                {ROLE_LABELS[r]}
              </option>
            ))}
          </select>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-2.5 font-semibold text-white transition hover:bg-blue-500 disabled:opacity-50"
          >
            {loading ? "認証中..." : "ログイン"}
          </button>

          <p className="mt-4 text-center text-xs text-blue-400/70">
            BCP/ITSCM統合プラットフォーム v0.1.0
          </p>
        </form>
      </div>
    </div>
  );
}
