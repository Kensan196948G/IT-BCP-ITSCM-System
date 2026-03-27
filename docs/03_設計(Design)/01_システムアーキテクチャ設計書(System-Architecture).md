# システムアーキテクチャ設計書 (System Architecture Design)

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-DES-ARCH-001 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 分類 | 設計文書 |
| 準拠規格 | ISO20000 ITSCM / ISO27001 / NIST CSF RECOVER RC |

---

## 目次

1. [概要](#1-概要)
2. [全体構成図](#2-全体構成図)
3. [コンポーネント一覧](#3-コンポーネント一覧)
4. [通信フロー](#4-通信フロー)
5. [高可用性設計](#5-高可用性設計)
6. [DR設計](#6-dr設計)
7. [フェイルオーバー設計](#7-フェイルオーバー設計)
8. [非機能要件](#8-非機能要件)
9. [変更履歴](#9-変更履歴)

---

## 1. 概要

### 1.1 システム名称

IT事業継続管理システム（IT-BCP-ITSCM-System）

### 1.2 目的

本システムは、災害・サイバー攻撃等のインシデント発生時におけるIT復旧計画の管理、BCP訓練の実施、RTO（Recovery Time Objective）のリアルタイム追跡を統合的に提供するプラットフォームである。

### 1.3 スコープ

- IT復旧計画（Recovery Plan）の作成・管理・実行
- BCP訓練（テーブルトップ演習）の計画・実行・評価
- RTOダッシュボードによるリアルタイム復旧状況の可視化
- エスカレーション管理（Teams/SMS/Email/Phone）
- オフライン対応（PWA）による災害時でもアクセス可能な設計

### 1.4 設計方針

| 方針 | 説明 |
|------|------|
| 可用性最優先 | 災害時にこそ必要なシステムであり、99.99%以上の可用性を目標とする |
| オフラインファースト | ネットワーク障害時でもBCP重要資料にアクセス可能 |
| マルチリージョン | Azure East Japan（Primary）+ West Japan（Standby）による地理冗長 |
| ゼロトラスト | Entra ID SSOによる厳格な認証・認可 |
| 自動化 | フェイルオーバー、エスカレーション、復旧手順の自動実行 |

---

## 2. 全体構成図

### 2.1 システム全体アーキテクチャ

```
                            ┌─────────────────────────┐
                            │       ユーザー端末        │
                            │  (PC / Mobile / Tablet)  │
                            │      PWA対応ブラウザ      │
                            └──────────┬──────────────┘
                                       │ HTTPS (TLS 1.3)
                                       ▼
                            ┌─────────────────────────┐
                            │    Azure Front Door      │
                            │  (グローバルロードバランサ) │
                            │  WAF / CDN / SSL終端     │
                            └──────┬──────────┬───────┘
                                   │          │
                    ┌──────────────┘          └──────────────┐
                    ▼                                        ▼
        ┌───────────────────────┐            ┌───────────────────────┐
        │  East Japan (Primary)  │            │  West Japan (Standby)  │
        │                       │            │                        │
        │ ┌───────────────────┐ │            │ ┌───────────────────┐  │
        │ │ Container Apps    │ │            │ │ Container Apps    │  │
        │ │ ┌───────────────┐ │ │            │ │ ┌───────────────┐ │  │
        │ │ │ Next.js Front │ │ │            │ │ │ Next.js Front │ │  │
        │ │ │ (SSR + Static)│ │ │            │ │ │ (SSR + Static)│ │  │
        │ │ └───────────────┘ │ │            │ │ └───────────────┘ │  │
        │ │ ┌───────────────┐ │ │            │ │ ┌───────────────┐ │  │
        │ │ │ FastAPI       │ │ │            │ │ │ FastAPI       │ │  │
        │ │ │ Backend API   │ │ │            │ │ │ Backend API   │ │  │
        │ │ └───────────────┘ │ │            │ │ └───────────────┘ │  │
        │ │ ┌───────────────┐ │ │            │ │ ┌───────────────┐ │  │
        │ │ │ Celery Worker │ │ │            │ │ │ Celery Worker │ │  │
        │ │ │ (非同期処理)   │ │ │            │ │ │ (非同期処理)   │ │  │
        │ │ └───────────────┘ │ │            │ │ └───────────────┘ │  │
        │ └───────────────────┘ │            │ └───────────────────┘  │
        │                       │            │                        │
        │ ┌───────────────────┐ │            │ ┌───────────────────┐  │
        │ │ PostgreSQL        │ │◄──同期───►│ │ PostgreSQL        │  │
        │ │ (Primary DB)      │ │ レプリカ   │ │ (Standby DB)      │  │
        │ └───────────────────┘ │            │ └───────────────────┘  │
        │                       │            │                        │
        │ ┌───────────────────┐ │            │ ┌───────────────────┐  │
        │ │ Redis Cluster     │ │◄──複製───►│ │ Redis Cluster     │  │
        │ │ (Cache/Session)   │ │            │ │ (Cache/Session)   │  │
        │ └───────────────────┘ │            │ └───────────────────┘  │
        └───────────────────────┘            └────────────────────────┘
                    │                                    │
                    └──────────────┬─────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │        外部連携サービス        │
                    │                             │
                    │ ┌─────────┐ ┌─────────────┐ │
                    │ │ ITSM    │ │ Teams API   │ │
                    │ │ (連携)  │ │ (通知)      │ │
                    │ └─────────┘ └─────────────┘ │
                    │ ┌─────────┐ ┌─────────────┐ │
                    │ │ SMS GW  │ │ Email SMTP  │ │
                    │ │ (Twilio)│ │ (SendGrid)  │ │
                    │ └─────────┘ └─────────────┘ │
                    └─────────────────────────────┘
```

### 2.2 ネットワーク構成図

```
Internet
    │
    ▼
┌─────────────────────────────────┐
│ Azure Front Door                │
│ ・WAF Policy (OWASP 3.2)       │
│ ・SSL/TLS 終端                  │
│ ・ヘルスプローブ (30秒間隔)      │
│ ・地理ベースルーティング          │
└─────────┬───────────┬───────────┘
          │           │
    ┌─────┘           └─────┐
    ▼                       ▼
┌────────────────┐  ┌────────────────┐
│ East Japan VNet│  │ West Japan VNet│
│ 10.1.0.0/16   │  │ 10.2.0.0/16   │
│                │  │                │
│ ├─ App Subnet  │  │ ├─ App Subnet  │
│ │  10.1.1.0/24│  │ │  10.2.1.0/24│
│ │              │  │ │              │
│ ├─ DB Subnet   │  │ ├─ DB Subnet   │
│ │  10.1.2.0/24│  │ │  10.2.2.0/24│
│ │              │  │ │              │
│ ├─ Cache Subnet│  │ ├─ Cache Subnet│
│ │  10.1.3.0/24│  │ │  10.2.3.0/24│
│ │              │  │ │              │
│ └─ Mgmt Subnet│  │ └─ Mgmt Subnet│
│    10.1.4.0/24│  │    10.2.4.0/24│
└────────┬───────┘  └────────┬───────┘
         │   VNet Peering    │
         └──────────────────┘
```

---

## 3. コンポーネント一覧

### 3.1 フロントエンドコンポーネント

| コンポーネント | 技術スタック | 役割 | 冗長性 |
|---------------|-------------|------|--------|
| Next.js 14 Application | TypeScript, React 18 | SSR/SSG/ISRによるWebアプリケーション配信 | 2リージョン各3インスタンス |
| Service Worker | Workbox 7 | オフラインキャッシュ、バックグラウンド同期 | クライアント側で動作 |
| PWA Manifest | Web App Manifest | ホーム画面追加、アプリライク動作 | クライアント側で動作 |
| IndexedDB Store | Dexie.js | オフラインデータストレージ | クライアント側で動作 |

### 3.2 バックエンドコンポーネント

| コンポーネント | 技術スタック | 役割 | 冗長性 |
|---------------|-------------|------|--------|
| FastAPI Application | Python 3.12, Uvicorn | REST API / WebSocket提供 | 2リージョン各3インスタンス |
| Celery Worker | Celery 5.x, Python | 非同期タスク処理（通知送信、レポート生成、データ集約） | 2リージョン各2ワーカー |
| Celery Beat | Celery Beat | 定期タスクスケジューラ（RTO計算、ヘルスチェック） | 各リージョン1インスタンス（Active-Standby） |

### 3.3 データストアコンポーネント

| コンポーネント | 技術スタック | 役割 | 冗長性 |
|---------------|-------------|------|--------|
| PostgreSQL | Azure Database for PostgreSQL Flexible Server v16 | メインRDBMS | Primary + Standby（同期レプリカ） |
| Redis Cluster | Azure Cache for Redis Premium | セッション管理、キャッシュ、Pub/Sub、Celeryブローカー | 3ノードクラスタ x 2リージョン |
| Azure Blob Storage | Azure Blob (GRS) | BCP文書、訓練記録、監査ログアーカイブ | GRS（地理冗長ストレージ） |

### 3.4 インフラコンポーネント

| コンポーネント | 技術スタック | 役割 |
|---------------|-------------|------|
| Azure Front Door | Premium tier | グローバルロードバランサ、WAF、SSL終端、CDN |
| Azure Container Apps | Consumption + Dedicated plan | コンテナオーケストレーション |
| Azure Container Registry | Premium tier | コンテナイメージレジストリ（Geo-replication） |
| Azure Key Vault | Premium tier | シークレット管理、暗号鍵管理 |
| Azure Monitor | Log Analytics + Application Insights | 監視、ログ収集、アラート |
| Azure DNS | パブリックDNSゾーン | DNS管理、フェイルオーバー |

### 3.5 外部連携コンポーネント

| コンポーネント | 連携方式 | 役割 |
|---------------|---------|------|
| ITSM（ServiceNow等） | REST API | インシデント連携、変更管理連携 |
| Microsoft Teams | Microsoft Graph API / Webhook | エスカレーション通知、インシデントチャネル自動作成 |
| SMS Gateway（Twilio） | REST API | 緊急SMS通知 |
| Email（SendGrid） | SMTP / REST API | メール通知、レポート配信 |
| Microsoft Entra ID | OIDC / SAML 2.0 | SSO認証、RBAC |

---

## 4. 通信フロー

### 4.1 通常リクエストフロー

```
ユーザー
  │
  │ ① HTTPS リクエスト (TLS 1.3)
  ▼
Azure Front Door
  │
  │ ② WAF検査 → ヘッダ付与 → ルーティング
  ▼
Container Apps (Next.js)
  │
  │ ③ SSR処理 / API Proxyリクエスト
  ▼
Container Apps (FastAPI)
  │
  │ ④ 認証トークン検証 (JWT / Entra ID)
  │ ⑤ ビジネスロジック処理
  │
  ├──▶ PostgreSQL (⑥ データ読み書き)
  ├──▶ Redis (⑦ キャッシュ参照/更新)
  └──▶ Celery (⑧ 非同期タスク投入)
  │
  │ ⑨ レスポンス返却 (JSON)
  ▼
ユーザー
```

### 4.2 WebSocket通信フロー（RTOリアルタイム更新）

```
ユーザー
  │
  │ ① WebSocket接続要求 (wss://)
  ▼
Azure Front Door
  │
  │ ② WebSocketアップグレード許可
  ▼
Container Apps (FastAPI WebSocket)
  │
  │ ③ 認証トークン検証
  │ ④ WebSocket接続確立
  │
  │ ◄──── Redis Pub/Sub (⑤ RTO更新イベント購読)
  │
  │ ⑥ リアルタイムRTO更新データ送信
  ▼
ユーザー（ダッシュボード自動更新）
```

### 4.3 エスカレーション通信フロー

```
インシデント検知
  │
  │ ① インシデント登録 (FastAPI)
  ▼
Celery Worker
  │
  │ ② エスカレーションルール評価
  │ ③ 通知先・手段決定
  │
  ├──▶ Teams API (④ チャネル作成 + メッセージ送信)
  ├──▶ Twilio API (⑤ SMS送信)
  ├──▶ SendGrid API (⑥ Email送信)
  └──▶ ITSM API (⑦ インシデントチケット作成)
  │
  │ ⑧ 通知結果記録 (PostgreSQL)
  │ ⑨ エスカレーション状態更新
  ▼
Redis Pub/Sub → WebSocket → ダッシュボード更新
```

### 4.4 オフライン同期フロー

```
オフライン状態
  │
  │ ① Service Worker がリクエストをインターセプト
  │ ② キャッシュからレスポンス返却
  │ ③ ユーザー操作はIndexedDBに記録
  │
  ▼
オンライン復帰
  │
  │ ④ Background Sync APIが発火
  │ ⑤ IndexedDB内の保留操作をサーバーに送信
  │ ⑥ コンフリクト解決（サーバー優先 + マージ）
  │ ⑦ キャッシュ更新
  ▼
同期完了
```

### 4.5 プロトコル一覧

| 通信経路 | プロトコル | ポート | 暗号化 |
|---------|-----------|--------|--------|
| ユーザー → Front Door | HTTPS (TLS 1.3) | 443 | TLS 1.3 |
| Front Door → Container Apps | HTTPS (mTLS) | 443 | mTLS |
| Container Apps → PostgreSQL | PostgreSQL SSL | 5432 | TLS 1.2+ |
| Container Apps → Redis | Redis TLS | 6380 | TLS 1.2+ |
| Container Apps → External API | HTTPS | 443 | TLS 1.2+ |
| WebSocket | WSS (TLS 1.3) | 443 | TLS 1.3 |
| VNet間 | VNet Peering | - | Azure暗号化 |

---

## 5. 高可用性設計

### 5.1 可用性目標

| 指標 | 目標値 | 備考 |
|------|--------|------|
| SLA | 99.99% | 年間ダウンタイム52.6分以内 |
| RPO（Recovery Point Objective） | 0秒 | 同期レプリケーション |
| RTO（Recovery Time Objective） | 90秒以内 | フェイルオーバー完了まで |
| MTBF（平均故障間隔） | 8,760時間以上 | 1年以上 |
| MTTR（平均修復時間） | 5分以内 | 自動フェイルオーバー + 手動確認 |

### 5.2 冗長構成

#### 5.2.1 アプリケーション層

- **Container Apps**: 各リージョンで最小3レプリカ、最大10レプリカ（オートスケール）
- **スケーリングルール**: CPU使用率70%、メモリ使用率80%、同時接続数100をトリガー
- **ヘルスチェック**: `/health`エンドポイントに対して10秒間隔で実施
- **ローリングアップデート**: maxSurge=1、maxUnavailable=0で無停止デプロイ

#### 5.2.2 データベース層

- **PostgreSQL**: Primary（East Japan）+ Standby（West Japan）の同期レプリケーション
- **自動フェイルオーバー**: Azure管理のフェイルオーバーグループにより自動昇格
- **リードレプリカ**: 各リージョンに1台のリードレプリカ（参照分離）
- **バックアップ**: 連続バックアップ（PITR 35日間保持）

#### 5.2.3 キャッシュ層

- **Redis Cluster**: 3ノード構成（1 Primary + 2 Replica）
- **クロスリージョン**: Active Geo-Replication
- **永続化**: AOF（Append Only File）+ RDBスナップショット

### 5.3 負荷分散

| レイヤー | 方式 | 詳細 |
|---------|------|------|
| L7（グローバル） | Azure Front Door | 地理ベースルーティング、重み付けルーティング |
| L7（リージョン） | Container Apps Ingress | ラウンドロビン |
| DB | アプリケーション層 | 書き込み→Primary、読み取り→Replica |

### 5.4 サーキットブレーカー

```
正常状態 (Closed)
    │
    │ エラー閾値超過（5回/10秒）
    ▼
開放状態 (Open)
    │
    │ タイムアウト（30秒）
    ▼
半開状態 (Half-Open)
    │
    ├─ 成功 → 正常状態 (Closed)
    └─ 失敗 → 開放状態 (Open)
```

- 外部API呼び出し（ITSM、Teams、Twilio、SendGrid）に適用
- ライブラリ: `tenacity`（Python）によるリトライ + サーキットブレーカー

---

## 6. DR設計

### 6.1 DR戦略

本システムはActive-Standby（ウォームスタンバイ）構成を採用する。

| 項目 | Primary（East Japan） | Standby（West Japan） |
|------|----------------------|----------------------|
| アプリケーション | Active（3レプリカ） | Warm Standby（1レプリカ、スケールアウト可能） |
| PostgreSQL | Primary（Read/Write） | Standby（同期レプリカ、Read Only） |
| Redis | Active Cluster | Geo-Replicaクラスタ |
| Blob Storage | Primary | GRS自動レプリカ |

### 6.2 DR発動条件

| レベル | 条件 | 対応 |
|--------|------|------|
| Level 1 | 単一コンポーネント障害 | Container Appsの自動復旧 |
| Level 2 | 複数コンポーネント障害 | リージョン内での自動復旧 |
| Level 3 | リージョン全体障害 | West Japanへのフェイルオーバー |
| Level 4 | 広域災害（東日本全域） | West Japan単独運用 + 縮退モード |

### 6.3 DRテスト計画

| テスト種別 | 頻度 | 内容 |
|-----------|------|------|
| コンポーネントフェイルオーバー | 月次 | 個別コンポーネントの障害注入テスト |
| リージョンフェイルオーバー | 四半期 | East Japan → West Japan切替テスト |
| 完全DRテスト | 年次 | 全面的なDR発動シミュレーション |
| カオスエンジニアリング | 週次 | Azure Chaos Studioによるランダム障害注入 |

### 6.4 データ保護

| データ種別 | バックアップ方式 | 保持期間 | RPO |
|-----------|----------------|---------|-----|
| PostgreSQL | 連続バックアップ（PITR） | 35日 | 0秒（同期レプリカ） |
| Redis | AOF + RDBスナップショット | 7日 | 1秒未満 |
| Blob Storage | GRS + ソフトデリート | 365日 | 0秒（GRS） |
| 監査ログ | Log Analytics + Blob Archive | 7年 | - |

---

## 7. フェイルオーバー設計

### 7.1 フェイルオーバー全体フロー

```
障害発生
  │
  │ ① Azure Front Door ヘルスプローブ失敗検知 (30秒以内)
  ▼
Front Door 判定
  │
  │ ② 3回連続失敗でバックエンド異常と判定
  │ ③ トラフィックルーティング変更開始
  ▼
DNSフェイルオーバー (60秒以内)
  │
  │ ④ West Japan バックエンドへルーティング切替
  │ ⑤ West Japan Container Apps スケールアウト開始
  ▼
West Japan Active化
  │
  │ ⑥ PostgreSQL Standby → Primary昇格
  │ ⑦ Redis Geo-Replica → Active昇格
  │ ⑧ Celery Worker起動
  ▼
復旧完了 (合計90秒以内)
  │
  │ ⑨ ヘルスチェック全項目GREEN確認
  │ ⑩ 運用チームへの自動通知
  ▼
正常運用（West Japan Primary）
```

### 7.2 フェイルオーバー時間目標

| フェーズ | 目標時間 | 詳細 |
|---------|---------|------|
| 障害検知 | 30秒以内 | Front Doorヘルスプローブ（10秒間隔 x 3回連続失敗） |
| ルーティング切替 | 30秒以内 | Front Doorトラフィック切替 |
| DB切替 | 30秒以内 | PostgreSQL自動フェイルオーバー（並行実行） |
| キャッシュ切替 | 10秒以内 | Redis Geo-Replicaアクティブ化（並行実行） |
| アプリスケールアウト | 60秒以内 | Container Appsスケーリング（並行実行） |
| **合計** | **90秒以内** | 検知 + ルーティング切替の合計 |

### 7.3 フェイルバック手順

フェイルバック（Primary復旧後の切り戻し）は以下の手順で実施する。

1. **East Japan復旧確認**: 全コンポーネントのヘルスチェック合格
2. **データ同期**: West Japan → East Japanへのデータ同期完了確認
3. **トラフィック段階切替**: 10% → 30% → 50% → 100%の段階的切替
4. **完全切替**: East Japan Primaryに復帰
5. **West Japan Standby化**: Standby構成に戻す

**重要**: フェイルバックは自動では実施せず、運用チームの判断で手動実施する。

### 7.4 スプリットブレイン対策

- PostgreSQL: Azure管理のフェイルオーバーグループによりスプリットブレイン防止
- Redis: WAIT コマンドによる書き込み確認 + fencing token
- アプリケーション: リーダー選出にRedis分散ロック（Redlock）を使用

---

## 8. 非機能要件

### 8.1 性能要件

| 指標 | 要件 |
|------|------|
| API応答時間（P95） | 200ms以内 |
| API応答時間（P99） | 500ms以内 |
| ページ初期表示（LCP） | 2.5秒以内 |
| WebSocket遅延 | 100ms以内 |
| 同時接続ユーザー数 | 500ユーザー |
| 同時WebSocket接続数 | 200接続 |
| スループット | 1,000 req/sec |

### 8.2 スケーラビリティ

| 項目 | 水平スケーリング | 垂直スケーリング |
|------|----------------|----------------|
| FastAPI | 3-10インスタンス（自動） | 0.5-2 vCPU / 1-4 GB RAM |
| Next.js | 3-10インスタンス（自動） | 0.5-2 vCPU / 1-4 GB RAM |
| Celery Worker | 2-8ワーカー（自動） | 0.5-2 vCPU / 1-4 GB RAM |
| PostgreSQL | リードレプリカ追加 | 2-16 vCPU / 8-64 GB RAM |
| Redis | ノード追加 | 6-53 GB |

### 8.3 監視・可観測性

| 項目 | ツール | 詳細 |
|------|--------|------|
| メトリクス | Azure Monitor + Prometheus | CPU、メモリ、レイテンシ、エラーレート |
| ログ | Azure Log Analytics | 構造化ログ（JSON）、30日保持 |
| トレース | Application Insights | 分散トレーシング（OpenTelemetry） |
| アラート | Azure Monitor Alerts | Severity別（Critical/Warning/Info） |
| ダッシュボード | Azure Dashboard + Grafana | 運用監視画面 |

---

## 9. 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-03-27 | - | 初版作成 |
