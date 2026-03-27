# ロールバック手順書（Rollback Procedure）

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-RM-003 |
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
2. [ロールバック判定基準](#2-ロールバック判定基準)
3. [ロールバックトリガー条件](#3-ロールバックトリガー条件)
4. [アプリケーションロールバック手順](#4-アプリケーションロールバック手順)
5. [データベースロールバック手順](#5-データベースロールバック手順)
6. [マルチリージョン環境でのロールバック手順](#6-マルチリージョン環境でのロールバック手順)
7. [部分ロールバック](#7-部分ロールバック)
8. [ロールバック後の対応](#8-ロールバック後の対応)
9. [ロールバック訓練](#9-ロールバック訓練)

---

## 1. 概要

### 1.1 目的

本文書は、IT-BCP-ITSCMシステムのリリースに問題が発生した場合のロールバック手順を定義する。迅速かつ安全にシステムを前バージョンに戻し、サービス影響を最小限に抑えることを目的とする。

### 1.2 ロールバック方針

| 方針 | 内容 |
|------|------|
| ロールバック猶予期間 | リリース後72時間以内は旧バージョンへの即時ロールバックが可能 |
| 最大ロールバック時間 | アプリケーション: 5分以内、DB含む: 30分以内 |
| ロールバック判断権限 | リリースマネージャー、運用マネージャー、CTO |
| ロールバック後の対応 | 原因分析 → 修正 → 再リリース |

### 1.3 ロールバック戦略の概要

```
┌──────────────────────────────────────────────────────────────┐
│                   ロールバック戦略マトリクス                     │
├──────────────────┬───────────────────────────────────────────┤
│ 状況              │ ロールバック方式                             │
├──────────────────┼───────────────────────────────────────────┤
│ アプリのみの問題    │ コンテナリビジョン切戻し（即時、5分以内）       │
│ DB変更なし        │                                           │
├──────────────────┼───────────────────────────────────────────┤
│ アプリ+DB変更      │ コンテナ切戻し + DBマイグレーション            │
│ 後方互換あり       │ ダウングレード（15分以内）                    │
├──────────────────┼───────────────────────────────────────────┤
│ アプリ+DB変更      │ コンテナ切戻し + DBバックアップリストア         │
│ 後方互換なし       │（30分以内、データ損失リスクあり）              │
├──────────────────┼───────────────────────────────────────────┤
│ インフラ変更含む    │ Terraform state切戻し + アプリ切戻し          │
│                  │（60分以内）                                 │
├──────────────────┼───────────────────────────────────────────┤
│ 一部コンポーネント  │ 部分ロールバック（該当コンポーネントのみ）       │
│ のみ問題          │                                           │
└──────────────────┴───────────────────────────────────────────┘
```

---

## 2. ロールバック判定基準

### 2.1 自動ロールバック基準

以下の条件に合致した場合、自動的にロールバックを開始する（監視システムによる自動トリガー）:

| 条件ID | 条件 | 閾値 | 検知方法 |
|--------|------|------|---------|
| AUTO-001 | ヘルスチェック連続失敗 | 5回連続失敗 | Azure Container Apps ヘルスプローブ |
| AUTO-002 | HTTP 5xxエラーレート急増 | > 5%（5分間平均） | Application Insights |
| AUTO-003 | 全レプリカ停止 | レプリカ数 = 0 | Azure Monitor |

### 2.2 手動ロールバック判定基準

以下の条件に合致した場合、リリースマネージャーの判断でロールバックを実行する:

| 条件ID | 条件 | 閾値 | 判定者 |
|--------|------|------|--------|
| MAN-001 | エラーレート増加 | > 1%（通常の10倍以上） | 運用チーム |
| MAN-002 | レイテンシ悪化 | p95 > 500ms（通常の2.5倍以上） | 運用チーム |
| MAN-003 | 主要機能障害 | クリティカルパスの機能停止 | リリースマネージャー |
| MAN-004 | データ不整合 | データ整合性チェック失敗 | DBA |
| MAN-005 | セキュリティ脆弱性発見 | Critical/High脆弱性 | CISO |
| MAN-006 | ユーザー影響大 | 重大クレーム/問い合わせ急増 | サービスデスク |
| MAN-007 | パフォーマンス劣化 | リソース使用量の異常増加 | 運用チーム |

### 2.3 ロールバック判定フロー

```
問題検知
  │
  ├── 自動検知（AUTO条件）──→ 自動ロールバック実行 ──→ 通知
  │
  └── 手動検知（MAN条件）
       │
       ├── 重大度評価
       │    ├── Critical: 即時ロールバック（リリースマネージャー単独判断可）
       │    ├── High: 15分以内にロールバック判定（運用+開発協議）
       │    └── Medium: 30分以内に判定（回避策検討後判断）
       │
       ├── ロールバック決定
       │    ├── ロールバック種別の決定
       │    ├── 影響範囲の確認
       │    └── 実行者のアサイン
       │
       └── ロールバック実行
```

---

## 3. ロールバックトリガー条件

### 3.1 アラートベースのトリガー

Azure Monitorのアラートルールとして設定:

```json
{
  "alertRules": [
    {
      "name": "rollback-trigger-5xx-rate",
      "description": "HTTP 5xxエラーレートが5%を超えた場合",
      "condition": {
        "metric": "Http5xx",
        "operator": "GreaterThan",
        "threshold": 5,
        "timeAggregation": "Average",
        "windowSize": "PT5M"
      },
      "severity": 0,
      "actionGroup": "ag-rollback-critical"
    },
    {
      "name": "rollback-trigger-latency",
      "description": "APIレイテンシp95が1秒を超えた場合",
      "condition": {
        "metric": "RequestDuration",
        "operator": "GreaterThan",
        "threshold": 1000,
        "timeAggregation": "Percentile95",
        "windowSize": "PT5M"
      },
      "severity": 1,
      "actionGroup": "ag-rollback-high"
    },
    {
      "name": "rollback-trigger-health",
      "description": "ヘルスチェック失敗",
      "condition": {
        "metric": "HealthCheckStatus",
        "operator": "LessThan",
        "threshold": 1,
        "timeAggregation": "Count",
        "windowSize": "PT2M"
      },
      "severity": 0,
      "actionGroup": "ag-rollback-critical"
    }
  ]
}
```

### 3.2 手動トリガー実行コマンド

```bash
# ロールバック手動実行スクリプト
# Usage: ./scripts/rollback.sh <component> <target-version> <region>

# 例: APIサーバーのロールバック（East Japan）
./scripts/rollback.sh api v0.9.0 eastjp

# 例: 全コンポーネントのロールバック（全リージョン）
./scripts/rollback.sh all v0.9.0 all
```

---

## 4. アプリケーションロールバック手順

### 4.1 コンテナリビジョン切戻し（最速、5分以内）

Blue-Greenデプロイメントの場合、旧リビジョンが保持されているため即時切戻しが可能。

#### Step 1: 現在のリビジョン状態確認

```bash
echo "=== ロールバック開始: $(date) ==="
echo "担当者: $(whoami)"

# 現在のリビジョン一覧確認
echo "--- フロントエンド ---"
az containerapp revision list \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-eastjp \
  --query "[].{name:name, active:properties.active, traffic:properties.trafficWeight, created:properties.createdTime}" \
  --output table

echo "--- バックエンドAPI ---"
az containerapp revision list \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --query "[].{name:name, active:properties.active, traffic:properties.trafficWeight, created:properties.createdTime}" \
  --output table

echo "--- Celery Worker ---"
az containerapp revision list \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-eastjp \
  --query "[].{name:name, active:properties.active, traffic:properties.trafficWeight, created:properties.createdTime}" \
  --output table
```

#### Step 2: トラフィック切戻し

```bash
# 旧リビジョン名を設定（実際のリビジョン名に置換すること）
OLD_FRONTEND_REVISION="itscm-frontend-prod--v0-9-0"
OLD_API_REVISION="itscm-api-prod--v0-9-0"
OLD_WORKER_REVISION="itscm-worker-prod--v0-9-0"

# フロントエンド: トラフィックを旧リビジョンに切替
az containerapp ingress traffic set \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight ${OLD_FRONTEND_REVISION}=100

# バックエンドAPI: トラフィックを旧リビジョンに切替
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight ${OLD_API_REVISION}=100

# Celery Worker: 旧リビジョンに切替
az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-worker:v0.9.0
```

#### Step 3: ロールバック確認

```bash
# ヘルスチェック
echo "--- ヘルスチェック ---"
curl -sf https://eastjp.itscm.example.com/api/health | jq .
curl -sf https://eastjp.itscm.example.com/api/version | jq .

# バージョン確認
echo "--- バージョン確認 ---"
CURRENT_VERSION=$(curl -sf https://eastjp.itscm.example.com/api/version | jq -r '.version')
echo "現在のバージョン: ${CURRENT_VERSION}"

if [ "${CURRENT_VERSION}" = "v0.9.0" ]; then
  echo "OK: ロールバック成功"
else
  echo "ERROR: ロールバック失敗 - 手動確認が必要"
fi

# トラフィック配分確認
az containerapp ingress traffic show \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --output table

echo "=== ロールバック完了: $(date) ==="
```

### 4.2 コンテナイメージ指定によるロールバック

旧リビジョンが利用できない場合（72時間経過後など）:

```bash
# 旧バージョンのイメージで新リビジョンを作成
# フロントエンド
az containerapp update \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-frontend:v0.9.0 \
  --revision-suffix rollback-$(date +%Y%m%d%H%M)

# バックエンドAPI
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-api:v0.9.0 \
  --revision-suffix rollback-$(date +%Y%m%d%H%M)

# Celery Worker
az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-worker:v0.9.0 \
  --revision-suffix rollback-$(date +%Y%m%d%H%M)

# トラフィック切替
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight latest=100
```

---

## 5. データベースロールバック手順

### 5.1 マイグレーションダウングレード（後方互換性あり）

リリース時のDBマイグレーションに後方互換性がある場合（カラム追加のみ、NOT NULL制約なし等）:

```bash
# 現在のマイグレーションバージョン確認
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "alembic current"

# マイグレーション履歴確認
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "alembic history --verbose"

# ダウングレード実行（1つ前のリビジョンに戻す）
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "alembic downgrade -1"

# 特定のリビジョンに戻す場合
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "alembic downgrade <target_revision_id>"

# ダウングレード確認
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "alembic current"
```

### 5.2 バックアップからのリストア（後方互換性なし）

データベース構造の破壊的変更を含むマイグレーションの場合:

```bash
echo "=== データベースロールバック（バックアップリストア）==="
echo "WARNING: RPO以降のデータが失われる可能性があります"
echo ""

# Step 1: アプリケーションの停止（新規書き込み防止）
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --scale-rule-name http-rule \
  --min-replicas 0 \
  --max-replicas 0

# Step 2: 利用可能なバックアップの確認
az postgres flexible-server backup list \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "[].{name:name, completedTime:completedTime, source:backupType}" \
  --output table

# Step 3: ポイントインタイムリストア（PITRを使用）
# リリース開始前の時刻を指定
RESTORE_TIME="2026-06-24T21:55:00Z"  # リリース開始5分前

az postgres flexible-server restore \
  --name itscm-db-prod-eastjp-restored \
  --resource-group rg-itscm-prod-eastjp \
  --source-server itscm-db-prod-eastjp \
  --restore-time "${RESTORE_TIME}"

# Step 4: リストアされたDBの整合性確認
# （接続先を一時的にリストアDBに変更して確認）
psql -h itscm-db-prod-eastjp-restored.postgres.database.azure.com \
  -U itscm_admin -d itscm_prod \
  -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"

# Step 5: 接続先の切替
# 環境変数のDATABASE_URLをリストアDBに変更
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --set-env-vars "DATABASE_URL=postgresql://itscm_admin:****@itscm-db-prod-eastjp-restored.postgres.database.azure.com:5432/itscm_prod"

# Step 6: アプリケーションの再開（旧バージョン）
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-api:v0.9.0 \
  --scale-rule-name http-rule \
  --min-replicas 2 \
  --max-replicas 10

# Step 7: データ整合性確認
curl -sf https://eastjp.itscm.example.com/api/health/db | jq .

echo "=== データベースロールバック完了 ==="
echo "注意: ${RESTORE_TIME} 以降のデータは失われています"
```

### 5.3 Redisキャッシュのロールバック

```bash
# Redis Clusterのフラッシュ（キャッシュデータの場合）
az redis flush \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp

# セッションデータの復元が必要な場合
# バックアップからのインポート
az redis import \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --files "https://itscmbackup.blob.core.windows.net/redis-backup/pre-release-20260624.rdb" \
  --file-format RDB
```

---

## 6. マルチリージョン環境でのロールバック手順

### 6.1 ロールバックシナリオ

```
シナリオA: East Japanのみに問題がある場合
  → East Japanのみロールバック、West Japanは現行維持

シナリオB: 両リージョンに問題がある場合
  → 両リージョン同時ロールバック

シナリオC: West Japanデプロイ前にEast Japanで問題発覚
  → East Japanのみロールバック、West Japanはデプロイ中止
```

### 6.2 シナリオA: East Japanのみロールバック

```bash
echo "=== シナリオA: East Japan単独ロールバック ==="

# Step 1: Azure Front Doorでのトラフィック制御
# East Japanへのトラフィックを一時的にWest Japanにフェイルオーバー
az network front-door backend-pool backend update \
  --front-door-name itscm-frontdoor \
  --resource-group rg-itscm-global \
  --pool-name itscm-backend-pool \
  --address eastjp.itscm.example.com \
  --enabled-state Disabled

echo "East Japanトラフィック停止 → West Japanで処理中"

# Step 2: East Japanロールバック実行
# （セクション4の手順に従う）
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight itscm-api-prod--v0-9-0=100

# Step 3: East Japan動作確認
curl -sf https://eastjp.itscm.example.com/api/health | jq .

# Step 4: Azure Front DoorでEast Japanを再有効化
az network front-door backend-pool backend update \
  --front-door-name itscm-frontdoor \
  --resource-group rg-itscm-global \
  --pool-name itscm-backend-pool \
  --address eastjp.itscm.example.com \
  --enabled-state Enabled

echo "East Japanロールバック完了・復旧"
```

### 6.3 シナリオB: 両リージョン同時ロールバック

```bash
echo "=== シナリオB: 両リージョン同時ロールバック ==="

# Step 1: メンテナンスモード有効化（オプション）
# Azure Front Doorでメンテナンスページを表示
az network front-door rules-engine rule update \
  --front-door-name itscm-frontdoor \
  --resource-group rg-itscm-global \
  --rules-engine-name maintenance \
  --rule-name redirect-to-maintenance \
  --action-type RequestHeader \
  --enabled true

# Step 2: East Japanロールバック
echo "--- East Japan ロールバック ---"
az containerapp ingress traffic set \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight itscm-frontend-prod--v0-9-0=100

az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight itscm-api-prod--v0-9-0=100

az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-worker:v0.9.0

# Step 3: West Japanロールバック
echo "--- West Japan ロールバック ---"
az containerapp ingress traffic set \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-westjp \
  --revision-weight itscm-frontend-prod--v0-9-0=100

az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-westjp \
  --revision-weight itscm-api-prod--v0-9-0=100

az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-westjp \
  --image itscmacr.azurecr.io/itscm-worker:v0.9.0

# Step 4: 両リージョン確認
echo "--- 動作確認 ---"
EAST_VER=$(curl -sf https://eastjp.itscm.example.com/api/version | jq -r '.version')
WEST_VER=$(curl -sf https://westjp.itscm.example.com/api/version | jq -r '.version')
echo "East Japan: ${EAST_VER}"
echo "West Japan: ${WEST_VER}"

# Step 5: メンテナンスモード解除
az network front-door rules-engine rule update \
  --front-door-name itscm-frontdoor \
  --resource-group rg-itscm-global \
  --rules-engine-name maintenance \
  --rule-name redirect-to-maintenance \
  --enabled false

# Step 6: Azure Front Door経由の最終確認
curl -sf https://itscm.example.com/api/health | jq .
curl -sf https://itscm.example.com/api/version | jq .

echo "=== 両リージョンロールバック完了 ==="
```

### 6.4 データベースレプリケーションを考慮したロールバック

```bash
# Geo冗長PostgreSQLのロールバック時の注意事項

# 1. レプリケーション状態確認
az postgres flexible-server replica list \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp

# 2. マイグレーションダウングレードの場合
#    → Primary（East Japan）でダウングレードを実行
#    → レプリカ（West Japan）に自動レプリケーションされる
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "alembic downgrade -1"

# 3. レプリケーション同期完了を待機
echo "レプリケーション同期を確認中..."
# レプリケーション遅延のモニタリング
az monitor metrics list \
  --resource "/subscriptions/{sub}/resourceGroups/rg-itscm-prod-eastjp/providers/Microsoft.DBforPostgreSQL/flexibleServers/itscm-db-prod-eastjp" \
  --metric "ReplicaLag" \
  --interval PT1M

# 4. バックアップリストアの場合
#    → レプリカを一旦削除
#    → Primaryをリストア
#    → レプリカを再作成
echo "WARNING: バックアップリストアはレプリカの再構築が必要です"
```

---

## 7. 部分ロールバック

### 7.1 フロントエンドのみロールバック

```bash
echo "=== フロントエンドのみロールバック ==="

# フロントエンドのリビジョン切戻し
az containerapp ingress traffic set \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight itscm-frontend-prod--v0-9-0=100

# 確認
curl -sf https://eastjp.itscm.example.com/ -o /dev/null -w "%{http_code}"

# West Japanも同様に
az containerapp ingress traffic set \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-westjp \
  --revision-weight itscm-frontend-prod--v0-9-0=100
```

### 7.2 バックエンドAPIのみロールバック

```bash
echo "=== バックエンドAPIのみロールバック ==="

# APIのリビジョン切戻し
az containerapp ingress traffic set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --revision-weight itscm-api-prod--v0-9-0=100

# DB マイグレーションのダウングレード（必要な場合）
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "alembic downgrade -1"

# 確認
curl -sf https://eastjp.itscm.example.com/api/health | jq .
```

### 7.3 Celery Workerのみロールバック

```bash
echo "=== Celery Workerのみロールバック ==="

# Workerイメージの切戻し
az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-eastjp \
  --image itscmacr.azurecr.io/itscm-worker:v0.9.0

# キュー内の処理中タスクの確認
# Celery Flowerダッシュボードで確認
echo "Flower: https://flower.itscm.example.com"

# 未処理タスクのパージ（必要な場合）
az containerapp exec \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "celery -A app.worker purge -f"
```

### 7.4 部分ロールバック時の互換性確認

| フロントエンド | API | Worker | 互換性 | 注意事項 |
|-------------|-----|--------|--------|---------|
| v1.0.0 | v0.9.0 | v0.9.0 | 要確認 | API後方互換性が必要 |
| v0.9.0 | v1.0.0 | v1.0.0 | 要確認 | 新APIの非使用確認 |
| v1.0.0 | v1.0.0 | v0.9.0 | 要確認 | タスクフォーマット互換性 |
| v0.9.0 | v0.9.0 | v1.0.0 | 非推奨 | 不整合リスク高 |

---

## 8. ロールバック後の対応

### 8.1 即時対応（ロールバック後0-1時間）

| 対応項目 | 担当 | 内容 |
|---------|------|------|
| 動作確認 | 運用チーム | 全コンポーネントのヘルスチェック |
| 監視強化 | 運用チーム | アラート閾値の一時引き下げ |
| ステークホルダー通知 | リリースマネージャー | ロールバック実施報告 |
| ログ収集 | 開発チーム | 障害発生時のログ・メトリクス保全 |
| ユーザー通知 | サービスデスク | 必要に応じてユーザーへの通知 |

### 8.2 原因分析（ロールバック後1-24時間）

| 分析項目 | 担当 | 内容 |
|---------|------|------|
| タイムライン作成 | リリースマネージャー | 障害発生から復旧までの時系列整理 |
| ログ分析 | 開発チーム | アプリケーションログ、システムログの分析 |
| メトリクス分析 | 運用チーム | パフォーマンスメトリクスの異常特定 |
| 根本原因特定 | 開発+運用 | 5 Whys分析等による根本原因の特定 |
| 影響範囲確認 | サービスデスク | ユーザー影響の範囲と程度の確認 |

### 8.3 再発防止（ロールバック後1-5営業日）

| 対応項目 | 担当 | 成果物 |
|---------|------|--------|
| ポストモーテム作成 | リリースマネージャー | ポストモーテムレポート |
| 修正対応 | 開発チーム | バグ修正PR |
| テスト強化 | QAチーム | テストケースの追加 |
| プロセス改善 | 全チーム | リリースプロセスの改善提案 |
| 再リリース計画 | リリースマネージャー | 修正版リリース計画 |

### 8.4 ポストモーテムテンプレート

```markdown
# ロールバック ポストモーテム

## 基本情報
- インシデント日時: YYYY-MM-DD HH:MM - HH:MM
- 影響時間: XX分
- リリースバージョン: vX.Y.Z
- ロールバック先バージョン: vX.Y.Z
- 影響ユーザー数: XXX名

## タイムライン
| 時刻 | イベント |
|------|---------|
| HH:MM | リリース開始 |
| HH:MM | 問題検知 |
| HH:MM | ロールバック判定 |
| HH:MM | ロールバック開始 |
| HH:MM | ロールバック完了 |
| HH:MM | サービス復旧確認 |

## 根本原因
（根本原因の記述）

## 影響
（影響範囲の記述）

## 対応内容
（実施した対応の記述）

## 再発防止策
| 対策 | 担当 | 期限 | ステータス |
|------|------|------|----------|
| （対策1） | （担当） | YYYY-MM-DD | 未着手 |

## 教訓
（得られた教訓の記述）
```

---

## 9. ロールバック訓練

### 9.1 訓練計画

| 訓練項目 | 頻度 | 対象環境 | 参加者 |
|---------|------|---------|--------|
| アプリケーションロールバック | 四半期に1回 | ステージング | 運用+開発 |
| DBロールバック（ダウングレード） | 四半期に1回 | ステージング | 運用+DBA |
| DBロールバック（リストア） | 半期に1回 | ステージング | 運用+DBA |
| マルチリージョンロールバック | 半期に1回 | ステージング | 運用+インフラ |
| 部分ロールバック | 四半期に1回 | ステージング | 運用+開発 |

### 9.2 訓練実施手順

```
1. 訓練計画の策定（1週間前）
   - シナリオの決定
   - 参加者のアサイン
   - 訓練環境の準備

2. 訓練の実施
   - ブリーフィング（10分）
   - ロールバック実行（目標時間内）
   - 確認作業

3. 訓練結果の評価
   - 目標時間の達成確認
   - 手順の適切性評価
   - 改善点の洗い出し

4. 手順書の更新
   - 訓練で発見された問題の反映
   - 手順の改善
```

### 9.3 訓練評価基準

| 評価項目 | 目標 | 合格基準 |
|---------|------|---------|
| ロールバック完了時間（アプリのみ） | 5分以内 | 10分以内 |
| ロールバック完了時間（DB含む） | 30分以内 | 45分以内 |
| 手順書の正確性 | 手順通りに実行可能 | 軽微な修正で実行可能 |
| コミュニケーション | 全関係者に適時通知 | 主要関係者に通知 |
| サービス復旧確認 | 全項目確認完了 | 主要項目確認完了 |

---

## 関連文書

| 文書番号 | 文書名 |
|---------|--------|
| ITSCM-RM-001 | リリース計画書 |
| ITSCM-RM-002 | リリース手順書 |
| ITSCM-RM-004 | デプロイメント構成管理 |
| ITSCM-OP-003 | 障害対応手順書 |
| ITSCM-OP-004 | バックアップリストア手順書 |
| ITSCM-OP-005 | DR手順書 |

---

以上
