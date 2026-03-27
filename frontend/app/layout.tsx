import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "IT-BCP-ITSCM-System",
  description: "IT事業継続管理システム - BCP/ITSCM統合プラットフォーム",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
