import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "./components/AppShell";
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
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
