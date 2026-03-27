"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

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
  { href: "/reports", label: "レポート", icon: "\u{1F4CB}" },
  { href: "/system-status", label: "システム状態", icon: "\u{1F4BB}" },
  { href: "/settings", label: "設定", icon: "\u2699\uFE0F" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

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
        <div className="flex h-14 items-center justify-center border-b border-blue-800 text-sm font-bold tracking-wide">
          BCP-ITSCM
        </div>
        <ul className="mt-2 flex-1 space-y-1 px-2">
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
      </nav>
    </>
  );
}
