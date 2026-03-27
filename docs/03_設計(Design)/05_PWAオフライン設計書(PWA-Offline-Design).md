# PWAオフライン設計書 (PWA Offline Design)

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-DES-PWA-005 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 分類 | 設計文書 |
| 準拠規格 | ISO20000 ITSCM / ISO27001 / NIST CSF RECOVER RC |

---

## 目次

1. [概要](#1-概要)
2. [PWA基本設計](#2-pwa基本設計)
3. [Service Worker設計](#3-service-worker設計)
4. [キャッシュ戦略](#4-キャッシュ戦略)
5. [オフラインデータ同期](#5-オフラインデータ同期)
6. [重要資料のプリキャッシュ](#6-重要資料のプリキャッシュ)
7. [オフラインUI設計](#7-オフラインui設計)
8. [セキュリティ考慮事項](#8-セキュリティ考慮事項)
9. [テスト戦略](#9-テスト戦略)
10. [変更履歴](#10-変更履歴)

---

## 1. 概要

### 1.1 オフライン対応の必要性

IT-BCP-ITSCMシステムは災害時に最も必要とされるシステムである。災害時にはネットワークインフラが損傷し、通常のWebアクセスが困難になることが想定される。そのため、以下の観点からPWAによるオフライン対応を実装する。

| 観点 | 説明 |
|------|------|
| 災害時のネットワーク断 | 地震・台風等でインターネット接続が断たれた場合でも、BCP手順書・連絡先にアクセスできること |
| サイバー攻撃時のネットワーク隔離 | ネットワークを意図的に隔離した場合でも、復旧手順にアクセスできること |
| 通信品質の低下 | 災害時のネットワーク輻輳下でも、キャッシュにより素早くコンテンツを表示できること |
| モバイルでの現場利用 | 災害対策本部外の現場でスマートフォンからBCP情報にアクセスできること |

### 1.2 オフライン対応レベル

| レベル | 説明 | 対応範囲 |
|--------|------|---------|
| Level 1: 読取アクセス | キャッシュ済みデータの閲覧 | BCP手順書、連絡先、システム情報 |
| Level 2: オフライン操作 | オフラインでのデータ入力・一時保存 | インシデント登録、状態更新 |
| Level 3: バックグラウンド同期 | オンライン復帰時の自動データ同期 | 保留操作の自動送信 |

---

## 2. PWA基本設計

### 2.1 Web App Manifest

```json
{
    "name": "IT事業継続管理システム (IT-BCP-ITSCM)",
    "short_name": "IT-BCP",
    "description": "災害・サイバー攻撃時のIT復旧計画・BCP訓練・RTOダッシュボード統合プラットフォーム",
    "start_url": "/",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#0F172A",
    "theme_color": "#1E40AF",
    "scope": "/",
    "lang": "ja",
    "categories": ["business", "productivity"],
    "icons": [
        {
            "src": "/icons/icon-72x72.png",
            "sizes": "72x72",
            "type": "image/png"
        },
        {
            "src": "/icons/icon-96x96.png",
            "sizes": "96x96",
            "type": "image/png"
        },
        {
            "src": "/icons/icon-128x128.png",
            "sizes": "128x128",
            "type": "image/png"
        },
        {
            "src": "/icons/icon-144x144.png",
            "sizes": "144x144",
            "type": "image/png"
        },
        {
            "src": "/icons/icon-152x152.png",
            "sizes": "152x152",
            "type": "image/png"
        },
        {
            "src": "/icons/icon-192x192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/icons/icon-384x384.png",
            "sizes": "384x384",
            "type": "image/png"
        },
        {
            "src": "/icons/icon-512x512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable"
        }
    ],
    "shortcuts": [
        {
            "name": "インシデント登録",
            "short_name": "インシデント",
            "url": "/incidents/new",
            "description": "新しいインシデントを登録する",
            "icons": [{"src": "/icons/shortcut-incident.png", "sizes": "96x96"}]
        },
        {
            "name": "RTOダッシュボード",
            "short_name": "RTO",
            "url": "/",
            "description": "RTOダッシュボードを表示する",
            "icons": [{"src": "/icons/shortcut-dashboard.png", "sizes": "96x96"}]
        }
    ]
}
```

### 2.2 インストール促進

| タイミング | 条件 | 表示方法 |
|-----------|------|---------|
| 初回ログイン後 | 未インストール | バナー表示 + インストール案内 |
| 3回目アクセス時 | 未インストール | モーダルダイアログ |
| BCP訓練前 | 演習参加者 | メール通知でインストール案内 |

---

## 3. Service Worker設計

### 3.1 Service Workerライフサイクル

```
┌──────────────┐
│   登録       │  navigator.serviceWorker.register('/sw.js')
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ インストール  │  precache重要資料
│  (install)   │  キャッシュストレージ初期化
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  アクティベート │  古いキャッシュの削除
│  (activate)   │  クライアント制御取得
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   リッスン    │  fetchイベントハンドリング
│  (fetch)     │  pushイベントハンドリング
│              │  syncイベントハンドリング
└──────────────┘
```

### 3.2 Service Worker構成

```javascript
// sw.js の構成

import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { CacheFirst, NetworkFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { BackgroundSyncPlugin } from 'workbox-background-sync';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// 1. プリキャッシュ（ビルド時に自動生成されるマニフェスト）
precacheAndRoute(self.__WB_MANIFEST);

// 2. ランタイムキャッシュ（後述のキャッシュ戦略を適用）

// 3. バックグラウンド同期

// 4. プッシュ通知ハンドリング
```

### 3.3 Service Worker更新戦略

| 項目 | 設定 |
|------|------|
| 更新チェック | ページナビゲーション時 + 1時間ごとの自動チェック |
| 更新通知 | アプリ内バナーで「新しいバージョンが利用可能です」と表示 |
| 適用タイミング | ユーザーが「更新」ボタンをクリックした時、またはすべてのタブが閉じられた時 |
| skipWaiting | ユーザー承認後に実行 |
| 重要更新 | BCP手順の変更時は強制更新を推奨するバナー表示 |

---

## 4. キャッシュ戦略

### 4.1 キャッシュストア一覧

| キャッシュ名 | 用途 | 最大サイズ | 有効期限 |
|------------|------|-----------|---------|
| `itscm-precache` | プリキャッシュ（アプリシェル、静的アセット） | - | ビルドバージョンに紐付く |
| `itscm-bcp-critical` | BCP重要資料（手順書、連絡先） | 200エントリ | 24時間（ただし手動更新可） |
| `itscm-api-data` | APIレスポンスキャッシュ | 500エントリ | 5分 |
| `itscm-api-static` | 更新頻度の低いAPIデータ | 200エントリ | 1時間 |
| `itscm-images` | 画像キャッシュ | 100エントリ | 30日 |
| `itscm-fonts` | フォントキャッシュ | 20エントリ | 365日 |

### 4.2 キャッシュ戦略マッピング

```
┌─────────────────────────────────────────────────────────────┐
│                    リクエスト分類                              │
├─────────────────────┬───────────────────────────────────────┤
│                     │                                       │
│  Cache First        │  BCP重要資料（手順書、連絡先、         │
│  (キャッシュ優先)    │  システム情報）                        │
│                     │  → キャッシュがあればキャッシュから返却  │
│                     │  → バックグラウンドで更新               │
│                     │                                       │
├─────────────────────┼───────────────────────────────────────┤
│                     │                                       │
│  Stale While        │  一般APIデータ（一覧、詳細）            │
│  Revalidate         │  → キャッシュから即座に返却             │
│  (古くても返却+更新) │  → バックグラウンドで最新データ取得     │
│                     │                                       │
├─────────────────────┼───────────────────────────────────────┤
│                     │                                       │
│  Network First      │  リアルタイムデータ（ダッシュボード、    │
│  (ネットワーク優先)  │  インシデント状態）                    │
│                     │  → ネットワーク応答をまず試みる         │
│                     │  → 失敗時はキャッシュにフォールバック   │
│                     │                                       │
├─────────────────────┼───────────────────────────────────────┤
│                     │                                       │
│  Network Only       │  認証API、書き込みAPI（POST/PUT/       │
│  (ネットワークのみ)  │  DELETE）                             │
│                     │  → オフライン時はキューに保存           │
│                     │                                       │
├─────────────────────┼───────────────────────────────────────┤
│                     │                                       │
│  Cache Only         │  静的アセット（JS/CSS/フォント/         │
│  (キャッシュのみ)    │  アイコン）                           │
│                     │  → プリキャッシュ済みアセットを使用     │
│                     │                                       │
└─────────────────────┴───────────────────────────────────────┘
```

### 4.3 ルーティング別キャッシュ設定

```javascript
// BCP重要資料 - Cache First
registerRoute(
    ({ url }) => url.pathname.match(/^\/api\/v1\/(systems|procedures|vendors)/),
    new CacheFirst({
        cacheName: 'itscm-bcp-critical',
        plugins: [
            new CacheableResponsePlugin({ statuses: [0, 200] }),
            new ExpirationPlugin({
                maxEntries: 200,
                maxAgeSeconds: 24 * 60 * 60, // 24時間
            }),
        ],
    })
);

// ダッシュボードAPI - Network First
registerRoute(
    ({ url }) => url.pathname.match(/^\/api\/v1\/dashboard/),
    new NetworkFirst({
        cacheName: 'itscm-api-data',
        plugins: [
            new CacheableResponsePlugin({ statuses: [0, 200] }),
            new ExpirationPlugin({
                maxEntries: 50,
                maxAgeSeconds: 5 * 60, // 5分
            }),
        ],
        networkTimeoutSeconds: 5,
    })
);

// インシデント・演習API - Stale While Revalidate
registerRoute(
    ({ url }) => url.pathname.match(/^\/api\/v1\/(incidents|exercises|scenarios)/),
    new StaleWhileRevalidate({
        cacheName: 'itscm-api-data',
        plugins: [
            new CacheableResponsePlugin({ statuses: [0, 200] }),
            new ExpirationPlugin({
                maxEntries: 500,
                maxAgeSeconds: 5 * 60, // 5分
            }),
        ],
    })
);

// 静的アセット - Cache First (長期)
registerRoute(
    ({ request }) => request.destination === 'image',
    new CacheFirst({
        cacheName: 'itscm-images',
        plugins: [
            new CacheableResponsePlugin({ statuses: [0, 200] }),
            new ExpirationPlugin({
                maxEntries: 100,
                maxAgeSeconds: 30 * 24 * 60 * 60, // 30日
            }),
        ],
    })
);

// フォント - Cache First (超長期)
registerRoute(
    ({ request }) => request.destination === 'font',
    new CacheFirst({
        cacheName: 'itscm-fonts',
        plugins: [
            new CacheableResponsePlugin({ statuses: [0, 200] }),
            new ExpirationPlugin({
                maxEntries: 20,
                maxAgeSeconds: 365 * 24 * 60 * 60, // 1年
            }),
        ],
    })
);
```

### 4.4 BCP重要資料のキャッシュ優先フロー

```
リクエスト発生
  │
  │ ① URLがBCP重要資料パスに一致？
  ▼
┌─── YES ───────────────────────────────────────┐
│                                                │
│  ② キャッシュに存在する？                        │
│  │                                             │
│  ├── YES ──▶ ③ キャッシュからレスポンス返却       │
│  │          ④ バックグラウンドでネットワーク取得   │
│  │          ⑤ 取得成功ならキャッシュ更新          │
│  │                                             │
│  └── NO ──▶ ③ ネットワークから取得               │
│             ④ 取得成功: レスポンス返却 + キャッシュ │
│             ⑤ 取得失敗: オフラインフォールバック   │
│                                                │
└────────────────────────────────────────────────┘
```

---

## 5. オフラインデータ同期

### 5.1 IndexedDB設計

```typescript
// db/offlineDb.ts
import Dexie, { Table } from 'dexie';

interface OfflineOperation {
    id?: number;
    timestamp: Date;
    method: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
    url: string;
    body: any;
    headers: Record<string, string>;
    retryCount: number;
    maxRetries: number;
    status: 'pending' | 'syncing' | 'failed' | 'synced';
    errorMessage?: string;
    conflictResolution?: 'server_wins' | 'client_wins' | 'manual';
}

interface CachedSystem {
    id: string;
    data: any;
    cachedAt: Date;
    version: number;
}

interface CachedProcedure {
    id: string;
    systemId: string;
    data: any;
    cachedAt: Date;
    version: number;
}

interface CachedVendor {
    id: string;
    data: any;
    cachedAt: Date;
    version: number;
}

interface CachedIncident {
    id: string;
    data: any;
    cachedAt: Date;
    version: number;
}

class OfflineDatabase extends Dexie {
    offlineOperations!: Table<OfflineOperation>;
    cachedSystems!: Table<CachedSystem>;
    cachedProcedures!: Table<CachedProcedure>;
    cachedVendors!: Table<CachedVendor>;
    cachedIncidents!: Table<CachedIncident>;

    constructor() {
        super('itscm-offline');
        this.version(1).stores({
            offlineOperations: '++id, timestamp, status, url',
            cachedSystems: 'id, cachedAt',
            cachedProcedures: 'id, systemId, cachedAt',
            cachedVendors: 'id, cachedAt',
            cachedIncidents: 'id, cachedAt',
        });
    }
}
```

### 5.2 バックグラウンド同期

```javascript
// Service Worker内のBackground Sync設定

const bgSyncPlugin = new BackgroundSyncPlugin('itscm-offline-queue', {
    maxRetentionTime: 24 * 60, // 24時間保持
    onSync: async ({ queue }) => {
        let entry;
        while ((entry = await queue.shiftRequest())) {
            try {
                const response = await fetch(entry.request.clone());
                if (!response.ok) {
                    // サーバーエラーの場合はキューに戻す
                    if (response.status >= 500) {
                        await queue.unshiftRequest(entry);
                        throw new Error(`Server error: ${response.status}`);
                    }
                    // 409 Conflict の場合はコンフリクト解決
                    if (response.status === 409) {
                        await handleConflict(entry, response);
                    }
                }
            } catch (error) {
                await queue.unshiftRequest(entry);
                throw error;
            }
        }
    },
});

// 書き込みAPI (POST/PUT/PATCH/DELETE) にBackground Syncを適用
registerRoute(
    ({ request }) => ['POST', 'PUT', 'PATCH', 'DELETE'].includes(request.method),
    new NetworkOnly({
        plugins: [bgSyncPlugin],
    }),
    'POST' // methodパラメータ
);
```

### 5.3 同期フロー

```
オフライン操作
  │
  │ ① ユーザーがフォーム送信（例: インシデント登録）
  ▼
フロントエンド
  │
  │ ② ネットワーク判定: オフライン
  │ ③ IndexedDB (offlineOperations) に操作を保存
  │ ④ ユーザーに「オフライン保存しました」と通知
  │ ⑤ UIを楽観的に更新（Optimistic Update）
  ▼
オンライン復帰
  │
  │ ⑥ navigator.onLine イベント検知
  │ ⑦ Background Sync API が発火
  ▼
Service Worker
  │
  │ ⑧ offlineOperationsキューからリクエストを順次取得
  │ ⑨ 各リクエストをサーバーに送信
  │
  ├── 成功 ──▶ ⑩ キューから削除、キャッシュ更新
  ├── 409 ──▶ ⑪ コンフリクト解決ロジック実行
  └── 500 ──▶ ⑫ リトライキューに戻す（最大5回）
  │
  │ ⑬ 同期完了通知をフロントエンドに送信
  ▼
フロントエンド
  │
  │ ⑭ 「データが同期されました」と通知
  │ ⑮ 最新データでUIを更新
  ▼
同期完了
```

### 5.4 コンフリクト解決

| コンフリクト種別 | 解決方式 | 説明 |
|----------------|---------|------|
| インシデント状態更新 | サーバー優先 | 他のユーザーの更新が優先される。ユーザーに差分を通知 |
| インシデント新規登録 | クライアント優先 | オフラインで登録した内容を維持 |
| RTO記録更新 | マージ | タイムスタンプが新しい方を採用 |
| タイムラインエントリ追加 | 両方保持 | オフライン中の追加分も含めて時系列で統合 |

```typescript
// conflictResolver.ts
async function resolveConflict(
    operation: OfflineOperation,
    serverResponse: Response
): Promise<ConflictResolution> {
    const serverData = await serverResponse.json();

    switch (operation.conflictResolution) {
        case 'server_wins':
            // サーバーデータでローカルキャッシュを更新
            await updateLocalCache(operation.url, serverData);
            return { resolved: true, strategy: 'server_wins' };

        case 'client_wins':
            // クライアントデータを強制送信（If-Matchなし）
            await forcePush(operation);
            return { resolved: true, strategy: 'client_wins' };

        case 'manual':
            // ユーザーに通知してマニュアル解決を依頼
            await notifyUser({
                type: 'conflict',
                message: 'データの競合が発生しました。確認してください。',
                operation,
                serverData,
            });
            return { resolved: false, strategy: 'manual' };
    }
}
```

---

## 6. 重要資料のプリキャッシュ

### 6.1 プリキャッシュ対象

| カテゴリ | 対象データ | プリキャッシュタイミング | 優先度 |
|---------|-----------|---------------------|--------|
| アプリシェル | HTML、CSS、JS、フォント、アイコン | Service Workerインストール時 | 最高 |
| BCP手順書 | 全システムの復旧手順 | ログイン後 + 定期更新(4時間) | 高 |
| 緊急連絡先 | 全ベンダー連絡先 | ログイン後 + 定期更新(4時間) | 高 |
| ITシステム情報 | 全BCP対象システム一覧 | ログイン後 + 定期更新(4時間) | 高 |
| BCPシナリオ | 全シナリオ概要 | ログイン後 + 定期更新(12時間) | 中 |
| 直近のインシデント | アクティブインシデント | ログイン後 + 定期更新(1時間) | 中 |

### 6.2 プリキャッシュ実装

```typescript
// hooks/usePreCache.ts
export function usePreCache() {
    const { isAuthenticated } = useAuth();

    useEffect(() => {
        if (!isAuthenticated) return;

        const preCacheAll = async () => {
            // Phase 1: 最重要データ（並列取得）
            await Promise.all([
                preCacheSystems(),
                preCacheVendors(),
                preCacheProceduresForAllSystems(),
            ]);

            // Phase 2: 中優先度データ
            await Promise.all([
                preCacheScenarios(),
                preCacheActiveIncidents(),
            ]);
        };

        // 初回キャッシュ
        preCacheAll();

        // 定期更新（4時間ごと）
        const intervalId = setInterval(preCacheAll, 4 * 60 * 60 * 1000);

        return () => clearInterval(intervalId);
    }, [isAuthenticated]);
}

async function preCacheSystems() {
    const response = await fetch('/api/v1/systems?limit=100');
    const data = await response.json();

    const db = new OfflineDatabase();
    for (const system of data.data) {
        await db.cachedSystems.put({
            id: system.id,
            data: system,
            cachedAt: new Date(),
            version: 1,
        });
    }
}

async function preCacheProceduresForAllSystems() {
    const db = new OfflineDatabase();
    const systems = await db.cachedSystems.toArray();

    for (const system of systems) {
        const response = await fetch(`/api/v1/systems/${system.id}/procedures`);
        const data = await response.json();

        for (const procedure of data.data) {
            await db.cachedProcedures.put({
                id: procedure.id,
                systemId: system.id,
                data: procedure,
                cachedAt: new Date(),
                version: 1,
            });
        }
    }
}
```

### 6.3 ストレージ容量管理

| 項目 | 上限目安 | 説明 |
|------|---------|------|
| プリキャッシュ（アプリシェル） | 5 MB | JS/CSS/フォント/アイコン |
| BCP重要資料キャッシュ | 50 MB | 手順書、連絡先、システム情報 |
| APIデータキャッシュ | 20 MB | 一般APIレスポンス |
| IndexedDB | 50 MB | オフラインデータ + 保留操作 |
| **合計** | **125 MB** | ブラウザストレージの約10%以下 |

```typescript
// ストレージ容量チェック
async function checkStorageQuota(): Promise<StorageInfo> {
    if (navigator.storage && navigator.storage.estimate) {
        const estimate = await navigator.storage.estimate();
        return {
            usage: estimate.usage ?? 0,
            quota: estimate.quota ?? 0,
            usagePercentage: ((estimate.usage ?? 0) / (estimate.quota ?? 1)) * 100,
        };
    }
    return { usage: 0, quota: 0, usagePercentage: 0 };
}

// ストレージ永続化リクエスト
async function requestPersistentStorage(): Promise<boolean> {
    if (navigator.storage && navigator.storage.persist) {
        return await navigator.storage.persist();
    }
    return false;
}
```

### 6.4 キャッシュ更新通知

BCP重要資料が更新された場合、以下の方法でキャッシュの更新をユーザーに通知する。

```
サーバーでBCP資料更新
  │
  │ ① WebSocket経由で更新通知
  ▼
フロントエンド（オンライン時）
  │
  │ ② 対象データのキャッシュを更新
  │ ③ 「BCP手順書が更新されました」バナー表示
  ▼
Service Worker
  │
  │ ④ Cache API + IndexedDB のデータを更新
  ▼
次回オフライン時に最新データが利用可能
```

---

## 7. オフラインUI設計

### 7.1 オフライン状態表示

```
オンライン時:
┌──────────────────────────────────────────┐
│ [通常のヘッダー]                          │
├──────────────────────────────────────────┤

オフライン時:
┌──────────────────────────────────────────┐
│ ⚠ オフラインモード - キャッシュデータを      │
│   表示しています。一部機能が制限されます。    │
├──────────────────────────────────────────┤
│ [通常のヘッダー]                          │
├──────────────────────────────────────────┤

同期中:
┌──────────────────────────────────────────┐
│ 🔄 データを同期中... (3/5)               │
├──────────────────────────────────────────┤
```

### 7.2 機能別オフライン対応

| 機能 | オンライン | オフライン | 表示 |
|------|-----------|-----------|------|
| RTOダッシュボード閲覧 | リアルタイム | 最終キャッシュデータ | キャッシュ時刻表示 |
| システム一覧/詳細 | 最新データ | キャッシュデータ | 通常表示 + オフラインバッジ |
| 復旧手順閲覧 | 最新データ | キャッシュデータ | 通常表示 |
| ベンダー連絡先 | 最新データ | キャッシュデータ | 通常表示 |
| インシデント登録 | 即座に登録 | ローカル保存 + 後で同期 | 「オフライン保存済」表示 |
| インシデント更新 | 即座に更新 | ローカル保存 + 後で同期 | 「オフライン保存済」表示 |
| 演習ライブ実施 | 利用可能 | 利用不可 | 「オンラインが必要です」表示 |
| WebSocket（RTO更新） | リアルタイム | 利用不可 | 自動再接続（オンライン復帰時） |
| 検索 | サーバー検索 | ローカル検索（IndexedDB） | 「オフライン検索」バッジ |
| フィルタリング | サーバー実行 | ローカル実行 | 通常表示 |

### 7.3 オフライン操作キュー表示

```
┌──────────────────────────────────────────┐
│ 保留中の操作 (3件)                        │
├──────────────────────────────────────────┤
│ 🕐 14:30 インシデント「サーバー障害」登録   │
│ 🕐 14:35 INC-2026-0042 ステータス更新     │
│ 🕐 14:40 タイムラインエントリ追加          │
├──────────────────────────────────────────┤
│ [オンライン復帰時に自動同期されます]        │
└──────────────────────────────────────────┘
```

---

## 8. セキュリティ考慮事項

### 8.1 キャッシュデータの保護

| 対策 | 説明 |
|------|------|
| ストレージ永続化 | `navigator.storage.persist()` でブラウザによる自動削除を防止 |
| セッション管理 | ログアウト時にキャッシュ・IndexedDBのセンシティブデータを削除 |
| 暗号化 | IndexedDB内のセンシティブデータはWeb Crypto APIで暗号化 |
| アクセス制御 | Service Workerのスコープを `/` に限定 |
| CSP設定 | Content-Security-Policyヘッダーで外部スクリプト読込を制限 |

### 8.2 ログアウト時のクリーンアップ

```typescript
async function cleanupOnLogout(): Promise<void> {
    // 1. IndexedDB内のセンシティブデータを削除
    const db = new OfflineDatabase();
    await db.cachedIncidents.clear();
    await db.offlineOperations.clear();
    // cachedSystems, cachedProcedures, cachedVendors は非機密のため保持可能

    // 2. APIデータキャッシュを削除
    const apiCache = await caches.open('itscm-api-data');
    const apiKeys = await apiCache.keys();
    await Promise.all(apiKeys.map(key => apiCache.delete(key)));

    // 3. 認証トークンを削除
    // HttpOnly Cookieはサーバーサイドで無効化
    // メモリ上のアクセストークンはZustandストアのリセットで消去

    // 4. WebSocket接続を閉じる
    // WebSocketProviderがクリーンアップ
}
```

### 8.3 オフライン時の認証

| 状況 | 対応 |
|------|------|
| オフライン中のアクセストークン期限切れ | ローカルキャッシュへのアクセスは許可。書き込み操作はキューに保存。オンライン復帰時にトークンリフレッシュ後に同期 |
| オフライン中のリフレッシュトークン期限切れ | キャッシュデータの読取は許可。オンライン復帰時に再ログインを要求 |
| 共有端末でのオフラインアクセス | ログアウト時の完全クリーンアップを徹底。端末ロック推奨 |

---

## 9. テスト戦略

### 9.1 PWAテスト項目

| テスト項目 | テスト方法 | 確認内容 |
|-----------|-----------|---------|
| Service Worker登録 | 自動テスト (Playwright) | 正常に登録・アクティベートされること |
| オフラインアクセス | 手動 + 自動テスト | ネットワーク切断後もBCP資料が閲覧可能であること |
| プリキャッシュ | 自動テスト | ログイン後にBCP重要資料がキャッシュされること |
| バックグラウンド同期 | 手動テスト | オフライン操作がオンライン復帰後に同期されること |
| コンフリクト解決 | 自動テスト | 競合時に正しい解決が行われること |
| PWAインストール | 手動テスト | 各ブラウザでインストール可能であること |
| マニフェスト | Lighthouse | PWAマニフェストの検証 |
| パフォーマンス | Lighthouse | PWAパフォーマンススコア90以上 |
| ストレージ容量 | 手動テスト | 125MB以内に収まること |
| キャッシュ更新 | 自動テスト | 新バージョンデプロイ後にキャッシュが更新されること |

### 9.2 災害シミュレーションテスト

| シナリオ | テスト手順 | 期待結果 |
|---------|-----------|---------|
| 完全ネットワーク断 | 1. 正常稼働中にネットワークを切断 2. BCP手順書にアクセス | キャッシュから表示される |
| 部分ネットワーク障害 | 1. APIサーバーを停止 2. 画面操作 | キャッシュ + オフラインバナー |
| 長時間オフライン後の同期 | 1. オフラインで複数操作 2. 8時間後にオンライン復帰 | 全操作が正しく同期される |
| 同時編集コンフリクト | 1. 端末Aでオフライン編集 2. 端末Bでオンライン編集 3. 端末Aオンライン復帰 | コンフリクト解決が正しく動作 |

---

## 10. 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-03-27 | - | 初版作成 |
