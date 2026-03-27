# リリース手順書（Release Procedure）

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-RM-002 |
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
2. [リリースフロー全体像](#2-リリースフロー全体像)
3. [リリース前準備](#3-リリース前準備)
4. [コードフリーズ手順](#4-コードフリーズ手順)
5. [ビルド・テスト手順](#5-ビルドテスト手順)
6. [Blue-Greenデプロイメント手順](#6-blue-greenデプロイメント手順)
7. [カナリアリリース手順](#7-カナリアリリース手順)
8. [マルチリージョン展開手順](#8-マルチリージョン展開手順)
9. [リリース前チェックリスト](#9-リリース前チェックリスト)
10. [リリース後確認項目](#10-リリース後確認項目)
11. [緊急リリース手順](#11-緊急リリース手順)

---

## 1. 概要

### 1.1 目的

本文書は、IT-BCP-ITSCMシステムのリリース作業を安全かつ確実に実施するための詳細手順を定義する。コードフリーズからビルド、テスト、デプロイ、確認までの全工程をステップバイステップで記載する。

### 1.2 前提条件

- リリース計画書（ITSCM-RM-001）に基づくリリース承認が完了していること
- ステージング環境での検証が全て合格していること
- ロールバック手順書（ITSCM-RM-003）が最新化されていること
- 運用チームへのリリース通知が完了していること

### 1.3 リリース種別

| 種別 | 説明 | デプロイ方式 | 承認レベル |
|------|------|------------|----------|
| 通常リリース | 計画されたフェーズリリース | Blue-Green | 全ステージ承認 |
| マイナーリリース | 機能追加・改善 | Blue-Green or カナリア | ステージ1-4承認 |
| パッチリリース | バグ修正 | カナリア | ステージ1-3承認 |
| ホットフィックス | 緊急バグ修正 | ローリング | 緊急承認 |
| セキュリティパッチ | 脆弱性修正 | 即時 | 緊急承認 |

---

## 2. リリースフロー全体像

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        リリースフロー全体像                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: 準備                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ リリース  │→│ コード   │→│ リリース  │→│ 承認取得  │                    │
│  │ 計画確認  │  │ フリーズ  │  │ ブランチ  │  │          │                    │
│  └──────────┘  └──────────┘  │ 作成     │  └──────────┘                    │
│                              └──────────┘                                    │
│  Phase 2: ビルド・テスト                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ ビルド   │→│ 自動テスト │→│ ステージ  │→│ 検証・承認 │                    │
│  │ 実行     │  │ 実行     │  │ デプロイ  │  │          │                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                    │
│                                                                              │
│  Phase 3: デプロイ                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ 本番前   │→│ East JP  │→│ 動作確認  │→│ West JP  │                    │
│  │ バックアップ│  │ デプロイ  │  │          │  │ デプロイ  │                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                    │
│                                                                              │
│  Phase 4: 確認・完了                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ 統合動作  │→│ 監視確認  │→│ リリース  │→│ リリース  │                    │
│  │ 確認     │  │          │  │ ノート公開 │  │ 完了報告  │                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. リリース前準備

### 3.1 リリース計画確認（T-5日）

**担当**: プロジェクトマネージャー / リリースマネージャー

```
手順:
1. リリース計画書の最終確認
   - リリーススコープ（含まれる機能・修正の確認）
   - リリーススケジュールの確認
   - リソース・担当者のアサイン確認

2. リリース会議の開催
   - 参加者: 開発リーダー、QAリーダー、運用リーダー、セキュリティ担当
   - 議題: スコープ確認、リスク確認、スケジュール確認
   - 議事録作成・配布

3. リリース通知の送信
   - 対象: 全ステークホルダー
   - 内容: リリース日時、影響範囲、メンテナンス窓
```

### 3.2 環境確認（T-3日）

**担当**: インフラチーム / DevOpsエンジニア

```bash
# ステージング環境の状態確認
az containerapp show \
  --name itscm-api-staging \
  --resource-group rg-itscm-staging \
  --query "{status:properties.runningStatus, replicas:properties.template.scale}"

# 本番環境の現在のバージョン確認
az containerapp show \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --query "properties.template.containers[0].image"

# データベース状態確認
az postgres flexible-server show \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "{state:state, version:version}"

# Redis Cluster状態確認
az redis show \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "{provisioningState:provisioningState, redisVersion:redisVersion}"
```

### 3.3 バックアップの事前取得（T-1日）

**担当**: DBA / インフラチーム

```bash
# PostgreSQL フルバックアップの取得
az postgres flexible-server backup create \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --backup-name "pre-release-$(date +%Y%m%d-%H%M%S)"

# Redis RDBスナップショット取得
az redis export \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --prefix "pre-release-$(date +%Y%m%d)" \
  --container "https://itscmbackup.blob.core.windows.net/redis-backup" \
  --file-format RDB

# Blob Storageバックアップ確認
az storage blob list \
  --account-name itscmbackup \
  --container-name db-backup \
  --query "[?contains(name,'pre-release')].{name:name,date:properties.lastModified}" \
  --output table
```

---

## 4. コードフリーズ手順

### 4.1 コードフリーズ宣言（T-5日）

**担当**: テックリード / 開発マネージャー

```bash
# 1. リリースブランチの作成
git checkout develop
git pull origin develop
git checkout -b release/v1.0.0

# 2. バージョン番号の更新
# package.json (フロントエンド)
cd frontend
npm version 1.0.0 --no-git-tag-version

# pyproject.toml (バックエンド)
cd ../backend
sed -i 's/version = ".*"/version = "1.0.0"/' pyproject.toml

# 3. コミット・プッシュ
git add -A
git commit -m "chore: bump version to v1.0.0 for release"
git push origin release/v1.0.0

# 4. developブランチの保護設定
# GitHub UI または gh CLI でブランチ保護を設定
gh api repos/{owner}/{repo}/branches/release/v1.0.0/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci/test","ci/lint","ci/security"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":2}'
```

### 4.2 コードフリーズ期間中の変更管理

```
コードフリーズ期間中に許可される変更:
  - リリースブロッカーとなるバグ修正
  - ドキュメントの修正
  - 設定値の調整

許可されない変更:
  - 新規機能の追加
  - リファクタリング
  - 依存ライブラリのアップデート（セキュリティ修正除く）

変更が必要な場合の手順:
  1. リリースマネージャーに変更要求を提出
  2. 影響度評価を実施
  3. リリースマネージャーの承認を取得
  4. PR作成 → レビュー → マージ
```

---

## 5. ビルド・テスト手順

### 5.1 CIパイプラインによる自動ビルド

**担当**: DevOpsエンジニア

GitHub Actionsワークフローが自動実行される:

```yaml
# .github/workflows/release.yml の概要
name: Release Pipeline
on:
  push:
    branches: ['release/*']

jobs:
  # ステップ1: コード品質チェック
  lint:
    - ESLint / Prettier (フロントエンド)
    - Ruff / Black (バックエンド)
    - hadolint (Dockerfile)

  # ステップ2: セキュリティスキャン
  security:
    - Trivy (コンテナ脆弱性)
    - Semgrep (SAST)
    - GitLeaks (シークレット検出)

  # ステップ3: テスト実行
  test:
    - Jest / React Testing Library (フロントエンド)
    - pytest (バックエンド)
    - E2E テスト (Playwright)

  # ステップ4: ビルド
  build:
    - Next.js ビルド
    - Docker イメージビルド
    - イメージのACRへのプッシュ

  # ステップ5: ステージングデプロイ
  deploy-staging:
    - ステージング環境へのデプロイ
    - スモークテスト実行
```

### 5.2 コンテナイメージのビルド

```bash
# フロントエンド イメージビルド
docker build \
  --file frontend/Dockerfile \
  --tag itscmacr.azurecr.io/itscm-frontend:v1.0.0 \
  --tag itscmacr.azurecr.io/itscm-frontend:sha-$(git rev-parse --short HEAD) \
  --build-arg NEXT_PUBLIC_API_URL=https://api.itscm.example.com \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  ./frontend

# バックエンド イメージビルド
docker build \
  --file backend/Dockerfile \
  --tag itscmacr.azurecr.io/itscm-api:v1.0.0 \
  --tag itscmacr.azurecr.io/itscm-api:sha-$(git rev-parse --short HEAD) \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  ./backend

# Celery Worker イメージビルド
docker build \
  --file backend/Dockerfile.worker \
  --tag itscmacr.azurecr.io/itscm-worker:v1.0.0 \
  --tag itscmacr.azurecr.io/itscm-worker:sha-$(git rev-parse --short HEAD) \
  ./backend

# ACRへのプッシュ
az acr login --name itscmacr
docker push itscmacr.azurecr.io/itscm-frontend:v1.0.0
docker push itscmacr.azurecr.io/itscm-api:v1.0.0
docker push itscmacr.azurecr.io/itscm-worker:v1.0.0
```

### 5.3 ステージング環境デプロイ

```bash
# ステージング環境へのデプロイ
# フロントエンド
az containerapp update \
  --name itscm-frontend-staging \
  --resource-group rg-itscm-staging \
  --image itscmacr.azurecr.io/itscm-frontend:v1.0.0

# バックエンドAPI
az containerapp update \
  --name itscm-api-staging \
  --resource-group rg-itscm-staging \
  --image itscmacr.azurecr.io/itscm-api:v1.0.0

# Celery Worker
az containerapp update \
  --name itscm-worker-staging \
  --resource-group rg-itscm-staging \
  --image itscmacr.azurecr.io/itscm-worker:v1.0.0

# データベースマイグレーション（ステージング）
az containerapp exec \
  --name itscm-api-staging \
  --resource-group rg-itscm-staging \
  --command "alembic upgrade head"

# スモークテスト実行
curl -f https://staging.itscm.example.com/api/health || echo "FAILED"
curl -f https://staging.itscm.example.com/ || echo "FAILED"
```

### 5.4 ステージング検証

```bash
# E2Eテスト実行
cd tests/e2e
npx playwright test --config=playwright.staging.config.ts

# パフォーマンステスト
cd tests/performance
k6 run --env ENV=staging load-test.js

# セキュリティスキャン
docker run --rm owasp/zap2docker-stable zap-baseline.py \
  -t https://staging.itscm.example.com \
  -r zap-report.html
```

---

## 6. Blue-Greenデプロイメント手順

### 6.1 概要

```
                    Azure Front Door
                         │
              ┌──────────┴──────────┐
              │                     │
         ┌────▼────┐          ┌────▼────┐
         │  Blue   │          │  Green  │
         │ (現行)  │          │ (新版)  │
         │ v0.9.0  │          │ v1.0.0  │
         └─────────┘          └─────────┘

Phase 1: Green環境に新バージョンをデプロイ
Phase 2: Green環境の動作確認
Phase 3: トラフィックをGreen環境に切替
Phase 4: Blue環境を保持（ロールバック用）
Phase 5: 安定確認後、Blue環境を更新
```

### 6.2 East Japan（Primary）Blue-Greenデプロイ手順

#### Step 1: Green環境のプロビジョニング確認

```bash
# Green環境（新バージョン用リビジョン）の状態確認
az containerapp revision list \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --query "[].{name:name, active:properties.active, traffic:properties.trafficWeight, replicas:properties.replicas}" \
  --output table
```

#### Step 2: 新バージョンのデプロイ（Green環境）

```bash
# フロントエンド - 新リビジョン作成（トラフィック0%）
az containerapp update \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-frontend:v1.0.0 \
  --revision-suffix v1-0-0 \
  --set-env-vars "APP_VERSION=v1.0.0"

# バックエンドAPI - 新リビジョン作成（トラフィック0%）
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-api:v1.0.0 \
  --revision-suffix v1-0-0 \
  --set-env-vars "APP_VERSION=v1.0.0"

# Celery Worker - 新リビジョン作成
az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-worker:v1.0.0 \
  --revision-suffix v1-0-0
```

#### Step 3: データベースマイグレーション

```bash
# マイグレーション前にバックアップ確認
az postgres flexible-server backup list \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "[0].{name:name, completedTime:completedTime}" \
  --output table

# マイグレーション実行（後方互換性のあるマイグレーションのみ）
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision itscm-api-prod--v1-0-0 \
  --command "alembic upgrade head"

# マイグレーション結果確認
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision itscm-api-prod--v1-0-0 \
  --command "alembic current"
```

#### Step 4: Green環境の動作確認

```bash
# Green環境の直接ヘルスチェック
REVISION_URL=$(az containerapp revision show \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision itscm-api-prod--v1-0-0 \
  --query "properties.fqdn" -o tsv)

curl -f "https://${REVISION_URL}/api/health"
curl -f "https://${REVISION_URL}/api/version"

# スモークテスト
curl -f "https://${REVISION_URL}/api/health/db"
curl -f "https://${REVISION_URL}/api/health/redis"
curl -f "https://${REVISION_URL}/api/health/celery"
```

#### Step 5: トラフィック切替

```bash
# トラフィックをGreen環境に100%切替
# フロントエンド
az containerapp ingress traffic set \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight itscm-frontend-prod--v1-0-0=100

# バックエンドAPI
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight itscm-api-prod--v1-0-0=100

# トラフィック配分確認
az containerapp ingress traffic show \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --output table
```

#### Step 6: Blue環境の旧リビジョン保持

```bash
# 旧リビジョンを非アクティブ化せず保持（ロールバック用、72時間）
echo "旧リビジョンはロールバック用に72時間保持"
echo "72時間後に自動クリーンアップスクリプトにより非アクティブ化"

# 旧リビジョン一覧の記録
az containerapp revision list \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --query "[?properties.active].{name:name, created:properties.createdTime, traffic:properties.trafficWeight}" \
  --output table > /tmp/revision-history-$(date +%Y%m%d).txt
```

---

## 7. カナリアリリース手順

### 7.1 概要

段階的にトラフィックを新バージョンに移行し、問題がないことを確認しながらロールアウトする方式。

```
Phase 1: 5%  のトラフィックを新バージョンへ → 15分間監視
Phase 2: 25% のトラフィックを新バージョンへ → 30分間監視
Phase 3: 50% のトラフィックを新バージョンへ → 30分間監視
Phase 4: 100% のトラフィックを新バージョンへ → 完了
```

### 7.2 カナリアデプロイ手順

#### Phase 1: 5%トラフィック

```bash
# 新リビジョンに5%のトラフィックを割り当て
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight \
    itscm-api-prod--v0-9-0=95 \
    itscm-api-prod--v1-0-0=5

# 15分間のモニタリング
echo "=== カナリア Phase 1: 5% トラフィック ==="
echo "監視項目:"
echo "  - エラーレート: < 0.1%"
echo "  - レイテンシ p95: < 200ms"
echo "  - HTTP 5xx: 0件"
echo "  - CPU/メモリ使用率: 正常範囲"
echo ""
echo "Azure Monitor ダッシュボード: https://portal.azure.com/..."
echo ""
echo "15分間監視し、問題がなければ Phase 2 に進む"
```

#### Phase 2: 25%トラフィック

```bash
# 25%に増加
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight \
    itscm-api-prod--v0-9-0=75 \
    itscm-api-prod--v1-0-0=25

echo "=== カナリア Phase 2: 25% トラフィック ==="
echo "30分間監視"
```

#### Phase 3: 50%トラフィック

```bash
# 50%に増加
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight \
    itscm-api-prod--v0-9-0=50 \
    itscm-api-prod--v1-0-0=50

echo "=== カナリア Phase 3: 50% トラフィック ==="
echo "30分間監視"
```

#### Phase 4: 100%トラフィック

```bash
# 100%切替
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight itscm-api-prod--v1-0-0=100

echo "=== カナリア Phase 4: 100% トラフィック ==="
echo "カナリアリリース完了"
```

### 7.3 カナリア中止基準

以下の条件に該当する場合、即座にロールバックを実行する:

| 条件 | 閾値 | 対応 |
|------|------|------|
| HTTP 5xxエラーレート | > 1% | 即時ロールバック |
| APIレイテンシ p95 | > 500ms | 即時ロールバック |
| アプリケーション例外 | 急増（通常の5倍以上） | 即時ロールバック |
| ヘルスチェック失敗 | 3回連続失敗 | 即時ロールバック |
| メモリ使用量 | > 90% | 進行停止・調査 |
| CPU使用量 | > 85%（持続5分以上） | 進行停止・調査 |

```bash
# カナリアロールバック（即時）
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight itscm-api-prod--v0-9-0=100
```

---

## 8. マルチリージョン展開手順

### 8.1 展開戦略

```
                    Azure Front Door
                         │
              ┌──────────┴──────────┐
              │                     │
    ┌─────────▼─────────┐ ┌───────▼─────────────┐
    │   East Japan      │ │   West Japan         │
    │   (Primary)       │ │   (Standby)          │
    │                   │ │                      │
    │ ① 先にデプロイ     │ │ ③ East確認後デプロイ   │
    │ ② 動作確認        │ │ ④ 動作確認            │
    └───────────────────┘ └──────────────────────┘

展開順序:
  1. East Japan (Primary) にデプロイ
  2. East Japan の動作確認（最低30分）
  3. West Japan (Standby) にデプロイ
  4. West Japan の動作確認
  5. フェイルオーバーテスト（任意）
  6. 展開完了確認
```

### 8.2 East Japan（Primary）デプロイ

```bash
echo "=========================================="
echo "Phase 1: East Japan (Primary) デプロイ開始"
echo "=========================================="

# 1. リリース前バックアップの最終確認
az postgres flexible-server backup list \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "[0].{name:name,completedTime:completedTime}"

# 2. データベースマイグレーション（East Japan）
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "alembic upgrade head"

# 3. アプリケーションデプロイ（Blue-Green方式）
# （セクション6の手順に従う）

# 4. 動作確認
curl -f https://eastjp.itscm.example.com/api/health
curl -f https://eastjp.itscm.example.com/api/version

# 5. Azure Front Doorヘルスチェック確認
az network front-door backend-pool backend list \
  --front-door-name itscm-frontdoor \
  --resource-group rg-itscm-global \
  --pool-name itscm-backend-pool \
  --query "[?contains(address,'eastjp')].{address:address,enabled:enabledState,health:healthProbeSettings}" \
  --output table

echo "East Japan デプロイ完了 - 30分間監視"
```

### 8.3 West Japan（Standby）デプロイ

```bash
echo "=========================================="
echo "Phase 2: West Japan (Standby) デプロイ開始"
echo "=========================================="

# 前提: East Japanで30分間問題がないことを確認済み

# 1. データベースレプリケーション状態確認
az postgres flexible-server replica list \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "[].{name:name,state:state,replicationRole:replicationRole}" \
  --output table

# 2. West Japan データベースマイグレーション
# ※ Geo冗長構成の場合、East Japanのマイグレーションが自動レプリケーションされるため
# ※ レプリケーション完了を確認する
echo "レプリケーション遅延確認..."

# 3. West Japan アプリケーションデプロイ
# フロントエンド
az containerapp update \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-westjp \
  --image itscmacr.azurecr.io/itscm-frontend:v1.0.0 \
  --revision-suffix v1-0-0

# バックエンドAPI
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-westjp \
  --image itscmacr.azurecr.io/itscm-api:v1.0.0 \
  --revision-suffix v1-0-0

# Celery Worker
az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-westjp \
  --image itscmacr.azurecr.io/itscm-worker:v1.0.0 \
  --revision-suffix v1-0-0

# 4. West Japan トラフィック切替
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-westjp \
  --revision-weight itscm-api-prod--v1-0-0=100

# 5. 動作確認
curl -f https://westjp.itscm.example.com/api/health
curl -f https://westjp.itscm.example.com/api/version

echo "West Japan デプロイ完了"
```

### 8.4 統合確認

```bash
echo "=========================================="
echo "Phase 3: 統合確認"
echo "=========================================="

# 1. Azure Front Door経由のアクセス確認
curl -f https://itscm.example.com/api/health
curl -f https://itscm.example.com/api/version

# 2. 両リージョンのバージョン一致確認
EAST_VERSION=$(curl -s https://eastjp.itscm.example.com/api/version | jq -r '.version')
WEST_VERSION=$(curl -s https://westjp.itscm.example.com/api/version | jq -r '.version')

if [ "$EAST_VERSION" = "$WEST_VERSION" ]; then
  echo "OK: 両リージョンのバージョンが一致: $EAST_VERSION"
else
  echo "ERROR: バージョン不一致 East=$EAST_VERSION West=$WEST_VERSION"
  exit 1
fi

# 3. フェイルオーバーテスト（オプション）
echo "フェイルオーバーテストは運用チームの判断で実施"
```

---

## 9. リリース前チェックリスト

### 9.1 T-5日チェックリスト（コードフリーズ）

- [ ] リリーススコープの最終確認
- [ ] 全PRのレビュー・マージ完了
- [ ] コードフリーズ宣言
- [ ] リリースブランチ作成
- [ ] バージョン番号更新
- [ ] リリース通知送信（ステークホルダー全員）
- [ ] リリース会議開催・議事録作成

### 9.2 T-3日チェックリスト（ステージング検証）

- [ ] ステージング環境デプロイ完了
- [ ] 自動テスト全PASS
- [ ] E2Eテスト全PASS
- [ ] パフォーマンステスト目標達成
- [ ] セキュリティスキャン結果確認（Critical/High 0件）
- [ ] DB マイグレーションテスト完了
- [ ] API互換性確認
- [ ] PWA動作確認

### 9.3 T-1日チェックリスト（リリース前日）

- [ ] 全承認ステージの承認取得完了
- [ ] 本番バックアップ取得完了（DB、Redis、Blob）
- [ ] ロールバック手順の最新化・確認
- [ ] 運用チームへの最終ブリーフィング
- [ ] 監視ダッシュボード準備
- [ ] 連絡体制確認（オンコール担当、エスカレーション先）
- [ ] メンテナンスページ準備（必要な場合）
- [ ] リリース手順の最終確認（リハーサル）

### 9.4 当日チェックリスト（リリース直前）

- [ ] リリースウィンドウ開始確認
- [ ] 現在のシステム状態確認（正常稼働中）
- [ ] 直近のアラート確認（未解決アラートなし）
- [ ] バックアップ取得日時確認
- [ ] 全リリース担当者の参加確認
- [ ] コミュニケーションチャネル確認（Slack/Teams）
- [ ] Go/No-Go最終判定

---

## 10. リリース後確認項目

### 10.1 即時確認（デプロイ後0-15分）

| 確認項目 | 確認方法 | 期待結果 |
|---------|---------|---------|
| ヘルスチェック | `curl /api/health` | 200 OK |
| バージョン確認 | `curl /api/version` | v1.0.0 |
| DB接続 | `curl /api/health/db` | connected |
| Redis接続 | `curl /api/health/redis` | connected |
| Celery Worker | `curl /api/health/celery` | active |
| 認証機能 | ログインテスト | ログイン成功 |
| 主要API | 主要エンドポイントテスト | 正常応答 |
| フロントエンド | ブラウザアクセス | 正常表示 |

### 10.2 短期確認（デプロイ後15分-2時間）

| 確認項目 | 確認方法 | 期待結果 |
|---------|---------|---------|
| エラーレート | Azure Monitor | < 0.1% |
| レイテンシ | Application Insights | p95 < 200ms |
| CPU使用率 | Azure Monitor | < 70% |
| メモリ使用率 | Azure Monitor | < 80% |
| DB接続プール | PostgreSQL monitoring | 正常範囲 |
| Redis メモリ | Redis INFO | 正常範囲 |
| Celery キュー | Flower dashboard | キュー滞留なし |
| ログ確認 | Log Analytics | 異常ログなし |

### 10.3 中期確認（デプロイ後2-24時間）

| 確認項目 | 確認方法 | 期待結果 |
|---------|---------|---------|
| メモリリーク | メモリ使用量推移 | 安定 |
| ディスク使用量 | Azure Monitor | 増加率正常 |
| バッチ処理 | Celery ログ | 正常完了 |
| 定期バックアップ | バックアップログ | 正常取得 |
| レプリケーション | DB レプリカ遅延 | < 1秒 |
| ユーザーフィードバック | サポートチケット | 重大問題なし |

### 10.4 長期確認（デプロイ後1-7日）

| 確認項目 | 確認方法 | 期待結果 |
|---------|---------|---------|
| SLA達成状況 | SLAレポート | 99.9%以上 |
| パフォーマンス推移 | 週次レポート | 劣化なし |
| エラー傾向 | エラーレポート | 増加傾向なし |
| ユーザー行動分析 | Application Insights | 想定通り |
| セキュリティイベント | Azure Sentinel | 異常なし |

### 10.5 リリース完了手続き

```bash
# 1. Gitタグの作成
git checkout release/v1.0.0
git tag -a v1.0.0 -m "Phase 1 GA Release - IT-BCP-ITSCM-System v1.0.0"
git push origin v1.0.0

# 2. リリースブランチのmainへのマージ
git checkout main
git merge --no-ff release/v1.0.0 -m "Merge release/v1.0.0 into main"
git push origin main

# 3. developブランチへのマージ
git checkout develop
git merge --no-ff release/v1.0.0 -m "Merge release/v1.0.0 into develop"
git push origin develop

# 4. GitHub Release作成
gh release create v1.0.0 \
  --title "v1.0.0 - Phase 1 GA Release" \
  --notes-file RELEASE_NOTES.md

# 5. リリースブランチの削除
git branch -d release/v1.0.0
git push origin --delete release/v1.0.0

# 6. 旧リビジョンのクリーンアップ（72時間後）
echo "72時間後に旧リビジョンをクリーンアップ"
```

---

## 11. 緊急リリース手順

### 11.1 緊急リリースの定義

| 分類 | 条件 | 対応時間 |
|------|------|---------|
| P1-Critical | サービス全停止、データ損失リスク | 即時対応（30分以内にリリース開始） |
| P2-High | 主要機能障害、セキュリティ脆弱性 | 4時間以内にリリース |
| P3-Medium | 一部機能障害、回避策あり | 次営業日リリース |

### 11.2 緊急リリースフロー

```
検知/報告 → トリアージ → 緊急修正 → レビュー → 緊急テスト → 緊急承認 → デプロイ → 確認
   │          │           │         │          │           │          │        │
   5分       15分        30-120分    15分       15-30分      15分       15-30分   15分
```

### 11.3 緊急リリース手順

```bash
# 1. ホットフィックスブランチ作成
git checkout main
git checkout -b hotfix/v1.0.1
# 修正作業

# 2. 最小限のテスト
pytest tests/ -k "critical" --timeout=300
npx playwright test --grep "@critical"

# 3. 緊急ビルド
docker build --tag itscmacr.azurecr.io/itscm-api:v1.0.1 ./backend
az acr login --name itscmacr
docker push itscmacr.azurecr.io/itscm-api:v1.0.1

# 4. 緊急デプロイ（ローリングアップデート）
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-api:v1.0.1

# 5. 即時確認
curl -f https://itscm.example.com/api/health
curl -f https://itscm.example.com/api/version

# 6. West Japanへも展開
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-westjp \
  --image itscmacr.azurecr.io/itscm-api:v1.0.1

# 7. 事後処理
git checkout main
git merge --no-ff hotfix/v1.0.1
git tag -a v1.0.1 -m "Hotfix: [修正内容]"
git push origin main --tags
git checkout develop
git merge --no-ff hotfix/v1.0.1
git push origin develop
```

---

## 関連文書

| 文書番号 | 文書名 |
|---------|--------|
| ITSCM-RM-001 | リリース計画書 |
| ITSCM-RM-003 | ロールバック手順書 |
| ITSCM-RM-004 | デプロイメント構成管理 |
| ITSCM-RM-006 | リリースチェックリスト |
| ITSCM-OP-001 | 運用手順書 |
| ITSCM-OP-003 | 障害対応手順書 |

---

以上
