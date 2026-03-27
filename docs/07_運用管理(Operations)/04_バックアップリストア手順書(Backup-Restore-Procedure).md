# バックアップリストア手順書（Backup & Restore Procedure）

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-OP-004 |
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
2. [バックアップ戦略](#2-バックアップ戦略)
3. [PostgreSQLバックアップ](#3-postgresqlバックアップ)
4. [Redisバックアップ](#4-redisバックアップ)
5. [アプリケーションデータバックアップ](#5-アプリケーションデータバックアップ)
6. [リストア手順](#6-リストア手順)
7. [RPO準拠確認](#7-rpo準拠確認)
8. [バックアップ監視・テスト](#8-バックアップ監視テスト)

---

## 1. 概要

### 1.1 目的

本文書は、IT-BCP-ITSCMシステムのデータバックアップ戦略とリストア手順を定義する。RPO（Recovery Point Objective）1時間以内を確保し、データ損失リスクを最小化する。

### 1.2 バックアップ対象

| 対象 | データ種別 | RPO要件 | RTO要件 |
|------|----------|---------|---------|
| PostgreSQL（Primary） | ビジネスデータ、ユーザーデータ | 1時間以内 | 15分以内 |
| PostgreSQL（Replica） | レプリカデータ | リアルタイム | - |
| Redis Cluster | セッション、キャッシュ | 1時間以内 | 5分以内 |
| Azure Blob Storage | ドキュメント、レポート | 1時間以内 | 30分以内 |
| Terraform State | インフラ構成 | リアルタイム | 即時 |
| Key Vault | シークレット、証明書 | リアルタイム | 即時 |
| コンテナイメージ | ACR内イメージ | リリース時 | 即時 |

---

## 2. バックアップ戦略

### 2.1 バックアップ方式

```
┌──────────────────────────────────────────────────────────────────┐
│                    バックアップ戦略の全体像                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: リアルタイムレプリケーション                               │
│  ┌─────────────────────────────────────────────────┐             │
│  │ PostgreSQL Geo-Replication                       │             │
│  │ East Japan (Primary) ──▶ West Japan (Replica)    │             │
│  │ RPO: ほぼ0  遅延: < 1秒                           │             │
│  └─────────────────────────────────────────────────┘             │
│  ┌─────────────────────────────────────────────────┐             │
│  │ Redis Geo-Replication                            │             │
│  │ East Japan ──▶ West Japan                        │             │
│  │ RPO: ほぼ0  遅延: < 1秒                           │             │
│  └─────────────────────────────────────────────────┘             │
│                                                                  │
│  Layer 2: 継続的バックアップ（PITR）                                │
│  ┌─────────────────────────────────────────────────┐             │
│  │ PostgreSQL Point-in-Time Recovery                │             │
│  │ WAL（Write-Ahead Log）の継続的アーカイブ            │             │
│  │ RPO: 最大5分                                      │             │
│  │ 保持期間: 35日                                     │             │
│  └─────────────────────────────────────────────────┘             │
│                                                                  │
│  Layer 3: 定期スナップショット                                     │
│  ┌─────────────────────────────────────────────────┐             │
│  │ PostgreSQL: 日次自動バックアップ                     │             │
│  │ Redis: 1時間ごとのRDBスナップショット                │             │
│  │ Blob Storage: 日次スナップショット                   │             │
│  └─────────────────────────────────────────────────┘             │
│                                                                  │
│  Layer 4: 長期保管                                                │
│  ┌─────────────────────────────────────────────────┐             │
│  │ 月次フルバックアップ → Azure Archive Storage       │             │
│  │ 保持期間: 1年                                      │             │
│  └─────────────────────────────────────────────────┘             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 バックアップスケジュール

| バックアップ種別 | 対象 | 頻度 | 保持期間 | RPO |
|---------------|------|------|---------|-----|
| WALアーカイブ | PostgreSQL | 継続的 | 35日 | ~5分 |
| 自動バックアップ | PostgreSQL | 日次 | 35日 | 24時間 |
| 手動バックアップ | PostgreSQL | リリース前 | 90日 | - |
| RDBスナップショット | Redis | 1時間ごと | 7日 | 1時間 |
| AOF（Append Only File） | Redis | リアルタイム | - | ~1秒 |
| Blobスナップショット | Azure Storage | 日次 | 30日 | 24時間 |
| 月次フルバックアップ | 全データ | 月次 | 1年 | 30日 |
| Terraform State | インフラ構成 | 変更時 | バージョニング | 即時 |

### 2.3 3-2-1バックアップルール

```
3 : 3つのコピーを保持
    ├── Primary データ（East Japan）
    ├── Geo Replica（West Japan）
    └── バックアップストレージ（別リソースグループ）

2 : 2つの異なるメディアに保存
    ├── Azure Database（マネージドサービス）
    └── Azure Blob Storage（バックアップ専用）

1 : 1つはオフサイト（異なるリージョン）に保管
    └── West Japan または Azure Archive Storage
```

---

## 3. PostgreSQLバックアップ

### 3.1 自動バックアップ（Azure管理）

Azure Database for PostgreSQL Flexible Serverの組み込みバックアップ:

```
設定:
  バックアップ保持期間: 35日
  バックアップ冗長性: Geo冗長（GRS）
  自動バックアップ時間: 02:00-04:00 JST（推定、Azureが自動決定）
  PITR（ポイントインタイムリカバリ）: 有効
```

```bash
# 自動バックアップの確認
az postgres flexible-server backup list \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "[].{name:name, type:backupType, completed:completedTime}" \
  --output table
```

### 3.2 手動バックアップ

リリース前やメンテナンス前に手動バックアップを取得:

```bash
# 手動バックアップの取得
az postgres flexible-server backup create \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --backup-name "manual-$(date +%Y%m%d-%H%M%S)"

# バックアップの確認
az postgres flexible-server backup show \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --backup-name "manual-20260327-100000"
```

### 3.3 論理バックアップ（pg_dump）

追加の安全策として、定期的に論理バックアップも取得:

```bash
# pg_dump による論理バックアップ（日次、Celeryタスクとして実行）
# バックアップスクリプト: scripts/backup/pg_backup.sh

#!/bin/bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="itscm-prod-${TIMESTAMP}.sql.gz"

# pg_dump実行（カスタムフォーマット、圧縮）
pg_dump \
  --host="${DB_HOST}" \
  --port=5432 \
  --username="${DB_USER}" \
  --dbname="${DB_NAME}" \
  --format=custom \
  --compress=9 \
  --file="/tmp/${BACKUP_FILE}"

# Azure Blob Storageへアップロード
az storage blob upload \
  --account-name itscmbackup \
  --container-name db-backup \
  --name "pg_dump/${BACKUP_FILE}" \
  --file "/tmp/${BACKUP_FILE}" \
  --overwrite

# 古いバックアップの削除（90日以上前）
az storage blob delete-batch \
  --account-name itscmbackup \
  --source db-backup \
  --pattern "pg_dump/itscm-prod-*" \
  --if-unmodified-since "$(date -u -d '90 days ago' +'%Y-%m-%dT%H:%M:%SZ')"

# クリーンアップ
rm -f "/tmp/${BACKUP_FILE}"

echo "Backup completed: ${BACKUP_FILE}"
```

### 3.4 Geo-レプリケーション設定

```bash
# レプリケーション状態の確認
az postgres flexible-server replica list \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "[].{name:name, state:state, role:replicationRole, location:location}" \
  --output table

# レプリケーション遅延の確認
az monitor metrics list \
  --resource "/subscriptions/{sub}/resourceGroups/rg-itscm-prod-eastjp/providers/Microsoft.DBforPostgreSQL/flexibleServers/itscm-db-prod-eastjp" \
  --metric "physical_replication_delay_in_seconds" \
  --interval PT1M \
  --query "value[0].timeseries[0].data[-1].average"
```

---

## 4. Redisバックアップ

### 4.1 RDBスナップショット

```bash
# Redis RDB設定確認
az redis show \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "{rdbEnabled:redisConfiguration.rdbBackupEnabled, frequency:redisConfiguration.rdbBackupFrequency, maxSnapshotCount:redisConfiguration.rdbBackupMaxSnapshotCount}"

# RDB設定の更新（1時間ごとのスナップショット）
az redis update \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --set "redisConfiguration.rdb-backup-enabled=true" \
  --set "redisConfiguration.rdb-backup-frequency=60" \
  --set "redisConfiguration.rdb-backup-max-snapshot-count=5" \
  --set "redisConfiguration.rdb-storage-connection-string=DefaultEndpointsProtocol=https;AccountName=itscmbackup;..."
```

### 4.2 手動エクスポート

```bash
# Redis手動エクスポート
az redis export \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --prefix "manual-backup-$(date +%Y%m%d)" \
  --container "https://itscmbackup.blob.core.windows.net/redis-backup" \
  --file-format RDB

# エクスポート結果確認
az storage blob list \
  --account-name itscmbackup \
  --container-name redis-backup \
  --prefix "manual-backup-" \
  --query "[].{name:name, size:properties.contentLength, modified:properties.lastModified}" \
  --output table
```

### 4.3 AOF（Append Only File）

```bash
# AOF設定確認
az redis show \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "redisConfiguration.aofEnabled"

# AOFはPremium SKUで利用可能
# AOFにより、最大1秒のRPOを実現
```

---

## 5. アプリケーションデータバックアップ

### 5.1 Azure Blob Storage

```bash
# Blob Storageのソフトデリート設定確認
az storage account blob-service-properties show \
  --account-name itscmstorage \
  --query "{softDelete:deleteRetentionPolicy, versioning:isVersioningEnabled}"

# Blob Storage設定:
#   ソフトデリート: 有効（30日保持）
#   バージョニング: 有効
#   変更フィード: 有効
#   ポイントインタイムリストア: 有効（30日）

# 日次スナップショットの取得
az storage blob snapshot \
  --account-name itscmstorage \
  --container-name documents \
  --name "important-file.pdf"
```

### 5.2 Terraform State バックアップ

```bash
# Terraform Stateのバージョニング確認
az storage account blob-service-properties show \
  --account-name stitscmtfstate \
  --query "isVersioningEnabled"

# Stateのバージョン一覧
az storage blob list \
  --account-name stitscmtfstate \
  --container-name tfstate-production \
  --include v \
  --query "[].{name:name, version:versionId, modified:properties.lastModified}" \
  --output table
```

### 5.3 Key Vault バックアップ

```bash
# Key Vaultのシークレット一括バックアップ
az keyvault secret list \
  --vault-name kv-itscm-prod-eastjp \
  --query "[].{name:name, enabled:attributes.enabled}" \
  --output table

# 個別シークレットのバックアップ（暗号化されたバックアップファイル）
az keyvault secret backup \
  --vault-name kv-itscm-prod-eastjp \
  --name "DATABASE-URL" \
  --file "backup/kv-DATABASE-URL-$(date +%Y%m%d).bak"

# Key Vaultは Azure によるソフトデリート（90日）と
# パージ保護が有効
```

---

## 6. リストア手順

### 6.1 PostgreSQLリストア

#### 6.1.1 ポイントインタイムリカバリ（PITR）

最も一般的なリストア方法。特定時点の状態に復元する。

```bash
echo "=== PostgreSQL PITR リストア開始 ==="

# Step 1: リストア対象時刻の決定
RESTORE_TIME="2026-03-27T09:00:00Z"  # UTCで指定
echo "リストア対象時刻: ${RESTORE_TIME}"

# Step 2: アプリケーションの停止（新規書き込み防止）
echo "アプリケーション停止中..."
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --min-replicas 0 --max-replicas 0

az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-eastjp \
  --min-replicas 0 --max-replicas 0

# Step 3: PITRリストア実行（新しいサーバーとして復元）
echo "PITRリストア実行中..."
az postgres flexible-server restore \
  --name itscm-db-prod-eastjp-restored \
  --resource-group rg-itscm-prod-eastjp \
  --source-server itscm-db-prod-eastjp \
  --restore-time "${RESTORE_TIME}"

# Step 4: リストア完了待機
echo "リストア完了を待機中..."
while true; do
  STATE=$(az postgres flexible-server show \
    --name itscm-db-prod-eastjp-restored \
    --resource-group rg-itscm-prod-eastjp \
    --query "state" -o tsv)
  if [ "$STATE" = "Ready" ]; then
    echo "リストア完了: サーバー Ready"
    break
  fi
  echo "  状態: ${STATE} - 待機中..."
  sleep 30
done

# Step 5: データ整合性確認
echo "データ整合性確認中..."
psql -h itscm-db-prod-eastjp-restored.postgres.database.azure.com \
  -U itscm_admin -d itscm_prod -c "
  SELECT 'テーブル数' as item, count(*) as value
  FROM information_schema.tables
  WHERE table_schema = 'public'
  UNION ALL
  SELECT 'BCP計画数', count(*)::text FROM bcp_plans
  UNION ALL
  SELECT 'ユーザー数', count(*)::text FROM users;
"

# Step 6: アプリケーションの接続先切替
echo "接続先を復元DBに切替..."
az containerapp secret set \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --secrets "database-url=postgresql://itscm_admin:****@itscm-db-prod-eastjp-restored.postgres.database.azure.com:5432/itscm_prod?sslmode=require"

# Step 7: アプリケーション再開
echo "アプリケーション再開..."
az containerapp update \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --min-replicas 3 --max-replicas 20

az containerapp update \
  --name itscm-worker-prod \
  --resource-group rg-itscm-prod-eastjp \
  --min-replicas 2 --max-replicas 10

# Step 8: 動作確認
echo "動作確認..."
sleep 60  # アプリ起動待ち
curl -sf https://eastjp.itscm.example.com/api/health | jq .

echo "=== PostgreSQL PITRリストア完了 ==="
echo "注意: ${RESTORE_TIME} 以降のデータは失われています"
echo "注意: レプリカの再構築が必要です"
```

#### 6.1.2 バックアップからのリストア

```bash
# 特定のバックアップからリストア
az postgres flexible-server restore \
  --name itscm-db-prod-eastjp-restored \
  --resource-group rg-itscm-prod-eastjp \
  --source-server itscm-db-prod-eastjp \
  --restore-time "2026-03-27T02:00:00Z"  # バックアップ完了時刻
```

#### 6.1.3 pg_dumpからのリストア

```bash
# Azure Blob Storageからバックアップファイルをダウンロード
az storage blob download \
  --account-name itscmbackup \
  --container-name db-backup \
  --name "pg_dump/itscm-prod-20260327-020000.sql.gz" \
  --file "/tmp/itscm-prod-restore.sql.gz"

# 新規データベース作成
psql -h itscm-db-prod-eastjp.postgres.database.azure.com \
  -U itscm_admin -d postgres \
  -c "CREATE DATABASE itscm_prod_restored;"

# リストア実行
pg_restore \
  --host="itscm-db-prod-eastjp.postgres.database.azure.com" \
  --port=5432 \
  --username="itscm_admin" \
  --dbname="itscm_prod_restored" \
  --format=custom \
  --jobs=4 \
  --verbose \
  "/tmp/itscm-prod-restore.sql.gz"
```

### 6.2 Redisリストア

#### 6.2.1 RDBスナップショットからのリストア

```bash
echo "=== Redis リストア開始 ==="

# Step 1: 現在のデータのエクスポート（安全策）
az redis export \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --prefix "pre-restore-$(date +%Y%m%d%H%M)" \
  --container "https://itscmbackup.blob.core.windows.net/redis-backup" \
  --file-format RDB

# Step 2: リストア対象のバックアップ確認
az storage blob list \
  --account-name itscmbackup \
  --container-name redis-backup \
  --query "[?contains(name,'manual-backup')].{name:name, modified:properties.lastModified, size:properties.contentLength}" \
  --output table

# Step 3: Redisインポート実行
BACKUP_FILE="https://itscmbackup.blob.core.windows.net/redis-backup/manual-backup-20260327-data.rdb"

az redis import \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --files "${BACKUP_FILE}" \
  --file-format RDB

# Step 4: リストア確認
echo "Redis接続確認..."
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "python -c \"import redis; r=redis.from_url('$REDIS_URL'); print(f'Keys: {r.dbsize()}')\""

echo "=== Redis リストア完了 ==="
```

#### 6.2.2 キャッシュのみの場合

キャッシュデータのみの場合、リストアではなくキャッシュクリアで対応:

```bash
# キャッシュフラッシュ（セッションは保持）
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "python -c \"
import redis
r = redis.from_url('$REDIS_URL')
# キャッシュキーのみ削除（セッションは保持）
for key in r.scan_iter('cache:*'):
    r.delete(key)
print('Cache cleared')
\""
```

### 6.3 Azure Blob Storage リストア

```bash
# ポイントインタイムリストア（30日以内）
az storage blob restore \
  --account-name itscmstorage \
  --time-to-restore "2026-03-27T09:00:00Z"

# 特定Blobのバージョン復元
az storage blob copy start \
  --account-name itscmstorage \
  --destination-container documents \
  --destination-blob "important-file.pdf" \
  --source-uri "https://itscmstorage.blob.core.windows.net/documents/important-file.pdf?versionid=2026-03-27T08:00:00.0000000Z"

# ソフトデリートからの復元
az storage blob undelete \
  --account-name itscmstorage \
  --container-name documents \
  --name "accidentally-deleted-file.pdf"
```

---

## 7. RPO準拠確認

### 7.1 RPO準拠の検証方法

| 検証項目 | 方法 | 目標 | 頻度 |
|---------|------|------|------|
| PostgreSQL WALアーカイブ遅延 | レプリケーション遅延メトリクス | < 5分 | 常時監視 |
| PostgreSQL自動バックアップ | バックアップ完了時刻の確認 | 24時間以内 | 日次 |
| Redis RDBスナップショット | スナップショット間隔の確認 | 1時間以内 | 日次 |
| Blob Storageバージョニング | バージョン作成確認 | 変更時即時 | 週次 |
| PITRリストアテスト | 実際のリストア実行 | リストア成功 | 月次 |

### 7.2 RPO監視アラート

```json
{
  "alertRules": [
    {
      "name": "rpo-db-replication-lag",
      "description": "DBレプリケーション遅延がRPOを超過",
      "condition": {
        "metric": "physical_replication_delay_in_seconds",
        "operator": "GreaterThan",
        "threshold": 300,
        "windowSize": "PT5M"
      },
      "severity": 1
    },
    {
      "name": "rpo-db-backup-missing",
      "description": "24時間以上バックアップが取得されていない",
      "type": "LogAlert",
      "query": "AzureActivity | where OperationNameValue contains 'backup' | where TimeGenerated > ago(24h) | count",
      "threshold": 0,
      "severity": 1
    },
    {
      "name": "rpo-redis-snapshot-age",
      "description": "Redisスナップショットが2時間以上古い",
      "condition": {
        "metric": "lastSnapshotTime",
        "operator": "GreaterThan",
        "threshold": 7200,
        "windowSize": "PT10M"
      },
      "severity": 2
    }
  ]
}
```

### 7.3 月次RPO検証レポート

```markdown
## RPO準拠検証レポート

### 検証期間: YYYY年MM月
### 検証実施日: YYYY-MM-DD
### 検証者:

### PostgreSQL RPO検証
| 項目 | 結果 | RPO目標 | 判定 |
|------|------|---------|------|
| 最大レプリケーション遅延 | X.X秒 | < 60秒 | OK/NG |
| 自動バックアップ取得率 | 100% | 100% | OK/NG |
| PITRリストアテスト | 成功/失敗 | 成功 | OK/NG |
| リストア時のデータロス | 0分 | < 60分 | OK/NG |

### Redis RPO検証
| 項目 | 結果 | RPO目標 | 判定 |
|------|------|---------|------|
| RDBスナップショット間隔 | 60分 | < 60分 | OK/NG |
| AOFデータ損失 | ~1秒 | < 60分 | OK/NG |
| リストアテスト | 成功/失敗 | 成功 | OK/NG |

### 総合判定: OK / NG
### 指摘事項:
### 改善提案:
```

---

## 8. バックアップ監視・テスト

### 8.1 日次バックアップ確認

```bash
# 朝のチェック（運用手順書 Step 5）
echo "=== バックアップ状態確認 ==="

# PostgreSQL
echo "--- PostgreSQL バックアップ ---"
az postgres flexible-server backup list \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "[0:3].{name:name, type:backupType, completed:completedTime}" \
  --output table

# Redis
echo "--- Redis スナップショット ---"
az storage blob list \
  --account-name itscmbackup \
  --container-name redis-backup \
  --query "sort_by([],&properties.lastModified)[-3:].{name:name, modified:properties.lastModified, size:properties.contentLength}" \
  --output table

# レプリケーション遅延
echo "--- レプリケーション遅延 ---"
az monitor metrics list \
  --resource "/subscriptions/{sub}/resourceGroups/rg-itscm-prod-eastjp/providers/Microsoft.DBforPostgreSQL/flexibleServers/itscm-db-prod-eastjp" \
  --metric "physical_replication_delay_in_seconds" \
  --interval PT1M \
  --query "value[0].timeseries[0].data[-1].{avg:average,max:maximum}" \
  --output json
```

### 8.2 月次リストアテスト

```bash
echo "=== 月次リストアテスト開始 ==="
echo "日時: $(date)"

# Step 1: テスト用リストア実行
RESTORE_TIME=$(date -u -d '1 hour ago' +'%Y-%m-%dT%H:%M:%SZ')
TEST_SERVER="itscm-db-restore-test-$(date +%Y%m%d)"

az postgres flexible-server restore \
  --name "${TEST_SERVER}" \
  --resource-group rg-itscm-staging \
  --source-server itscm-db-prod-eastjp \
  --restore-time "${RESTORE_TIME}"

# Step 2: 復元完了待ち
echo "復元完了待ち..."
while [ "$(az postgres flexible-server show --name ${TEST_SERVER} --resource-group rg-itscm-staging --query state -o tsv)" != "Ready" ]; do
  sleep 30
done

# Step 3: データ整合性検証
echo "データ整合性検証..."
psql -h "${TEST_SERVER}.postgres.database.azure.com" \
  -U itscm_admin -d itscm_prod -c "
  SELECT 'tables' as type, count(*) as cnt FROM information_schema.tables WHERE table_schema='public'
  UNION ALL
  SELECT 'users', count(*) FROM users
  UNION ALL
  SELECT 'bcp_plans', count(*) FROM bcp_plans
  UNION ALL
  SELECT 'audit_logs', count(*) FROM audit_logs;"

# Step 4: テストサーバー削除
echo "テストサーバー削除..."
az postgres flexible-server delete \
  --name "${TEST_SERVER}" \
  --resource-group rg-itscm-staging \
  --yes

echo "=== 月次リストアテスト完了 ==="
```

### 8.3 バックアップ障害時の対応

| 障害 | 検知方法 | 対応 |
|------|---------|------|
| 自動バックアップ失敗 | アラート | Azureサポート確認、手動バックアップ取得 |
| レプリケーション断 | アラート | レプリカ状態確認、再構築 |
| RDBスナップショット失敗 | アラート | ストレージ接続確認、手動エクスポート |
| バックアップストレージ容量不足 | アラート | 古いバックアップ削除、ストレージ拡張 |
| リストアテスト失敗 | 月次テスト | 原因調査、バックアップ方式見直し |

---

## 関連文書

| 文書番号 | 文書名 |
|---------|--------|
| ITSCM-OP-001 | 運用手順書 |
| ITSCM-OP-003 | 障害対応手順書 |
| ITSCM-OP-005 | DR手順書 |
| ITSCM-RM-003 | ロールバック手順書 |
| ITSCM-RM-004 | デプロイメント構成管理 |

---

以上
