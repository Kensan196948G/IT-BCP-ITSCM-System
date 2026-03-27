# DR手順書（Disaster Recovery Procedure）

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-OP-005 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 作成者 | IT-BCP-ITSCMシステム開発チーム |
| 承認者 | （承認者名） |
| 分類 | 運用管理 |
| 準拠規格 | ISO20000 / ISO27001 / NIST CSF |

---

## 改訂履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-03-27 | 開発チーム | 初版作成 |

---

## 目次

1. [概要](#1-概要)
2. [DR構成](#2-dr構成)
3. [フェイルオーバー手順（East Japan → West Japan）](#3-フェイルオーバー手順east-japan--west-japan)
4. [フェイルバック手順（West Japan → East Japan）](#4-フェイルバック手順west-japan--east-japan)
5. [DR訓練計画](#5-dr訓練計画)
6. [DRシナリオ別対応](#6-drシナリオ別対応)
7. [DR訓練評価・改善](#7-dr訓練評価改善)

---

## 1. 概要

### 1.1 目的

本文書は、IT-BCP-ITSCMシステムの災害復旧（Disaster Recovery）手順を定義する。Primaryリージョン（East Japan）が利用不可となった場合にStandbyリージョン（West Japan）へ迅速に切り替え、サービスを継続する。

### 1.2 DR目標

| 目標 | 値 | 説明 |
|------|-----|------|
| RTO（Recovery Time Objective） | 15分以内 | システム全体の復旧時間目標 |
| RPO（Recovery Point Objective） | 1時間以内 | データ損失の許容時間 |
| フェイルオーバー時間 | 90秒以内 | Azure Front Doorによる自動切替 |
| フェイルバック時間 | 60分以内 | Primary復旧後の切戻し |

### 1.3 DR発動条件

| 条件 | 判断者 | 対応 |
|------|--------|------|
| East Japan リージョン全体障害 | Azure通知 + 運用マネージャー | 自動フェイルオーバー + 手動確認 |
| East Japan Container Apps障害 | 監視アラート | 自動フェイルオーバー |
| East Japan DB障害（復旧見込みなし） | DBA + 運用マネージャー | 手動フェイルオーバー |
| 大規模自然災害 | CTO | 手動フェイルオーバー |
| サイバー攻撃によるリージョン隔離 | CISO + CTO | 手動フェイルオーバー |

---

## 2. DR構成

### 2.1 マルチリージョン構成図

```
                         ┌───────────────────┐
                         │  Azure Front Door   │
                         │  (Global LB/WAF)    │
                         │                     │
                         │  ヘルスチェック:       │
                         │  30秒間隔            │
                         │  失敗閾値: 3回        │
                         │  → 自動切替: ~90秒    │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              │ Active (通常時: 100%)                       │ Standby (通常時: 0%)
              │                                            │
    ┌─────────▼─────────────────┐            ┌────────────▼──────────────┐
    │   East Japan (Primary)     │            │   West Japan (Standby)    │
    │                            │            │                           │
    │  ┌──────────────────────┐  │            │  ┌──────────────────────┐ │
    │  │ Container Apps        │  │            │  │ Container Apps        │ │
    │  │ ├ Frontend (3 rep)    │  │            │  │ ├ Frontend (1 rep*)   │ │
    │  │ ├ API (3 rep)         │  │            │  │ ├ API (1 rep*)        │ │
    │  │ └ Worker (2 rep)      │  │            │  │ └ Worker (1 rep*)     │ │
    │  └──────────────────────┘  │            │  └──────────────────────┘ │
    │                            │            │    * DR時にスケールアウト    │
    │  ┌──────────────────────┐  │  Geo-Repl  │  ┌──────────────────────┐ │
    │  │ PostgreSQL            │  │ ─────────▶ │  │ PostgreSQL            │ │
    │  │ (Primary/Read-Write)  │  │ 非同期      │  │ (Read Replica)        │ │
    │  └──────────────────────┘  │            │  └──────────────────────┘ │
    │                            │            │                           │
    │  ┌──────────────────────┐  │  Geo-Repl  │  ┌──────────────────────┐ │
    │  │ Redis Cluster         │  │ ─────────▶ │  │ Redis Cluster         │ │
    │  │ (Primary)             │  │            │  │ (Geo-Secondary)       │ │
    │  └──────────────────────┘  │            │  └──────────────────────┘ │
    │                            │            │                           │
    │  ┌──────────────────────┐  │            │  ┌──────────────────────┐ │
    │  │ Key Vault             │  │            │  │ Key Vault             │ │
    │  └──────────────────────┘  │            │  └──────────────────────┘ │
    │                            │            │                           │
    └────────────────────────────┘            └───────────────────────────┘
```

### 2.2 コンポーネント別DR構成

| コンポーネント | Primary (East JP) | Standby (West JP) | 切替方式 | 切替時間 |
|-------------|-------------------|-------------------|---------|---------|
| Azure Front Door | Active | Active（ヘルスチェック連動） | 自動 | ~90秒 |
| Frontend | 3レプリカ | 1レプリカ（DR時スケール） | 自動（Front Door） | ~90秒 |
| Backend API | 3レプリカ | 1レプリカ（DR時スケール） | 自動（Front Door） | ~90秒 |
| Celery Worker | 2レプリカ | 1レプリカ（DR時スケール） | 自動 | ~2分 |
| PostgreSQL | Primary (RW) | Read Replica → Promote | 手動 | ~5-10分 |
| Redis | Primary | Geo-Secondary → Promote | 手動 | ~2-5分 |
| Key Vault | リージョン内冗長 | 独立Key Vault | 自動 | 即時 |
| Azure Blob Storage | RA-GRS | 読取専用 → RW昇格 | 手動 | ~15分 |

---

## 3. フェイルオーバー手順（East Japan → West Japan）

### 3.1 自動フェイルオーバー（Azure Front Door）

Azure Front Doorのヘルスプローブにより自動的にトラフィックが切り替わる:

```
通常時:
  Azure Front Door → East Japan (100%) + West Japan (0%)

East Japan異常検知（ヘルスプローブ3回連続失敗、~90秒）:
  Azure Front Door → East Japan (0%) + West Japan (100%)
```

この自動フェイルオーバーはアプリケーション層のみ。データベースおよびRedisは手動操作が必要。

### 3.2 手動フェイルオーバー全体手順

**所要時間目標**: 15分以内
**判断者**: 運用マネージャー / CTO
**実行者**: インフラチーム + DBA

```
Timeline:
  T+0分   : DR発動判断
  T+1分   : フェイルオーバー開始宣言
  T+2分   : PostgreSQLレプリカ昇格開始
  T+5分   : PostgreSQLレプリカ昇格完了
  T+6分   : Redis Geo-Secondary昇格
  T+8分   : West Japan Container Appsスケールアウト
  T+10分  : Azure Front Doorトラフィック確認
  T+12分  : 動作確認
  T+15分  : フェイルオーバー完了宣言
```

#### Step 1: DR発動宣言（T+0~1分）

```bash
echo "=============================================="
echo "DR フェイルオーバー発動"
echo "日時: $(date)"
echo "発動者: ${OPERATOR_NAME}"
echo "理由: ${FAILOVER_REASON}"
echo "=============================================="

# Slack通知
curl -X POST "${SLACK_WEBHOOK_URL}" \
  -H 'Content-Type: application/json' \
  -d '{
    "channel": "#ops-critical",
    "text": "DR フェイルオーバー発動 - East Japan → West Japan\n理由: '"${FAILOVER_REASON}"'\n発動者: '"${OPERATOR_NAME}"'"
  }'
```

#### Step 2: PostgreSQL レプリカ昇格（T+2~5分）

```bash
echo "=== Step 2: PostgreSQL レプリカ昇格 ==="

# 2-1. レプリケーション遅延の最終確認
echo "レプリケーション遅延確認..."
az monitor metrics list \
  --resource "/subscriptions/{sub}/resourceGroups/rg-itscm-prod-eastjp/providers/Microsoft.DBforPostgreSQL/flexibleServers/itscm-db-prod-eastjp" \
  --metric "physical_replication_delay_in_seconds" \
  --interval PT1M \
  --query "value[0].timeseries[0].data[-1].average" \
  --output tsv 2>/dev/null || echo "Primary到達不可 - レプリカ昇格を続行"

# 2-2. レプリカを独立サーバーに昇格
echo "レプリカ昇格実行..."
az postgres flexible-server replica stop-replication \
  --name itscm-db-prod-westjp \
  --resource-group rg-itscm-prod-westjp

# 2-3. 昇格完了確認
echo "昇格完了確認..."
while true; do
  ROLE=$(az postgres flexible-server show \
    --name itscm-db-prod-westjp \
    --resource-group rg-itscm-prod-westjp \
    --query "replicationRole" -o tsv)
  if [ "$ROLE" = "None" ] || [ "$ROLE" = "" ]; then
    echo "昇格完了: サーバーは独立Primary"
    break
  fi
  echo "  役割: ${ROLE} - 待機中..."
  sleep 5
done

# 2-4. Read-Write確認
echo "Read-Write確認..."
psql -h itscm-db-prod-westjp.postgres.database.azure.com \
  -U itscm_admin -d itscm_prod \
  -c "INSERT INTO health_check (checked_at) VALUES (NOW()); SELECT 'Write OK';"

echo "=== PostgreSQL レプリカ昇格完了 ==="
```

#### Step 3: Redis Geo-Secondary昇格（T+6分）

```bash
echo "=== Step 3: Redis Geo-Secondary昇格 ==="

# 3-1. Geoレプリケーションのリンク解除
az redis server-link delete \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --linked-server-name itscm-redis-prod-westjp

# 3-2. West Japan RedisがPrimaryとして動作確認
echo "Redis昇格確認..."
az redis show \
  --name itscm-redis-prod-westjp \
  --resource-group rg-itscm-prod-westjp \
  --query "{state:provisioningState, linkedServers:linkedServers}"

echo "=== Redis Geo-Secondary昇格完了 ==="
```

#### Step 4: West Japan Container Appsスケールアウト（T+8分）

```bash
echo "=== Step 4: West Japan スケールアウト ==="

# 4-1. フロントエンドのスケールアウト
az containerapp update \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-westjp \
  --min-replicas 3 \
  --max-replicas 10

# 4-2. APIのスケールアウト
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-westjp \
  --min-replicas 3 \
  --max-replicas 20

# 4-3. Workerのスケールアウト
az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-westjp \
  --min-replicas 2 \
  --max-replicas 10

# 4-4. 環境変数更新（DB/Redis接続先をWest Japanに変更）
az containerapp secret set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-westjp \
  --secrets \
    "database-url=keyvaultref:kv-itscm-prod-westjp/DATABASE-URL-DR,identityref:..." \
    "redis-url=keyvaultref:kv-itscm-prod-westjp/REDIS-URL-DR,identityref:..."

# 4-5. レプリカ起動確認
echo "レプリカ起動確認..."
sleep 30
az containerapp show \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-westjp \
  --query "properties.runningStatus"

echo "=== West Japan スケールアウト完了 ==="
```

#### Step 5: Azure Front Doorトラフィック確認（T+10分）

```bash
echo "=== Step 5: トラフィック確認 ==="

# 5-1. Front Doorバックエンド状態確認
az network front-door backend-pool backend list \
  --front-door-name itscm-frontdoor \
  --resource-group rg-itscm-global \
  --pool-name itscm-backend-pool \
  --output table

# 5-2. East Japanを明示的に無効化（自動切替が完了していない場合）
az network front-door backend-pool backend update \
  --front-door-name itscm-frontdoor \
  --resource-group rg-itscm-global \
  --pool-name itscm-backend-pool \
  --address eastjp.itscm.example.com \
  --enabled-state Disabled

# 5-3. Front Door経由のアクセス確認
curl -sf https://itscm.example.com/api/health | jq .
curl -sf https://itscm.example.com/api/version | jq .

echo "=== トラフィック確認完了 ==="
```

#### Step 6: 動作確認・完了宣言（T+12~15分）

```bash
echo "=== Step 6: 最終動作確認 ==="

# 6-1. ヘルスチェック
echo "--- ヘルスチェック ---"
curl -sf https://itscm.example.com/api/health | jq .
curl -sf https://itscm.example.com/api/health/db | jq .
curl -sf https://itscm.example.com/api/health/redis | jq .
curl -sf https://itscm.example.com/api/health/celery | jq .

# 6-2. 認証テスト
echo "--- 認証テスト ---"
# テストユーザーでログイン確認

# 6-3. 主要機能テスト
echo "--- 主要機能テスト ---"
# BCP計画一覧取得
# RTOダッシュボードアクセス

# 6-4. データ整合性確認
echo "--- データ整合性確認 ---"
# 最新のデータが存在するか確認

# 6-5. 完了宣言
echo "=============================================="
echo "DR フェイルオーバー完了"
echo "完了日時: $(date)"
echo "稼働リージョン: West Japan"
echo "=============================================="

# Slack通知
curl -X POST "${SLACK_WEBHOOK_URL}" \
  -H 'Content-Type: application/json' \
  -d '{
    "channel": "#ops-critical",
    "text": "DR フェイルオーバー完了 - West Japanで稼働中"
  }'
```

---

## 4. フェイルバック手順（West Japan → East Japan）

### 4.1 フェイルバック前提条件

| 条件 | 確認方法 |
|------|---------|
| East Japanリージョンが正常稼働 | Azure Status確認 |
| East Japan Container Apps Environmentが正常 | az containerapp env show |
| East Japan PostgreSQLが再構築可能 | az postgres flexible-server show |
| East Japan Redisが正常 | az redis show |
| フェイルバック実施の承認 | 運用マネージャー / CTO承認 |

### 4.2 フェイルバック手順

**所要時間**: 約60分
**実施タイミング**: 計画メンテナンスウィンドウ内

#### Step 1: East Japan PostgreSQLの再構築

```bash
echo "=== フェイルバック Step 1: East Japan DB再構築 ==="

# 1-1. West Japan を新Primaryとして、East Japanにレプリカ作成
az postgres flexible-server replica create \
  --name itscm-db-prod-eastjp-new \
  --resource-group rg-itscm-prod-eastjp \
  --source-server "/subscriptions/{sub}/resourceGroups/rg-itscm-prod-westjp/providers/Microsoft.DBforPostgreSQL/flexibleServers/itscm-db-prod-westjp" \
  --location "Japan East"

# 1-2. レプリケーション同期完了待ち
echo "レプリケーション同期待ち..."
while true; do
  LAG=$(az monitor metrics list \
    --resource "/subscriptions/{sub}/resourceGroups/rg-itscm-prod-westjp/providers/Microsoft.DBforPostgreSQL/flexibleServers/itscm-db-prod-westjp" \
    --metric "physical_replication_delay_in_seconds" \
    --interval PT1M \
    --query "value[0].timeseries[0].data[-1].average" -o tsv)
  echo "  レプリケーション遅延: ${LAG}秒"
  if (( $(echo "$LAG < 1" | bc -l) )); then
    echo "同期完了"
    break
  fi
  sleep 30
done

# 1-3. East Japanレプリカを昇格してPrimaryに
az postgres flexible-server replica stop-replication \
  --name itscm-db-prod-eastjp-new \
  --resource-group rg-itscm-prod-eastjp

# 1-4. West Japanサーバーにレプリカを再設定
az postgres flexible-server replica create \
  --name itscm-db-prod-westjp-new \
  --resource-group rg-itscm-prod-westjp \
  --source-server "/subscriptions/{sub}/resourceGroups/rg-itscm-prod-eastjp/providers/Microsoft.DBforPostgreSQL/flexibleServers/itscm-db-prod-eastjp-new" \
  --location "Japan West"

echo "=== East Japan DB再構築完了 ==="
```

#### Step 2: East Japan Redisの再構築

```bash
echo "=== フェイルバック Step 2: Redis Geoレプリケーション再構築 ==="

# 2-1. East Japan Redisの確認
az redis show \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "provisioningState"

# 2-2. Geoレプリケーションリンクの再作成
az redis server-link create \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --linked-server-name itscm-redis-prod-westjp \
  --replication-role Secondary \
  --server-to-link "/subscriptions/{sub}/resourceGroups/rg-itscm-prod-westjp/providers/Microsoft.Cache/Redis/itscm-redis-prod-westjp"

# 2-3. データ同期確認
sleep 60
az redis show \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "linkedServers"

echo "=== Redis Geoレプリケーション再構築完了 ==="
```

#### Step 3: East Japan Container Appsの更新

```bash
echo "=== フェイルバック Step 3: East Japan アプリケーション更新 ==="

# 3-1. DB/Redis接続先をEast Japanに更新
az containerapp secret set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --secrets \
    "database-url=keyvaultref:kv-itscm-prod-eastjp/DATABASE-URL,identityref:..." \
    "redis-url=keyvaultref:kv-itscm-prod-eastjp/REDIS-URL,identityref:..."

# 3-2. East Japan Container Appsのスケール設定復元
az containerapp update \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-eastjp \
  --min-replicas 3 --max-replicas 10

az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --min-replicas 3 --max-replicas 20

az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-eastjp \
  --min-replicas 2 --max-replicas 10

# 3-3. East Japan動作確認
curl -sf https://eastjp.itscm.example.com/api/health | jq .

echo "=== East Japan アプリケーション更新完了 ==="
```

#### Step 4: トラフィック切替（West → East）

```bash
echo "=== フェイルバック Step 4: トラフィック切替 ==="

# 4-1. East Japanバックエンドを有効化
az network front-door backend-pool backend update \
  --front-door-name itscm-frontdoor \
  --resource-group rg-itscm-global \
  --pool-name itscm-backend-pool \
  --address eastjp.itscm.example.com \
  --enabled-state Enabled \
  --priority 1

# 4-2. West Japanの優先度を下げる
az network front-door backend-pool backend update \
  --front-door-name itscm-frontdoor \
  --resource-group rg-itscm-global \
  --pool-name itscm-backend-pool \
  --address westjp.itscm.example.com \
  --priority 2

# 4-3. トラフィック切替確認
sleep 120  # ヘルスプローブ反映待ち
curl -sf https://itscm.example.com/api/health | jq .

echo "=== トラフィック切替完了 ==="
```

#### Step 5: West Japan Standby構成に復帰

```bash
echo "=== フェイルバック Step 5: West Japan Standby復帰 ==="

# 5-1. West Japan Container Appsをスケールダウン
az containerapp update \
  --name itscm-frontend-prod \
  --resource-group rg-itscm-prod-westjp \
  --min-replicas 1 --max-replicas 5

az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-westjp \
  --min-replicas 1 --max-replicas 8

az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-westjp \
  --min-replicas 1 --max-replicas 5

# 5-2. 最終確認
echo "--- 最終確認 ---"
curl -sf https://itscm.example.com/api/health | jq .
curl -sf https://eastjp.itscm.example.com/api/health | jq .
curl -sf https://westjp.itscm.example.com/api/health | jq .

echo "=============================================="
echo "フェイルバック完了"
echo "完了日時: $(date)"
echo "Primary: East Japan"
echo "Standby: West Japan"
echo "=============================================="
```

---

## 5. DR訓練計画

### 5.1 訓練種別

| 種別 | 内容 | 頻度 | 環境 | 参加者 |
|------|------|------|------|--------|
| テーブルトップ訓練 | 手順書に基づく机上訓練 | 四半期 | - | 全運用チーム |
| 部分フェイルオーバー訓練 | 特定コンポーネントの切替テスト | 四半期 | ステージング | 運用+インフラ |
| 完全フェイルオーバー訓練 | East→West完全切替テスト | 半期 | ステージング | 全運用+開発 |
| 本番フェイルオーバー訓練 | 本番環境での切替テスト | 年次 | 本番 | 全チーム |
| フェイルバック訓練 | West→East切戻しテスト | 半期 | ステージング | 運用+インフラ |
| 複合シナリオ訓練 | 複数障害の同時発生対応 | 年次 | ステージング | 全チーム |

### 5.2 訓練スケジュール

```
Q1 (1-3月):
  ├── 1月: テーブルトップ訓練
  ├── 2月: 部分フェイルオーバー訓練（ステージング）
  └── 3月: 完全フェイルオーバー訓練（ステージング）

Q2 (4-6月):
  ├── 4月: テーブルトップ訓練
  ├── 5月: フェイルバック訓練（ステージング）
  └── 6月: 本番フェイルオーバー訓練

Q3 (7-9月):
  ├── 7月: テーブルトップ訓練
  ├── 8月: 部分フェイルオーバー訓練（ステージング）
  └── 9月: 完全フェイルオーバー訓練（ステージング）+ 複合シナリオ

Q4 (10-12月):
  ├── 10月: テーブルトップ訓練
  ├── 11月: フェイルバック訓練（ステージング）
  └── 12月: 本番フェイルオーバー訓練
```

### 5.3 訓練実施手順

#### 訓練前準備（T-1週間）

```
1. 訓練計画書の作成・配布
   - 訓練目的
   - シナリオ
   - 参加者・役割
   - タイムスケジュール
   - 成功基準

2. 環境準備
   - ステージング環境の確認
   - 監視ダッシュボードの準備
   - コミュニケーションチャネルの確認

3. リスク軽減
   - 本番訓練の場合: メンテナンスウィンドウの設定
   - ロールバック手順の確認
   - 中止基準の設定
```

#### 訓練実施

```
1. ブリーフィング（15分）
   - シナリオの説明
   - 役割の確認
   - 安全策の確認

2. 訓練実行
   - シナリオに基づく障害注入
   - フェイルオーバー手順の実行
   - タイムスタンプの記録
   - コミュニケーションの実践

3. 確認
   - サービス復旧の確認
   - データ整合性の確認
   - 時間目標の達成確認

4. フェイルバック（フェイルオーバー訓練の場合）
   - フェイルバック手順の実行
   - 元の構成への復帰確認

5. デブリーフィング（30分）
   - タイムラインのレビュー
   - 問題点の洗い出し
   - 改善提案
```

### 5.4 訓練シナリオ

#### シナリオ1: East Japan Container Apps全停止

```
前提: East JapanのContainer Apps Environmentが障害で全停止
目標: 15分以内にWest Japanでサービスを復旧
手順:
  1. Azure Front Doorの自動切替を確認
  2. West Japan Container Appsのスケールアウト
  3. DB/Redisの接続確認
  4. サービス復旧確認
```

#### シナリオ2: East Japan PostgreSQL障害

```
前提: East Japan PostgreSQLサーバーが利用不可
目標: 15分以内にWest Japanのレプリカを昇格してサービス復旧
手順:
  1. PostgreSQLレプリカの昇格
  2. アプリケーションの接続先変更
  3. データ整合性確認
  4. サービス復旧確認
```

#### シナリオ3: リージョン全体障害

```
前提: Azure East Japan リージョンが完全停止
目標: 15分以内にWest Japanで全サービスを復旧
手順:
  1. DR発動宣言
  2. PostgreSQLレプリカ昇格
  3. Redis Geo-Secondary昇格
  4. Container Appsスケールアウト
  5. Front Doorトラフィック確認
  6. 全サービス復旧確認
```

#### シナリオ4: サイバー攻撃によるデータ破壊

```
前提: ランサムウェア等によりEast Japanのデータが破壊
目標: RPO 1時間以内のデータ復旧、West Japanでのサービス継続
手順:
  1. East Japanの隔離
  2. West Japanのレプリカ昇格
  3. データ整合性の確認
  4. West Japanでのサービス復旧
  5. East Japanの調査・復旧
```

---

## 6. DRシナリオ別対応

### 6.1 自然災害（地震・津波）

| 項目 | 対応 |
|------|------|
| 想定 | 東日本大震災級の地震により東京リージョンが長期停止 |
| 初動 | 人命安全確認後、DR発動判断 |
| フェイルオーバー | セクション3に従い全面的にWest Japanへ切替 |
| 長期運用 | West Japanを新Primaryとして運用継続 |
| フェイルバック | East Japan復旧後、計画的にフェイルバック |

### 6.2 大規模サイバー攻撃

| 項目 | 対応 |
|------|------|
| 想定 | APT攻撃によるシステム侵害、データ暗号化 |
| 初動 | セキュリティインシデント対応プロセス発動、侵害範囲特定 |
| フェイルオーバー | 侵害されていないリージョンでの復旧 |
| データ復旧 | 侵害前のバックアップからのリストア |
| フォレンジック | 侵害されたシステムの保全・分析 |

### 6.3 クラウドプロバイダー障害

| 項目 | 対応 |
|------|------|
| 想定 | Azure East Japanリージョンの長時間停止 |
| 初動 | Azure Status確認、Azureサポートへ連絡 |
| フェイルオーバー | 自動フェイルオーバー + 手動DB/Redis切替 |
| コミュニケーション | ユーザーへのステータスページ更新 |
| フェイルバック | Azureリージョン復旧後にフェイルバック |

### 6.4 パンデミック・長期リモート運用

| 項目 | 対応 |
|------|------|
| 想定 | 運用チームの大部分がリモート作業 |
| 影響 | オフィスからのみアクセス可能な管理ツールが使えない |
| 対策 | VPN経由での管理アクセス、Azure Portalからのリモート管理 |
| 運用体制 | オンコール体制の強化、コミュニケーション手段の多重化 |

---

## 7. DR訓練評価・改善

### 7.1 評価基準

| 評価項目 | 目標 | 合格基準 |
|---------|------|---------|
| フェイルオーバー完了時間 | 15分以内 | 20分以内 |
| フェイルオーバー中のダウンタイム | 90秒以内 | 3分以内 |
| データ損失量 | RPO 1時間以内 | RPO 2時間以内 |
| 手順書の正確性 | 手順通り実行可能 | 軽微な修正で実行可能 |
| コミュニケーション | 全関係者に適時通知 | 主要関係者に通知 |
| ロールバック/フェイルバック | 60分以内 | 90分以内 |
| 全テスト合格 | 全動作確認PASS | 主要機能確認PASS |

### 7.2 訓練報告書テンプレート

```markdown
## DR訓練報告書

### 基本情報
- 訓練日: YYYY-MM-DD
- 訓練種別: テーブルトップ / 部分 / 完全 / 本番
- シナリオ:
- 参加者:

### 結果サマリー
| 評価項目 | 目標 | 実績 | 判定 |
|---------|------|------|------|
| フェイルオーバー時間 | 15分 | XX分 | OK/NG |
| ダウンタイム | 90秒 | XX秒 | OK/NG |
| データ損失 | 1時間以内 | XX分 | OK/NG |

### タイムライン
| 時刻 | アクション | 結果 | 所要時間 |
|------|----------|------|---------|
| | | | |

### 問題点
| # | 問題 | 影響 | 改善案 |
|---|------|------|--------|
| | | | |

### 改善アクション
| アクション | 担当 | 期限 | ステータス |
|----------|------|------|----------|
| | | | |

### 総合評価
（総合評価のコメント）

### 次回訓練への提案
（次回訓練へのフィードバック）
```

### 7.3 継続的改善

| 改善活動 | 頻度 | 担当 |
|---------|------|------|
| 訓練結果の振り返り | 訓練後毎回 | 全参加者 |
| 手順書の更新 | 訓練後・障害後 | 運用チーム |
| アーキテクチャ改善 | 四半期 | アーキテクト |
| RTO/RPO目標の見直し | 年次 | CTO + 経営 |
| DR構成の最適化 | 年次 | インフラチーム |

---

## 関連文書

| 文書番号 | 文書名 |
|---------|--------|
| ITSCM-OP-001 | 運用手順書 |
| ITSCM-OP-002 | 監視設計書 |
| ITSCM-OP-003 | 障害対応手順書 |
| ITSCM-OP-004 | バックアップリストア手順書 |
| ITSCM-RM-003 | ロールバック手順書 |
| ITSCM-RM-004 | デプロイメント構成管理 |

---

以上
