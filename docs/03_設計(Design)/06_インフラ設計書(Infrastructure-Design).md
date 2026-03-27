# インフラ設計書 (Infrastructure Design)

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-DES-INFRA-006 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 分類 | 設計文書 |
| 準拠規格 | ISO20000 ITSCM / ISO27001 / NIST CSF RECOVER RC |

---

## 目次

1. [概要](#1-概要)
2. [Azure全体構成](#2-azure全体構成)
3. [リージョン構成](#3-リージョン構成)
4. [Azure Front Door設計](#4-azure-front-door設計)
5. [Azure Container Apps設計](#5-azure-container-apps設計)
6. [データベースインフラ設計](#6-データベースインフラ設計)
7. [キャッシュインフラ設計](#7-キャッシュインフラ設計)
8. [ネットワーク設計](#8-ネットワーク設計)
9. [ストレージ設計](#9-ストレージ設計)
10. [監視・ログ設計](#10-監視ログ設計)
11. [Terraform設計](#11-terraform設計)
12. [CI/CDパイプライン設計](#12-cicdパイプライン設計)
13. [コスト見積もり](#13-コスト見積もり)
14. [変更履歴](#14-変更履歴)

---

## 1. 概要

### 1.1 インフラ設計方針

| 方針 | 説明 |
|------|------|
| Infrastructure as Code | Terraformによる完全なコード管理。手動構築禁止 |
| マルチリージョン | East Japan（Primary）+ West Japan（Standby）による地理冗長 |
| 最小権限の原則 | Azure RBACによるきめ細かいアクセス制御 |
| 自動スケーリング | 負荷に応じた自動スケールアウト/スケールイン |
| コスト最適化 | Standbyリージョンは最小構成で待機、オートスケールで動的拡張 |
| 監視・可観測性 | Azure Monitor + Application Insightsによる統合監視 |

### 1.2 リソースグループ構成

| リソースグループ | 用途 | リージョン |
|---------------|------|-----------|
| rg-itscm-global | グローバルリソース（Front Door、DNS、Container Registry） | グローバル |
| rg-itscm-eastjp-prod | East Japan本番環境 | Japan East |
| rg-itscm-westjp-prod | West Japan本番環境 | Japan West |
| rg-itscm-eastjp-stg | East Japanステージング環境 | Japan East |
| rg-itscm-shared | 共有リソース（Key Vault、Monitor、Defender） | Japan East |

### 1.3 命名規則

```
{リソース種別}-{プロジェクト名}-{環境}-{リージョン}-{番号}

例:
aca-itscm-prod-eastjp-001     (Container Apps)
psql-itscm-prod-eastjp-001    (PostgreSQL)
redis-itscm-prod-eastjp-001   (Redis)
vnet-itscm-prod-eastjp-001    (Virtual Network)
kv-itscm-prod-eastjp-001      (Key Vault)
fd-itscm-prod-001             (Front Door: グローバル)
acr-itscm-prod-001            (Container Registry: グローバル)
```

---

## 2. Azure全体構成

### 2.1 リソース構成図

```
Azure Subscription (IT-BCP-ITSCM-System)
│
├── rg-itscm-global
│   ├── Azure Front Door Premium (fd-itscm-prod-001)
│   │   ├── WAF Policy
│   │   ├── Custom Domain (itscm.example.com)
│   │   └── Origin Groups (East JP / West JP)
│   ├── Azure DNS Zone (itscm.example.com)
│   └── Azure Container Registry Premium (acr-itscm-prod-001)
│       └── Geo-Replication (East JP + West JP)
│
├── rg-itscm-eastjp-prod
│   ├── Virtual Network (vnet-itscm-prod-eastjp-001)
│   │   ├── snet-app (10.1.1.0/24)
│   │   ├── snet-db (10.1.2.0/24)
│   │   ├── snet-cache (10.1.3.0/24)
│   │   └── snet-mgmt (10.1.4.0/24)
│   ├── Container Apps Environment
│   │   ├── aca-frontend-prod-eastjp (Next.js x3)
│   │   ├── aca-backend-prod-eastjp (FastAPI x3)
│   │   ├── aca-worker-prod-eastjp (Celery Worker x2)
│   │   └── aca-beat-prod-eastjp (Celery Beat x1)
│   ├── PostgreSQL Flexible Server (Primary)
│   │   ├── Database: itscm
│   │   └── Read Replica x1
│   ├── Azure Cache for Redis Premium
│   │   └── Cluster (3 shards)
│   └── Storage Account (GRS)
│
├── rg-itscm-westjp-prod
│   ├── Virtual Network (vnet-itscm-prod-westjp-001)
│   │   ├── snet-app (10.2.1.0/24)
│   │   ├── snet-db (10.2.2.0/24)
│   │   ├── snet-cache (10.2.3.0/24)
│   │   └── snet-mgmt (10.2.4.0/24)
│   ├── Container Apps Environment
│   │   ├── aca-frontend-prod-westjp (Next.js x1 warm)
│   │   ├── aca-backend-prod-westjp (FastAPI x1 warm)
│   │   └── aca-worker-prod-westjp (Celery Worker x1 warm)
│   ├── PostgreSQL Flexible Server (Standby)
│   │   └── Sync Replica
│   ├── Azure Cache for Redis Premium
│   │   └── Geo-Replica Cluster
│   └── Storage Account (RA-GRS secondary)
│
└── rg-itscm-shared
    ├── Azure Key Vault Premium (kv-itscm-prod-001)
    ├── Azure Monitor / Log Analytics Workspace
    ├── Application Insights
    ├── Azure Defender for Cloud
    └── Azure Managed Identity
```

---

## 3. リージョン構成

### 3.1 East Japan（Primary）

| リソース | SKU/Tier | スペック | 数量 |
|---------|---------|--------|------|
| Container Apps (Frontend) | Consumption | 0.5 vCPU / 1 GB RAM | 最小3、最大10 |
| Container Apps (Backend) | Consumption | 0.5 vCPU / 1 GB RAM | 最小3、最大10 |
| Container Apps (Worker) | Consumption | 0.5 vCPU / 1 GB RAM | 最小2、最大8 |
| Container Apps (Beat) | Consumption | 0.25 vCPU / 0.5 GB RAM | 1 |
| PostgreSQL | General Purpose D4ds_v5 | 4 vCPU / 16 GB RAM / 512 GB SSD | 1 Primary + 1 Read Replica |
| Redis | Premium P1 | 6 GB | 3ノードクラスタ |
| Storage Account | Standard GRS | - | 1 |

### 3.2 West Japan（Standby）

| リソース | SKU/Tier | スペック | 数量 |
|---------|---------|--------|------|
| Container Apps (Frontend) | Consumption | 0.5 vCPU / 1 GB RAM | 最小1、最大10（フェイルオーバー時） |
| Container Apps (Backend) | Consumption | 0.5 vCPU / 1 GB RAM | 最小1、最大10（フェイルオーバー時） |
| Container Apps (Worker) | Consumption | 0.5 vCPU / 1 GB RAM | 最小1、最大8（フェイルオーバー時） |
| PostgreSQL | General Purpose D4ds_v5 | 4 vCPU / 16 GB RAM / 512 GB SSD | 1 Standby Replica |
| Redis | Premium P1 | 6 GB | Geo-Replicaクラスタ |
| Storage Account | RA-GRS Secondary | - | 自動レプリケーション |

---

## 4. Azure Front Door設計

### 4.1 Front Door構成

```
Azure Front Door Premium
│
├── Frontend: itscm.example.com
│   ├── Custom Domain + Managed Certificate
│   ├── HTTPS Redirect (HTTP → HTTPS)
│   └── HSTS (max-age=31536000; includeSubDomains)
│
├── WAF Policy (fd-waf-itscm-prod)
│   ├── Managed Rule Set: Microsoft_DefaultRuleSet 2.1
│   ├── Managed Rule Set: Microsoft_BotManagerRuleSet 1.0
│   ├── Custom Rules:
│   │   ├── Rate Limit: 1000 req/min per IP
│   │   ├── Geo Restriction: Japan only (optional)
│   │   └── IP Allow List: 管理者IP (optional)
│   └── Mode: Prevention
│
├── Origin Group: og-frontend
│   ├── Origin: aca-frontend-prod-eastjp (Priority 1, Weight 100)
│   └── Origin: aca-frontend-prod-westjp (Priority 2, Weight 100)
│
├── Origin Group: og-backend-api
│   ├── Origin: aca-backend-prod-eastjp (Priority 1, Weight 100)
│   └── Origin: aca-backend-prod-westjp (Priority 2, Weight 100)
│
├── Routes:
│   ├── /api/* → og-backend-api (No caching, WebSocket support)
│   ├── /ws/* → og-backend-api (WebSocket)
│   ├── /health* → og-backend-api (No caching)
│   ├── /_next/static/* → og-frontend (CDN caching: 30 days)
│   ├── /icons/* → og-frontend (CDN caching: 30 days)
│   └── /* → og-frontend (SSR, no CDN caching)
│
└── Health Probes:
    ├── Frontend: GET /health (interval: 10s, threshold: 3)
    └── Backend: GET /health (interval: 10s, threshold: 3)
```

### 4.2 ヘルスプローブ設定

| 項目 | 値 |
|------|-----|
| プローブパス | /health |
| プロトコル | HTTPS |
| プローブ間隔 | 10秒 |
| サンプルサイズ | 4 |
| 成功判定サンプル数 | 2 |
| レイテンシ感度 | 中 (additional latency: 500ms) |

### 4.3 キャッシュルール

| パスパターン | キャッシュ | TTL | クエリストリング |
|------------|----------|-----|----------------|
| /_next/static/* | 有効 | 30日 | 無視 |
| /icons/* | 有効 | 30日 | 無視 |
| /api/* | 無効 | - | - |
| /ws/* | 無効 | - | - |
| /* | 無効 | - | - |

---

## 5. Azure Container Apps設計

### 5.1 Container Apps Environment

| 項目 | East Japan | West Japan |
|------|-----------|-----------|
| Environment名 | cae-itscm-prod-eastjp | cae-itscm-prod-westjp |
| プラン | Consumption | Consumption |
| VNet統合 | あり (snet-app) | あり (snet-app) |
| 内部通信 | HTTPS (mTLS自動) | HTTPS (mTLS自動) |
| ログ出力先 | Log Analytics | Log Analytics |

### 5.2 コンテナアプリ定義

#### Frontend (Next.js)

```yaml
name: aca-frontend-prod-eastjp
image: acritscmprod001.azurecr.io/itscm-frontend:latest
resources:
  cpu: 0.5
  memory: 1Gi
scale:
  minReplicas: 3
  maxReplicas: 10
  rules:
    - name: http-scaling
      http:
        metadata:
          concurrentRequests: "100"
    - name: cpu-scaling
      custom:
        type: cpu
        metadata:
          value: "70"
ingress:
  external: true
  targetPort: 3000
  transport: http
  allowInsecure: false
probes:
  startup:
    httpGet:
      path: /health
      port: 3000
    initialDelaySeconds: 5
    periodSeconds: 3
    failureThreshold: 10
  liveness:
    httpGet:
      path: /health/live
      port: 3000
    periodSeconds: 10
    failureThreshold: 3
  readiness:
    httpGet:
      path: /health/ready
      port: 3000
    periodSeconds: 5
    failureThreshold: 3
env:
  - name: NEXT_PUBLIC_API_URL
    value: https://api.itscm.example.com
  - name: NODE_ENV
    value: production
secrets:
  - name: entra-client-secret
    keyVaultUrl: https://kv-itscm-prod-eastjp-001.vault.azure.net/secrets/entra-client-secret
```

#### Backend (FastAPI)

```yaml
name: aca-backend-prod-eastjp
image: acritscmprod001.azurecr.io/itscm-backend:latest
resources:
  cpu: 0.5
  memory: 1Gi
scale:
  minReplicas: 3
  maxReplicas: 10
  rules:
    - name: http-scaling
      http:
        metadata:
          concurrentRequests: "80"
    - name: cpu-scaling
      custom:
        type: cpu
        metadata:
          value: "70"
ingress:
  external: true
  targetPort: 8000
  transport: http
  allowInsecure: false
probes:
  startup:
    httpGet:
      path: /health
      port: 8000
    initialDelaySeconds: 10
    periodSeconds: 3
    failureThreshold: 10
  liveness:
    httpGet:
      path: /health/live
      port: 8000
    periodSeconds: 10
    failureThreshold: 3
  readiness:
    httpGet:
      path: /health/ready
      port: 8000
    periodSeconds: 5
    failureThreshold: 3
env:
  - name: DATABASE_URL
    secretRef: database-url
  - name: REDIS_URL
    secretRef: redis-url
  - name: CELERY_BROKER_URL
    secretRef: celery-broker-url
```

#### Celery Worker

```yaml
name: aca-worker-prod-eastjp
image: acritscmprod001.azurecr.io/itscm-backend:latest
command: ["celery", "-A", "app.worker", "worker", "--loglevel=info", "--concurrency=4"]
resources:
  cpu: 0.5
  memory: 1Gi
scale:
  minReplicas: 2
  maxReplicas: 8
  rules:
    - name: queue-scaling
      custom:
        type: azure-queue
        metadata:
          queueLength: "10"
```

#### Celery Beat

```yaml
name: aca-beat-prod-eastjp
image: acritscmprod001.azurecr.io/itscm-backend:latest
command: ["celery", "-A", "app.worker", "beat", "--loglevel=info"]
resources:
  cpu: 0.25
  memory: 0.5Gi
scale:
  minReplicas: 1
  maxReplicas: 1
```

### 5.3 デプロイ戦略

| 項目 | 値 |
|------|-----|
| デプロイ方式 | ローリングアップデート（リビジョンベース） |
| トラフィック分割 | 新リビジョン10% → 50% → 100%（段階的） |
| ロールバック | 前リビジョンへのトラフィック切替（即座） |
| ヘルスチェック | Startup Probe成功後にトラフィック投入 |
| イメージタグ | Git SHA + semantic version (例: v1.2.3-abc1234) |

---

## 6. データベースインフラ設計

### 6.1 PostgreSQL構成

| 項目 | East Japan (Primary) | West Japan (Standby) |
|------|---------------------|---------------------|
| サーバー名 | psql-itscm-prod-eastjp-001 | psql-itscm-prod-westjp-001 |
| SKU | General Purpose D4ds_v5 | General Purpose D4ds_v5 |
| vCPU | 4 | 4 |
| メモリ | 16 GB | 16 GB |
| ストレージ | 512 GB Premium SSD | 512 GB Premium SSD |
| PostgreSQLバージョン | 16 | 16 |
| 高可用性 | Zone Redundant HA | Zone Redundant HA |
| バックアップ保持期間 | 35日 | 35日 |
| Geo-Redundant Backup | 有効 | - |

### 6.2 主要パラメータ設定

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| max_connections | 200 | 最大接続数 |
| shared_buffers | 4GB | 共有バッファ (メモリの25%) |
| effective_cache_size | 12GB | 有効キャッシュサイズ (メモリの75%) |
| work_mem | 64MB | ソート・ハッシュ用メモリ |
| maintenance_work_mem | 1GB | メンテナンス操作用メモリ |
| wal_level | logical | WALレベル（将来の拡張性） |
| max_wal_senders | 10 | WAL送信者最大数 |
| synchronous_commit | remote_apply | 同期コミットレベル |
| log_min_duration_statement | 1000 | 1秒以上のクエリをログ |
| idle_in_transaction_session_timeout | 60000 | アイドルトランザクション60秒タイムアウト |
| statement_timeout | 30000 | ステートメント30秒タイムアウト |

### 6.3 接続プール設定

アプリケーション側のコネクションプール（SQLAlchemy + asyncpg）設定。

| 項目 | 値 |
|------|-----|
| pool_size | 10 |
| max_overflow | 10 |
| pool_timeout | 30秒 |
| pool_recycle | 1800秒 (30分) |
| pool_pre_ping | true |

---

## 7. キャッシュインフラ設計

### 7.1 Redis構成

| 項目 | East Japan | West Japan |
|------|-----------|-----------|
| サーバー名 | redis-itscm-prod-eastjp-001 | redis-itscm-prod-westjp-001 |
| SKU | Premium P1 | Premium P1 |
| メモリ | 6 GB | 6 GB |
| クラスタリング | 有効 (3 shards) | 有効 (3 shards) |
| Geo-Replication | Primary | Secondary |
| TLS | 有効 (ポート6380) | 有効 (ポート6380) |
| VNet統合 | あり (snet-cache) | あり (snet-cache) |
| 永続化 | AOF + RDB | AOF + RDB |
| maxmemory-policy | allkeys-lru | allkeys-lru |

### 7.2 Redis用途別設計

| 用途 | DB番号 | キープレフィックス | TTL |
|------|--------|-----------------|-----|
| セッション | DB 0 | session: | 7日 |
| APIキャッシュ | DB 1 | cache: | 5分-1時間 |
| Celeryブローカー | DB 2 | celery: | - |
| Pub/Sub (WebSocket) | DB 3 | ws: | - |
| 分散ロック | DB 4 | lock: | 30秒 |
| レート制限 | DB 5 | ratelimit: | 1分 |

---

## 8. ネットワーク設計

### 8.1 VNet設計

| VNet | CIDR | リージョン |
|------|------|-----------|
| vnet-itscm-prod-eastjp-001 | 10.1.0.0/16 | Japan East |
| vnet-itscm-prod-westjp-001 | 10.2.0.0/16 | Japan West |

### 8.2 サブネット設計

| サブネット | CIDR (East) | CIDR (West) | 用途 | NSG |
|-----------|-------------|-------------|------|-----|
| snet-app | 10.1.1.0/24 | 10.2.1.0/24 | Container Apps | nsg-app |
| snet-db | 10.1.2.0/24 | 10.2.2.0/24 | PostgreSQL | nsg-db |
| snet-cache | 10.1.3.0/24 | 10.2.3.0/24 | Redis | nsg-cache |
| snet-mgmt | 10.1.4.0/24 | 10.2.4.0/24 | 管理・監視 | nsg-mgmt |
| snet-pe | 10.1.5.0/24 | 10.2.5.0/24 | Private Endpoint | nsg-pe |

### 8.3 NSG設計（主要ルール）

#### nsg-app

| 優先度 | 方向 | アクション | ソース | 宛先 | ポート | 説明 |
|--------|------|----------|--------|------|--------|------|
| 100 | Inbound | Allow | AzureFrontDoor.Backend | snet-app | 443 | Front Doorからのトラフィック |
| 200 | Inbound | Allow | snet-app | snet-app | * | アプリ間通信 |
| 1000 | Inbound | Deny | * | * | * | その他すべて拒否 |
| 100 | Outbound | Allow | snet-app | snet-db | 5432 | DB接続 |
| 200 | Outbound | Allow | snet-app | snet-cache | 6380 | Redis接続 |
| 300 | Outbound | Allow | snet-app | Internet | 443 | 外部API (Teams/Twilio/SendGrid) |

#### nsg-db

| 優先度 | 方向 | アクション | ソース | 宛先 | ポート | 説明 |
|--------|------|----------|--------|------|--------|------|
| 100 | Inbound | Allow | snet-app | snet-db | 5432 | アプリからのDB接続 |
| 200 | Inbound | Allow | snet-mgmt | snet-db | 5432 | 管理用DB接続 |
| 1000 | Inbound | Deny | * | * | * | その他すべて拒否 |

### 8.4 VNet Peering

| Peering名 | ソース | 宛先 | 用途 |
|-----------|--------|------|------|
| peer-eastjp-to-westjp | vnet-eastjp | vnet-westjp | リージョン間通信 |
| peer-westjp-to-eastjp | vnet-westjp | vnet-eastjp | リージョン間通信 |

### 8.5 Private Endpoint

| サービス | Private Endpoint | プライベートDNSゾーン |
|---------|-----------------|---------------------|
| PostgreSQL | pe-psql-eastjp / pe-psql-westjp | privatelink.postgres.database.azure.com |
| Redis | pe-redis-eastjp / pe-redis-westjp | privatelink.redis.cache.windows.net |
| Key Vault | pe-kv | privatelink.vaultcore.azure.net |
| Storage | pe-storage-eastjp | privatelink.blob.core.windows.net |
| Container Registry | pe-acr | privatelink.azurecr.io |

---

## 9. ストレージ設計

### 9.1 Azure Blob Storage

| 項目 | 値 |
|------|-----|
| アカウント名 | stitscmprodeastjp001 |
| レプリケーション | GRS (Geo-Redundant Storage) |
| アクセス層 | Hot (デフォルト) |
| Soft Delete | 有効 (14日) |
| バージョニング | 有効 |

### 9.2 コンテナ（Blob）設計

| コンテナ名 | 用途 | アクセス層 | ライフサイクル |
|-----------|------|-----------|-------------|
| bcp-documents | BCP文書、手順書PDF | Hot | - |
| exercise-records | 演習記録、添付ファイル | Hot → Cool (90日後) | - |
| audit-archives | 監査ログアーカイブ | Hot → Cool (30日後) → Archive (365日後) | 7年後削除 |
| db-backups | DB論理バックアップ | Cool | 90日後削除 (月次は1年) |
| system-exports | エクスポートデータ | Hot | 7日後削除 |

---

## 10. 監視・ログ設計

### 10.1 Azure Monitor構成

```
Azure Monitor
│
├── Log Analytics Workspace (law-itscm-prod)
│   ├── Container Apps ログ
│   ├── PostgreSQL ログ
│   ├── Redis ログ
│   ├── Front Door ログ
│   ├── NSG Flow ログ
│   └── Activity Log
│
├── Application Insights (ai-itscm-prod)
│   ├── Frontend (Next.js) テレメトリ
│   ├── Backend (FastAPI) テレメトリ
│   ├── 分散トレーシング (OpenTelemetry)
│   ├── カスタムメトリクス
│   └── 可用性テスト
│
└── アラートルール
    ├── Critical
    │   ├── Container Apps ヘルスチェック失敗
    │   ├── PostgreSQL 接続エラー
    │   ├── Redis 接続エラー
    │   ├── API エラーレート > 5%
    │   └── フェイルオーバー発生
    ├── Warning
    │   ├── API レイテンシ P95 > 500ms
    │   ├── CPU使用率 > 80%
    │   ├── メモリ使用率 > 85%
    │   ├── DB接続数 > 150
    │   └── Redis メモリ使用率 > 80%
    └── Info
        ├── デプロイ完了
        ├── スケーリングイベント
        └── 証明書更新
```

### 10.2 アラート通知先

| 重要度 | 通知先 | 方法 |
|--------|--------|------|
| Critical (Sev 0) | 運用チーム全員 + 管理者 | Teams + SMS + Email + PagerDuty |
| Warning (Sev 1) | 運用チーム | Teams + Email |
| Info (Sev 2) | 運用チーム | Teams |

### 10.3 ログ保持期間

| ログ種別 | Log Analytics保持 | アーカイブ保持 |
|---------|-----------------|-------------|
| アプリケーションログ | 30日 | 1年 |
| 監査ログ | 90日 | 7年 |
| セキュリティログ | 90日 | 7年 |
| インフラメトリクス | 90日 | 1年 |
| NSGフローログ | 30日 | 90日 |

---

## 11. Terraform設計

### 11.1 ディレクトリ構成

```
terraform/
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── container-apps/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── database/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── redis/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── front-door/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── monitoring/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── security/
│   │   ├── main.tf        (Key Vault, Managed Identity)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── storage/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── prod/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   ├── backend.tf
│   │   └── providers.tf
│   └── stg/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       ├── backend.tf
│       └── providers.tf
├── .terraform-version
└── README.md
```

### 11.2 State管理

| 項目 | 値 |
|------|-----|
| Backend | Azure Blob Storage |
| Storage Account | stitscmtfstate001 |
| Container | tfstate |
| State File | prod/terraform.tfstate |
| State Lock | Azure Blob Lease |
| 暗号化 | Microsoft Managed Key |

### 11.3 主要Terraformリソース例

```hcl
# environments/prod/main.tf

module "networking_eastjp" {
  source              = "../../modules/networking"
  resource_group_name = "rg-itscm-eastjp-prod"
  location            = "japaneast"
  vnet_name           = "vnet-itscm-prod-eastjp-001"
  vnet_address_space  = ["10.1.0.0/16"]
  subnets = {
    app   = { address_prefix = "10.1.1.0/24" }
    db    = { address_prefix = "10.1.2.0/24" }
    cache = { address_prefix = "10.1.3.0/24" }
    mgmt  = { address_prefix = "10.1.4.0/24" }
    pe    = { address_prefix = "10.1.5.0/24" }
  }
}

module "networking_westjp" {
  source              = "../../modules/networking"
  resource_group_name = "rg-itscm-westjp-prod"
  location            = "japanwest"
  vnet_name           = "vnet-itscm-prod-westjp-001"
  vnet_address_space  = ["10.2.0.0/16"]
  subnets = {
    app   = { address_prefix = "10.2.1.0/24" }
    db    = { address_prefix = "10.2.2.0/24" }
    cache = { address_prefix = "10.2.3.0/24" }
    mgmt  = { address_prefix = "10.2.4.0/24" }
    pe    = { address_prefix = "10.2.5.0/24" }
  }
}

module "database_eastjp" {
  source              = "../../modules/database"
  resource_group_name = "rg-itscm-eastjp-prod"
  location            = "japaneast"
  server_name         = "psql-itscm-prod-eastjp-001"
  sku_name            = "GP_Standard_D4ds_v5"
  storage_mb          = 524288
  postgresql_version   = "16"
  ha_mode             = "ZoneRedundant"
  backup_retention_days = 35
  geo_redundant_backup = true
  subnet_id           = module.networking_eastjp.subnet_ids["db"]
}

module "container_apps_eastjp" {
  source              = "../../modules/container-apps"
  resource_group_name = "rg-itscm-eastjp-prod"
  location            = "japaneast"
  environment_name    = "cae-itscm-prod-eastjp"
  subnet_id           = module.networking_eastjp.subnet_ids["app"]
  log_analytics_id    = module.monitoring.log_analytics_workspace_id

  apps = {
    frontend = {
      image       = "acritscmprod001.azurecr.io/itscm-frontend:latest"
      cpu         = 0.5
      memory      = "1Gi"
      min_replicas = 3
      max_replicas = 10
      target_port  = 3000
    }
    backend = {
      image       = "acritscmprod001.azurecr.io/itscm-backend:latest"
      cpu         = 0.5
      memory      = "1Gi"
      min_replicas = 3
      max_replicas = 10
      target_port  = 8000
    }
  }
}
```

---

## 12. CI/CDパイプライン設計

### 12.1 パイプライン構成

```
GitHub Repository
  │
  │ Push / PR
  ▼
GitHub Actions
  │
  ├── CI Pipeline (on: push / pull_request)
  │   ├── Lint (ESLint / Ruff)
  │   ├── Type Check (TypeScript / MyPy)
  │   ├── Unit Test (Vitest / Pytest)
  │   ├── Build (Next.js build / Docker build)
  │   ├── Security Scan (Trivy / Snyk)
  │   └── SAST (CodeQL)
  │
  ├── CD Pipeline (on: merge to main)
  │   ├── Docker Build & Push to ACR
  │   ├── Deploy to Staging
  │   ├── E2E Test (Playwright)
  │   ├── Performance Test (k6)
  │   ├── Manual Approval Gate
  │   └── Deploy to Production
  │       ├── East Japan (10% → 50% → 100%)
  │       └── West Japan (warm standby update)
  │
  └── Infrastructure Pipeline (on: changes to terraform/)
      ├── terraform fmt
      ├── terraform validate
      ├── terraform plan
      ├── Manual Approval
      └── terraform apply
```

### 12.2 デプロイフロー

```
main merge
  │
  │ ① Docker イメージビルド (frontend + backend)
  │ ② ACR にプッシュ (タグ: v1.2.3-sha1234)
  ▼
Staging 環境デプロイ
  │
  │ ③ Container Apps リビジョン作成
  │ ④ E2Eテスト実行 (Playwright)
  │ ⑤ パフォーマンステスト (k6)
  ▼
承認ゲート（手動承認）
  │
  │ ⑥ 運用チームが承認
  ▼
Production East Japan デプロイ
  │
  │ ⑦ 新リビジョン作成 → トラフィック10%
  │ ⑧ 5分間監視（エラーレート、レイテンシ）
  │ ⑨ 問題なし → トラフィック50%
  │ ⑩ 5分間監視
  │ ⑪ 問題なし → トラフィック100%
  ▼
Production West Japan デプロイ
  │
  │ ⑫ Standbyインスタンスのイメージ更新
  ▼
デプロイ完了通知
```

---

## 13. コスト見積もり

### 13.1 月額コスト概算（本番環境）

| リソース | SKU | 月額概算 (JPY) |
|---------|-----|---------------|
| Azure Front Door Premium | Premium | 50,000 |
| Container Apps (East JP) | Consumption | 30,000 |
| Container Apps (West JP) | Consumption (warm) | 10,000 |
| PostgreSQL (East JP Primary) | GP D4ds_v5 | 80,000 |
| PostgreSQL (East JP Read Replica) | GP D4ds_v5 | 80,000 |
| PostgreSQL (West JP Standby) | GP D4ds_v5 | 80,000 |
| Redis (East JP) | Premium P1 x3 | 90,000 |
| Redis (West JP Geo-Replica) | Premium P1 x3 | 90,000 |
| Container Registry Premium | Geo-Replication | 15,000 |
| Blob Storage (GRS) | Standard GRS | 5,000 |
| Key Vault | Premium | 3,000 |
| Log Analytics + App Insights | Pay-as-you-go | 20,000 |
| VNet / Private Endpoints | - | 10,000 |
| Azure DNS | - | 1,000 |
| **合計** | | **約 564,000** |

**注**: 実際のコストはトラフィック量、データ量、スケーリング状況により変動する。

---

## 14. 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-03-27 | - | 初版作成 |
