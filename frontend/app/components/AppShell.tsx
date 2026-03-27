"use client";

import { type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { AuthProvider } from "../../lib/auth-context";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  return (
    <AuthProvider>
      {isLoginPage ? (
        <>{children}</>
      ) : (
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex flex-1 flex-col overflow-hidden">
            <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6">
              <h1 className="text-lg font-bold text-blue-800">
                IT-BCP-ITSCM-System
              </h1>
              <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                稼働中
              </span>
            </header>
            <main className="flex-1 overflow-y-auto p-6">{children}</main>
          </div>
        </div>
      )}
    </AuthProvider>
  );
}
