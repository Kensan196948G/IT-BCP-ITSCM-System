# デプロイメント構成管理（Deployment Configuration）

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-RM-004 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 作成者 | IT-BCP-ITSCMシステム開発チーム |
| 承認者 | （承認者名） |
| 分類 | リリース管理 |
| 準拠規格 | ISO20000 / ISO27001 / NIST CSF |

---

## 改訂履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-03-27 | 開発チーム | 初版作成 |

---

## 目次

1. [概要](#1-概要)
2. [環境構成](#2-環境構成)
3. [各環境の設定値管理](#3-各環境の設定値管理)
4. [コンテナイメージ管理](#4-コンテナイメージ管理)
5. [環境変数・シークレット管理](#5-環境変数シークレット管理)
6. [Terraform状態管理](#6-terraform状態管理)
7. [構成変更管理プロセス](#7-構成変更管理プロセス)

---

## 1. 概要

### 1.1 目的

本文書は、IT-BCP-ITSCMシステムの全環境（dev/staging/production）におけるデプロイメント構成を一元管理するための方針と手順を定義する。Infrastructure as Code（IaC）を基本とし、構成の再現性、追跡可能性、セキュリティを確保する。

### 1.2 基本方針

| 方針 | 内容 |
|------|------|
| Infrastructure as Code | 全インフラ構成をTerraformで管理 |
| 環境パリティ | staging環境は本番環境と同等構成 |
| 不変インフラ | コンテナイメージは一度ビルドしたら変更しない |
| シークレット分離 | シークレットはAzure Key Vaultで管理、コードに含めない |
| バージョン管理 | 全構成ファイルをGitで管理 |
| 最小権限原則 | 各環境・コンポーネントに必要最小限の権限のみ付与 |

---

## 2. 環境構成

### 2.1 環境一覧

| 環境 | 用途 | リージョン | 可用性 | データ |
|------|------|----------|--------|-------|
| dev | 開発・デバッグ | East Japan | 単一 | テストデータ |
| staging | リリース前検証 | East Japan + West Japan | 冗長 | 匿名化データ |
| production | 本番運用 | East Japan (Primary) + West Japan (Standby) | Geo冗長 | 本番データ |

### 2.2 アーキテクチャ図

```
                         ┌─────────────────────┐
                         │    Azure Front Door   │
                         │  (Global Load Balancer)│
                         └──────────┬────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
          ┌─────────▼─────────┐          ┌─────────▼─────────┐
          │  East Japan        │          │  West Japan        │
          │  (Primary)         │          │  (Standby)         │
          │                    │          │                    │
          │ ┌────────────────┐ │          │ ┌────────────────┐ │
          │ │ Container Apps │ │          │ │ Container Apps │ │
          │ │ ├ Frontend     │ │          │ │ ├ Frontend     │ │
          │ │ ├ API          │ │          │ │ ├ API          │ │
          │ │ └ Worker       │ │          │ │ └ Worker       │ │
          │ └────────────────┘ │          │ └────────────────┘ │
          │                    │          │                    │
          │ ┌────────────────┐ │          │ ┌────────────────┐ │
          │ │ PostgreSQL     │ │──Geo────▶│ │ PostgreSQL     │ │
          │ │ (Primary)      │ │  Replica │ │ (Read Replica) │ │
          │ └────────────────┘ │          │ └────────────────┘ │
          │                    │          │                    │
          │ ┌────────────────┐ │          │ ┌────────────────┐ │
          │ │ Redis Cluster  │ │──Geo────▶│ │ Redis Cluster  │ │
          │ └────────────────┘ │  Repl.  │ └────────────────┘ │
          │                    │          │                    │
          │ ┌────────────────┐ │          │ ┌────────────────┐ │
          │ │ Key Vault      │ │          │ │ Key Vault      │ │
          │ └────────────────┘ │          │ └────────────────┘ │
          └────────────────────┘          └────────────────────┘
```

### 2.3 各環境のリソース構成

#### Development環境

| リソース | SKU/構成 | 備考 |
|---------|---------|------|
| Container Apps Environment | Consumption | コスト最適化 |
| Frontend Container App | min: 1, max: 2 | vCPU: 0.25, Memory: 0.5Gi |
| API Container App | min: 1, max: 3 | vCPU: 0.5, Memory: 1Gi |
| Worker Container App | min: 1, max: 2 | vCPU: 0.5, Memory: 1Gi |
| PostgreSQL Flexible Server | Burstable B1ms | 1 vCore, 2GB RAM, 32GB Storage |
| Redis Cache | Basic C0 | 250MB |
| Key Vault | Standard | - |
| Container Registry | Basic | 共有（全環境共通） |

#### Staging環境

| リソース | SKU/構成 | 備考 |
|---------|---------|------|
| Container Apps Environment | Workload profiles | 本番同等 |
| Frontend Container App | min: 2, max: 5 | vCPU: 0.5, Memory: 1Gi |
| API Container App | min: 2, max: 8 | vCPU: 1, Memory: 2Gi |
| Worker Container App | min: 2, max: 5 | vCPU: 1, Memory: 2Gi |
| PostgreSQL Flexible Server | General Purpose D2s_v3 | 2 vCore, 8GB RAM, 128GB + Replica |
| Redis Cache | Standard C1 | 1GB, Geo-replication |
| Key Vault | Standard | リージョンごと |
| Application Insights | - | 本番同等の監視 |

#### Production環境

| リソース | SKU/構成 | 備考 |
|---------|---------|------|
| Container Apps Environment | Workload profiles (Dedicated) | 高可用性 |
| Frontend Container App | min: 3, max: 10 | vCPU: 1, Memory: 2Gi |
| API Container App | min: 3, max: 20 | vCPU: 2, Memory: 4Gi |
| Worker Container App | min: 2, max: 10 | vCPU: 2, Memory: 4Gi |
| PostgreSQL Flexible Server | General Purpose D4s_v3 | 4 vCore, 16GB RAM, 512GB + Geo Replica |
| Redis Cache | Premium P1 | 6GB, Cluster (3 shards), Geo-replication |
| Key Vault | Premium (HSM) | リージョンごと、HSMバックド |
| Application Insights | - | 全監視有効 |
| Azure Front Door | Premium | WAF、DDoS Protection |
| Azure DDoS Protection | Standard | - |
| Log Analytics Workspace | - | 90日保持 |

---

## 3. 各環境の設定値管理

### 3.1 設定値の分類

| 分類 | 管理方法 | 例 |
|------|---------|-----|
| アプリケーション設定 | 環境変数（Container Appsの設定） | API_URL, LOG_LEVEL |
| シークレット | Azure Key Vault | DB_PASSWORD, API_KEY |
| インフラ設定 | Terraform変数 | SKU, リージョン, スケール設定 |
| 機能フラグ | 環境変数 or 設定DB | FEATURE_AI_ENABLED |

### 3.2 環境別設定値一覧

#### フロントエンド設定

| 設定名 | dev | staging | production | 説明 |
|--------|-----|---------|------------|------|
| NEXT_PUBLIC_API_URL | http://localhost:8000 | https://staging-api.itscm.example.com | https://api.itscm.example.com | APIエンドポイント |
| NEXT_PUBLIC_APP_ENV | development | staging | production | 環境識別子 |
| NEXT_PUBLIC_ENABLE_PWA | false | true | true | PWA有効化 |
| NEXT_PUBLIC_SENTRY_DSN | (dev用DSN) | (staging用DSN) | (prod用DSN) | Sentry DSN |
| NEXT_PUBLIC_APP_INSIGHTS_KEY | (dev用key) | (staging用key) | (prod用key) | Application Insights |
| NEXT_PUBLIC_FEATURE_AI | false | true | false | AI機能フラグ |

#### バックエンド設定

| 設定名 | dev | staging | production | 説明 |
|--------|-----|---------|------------|------|
| APP_ENV | development | staging | production | 環境識別子 |
| LOG_LEVEL | DEBUG | INFO | WARNING | ログレベル |
| CORS_ORIGINS | * | https://staging.itscm.example.com | https://itscm.example.com | CORS許可オリジン |
| MAX_WORKERS | 2 | 4 | 8 | Uvicornワーカー数 |
| DB_POOL_SIZE | 5 | 10 | 20 | DBコネクションプールサイズ |
| DB_POOL_MAX_OVERFLOW | 5 | 10 | 20 | DBプール最大オーバーフロー |
| REDIS_MAX_CONNECTIONS | 10 | 50 | 100 | Redis最大接続数 |
| CELERY_CONCURRENCY | 2 | 4 | 8 | Celery並行数 |
| CELERY_PREFETCH_MULTIPLIER | 1 | 2 | 4 | Celeryプリフェッチ |
| SESSION_TIMEOUT | 3600 | 1800 | 1800 | セッションタイムアウト(秒) |
| RATE_LIMIT | 1000/min | 500/min | 100/min | APIレートリミット |
| ENABLE_DOCS | true | true | false | Swagger UI有効化 |

#### シークレット（Azure Key Vault管理）

| シークレット名 | 用途 | ローテーション周期 |
|-------------|------|-----------------|
| DATABASE-URL | PostgreSQL接続文字列 | 90日 |
| REDIS-URL | Redis接続文字列 | 90日 |
| SECRET-KEY | アプリケーションシークレットキー | 90日 |
| AZURE-AD-CLIENT-SECRET | Azure AD認証クライアントシークレット | 365日 |
| AZURE-AD-TENANT-ID | Azure ADテナントID | - (変更なし) |
| STORAGE-CONNECTION-STRING | Azure Storage接続文字列 | 90日 |
| SENDGRID-API-KEY | メール送信APIキー | 365日 |
| SENTRY-DSN | Sentry接続DSN | - (変更なし) |
| ENCRYPTION-KEY | データ暗号化キー | 365日 |
| JWT-SECRET-KEY | JWTトークン署名キー | 90日 |

---

## 4. コンテナイメージ管理

### 4.1 Azure Container Registry (ACR)

```
ACR名: itscmacr.azurecr.io
SKU: Premium（Geo-replication対応）
レプリケーション: East Japan + West Japan

リポジトリ構成:
  itscmacr.azurecr.io/
    ├── itscm-frontend        # Next.jsフロントエンド
    ├── itscm-api             # FastAPIバックエンド
    ├── itscm-worker          # Celery Worker
    ├── itscm-migration       # DBマイグレーション用
    └── itscm-tools           # 運用ツール
```

### 4.2 イメージビルド仕様

#### フロントエンド Dockerfile

```dockerfile
# マルチステージビルド
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

#### バックエンド Dockerfile

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt > requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --from=builder /install /usr/local
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.3 イメージタグ戦略

| タグパターン | 生成タイミング | 用途 | 保持期間 |
|------------|-------------|------|---------|
| `v1.0.0` | リリースタグ時 | 本番デプロイ | 永久 |
| `v1.0.0-rc.1` | RCタグ時 | ステージングデプロイ | 90日 |
| `v1.0.0-beta.1` | Betaタグ時 | ステージングデプロイ | 60日 |
| `sha-abc1234` | 全コミット | 開発デプロイ | 30日 |
| `develop` | develop pushごと | dev環境自動デプロイ | 最新のみ |
| `latest` | GAリリース時 | 最新安定版参照 | 最新のみ |

### 4.4 イメージスキャン・署名

```bash
# ビルド時の脆弱性スキャン
trivy image --severity HIGH,CRITICAL \
  itscmacr.azurecr.io/itscm-api:v1.0.0

# ACR組み込みスキャン（Microsoft Defender for Containers）
az acr manifest list-metadata \
  --registry itscmacr \
  --name itscm-api \
  --query "[?vulnerabilities]"

# イメージ署名（Notation / Cosign）
cosign sign --key cosign.key \
  itscmacr.azurecr.io/itscm-api:v1.0.0

# 署名検証
cosign verify --key cosign.pub \
  itscmacr.azurecr.io/itscm-api:v1.0.0
```

### 4.5 イメージ保持ポリシー

```bash
# ACR保持ポリシーの設定
az acr config retention update \
  --registry itscmacr \
  --status enabled \
  --days 90 \
  --type UntaggedManifests

# 古いイメージの定期クリーンアップ
az acr run \
  --registry itscmacr \
  --cmd "acr purge \
    --filter 'itscm-api:sha-*' \
    --ago 30d \
    --untagged \
    --keep 10" \
  /dev/null
```

---

## 5. 環境変数・シークレット管理

### 5.1 Azure Key Vault構成

| Key Vault | リージョン | 用途 | SKU |
|-----------|----------|------|-----|
| kv-itscm-dev | East Japan | dev環境シークレット | Standard |
| kv-itscm-staging-eastjp | East Japan | staging環境シークレット | Standard |
| kv-itscm-staging-westjp | West Japan | staging環境シークレット | Standard |
| kv-itscm-prod-eastjp | East Japan | production環境シークレット | Premium (HSM) |
| kv-itscm-prod-westjp | West Japan | production環境シークレット | Premium (HSM) |

### 5.2 Key Vaultアクセスポリシー

```
Role-Based Access Control (RBAC):

┌─────────────────────────────────┐
│ Key Vault: kv-itscm-prod-eastjp │
├─────────────────────────────────┤
│                                 │
│ Key Vault Administrator         │
│   └── CTO, CISO               │
│                                 │
│ Key Vault Secrets Officer       │
│   └── DevOps Team Lead         │
│                                 │
│ Key Vault Secrets User          │
│   └── Container Apps           │
│       (Managed Identity)       │
│                                 │
│ Key Vault Reader                │
│   └── 開発チーム (read-only)    │
│                                 │
└─────────────────────────────────┘
```

### 5.3 シークレットローテーション

```bash
# シークレットローテーションの手順

# 1. 新しいシークレット値の生成
NEW_SECRET=$(openssl rand -base64 32)

# 2. Key Vaultにバージョニングして保存
az keyvault secret set \
  --vault-name kv-itscm-prod-eastjp \
  --name "JWT-SECRET-KEY" \
  --value "${NEW_SECRET}" \
  --tags "rotated=$(date +%Y-%m-%d)" "rotatedBy=automation"

# 3. Container Appsのシークレット参照を更新
az containerapp secret set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --secrets "jwt-secret=keyvaultref:kv-itscm-prod-eastjp/JWT-SECRET-KEY,identityref:/subscriptions/{sub}/resourcegroups/rg-itscm-prod-eastjp/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-itscm-prod"

# 4. アプリケーションの再起動（新シークレットの読み込み）
az containerapp revision restart \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision itscm-api-prod--v1-0-0

# 5. West Japanも同様に実施
```

### 5.4 環境変数のContainer Apps設定

```bash
# 環境変数の一括設定
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --set-env-vars \
    "APP_ENV=production" \
    "LOG_LEVEL=WARNING" \
    "CORS_ORIGINS=https://itscm.example.com" \
    "MAX_WORKERS=8" \
    "DB_POOL_SIZE=20" \
    "REDIS_MAX_CONNECTIONS=100" \
    "CELERY_CONCURRENCY=8" \
    "ENABLE_DOCS=false" \
    "DATABASE_URL=secretref:database-url" \
    "REDIS_URL=secretref:redis-url" \
    "SECRET_KEY=secretref:secret-key" \
    "JWT_SECRET_KEY=secretref:jwt-secret"

# 設定値の確認（シークレットはマスク表示）
az containerapp show \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --query "properties.template.containers[0].env" \
  --output table
```

---

## 6. Terraform状態管理

### 6.1 Terraformプロジェクト構成

```
infrastructure/
├── modules/                          # 再利用可能モジュール
│   ├── container-apps/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── postgresql/
│   ├── redis/
│   ├── key-vault/
│   ├── front-door/
│   ├── monitoring/
│   └── networking/
│
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── backend.tf
│
├── global/                           # グローバルリソース
│   ├── front-door/
│   ├── dns/
│   └── acr/
│
└── scripts/
    ├── init.sh
    ├── plan.sh
    └── apply.sh
```

### 6.2 Terraform State管理

```
State管理方式: Azure Blob Storage (Remote Backend)

Storage Account構成:
┌──────────────────────────────────────────┐
│ Storage Account: stitscmtfstate           │
│ SKU: Standard_GRS (Geo冗長)               │
│ Encryption: Microsoft Managed Keys       │
├──────────────────────────────────────────┤
│ Container: tfstate-dev                    │
│   └── dev.tfstate                        │
│                                          │
│ Container: tfstate-staging                │
│   └── staging.tfstate                    │
│                                          │
│ Container: tfstate-production             │
│   └── production.tfstate                 │
│                                          │
│ Container: tfstate-global                 │
│   └── global.tfstate                     │
└──────────────────────────────────────────┘
```

### 6.3 バックエンド設定例

```hcl
# environments/production/backend.tf
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-itscm-tfstate"
    storage_account_name = "stitscmtfstate"
    container_name       = "tfstate-production"
    key                  = "production.tfstate"
    use_oidc             = true
    subscription_id      = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
}
```

### 6.4 Terraform実行フロー

```
PR作成 → terraform plan → レビュー → マージ → terraform apply

詳細:
1. 開発者がインフラ変更のPRを作成
2. GitHub Actionsで自動的に terraform plan を実行
3. planの結果をPRにコメントとして投稿
4. レビュアーがplan結果を確認・承認
5. mainブランチへのマージをトリガーに terraform apply を実行
6. apply結果を通知
```

```yaml
# .github/workflows/terraform.yml の概要
name: Terraform
on:
  pull_request:
    paths: ['infrastructure/**']
  push:
    branches: [main]
    paths: ['infrastructure/**']

jobs:
  plan:
    if: github.event_name == 'pull_request'
    steps:
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform plan -out=tfplan
      - run: terraform show -no-color tfplan > plan.txt
      # PRにplan結果をコメント

  apply:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform apply -auto-approve
```

### 6.5 Terraform State ロック

```bash
# State ロックの確認
az storage blob show \
  --account-name stitscmtfstate \
  --container-name tfstate-production \
  --name production.tfstate \
  --query "properties.lease.status"

# 強制ロック解除（緊急時のみ）
terraform force-unlock <LOCK_ID>
```

### 6.6 Terraform Stateのバックアップ・復元

```bash
# Stateのバックアップ（apply前に自動実行）
az storage blob copy start \
  --account-name stitscmtfstate \
  --destination-container tfstate-backup \
  --destination-blob "production.tfstate.$(date +%Y%m%d%H%M%S)" \
  --source-uri "https://stitscmtfstate.blob.core.windows.net/tfstate-production/production.tfstate"

# Stateの復元（ロールバック時）
az storage blob copy start \
  --account-name stitscmtfstate \
  --destination-container tfstate-production \
  --destination-blob production.tfstate \
  --source-uri "https://stitscmtfstate.blob.core.windows.net/tfstate-backup/production.tfstate.20260624220000"

# バージョニングによる復元
az storage blob restore \
  --account-name stitscmtfstate \
  --time-to-restore "2026-06-24T22:00:00Z"
```

---

## 7. 構成変更管理プロセス

### 7.1 構成変更フロー

```
変更要求 → 影響度評価 → レビュー → テスト → デプロイ → 確認
    │          │           │         │        │        │
    │          │           │         │        │        └ 本番動作確認
    │          │           │         │        └ terraform apply
    │          │           │         └ staging環境で検証
    │          │           └ PRレビュー・承認
    │          └ 影響範囲・リスク評価
    └ GitHub Issue作成
```

### 7.2 構成変更承認マトリクス

| 変更種別 | 影響度 | 承認者 | テスト要件 |
|---------|--------|--------|----------|
| 環境変数変更（非シークレット） | 低 | テックリード | staging確認 |
| シークレット変更 | 中 | テックリード + CISO | staging確認 |
| スケール設定変更 | 中 | テックリード + 運用マネージャー | 負荷テスト |
| ネットワーク設定変更 | 高 | CTO + CISO | staging全テスト |
| リージョン構成変更 | 高 | CTO + 運用マネージャー | DR訓練 |
| SKU/リソース変更 | 中 | テックリード + 経営企画 | パフォーマンステスト |

### 7.3 構成ドリフト検出

```bash
# Terraformによるドリフト検出（定期実行）
terraform plan -detailed-exitcode
# Exit code: 0=差分なし, 1=エラー, 2=差分あり

# ドリフト検出のGitHub Actions（毎日実行）
# .github/workflows/drift-detection.yml
# ドリフト検出時にSlack通知
```

### 7.4 構成の監査

| 監査項目 | 頻度 | ツール | 担当 |
|---------|------|--------|------|
| Terraformドリフト検出 | 毎日 | GitHub Actions | DevOps |
| Key Vaultアクセスログ | リアルタイム | Azure Monitor | セキュリティ |
| コンテナイメージ脆弱性 | 毎日 | Microsoft Defender | セキュリティ |
| 環境間設定差分 | 週次 | カスタムスクリプト | DevOps |
| RBAC権限レビュー | 月次 | Azure AD | セキュリティ |

---

## 関連文書

| 文書番号 | 文書名 |
|---------|--------|
| ITSCM-RM-001 | リリース計画書 |
| ITSCM-RM-002 | リリース手順書 |
| ITSCM-RM-005 | 変更管理プロセス |
| ITSCM-OP-001 | 運用手順書 |
| ITSCM-OP-002 | 監視設計書 |
| ITSCM-OP-005 | DR手順書 |

---

以上
