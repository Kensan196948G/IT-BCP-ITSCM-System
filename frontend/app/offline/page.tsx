"use client";

export default function OfflinePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full text-center p-8">
        <div className="text-6xl mb-4">📡</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          オフラインモード
        </h1>
        <p className="text-gray-600 mb-6">
          ネットワーク接続がありません。
          <br />
          キャッシュされたBCP重要資料は引き続き参照可能です。
        </p>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left">
          <h2 className="font-semibold text-blue-800 mb-2">
            📋 オフラインで利用可能な機能
          </h2>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>✅ BCP計画・復旧手順書の閲覧</li>
            <li>✅ 緊急連絡網の参照</li>
            <li>✅ RTOモニタリング（最終キャッシュ）</li>
            <li>✅ インシデント初動チェックリスト</li>
          </ul>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 text-left">
          <h2 className="font-semibold text-yellow-800 mb-2">
            ⚠️ オフラインで制限される機能
          </h2>
          <ul className="text-sm text-yellow-700 space-y-1">
            <li>❌ リアルタイムRTO更新</li>
            <li>❌ 新規データの登録・編集</li>
            <li>❌ レポート自動生成</li>
            <li>❌ 通知・エスカレーション</li>
          </ul>
        </div>

        <button
          onClick={() => window.location.reload()}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          🔄 再接続を試みる
        </button>

        <p className="text-xs text-gray-400 mt-4">
          IT-BCP-ITSCM-System | PWA Offline Mode
        </p>
      </div>
    </div>
  );
}
