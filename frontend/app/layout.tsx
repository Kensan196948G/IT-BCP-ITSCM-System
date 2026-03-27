import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "./components/Sidebar";
import { ServiceWorkerRegistrar } from "./components/ServiceWorkerRegistrar";

export const metadata: Metadata = {
  title: "IT-BCP-ITSCM-System",
  description: "IT事業継続管理システム - BCP/ITSCM統合プラットフォーム",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="bg-slate-50 text-slate-900">
        <ServiceWorkerRegistrar />
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
      </body>
    </html>
  );
}
