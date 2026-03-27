# フロントエンド設計書 (Frontend Design)

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-DES-FE-004 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 分類 | 設計文書 |
| 準拠規格 | ISO20000 ITSCM / ISO27001 / NIST CSF RECOVER RC |

---

## 目次

1. [概要](#1-概要)
2. [技術スタック](#2-技術スタック)
3. [ページ構成](#3-ページ構成)
4. [ルーティング設計](#4-ルーティング設計)
5. [コンポーネント設計](#5-コンポーネント設計)
6. [状態管理](#6-状態管理)
7. [レスポンシブ設計](#7-レスポンシブ設計)
8. [パフォーマンス設計](#8-パフォーマンス設計)
9. [アクセシビリティ](#9-アクセシビリティ)
10. [変更履歴](#10-変更履歴)

---

## 1. 概要

### 1.1 設計方針

| 方針 | 説明 |
|------|------|
| オフラインファースト | PWA対応により、ネットワーク障害時でもBCP重要資料にアクセス可能 |
| リアルタイム性 | WebSocketによるRTOダッシュボードのリアルタイム更新 |
| レスポンシブ | PC、タブレット、スマートフォン全対応 |
| アクセシビリティ | WCAG 2.1 AA準拠 |
| 高速表示 | SSR + ISR + キャッシュ最適化によりLCP 2.5秒以内 |
| セキュア | XSS/CSRF対策、CSP設定、認証トークンの安全な管理 |

### 1.2 対応ブラウザ

| ブラウザ | 最低バージョン |
|---------|-------------|
| Google Chrome | 最新2バージョン |
| Microsoft Edge | 最新2バージョン |
| Mozilla Firefox | 最新2バージョン |
| Safari (macOS/iOS) | 最新2バージョン |

---

## 2. 技術スタック

| カテゴリ | 技術 | バージョン | 用途 |
|---------|------|-----------|------|
| フレームワーク | Next.js | 14.x | SSR/SSG/ISR、ルーティング |
| 言語 | TypeScript | 5.x | 型安全な開発 |
| UIライブラリ | React | 18.x | UIコンポーネント |
| UIコンポーネント | shadcn/ui | 最新 | デザインシステム基盤 |
| スタイリング | Tailwind CSS | 3.x | ユーティリティファーストCSS |
| 状態管理 | Zustand | 4.x | グローバル状態管理 |
| サーバー状態 | TanStack Query | 5.x | APIデータフェッチ・キャッシュ |
| フォーム | React Hook Form + Zod | 最新 | フォーム管理・バリデーション |
| WebSocket | 自前実装 (reconnecting) | - | リアルタイム通信 |
| チャート | Recharts | 2.x | ダッシュボードグラフ |
| テーブル | TanStack Table | 8.x | データテーブル |
| 日付 | date-fns | 3.x | 日付操作 |
| アイコン | Lucide React | 最新 | アイコンセット |
| PWA | next-pwa + Workbox | 最新 | オフライン対応 |
| テスト | Vitest + Testing Library + Playwright | 最新 | ユニット/E2Eテスト |
| リンター | ESLint + Prettier | 最新 | コード品質 |

---

## 3. ページ構成

### 3.1 ページ一覧

| ページ | パス | 説明 | 認証 | オフライン対応 |
|--------|------|------|------|-------------|
| ログイン | /login | Entra ID SSO ログイン | 不要 | - |
| 認証コールバック | /auth/callback | Entra ID認証コールバック | 不要 | - |
| ダッシュボード | / | RTOダッシュボード（メイン画面） | 必要 | 読取のみ |
| システム一覧 | /systems | ITシステム一覧 | 必要 | 読取のみ |
| システム詳細 | /systems/[id] | ITシステム詳細・復旧手順 | 必要 | 読取のみ |
| システム登録/編集 | /systems/new, /systems/[id]/edit | ITシステム登録・編集 | 必要 | - |
| インシデント一覧 | /incidents | インシデント一覧 | 必要 | 読取のみ |
| インシデント詳細 | /incidents/[id] | インシデント詳細・タイムライン | 必要 | 読取のみ |
| インシデント登録 | /incidents/new | インシデント登録 | 必要 | オフライン登録可 |
| インシデント戦況室 | /incidents/[id]/war-room | インシデント戦況室（リアルタイム） | 必要 | - |
| 演習一覧 | /exercises | BCP演習一覧 | 必要 | 読取のみ |
| 演習詳細 | /exercises/[id] | 演習詳細・結果 | 必要 | 読取のみ |
| 演習実施 | /exercises/[id]/live | 演習ライブ実施画面 | 必要 | - |
| 演習作成 | /exercises/new | 演習作成 | 必要 | - |
| シナリオ一覧 | /scenarios | BCPシナリオ一覧 | 必要 | 読取のみ |
| シナリオ詳細 | /scenarios/[id] | シナリオ詳細 | 必要 | 読取のみ |
| シナリオ作成/編集 | /scenarios/new, /scenarios/[id]/edit | シナリオ作成・編集 | 必要 | - |
| ベンダー一覧 | /vendors | ベンダー連絡先一覧 | 必要 | 読取のみ |
| ベンダー詳細 | /vendors/[id] | ベンダー詳細 | 必要 | 読取のみ |
| 復旧手順一覧 | /procedures | 全復旧手順一覧 | 必要 | 読取のみ |
| ユーザー管理 | /admin/users | ユーザー管理 | 管理者のみ | - |
| 監査ログ | /admin/audit-logs | 監査ログ閲覧 | 管理者のみ | - |
| 設定 | /settings | 個人設定・通知設定 | 必要 | - |
| コンプライアンス | /compliance | コンプライアンスダッシュボード | 管理者のみ | - |

### 3.2 画面遷移図

```
ログイン ─────────────────────────────────┐
  │                                        │
  │ 認証成功                                │ 未認証リダイレクト
  ▼                                        │
┌──────────────────────────────────────────┤
│           ダッシュボード (/)               │
│  ┌────────────────────────────────────┐  │
│  │ RTOサマリー | アクティブインシデント   │  │
│  │ 演習スケジュール | コンプライアンス    │  │
│  └──┬──────┬──────┬──────┬───────────┘  │
│     │      │      │      │               │
│     ▼      ▼      ▼      ▼               │
│  システム インシデント 演習  シナリオ        │
│  一覧     一覧     一覧   一覧            │
│   │        │        │      │              │
│   ▼        ▼        ▼      ▼              │
│  詳細     詳細      詳細   詳細            │
│   │        │        │                     │
│   │        ▼        ▼                     │
│   │     戦況室    ライブ実施               │
│   │                                      │
│   ├──▶ ベンダー一覧 ──▶ ベンダー詳細      │
│   └──▶ 復旧手順一覧                      │
│                                          │
│  ┌─────────── 管理メニュー ──────────────┐ │
│  │ ユーザー管理 | 監査ログ | 設定         │ │
│  │ コンプライアンス                       │ │
│  └────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

---

## 4. ルーティング設計

### 4.1 Next.js App Router 構成

```
app/
├── (auth)/
│   ├── login/
│   │   └── page.tsx
│   └── auth/
│       └── callback/
│           └── page.tsx
├── (dashboard)/
│   ├── layout.tsx              ← 認証済みレイアウト（サイドバー・ヘッダー）
│   ├── page.tsx                ← ダッシュボード
│   ├── systems/
│   │   ├── page.tsx            ← システム一覧
│   │   ├── new/
│   │   │   └── page.tsx        ← システム登録
│   │   └── [id]/
│   │       ├── page.tsx        ← システム詳細
│   │       └── edit/
│   │           └── page.tsx    ← システム編集
│   ├── incidents/
│   │   ├── page.tsx            ← インシデント一覧
│   │   ├── new/
│   │   │   └── page.tsx        ← インシデント登録
│   │   └── [id]/
│   │       ├── page.tsx        ← インシデント詳細
│   │       └── war-room/
│   │           └── page.tsx    ← 戦況室
│   ├── exercises/
│   │   ├── page.tsx            ← 演習一覧
│   │   ├── new/
│   │   │   └── page.tsx        ← 演習作成
│   │   └── [id]/
│   │       ├── page.tsx        ← 演習詳細
│   │       └── live/
│   │           └── page.tsx    ← ライブ実施
│   ├── scenarios/
│   │   ├── page.tsx
│   │   ├── new/
│   │   │   └── page.tsx
│   │   └── [id]/
│   │       ├── page.tsx
│   │       └── edit/
│   │           └── page.tsx
│   ├── vendors/
│   │   ├── page.tsx
│   │   └── [id]/
│   │       └── page.tsx
│   ├── procedures/
│   │   └── page.tsx
│   ├── admin/
│   │   ├── users/
│   │   │   └── page.tsx
│   │   └── audit-logs/
│   │       └── page.tsx
│   ├── compliance/
│   │   └── page.tsx
│   └── settings/
│       └── page.tsx
├── api/                        ← Next.js API Routes (BFF)
│   └── ...
├── layout.tsx                  ← ルートレイアウト
├── not-found.tsx
├── error.tsx
└── loading.tsx
```

### 4.2 ミドルウェア

```typescript
// middleware.ts
// 認証チェック、ロールベースアクセス制御、オフラインフォールバック

const publicPaths = ['/login', '/auth/callback'];
const adminPaths = ['/admin', '/compliance'];

export function middleware(request: NextRequest) {
    // 1. 公開パスはスキップ
    // 2. 認証トークン検証
    // 3. 管理者パスはロール検証
    // 4. 未認証 → /login にリダイレクト
}
```

---

## 5. コンポーネント設計

### 5.1 コンポーネントアーキテクチャ

```
components/
├── ui/                         ← shadcn/ui ベースコンポーネント
│   ├── button.tsx
│   ├── card.tsx
│   ├── dialog.tsx
│   ├── dropdown-menu.tsx
│   ├── input.tsx
│   ├── select.tsx
│   ├── table.tsx
│   ├── tabs.tsx
│   ├── badge.tsx
│   ├── toast.tsx
│   ├── skeleton.tsx
│   └── ...
├── layout/                     ← レイアウトコンポーネント
│   ├── Header.tsx              ← ヘッダー（検索、通知、ユーザーメニュー）
│   ├── Sidebar.tsx             ← サイドバーナビゲーション
│   ├── Footer.tsx              ← フッター
│   ├── MobileNav.tsx           ← モバイルナビゲーション
│   └── BreadcrumbNav.tsx       ← パンくずナビゲーション
├── dashboard/                  ← ダッシュボードコンポーネント
│   ├── RtoOverviewCard.tsx     ← RTO概要カード
│   ├── RtoStatusChart.tsx      ← RTOステータスチャート（ドーナツ）
│   ├── RtoTierBreakdown.tsx    ← ティア別内訳
│   ├── ActiveIncidentBanner.tsx ← アクティブインシデントバナー
│   ├── SystemHealthGrid.tsx    ← システムヘルスグリッド
│   ├── UpcomingExercises.tsx   ← 直近の演習スケジュール
│   └── ComplianceWidget.tsx    ← コンプライアンスウィジェット
├── incidents/                  ← インシデント関連コンポーネント
│   ├── IncidentList.tsx        ← インシデント一覧テーブル
│   ├── IncidentCard.tsx        ← インシデントカード
│   ├── IncidentForm.tsx        ← インシデント登録/編集フォーム
│   ├── IncidentTimeline.tsx    ← タイムライン表示
│   ├── IncidentWarRoom.tsx     ← 戦況室メインコンポーネント
│   ├── BcpActivationDialog.tsx ← BCP発動ダイアログ
│   ├── EscalationPanel.tsx     ← エスカレーションパネル
│   ├── AffectedSystemsTable.tsx ← 影響システムテーブル
│   └── SeverityBadge.tsx       ← 重大度バッジ
├── exercises/                  ← 演習関連コンポーネント
│   ├── ExerciseList.tsx        ← 演習一覧
│   ├── ExerciseForm.tsx        ← 演習作成フォーム
│   ├── ExerciseLivePanel.tsx   ← ライブ実施パネル
│   ├── InjectionController.tsx ← インジェクションコントローラー
│   ├── RtoRecordTable.tsx      ← RTO記録テーブル
│   ├── ExerciseScoreCard.tsx   ← スコアカード
│   └── ExerciseReport.tsx      ← レポート表示
├── systems/                    ← システム関連コンポーネント
│   ├── SystemList.tsx          ← システム一覧
│   ├── SystemForm.tsx          ← システム登録/編集フォーム
│   ├── SystemDetailCard.tsx    ← システム詳細カード
│   ├── RecoveryProcedureList.tsx ← 復旧手順一覧
│   ├── DependencyGraph.tsx     ← 依存関係グラフ
│   ├── RtoHistoryChart.tsx     ← RTO履歴チャート
│   └── CriticalityBadge.tsx    ← 重要度バッジ
├── rto/                        ← RTO関連コンポーネント
│   ├── RtoStatusIndicator.tsx  ← RTOステータスインジケーター
│   ├── RtoProgressBar.tsx      ← RTO進捗バー
│   ├── RtoCountdown.tsx        ← RTOカウントダウンタイマー
│   └── RtoColorLegend.tsx      ← 色凡例
├── common/                     ← 共通コンポーネント
│   ├── DataTable.tsx           ← 汎用データテーブル
│   ├── SearchInput.tsx         ← 検索入力
│   ├── FilterPanel.tsx         ← フィルターパネル
│   ├── ConfirmDialog.tsx       ← 確認ダイアログ
│   ├── EmptyState.tsx          ← 空状態表示
│   ├── ErrorBoundary.tsx       ← エラーバウンダリ
│   ├── LoadingSpinner.tsx      ← ローディングスピナー
│   ├── OfflineBanner.tsx       ← オフライン通知バナー
│   ├── NotificationBell.tsx    ← 通知ベル
│   └── UserAvatar.tsx          ← ユーザーアバター
└── providers/                  ← プロバイダーコンポーネント
    ├── AuthProvider.tsx        ← 認証プロバイダー
    ├── ThemeProvider.tsx       ← テーマプロバイダー
    ├── WebSocketProvider.tsx   ← WebSocketプロバイダー
    ├── OfflineProvider.tsx     ← オフライン状態プロバイダー
    └── QueryProvider.tsx       ← TanStack Queryプロバイダー
```

### 5.2 主要コンポーネント仕様

#### 5.2.1 RtoStatusIndicator

RTOの状態を色付きインジケーターで表示するコンポーネント。

```typescript
interface RtoStatusIndicatorProps {
    status: 'on_track' | 'at_risk' | 'overdue' | 'recovered' | 'not_started';
    rtoTargetMinutes: number;
    elapsedMinutes?: number;
    showLabel?: boolean;
    showCountdown?: boolean;
    size?: 'sm' | 'md' | 'lg';
}
```

| ステータス | 色 | アイコン | 説明 |
|-----------|-----|---------|------|
| on_track | 緑 (#22C55E) | CheckCircle | RTO目標内で順調 |
| at_risk | 黄 (#EAB308) | AlertTriangle | RTO目標の80%以上経過 |
| overdue | 赤 (#EF4444) | XCircle | RTO目標を超過 |
| recovered | 青 (#3B82F6) | CheckCircle2 | 復旧完了 |
| not_started | グレー (#6B7280) | Clock | 未開始 |

#### 5.2.2 IncidentWarRoom

インシデント戦況室のメインコンポーネント。リアルタイムで情報を更新する。

```typescript
interface IncidentWarRoomProps {
    incidentId: string;
}
```

内部構成:
- 左パネル: インシデント概要 + タイムライン
- 中央パネル: 影響システムRTOダッシュボード
- 右パネル: エスカレーション状態 + 通信ログ
- 下部バー: アクションボタン（BCP発動、エスカレーション、ステータス変更）

#### 5.2.3 InjectionController

テーブルトップ演習のインジェクションコントローラー。

```typescript
interface InjectionControllerProps {
    exerciseId: string;
    scenario: BcpScenario;
    currentStep: number;
    onInject: (step: number) => void;
}
```

機能:
- シナリオステップの一覧表示
- 現在のステップのハイライト
- インジェクション実行ボタン
- タイマー表示（インジェクション間隔）
- 参加者の反応記録欄

---

## 6. 状態管理

### 6.1 状態管理戦略

| 状態種別 | 管理方法 | 用途 |
|---------|---------|------|
| サーバー状態 | TanStack Query | API データのフェッチ、キャッシュ、同期 |
| クライアント状態 | Zustand | UI状態、ユーザー設定、一時データ |
| フォーム状態 | React Hook Form | フォーム入力値、バリデーション |
| URL状態 | Next.js Router / useSearchParams | フィルター、ページネーション、検索クエリ |
| リアルタイム状態 | WebSocket + Zustand | RTOリアルタイム更新、インシデント通知 |
| オフライン状態 | IndexedDB (Dexie.js) | オフラインデータ、保留操作キュー |

### 6.2 Zustand ストア設計

```typescript
// stores/authStore.ts - 認証ストア
interface AuthState {
    user: User | null;
    accessToken: string | null;
    isAuthenticated: boolean;
    login: (token: string, user: User) => void;
    logout: () => void;
    refreshToken: () => Promise<void>;
}

// stores/incidentStore.ts - インシデントストア
interface IncidentState {
    activeIncidents: ActiveIncident[];
    selectedIncidentId: string | null;
    bcpActivationLevel: BcpActivationLevel;
    setActiveIncidents: (incidents: ActiveIncident[]) => void;
    selectIncident: (id: string) => void;
    updateIncidentStatus: (id: string, status: IncidentStatus) => void;
}

// stores/rtoStore.ts - RTOリアルタイムストア
interface RtoState {
    rtoOverview: RtoOverview | null;
    systemRtoMap: Map<string, RtoStatus>;
    updateRtoStatus: (systemId: string, status: RtoStatus) => void;
    setOverview: (overview: RtoOverview) => void;
}

// stores/exerciseStore.ts - 演習ストア
interface ExerciseState {
    activeExercise: Exercise | null;
    currentInjectionStep: number;
    rtoRecords: ExerciseRtoRecord[];
    setActiveExercise: (exercise: Exercise) => void;
    advanceInjection: (step: number) => void;
    updateRtoRecord: (record: ExerciseRtoRecord) => void;
}

// stores/uiStore.ts - UI状態ストア
interface UiState {
    sidebarOpen: boolean;
    theme: 'light' | 'dark' | 'system';
    isOnline: boolean;
    notifications: Notification[];
    toggleSidebar: () => void;
    setOnlineStatus: (online: boolean) => void;
    addNotification: (notification: Notification) => void;
    dismissNotification: (id: string) => void;
}

// stores/offlineStore.ts - オフラインストア
interface OfflineState {
    pendingOperations: OfflineOperation[];
    addOperation: (op: OfflineOperation) => void;
    removeSyncedOperation: (id: string) => void;
    syncAll: () => Promise<void>;
}
```

### 6.3 TanStack Query キー設計

```typescript
// queryKeys.ts
export const queryKeys = {
    systems: {
        all: ['systems'] as const,
        list: (filters: SystemFilters) => ['systems', 'list', filters] as const,
        detail: (id: string) => ['systems', 'detail', id] as const,
        procedures: (id: string) => ['systems', id, 'procedures'] as const,
        dependencies: (id: string) => ['systems', id, 'dependencies'] as const,
        rtoHistory: (id: string) => ['systems', id, 'rto-history'] as const,
    },
    incidents: {
        all: ['incidents'] as const,
        list: (filters: IncidentFilters) => ['incidents', 'list', filters] as const,
        detail: (id: string) => ['incidents', 'detail', id] as const,
        timeline: (id: string) => ['incidents', id, 'timeline'] as const,
        affectedSystems: (id: string) => ['incidents', id, 'affected-systems'] as const,
    },
    exercises: {
        all: ['exercises'] as const,
        list: (filters: ExerciseFilters) => ['exercises', 'list', filters] as const,
        detail: (id: string) => ['exercises', 'detail', id] as const,
        rtoRecords: (id: string) => ['exercises', id, 'rto-records'] as const,
    },
    scenarios: {
        all: ['scenarios'] as const,
        list: (filters: ScenarioFilters) => ['scenarios', 'list', filters] as const,
        detail: (id: string) => ['scenarios', 'detail', id] as const,
    },
    vendors: {
        all: ['vendors'] as const,
        list: (filters: VendorFilters) => ['vendors', 'list', filters] as const,
        detail: (id: string) => ['vendors', 'detail', id] as const,
    },
    dashboard: {
        rtoOverview: ['dashboard', 'rto-overview'] as const,
        activeIncidents: ['dashboard', 'active-incidents'] as const,
        exerciseStats: ['dashboard', 'exercise-stats'] as const,
        compliance: ['dashboard', 'compliance'] as const,
    },
} as const;
```

### 6.4 キャッシュ戦略

| データ種別 | staleTime | gcTime | refetchOnWindowFocus |
|-----------|-----------|--------|---------------------|
| ダッシュボードRTO | 10秒 | 5分 | true |
| アクティブインシデント | 30秒 | 5分 | true |
| システム一覧 | 5分 | 30分 | true |
| システム詳細 | 5分 | 30分 | true |
| 演習一覧 | 5分 | 30分 | true |
| シナリオ一覧 | 10分 | 60分 | false |
| ベンダー一覧 | 10分 | 60分 | false |
| 復旧手順 | 5分 | 30分 | true |
| 監査ログ | 1分 | 5分 | true |

---

## 7. レスポンシブ設計

### 7.1 ブレークポイント

| 名前 | 幅 | 対象デバイス |
|------|-----|------------|
| sm | 640px | スマートフォン（横向き） |
| md | 768px | タブレット（縦向き） |
| lg | 1024px | タブレット（横向き）/ ノートPC |
| xl | 1280px | デスクトップ |
| 2xl | 1536px | ワイドスクリーン |

### 7.2 レイアウト別対応

#### デスクトップ (xl以上)

```
┌──────────────────────────────────────────────┐
│ ヘッダー（ロゴ / 検索 / 通知 / ユーザー）      │
├─────────┬────────────────────────────────────┤
│         │                                    │
│ サイド   │          メインコンテンツ            │
│ バー     │                                    │
│ (展開)   │                                    │
│         │                                    │
│         │                                    │
│         │                                    │
├─────────┴────────────────────────────────────┤
│ フッター                                      │
└──────────────────────────────────────────────┘
```

#### タブレット (md - lg)

```
┌──────────────────────────────────┐
│ ヘッダー（ハンバーガー / ロゴ）    │
├──────────────────────────────────┤
│                                  │
│       メインコンテンツ             │
│    （サイドバーはオーバーレイ）     │
│                                  │
│                                  │
├──────────────────────────────────┤
│ フッター                          │
└──────────────────────────────────┘
```

#### スマートフォン (sm以下)

```
┌────────────────────────┐
│ ヘッダー（最小限）      │
├────────────────────────┤
│                        │
│    メインコンテンツ     │
│   （1カラム表示）       │
│                        │
│                        │
├────────────────────────┤
│ ボトムナビゲーション    │
│ (ダッシュ|インシデント  │
│  |演習|システム|メニュー)│
└────────────────────────┘
```

### 7.3 ダッシュボードのレスポンシブ対応

| コンポーネント | デスクトップ | タブレット | スマートフォン |
|-------------|-----------|---------|------------|
| RTOサマリー | 横並び5カード | 横並び3+2カード | 縦並びスクロール |
| RTOチャート | ドーナツ + 棒グラフ並列 | 縦積み | 縦積み（小型） |
| インシデントバナー | フル幅帯状 | フル幅帯状 | カード型 |
| システムグリッド | 4列グリッド | 2列グリッド | 1列リスト |
| 演習スケジュール | カレンダー表示 | リスト表示 | リスト表示 |

---

## 8. パフォーマンス設計

### 8.1 レンダリング戦略

| ページ | レンダリング方式 | 理由 |
|--------|---------------|------|
| ダッシュボード | SSR + Client-side hydration | リアルタイムデータ + SEO不要 |
| システム一覧 | SSR | 初期表示速度重視 |
| システム詳細 | SSR | 初期表示速度重視 |
| インシデント一覧 | SSR | 最新データ表示重視 |
| インシデント戦況室 | CSR | リアルタイム性最優先 |
| 演習ライブ | CSR | リアルタイム性最優先 |
| シナリオ一覧 | ISR (60秒) | 更新頻度低 |
| ベンダー一覧 | ISR (300秒) | 更新頻度低 |

### 8.2 最適化施策

| 施策 | 実装方法 | 効果 |
|------|---------|------|
| コード分割 | Next.js dynamic import | 初期バンドルサイズ削減 |
| 画像最適化 | Next.js Image | 自動リサイズ・WebP変換 |
| フォント最適化 | next/font | FLOUTの防止 |
| プリフェッチ | Next.js Link prefetch | ナビゲーション高速化 |
| 仮想スクロール | TanStack Virtual | 大量データ表示のパフォーマンス |
| メモ化 | React.memo, useMemo | 不要な再レンダリング防止 |
| バンドル分析 | @next/bundle-analyzer | バンドルサイズの監視 |

### 8.3 パフォーマンス目標（Core Web Vitals）

| 指標 | 目標値 |
|------|--------|
| LCP (Largest Contentful Paint) | 2.5秒以内 |
| FID (First Input Delay) | 100ms以内 |
| CLS (Cumulative Layout Shift) | 0.1以下 |
| INP (Interaction to Next Paint) | 200ms以内 |
| TTFB (Time to First Byte) | 800ms以内 |

---

## 9. アクセシビリティ

### 9.1 準拠基準

WCAG 2.1 AA準拠を目標とする。

### 9.2 主要対応項目

| 項目 | 実装方法 |
|------|---------|
| キーボードナビゲーション | 全操作がキーボードのみで可能 |
| スクリーンリーダー | 適切なaria-label、aria-live、role属性 |
| 色のコントラスト | WCAG AA基準（4.5:1以上） |
| RTO色分け | 色だけでなくアイコン+テキストラベルで判別可能 |
| フォーカス管理 | 可視的フォーカスインジケーター |
| エラー通知 | aria-liveによるスクリーンリーダーへの即座の通知 |
| 代替テキスト | チャート等にaria-descriptionで数値情報を提供 |
| ズーム対応 | 200%ズームでもレイアウト崩れなし |

---

## 10. 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-03-27 | - | 初版作成 |
