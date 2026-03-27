"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "../../lib/auth-context";

const navItems = [
  { href: "/", label: "ダッシュボード", icon: "\u{1F4CA}" },
  { href: "/plans", label: "BCP計画", icon: "\u{1F5C2}\uFE0F" },
  { href: "/procedures", label: "復旧手順書", icon: "\u{1F4DD}" },
  { href: "/contacts", label: "連絡網", icon: "\u{1F4DE}" },
  { href: "/bia", label: "BIA分析", icon: "\u{1F4C9}" },
  { href: "/exercises", label: "訓練管理", icon: "\u{1F3CB}\uFE0F" },
  { href: "/scenarios", label: "シナリオ", icon: "\u{1F3AD}" },
  { href: "/incidents", label: "インシデント", icon: "\u{1F6A8}" },
  { href: "/notifications", label: "通知管理", icon: "\u{1F514}" },
  { href: "/rto-monitor", label: "RTOモニタ", icon: "\u{1F4C8}" },
  { href: "/audit", label: "監査ログ", icon: "\u{1F50D}" },
  { href: "/reports", label: "レポート", icon: "\u{1F4CB}" },
  { href: "/runbook", label: "運用ランブック", icon: "\u{1F4D6}" },
  { href: "/system-status", label: "システム状態", icon: "\u{1F4BB}" },
  { href: "/settings", label: "設定", icon: "\u2699\uFE0F" },
];

const ROLE_LABELS: Record<string, string> = {
  admin: "管理者",
  operator: "運用担当",
  viewer: "閲覧者",
  auditor: "監査人",
};

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { currentUser, isAuthenticated, logout } = useAuth();
  const [open, setOpen] = useState(false);

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <>
      {/* Mobile hamburger */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed left-4 top-3 z-50 rounded-md bg-blue-800 p-2 text-white md:hidden"
        aria-label="メニュー"
      >
        <span className="block text-lg leading-none">{open ? "\u2715" : "\u2630"}</span>
      </button>

      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/30 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <nav
        className={`fixed z-40 flex h-full w-60 flex-col bg-blue-900 text-white transition-transform md:static md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header with user info */}
        <div className="flex flex-col border-b border-blue-800 px-4 py-3">
          <span className="text-sm font-bold tracking-wide">BCP-ITSCM</span>
          {isAuthenticated && currentUser && (
            <div className="mt-1.5 flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-700 text-xs font-bold uppercase">
                {currentUser.user_id.charAt(0)}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium">{currentUser.user_id}</p>
                <p className="text-[10px] text-blue-300">
                  {ROLE_LABELS[currentUser.role] ?? currentUser.role}
                </p>
              </div>
            </div>
          )}
        </div>

        <ul className="mt-2 flex-1 space-y-1 overflow-y-auto px-2">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                    active
                      ? "bg-blue-700 font-semibold"
                      : "hover:bg-blue-800"
                  }`}
                >
                  <span className="text-lg">{item.icon}</span>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Logout button */}
        {isAuthenticated && (
          <div className="border-t border-blue-800 px-3 py-3">
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-blue-300 transition-colors hover:bg-blue-800 hover:text-white"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                className="h-4 w-4"
              >
                <path
                  fillRule="evenodd"
                  d="M3 4.25A2.25 2.25 0 0 1 5.25 2h5.5A2.25 2.25 0 0 1 13 4.25v2a.75.75 0 0 1-1.5 0v-2a.75.75 0 0 0-.75-.75h-5.5a.75.75 0 0 0-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 0 0 .75-.75v-2a.75.75 0 0 1 1.5 0v2A2.25 2.25 0 0 1 10.75 18h-5.5A2.25 2.25 0 0 1 3 15.75V4.25Z"
                  clipRule="evenodd"
                />
                <path
                  fillRule="evenodd"
                  d="M19 10a.75.75 0 0 0-.75-.75H8.704l1.048-.943a.75.75 0 1 0-1.004-1.114l-2.5 2.25a.75.75 0 0 0 0 1.114l2.5 2.25a.75.75 0 1 0 1.004-1.114l-1.048-.943h9.546A.75.75 0 0 0 19 10Z"
                  clipRule="evenodd"
                />
              </svg>
              ログアウト
            </button>
          </div>
        )}
      </nav>
    </>
  );
}
