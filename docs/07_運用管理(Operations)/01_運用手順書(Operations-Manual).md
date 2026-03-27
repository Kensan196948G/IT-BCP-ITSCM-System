# 運用手順書（Operations Manual）

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-OP-001 |
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
2. [運用体制](#2-運用体制)
3. [日常運用](#3-日常運用)
4. [定期メンテナンス](#4-定期メンテナンス)
5. [ログ管理](#5-ログ管理)
6. [パフォーマンス管理](#6-パフォーマンス管理)
7. [セキュリティ運用](#7-セキュリティ運用)
8. [ユーザーサポート](#8-ユーザーサポート)

---

## 1. 概要

### 1.1 目的

本文書は、IT-BCP-ITSCMシステムの安定稼働を維持するための日常運用手順および定期メンテナンス手順を定義する。

### 1.2 システム構成概要

| コンポーネント | 技術 | デプロイ先 |
|-------------|------|----------|
| フロントエンド | Next.js 14 / TypeScript / PWA | Azure Container Apps |
| バックエンドAPI | Python FastAPI | Azure Container Apps |
| ワーカー | Celery Worker | Azure Container Apps |
| データベース | PostgreSQL (Geo冗長) | Azure Database for PostgreSQL Flexible Server |
| キャッシュ | Redis Cluster | Azure Cache for Redis |
| CDN/LB | Azure Front Door | グローバル |
| 監視 | Azure Monitor / Application Insights | グローバル |
| ログ | Log Analytics Workspace | East Japan |

### 1.3 SLA/SLO

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| 可用性 | 99.9%（月間） | Azure Monitor |
| API応答時間 | p95 < 200ms | Application Insights |
| ページロード時間 | < 3秒（初回）| Lighthouse |
| フェイルオーバー時間 | 90秒以内 | DR訓練 |
| システムRTO | 15分以内 | DR訓練 |
| RPO | 1時間以内 | バックアップ検証 |

---

## 2. 運用体制

### 2.1 運用チーム構成

| 役割 | 担当 | 責務 |
|------|------|------|
| 運用マネージャー | 1名 | 運用全体の管理、エスカレーション最終判断 |
| L1サポート | 2名 | 日常監視、初動対応、ユーザー問い合わせ対応 |
| L2サポート | 2名 | 技術的障害対応、パフォーマンス調査 |
| L3サポート（開発チーム） | オンコール | アプリケーション障害の根本解決 |
| DBA | 1名 | データベース管理、パフォーマンスチューニング |
| インフラエンジニア | 1名 | インフラ管理、ネットワーク管理 |

### 2.2 オンコール体制

| 時間帯 | 体制 | 連絡方法 |
|--------|------|---------|
| 平日 09:00-18:00 | L1/L2常駐 | Slack #ops-itscm |
| 平日 18:00-22:00 | L2オンコール | PagerDuty |
| 平日 22:00-09:00 | L2オンコール（待機） | PagerDuty |
| 休日・祝日 | L2オンコール（待機） | PagerDuty |

### 2.3 エスカレーション連絡先

| レベル | 担当 | 連絡先 | 対応時間 |
|--------|------|--------|---------|
| L1 | 運用サポート | Slack: #ops-itscm | 即時 |
| L2 | 運用エンジニア | PagerDuty + 電話 | 15分以内 |
| L3 | 開発チーム | PagerDuty + 電話 | 30分以内 |
| 管理者 | 運用マネージャー | 電話 | 30分以内 |
| 経営 | CTO | 電話 | 1時間以内 |

---

## 3. 日常運用

### 3.1 朝の始業チェック（毎日 09:00）

**担当**: L1サポート
**所要時間**: 15-20分

#### Step 1: システム全体ヘルスチェック

```bash
# 1. Azure Front Door経由の疎通確認
curl -sf https://itscm.example.com/api/health | jq .
# 期待: {"status":"healthy","version":"v1.0.0","timestamp":"..."}

# 2. East Japan直接確認
curl -sf https://eastjp.itscm.example.com/api/health | jq .

# 3. West Japan直接確認
curl -sf https://westjp.itscm.example.com/api/health | jq .

# 4. 詳細ヘルスチェック
curl -sf https://itscm.example.com/api/health/detail | jq .
# 期待: DB接続OK, Redis接続OK, Celery Worker active
```

#### Step 2: 監視ダッシュボード確認

```
確認場所: Azure Portal > Monitor > ダッシュボード > ITSCM-Overview

確認項目:
  [ ] 可用性: 99.9%以上
  [ ] エラーレート: 0.1%以下
  [ ] API応答時間 p95: 200ms以下
  [ ] CPU使用率: 70%以下
  [ ] メモリ使用率: 80%以下
  [ ] DB接続数: プールサイズの80%以下
  [ ] Redis メモリ使用率: 80%以下
  [ ] Celeryキュー滞留: 0
```

#### Step 3: アラート確認

```
確認場所: Azure Portal > Monitor > アラート

確認項目:
  [ ] 夜間に発生したアラートの確認
  [ ] 未解決アラートの有無
  [ ] アラートの対応状況確認

異常があった場合:
  → 障害対応手順書（ITSCM-OP-003）に従い対応
  → Slack #ops-itscm に状況報告
```

#### Step 4: ログ確認

```
確認場所: Azure Portal > Log Analytics > ITSCM Workspace

KQLクエリ:
// 過去12時間のエラーログ確認
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(12h)
| where Log_s contains "ERROR" or Log_s contains "CRITICAL"
| project TimeGenerated, ContainerAppName_s, Log_s
| order by TimeGenerated desc
| take 50
```

#### Step 5: バックアップ確認

```bash
# PostgreSQLバックアップ状態確認
az postgres flexible-server backup list \
  --name itscm-db-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "[0].{name:name, completed:completedTime, type:backupType}" \
  --output table

# 最新バックアップが24時間以内であることを確認
```

### 3.2 昼の確認（毎日 13:00）

**担当**: L1サポート
**所要時間**: 5-10分

```
確認項目:
  [ ] 監視ダッシュボードの簡易確認
  [ ] 午前中に発生したアラートの確認
  [ ] ユーザー問い合わせの状況確認
  [ ] Celeryタスクの実行状況確認
```

### 3.3 終業チェック（毎日 17:30）

**担当**: L1サポート
**所要時間**: 10分

```
確認項目:
  [ ] 日中の運用状況サマリー作成
  [ ] 未解決のインシデント・問い合わせの引継ぎ
  [ ] 翌日の作業予定確認
  [ ] 夜間メンテナンスの有無確認
  [ ] オンコール担当者への引継ぎ
```

### 3.4 日次運用レポート

```markdown
## 日次運用レポート

### 日付: YYYY-MM-DD
### 報告者:

### システム稼働状況
- 可用性: XX.XX%
- 平均応答時間: XXms
- エラー件数: XX件
- ピークトラフィック時刻: HH:MM
- ピーク時リクエスト数: XXXX req/min

### インシデント
| 時刻 | 内容 | 影響 | 対応 | ステータス |
|------|------|------|------|----------|
| | | | | |

### アラート
| 時刻 | アラート | 対応 |
|------|---------|------|
| | | |

### 特記事項
（特記事項があれば記載）

### 翌日の予定
（メンテナンス、リリース等の予定）
```

---

## 4. 定期メンテナンス

### 4.1 週次メンテナンス

**実施日**: 毎週月曜日
**担当**: L2サポート / インフラエンジニア

| 作業項目 | 手順 | 所要時間 |
|---------|------|---------|
| ディスク使用量確認 | Azure Monitor確認、不要データクリーンアップ | 15分 |
| ログローテーション確認 | Log Analytics保持ポリシー確認 | 5分 |
| SSL証明書有効期限確認 | 証明書の有効期限が30日以上あることを確認 | 5分 |
| コンテナイメージクリーンアップ | ACRの古いイメージ削除確認 | 10分 |
| セキュリティアラートレビュー | Microsoft Defender for Cloudの確認 | 15分 |
| バックアップ整合性確認 | 週次バックアップの取得確認 | 10分 |
| パフォーマンストレンド確認 | 週次パフォーマンスレポート作成 | 20分 |

```bash
# SSL証明書有効期限確認
az network front-door frontend-endpoint list \
  --front-door-name itscm-frontdoor \
  --resource-group rg-itscm-global \
  --query "[].{name:name, customHttpsProvisioningState:customHttpsProvisioningState}" \
  --output table

# ディスク使用量確認
az monitor metrics list \
  --resource "/subscriptions/{sub}/resourceGroups/rg-itscm-prod-eastjp/providers/Microsoft.DBforPostgreSQL/flexibleServers/itscm-db-prod-eastjp" \
  --metric "storage_percent" \
  --interval PT1H \
  --start-time "$(date -u -d '7 days ago' +'%Y-%m-%dT%H:%M:%SZ')" \
  --query "value[0].timeseries[0].data[-1].average"

# ACRイメージクリーンアップ（30日以上前の未タグイメージ）
az acr run \
  --registry itscmacr \
  --cmd "acr purge --filter 'itscm-api:sha-*' --ago 30d --keep 10 --untagged" \
  /dev/null
```

### 4.2 月次メンテナンス

**実施日**: 毎月第1月曜日
**担当**: L2サポート / DBA / インフラエンジニア

| 作業項目 | 手順 | 所要時間 |
|---------|------|---------|
| データベースメンテナンス | VACUUM ANALYZE、インデックス再構築 | 30分 |
| Redis メンテナンス | メモリ断片化率確認、必要に応じてリスタート | 15分 |
| 容量計画レビュー | リソース使用量のトレンド分析、増強計画 | 30分 |
| セキュリティパッチ確認 | OS/ミドルウェアのセキュリティパッチ適用確認 | 30分 |
| 監視・アラート設定レビュー | 閾値の適正性確認、不要アラートの整理 | 20分 |
| 月次運用レポート作成 | SLA達成状況、インシデント分析、改善提案 | 60分 |
| バックアップリストアテスト | 月次バックアップからの復元テスト | 60分 |

```bash
# PostgreSQL VACUUM ANALYZE
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c 'VACUUM ANALYZE;'"

# PostgreSQL統計情報確認
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c '
    SELECT schemaname, tablename, n_live_tup, n_dead_tup,
           last_vacuum, last_autovacuum, last_analyze
    FROM pg_stat_user_tables
    ORDER BY n_dead_tup DESC
    LIMIT 20;'"

# Redisメモリ断片化率確認
az redis show \
  --name itscm-redis-prod-eastjp \
  --resource-group rg-itscm-prod-eastjp \
  --query "{memory:redisConfiguration.maxmemoryPolicy, connected:linkedServers}" \
  --output json
```

### 4.3 四半期メンテナンス

**実施日**: 四半期末月の第2週
**担当**: 運用マネージャー / 全運用チーム

| 作業項目 | 手順 | 所要時間 |
|---------|------|---------|
| DR訓練 | フェイルオーバー/フェイルバックテスト | 4時間 |
| ロールバック訓練 | ロールバック手順のリハーサル | 2時間 |
| セキュリティ監査 | 脆弱性スキャン、ペネトレーションテスト | 8時間 |
| 容量計画見直し | 四半期の成長率を踏まえた容量計画 | 2時間 |
| SLA/SLOレビュー | SLA達成状況の四半期レビュー | 2時間 |
| 運用手順書レビュー | 全手順書の最新化確認 | 4時間 |
| 運用チーム教育 | 新手順・新ツールのトレーニング | 4時間 |

### 4.4 年次メンテナンス

| 作業項目 | 時期 | 担当 |
|---------|------|------|
| ISO20000/27001内部監査 | 年1回 | コンプライアンスチーム |
| 外部セキュリティ監査 | 年1回 | 外部監査法人 |
| BCP計画見直し | 年1回 | 全ステークホルダー |
| 技術スタック見直し | 年1回 | アーキテクト / CTO |
| ライセンス監査 | 年1回 | 法務 / 経理 |

---

## 5. ログ管理

### 5.1 ログ種別

| ログ種別 | 収集先 | 保持期間 | 用途 |
|---------|--------|---------|------|
| アプリケーションログ | Log Analytics | 90日 | 障害調査、デバッグ |
| アクセスログ | Log Analytics | 90日 | トラフィック分析 |
| 監査ログ | Log Analytics | 365日 | コンプライアンス、セキュリティ |
| セキュリティログ | Log Analytics + Sentinel | 365日 | セキュリティ監視 |
| パフォーマンスログ | Application Insights | 90日 | パフォーマンス分析 |
| インフラログ | Azure Activity Log | 90日 | インフラ変更追跡 |
| DBログ | PostgreSQLログ | 30日 | DB障害調査 |

### 5.2 重要KQLクエリ集

```kql
// エラーログの集計（過去24時間）
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(24h)
| where Log_s contains "ERROR"
| summarize count() by bin(TimeGenerated, 1h), ContainerAppName_s
| render timechart

// スロークエリの検出（100ms以上）
AppRequests
| where TimeGenerated > ago(24h)
| where DurationMs > 100
| summarize count(), avg(DurationMs), max(DurationMs) by Name
| order by count_ desc

// HTTP 5xxエラーの詳細
AppRequests
| where TimeGenerated > ago(24h)
| where ResultCode startswith "5"
| project TimeGenerated, Name, ResultCode, DurationMs, Url
| order by TimeGenerated desc

// ユーザーセッション分析
AppPageViews
| where TimeGenerated > ago(24h)
| summarize Users=dcount(UserId), PageViews=count() by bin(TimeGenerated, 1h)
| render timechart

// セキュリティイベント
AzureActivity
| where TimeGenerated > ago(24h)
| where CategoryValue == "Security"
| project TimeGenerated, OperationNameValue, Caller, ResourceGroup
| order by TimeGenerated desc
```

---

## 6. パフォーマンス管理

### 6.1 パフォーマンス指標

| 指標 | 目標値 | 警告閾値 | 危険閾値 |
|------|--------|---------|---------|
| API応答時間 p50 | < 50ms | > 100ms | > 200ms |
| API応答時間 p95 | < 200ms | > 300ms | > 500ms |
| API応答時間 p99 | < 500ms | > 800ms | > 1000ms |
| フロントエンド LCP | < 2.5秒 | > 3秒 | > 4秒 |
| CPU使用率 | < 50% | > 70% | > 85% |
| メモリ使用率 | < 60% | > 80% | > 90% |
| DB接続使用率 | < 60% | > 80% | > 90% |
| Redis メモリ使用率 | < 60% | > 80% | > 90% |
| Celeryキュー長 | 0 | > 100 | > 1000 |

### 6.2 パフォーマンス劣化時の対応

```
劣化検知
  │
  ├── API応答時間劣化
  │    ├── スロークエリの特定 → DBチューニング
  │    ├── キャッシュヒット率低下 → Redis確認
  │    └── リソース不足 → スケールアウト
  │
  ├── CPU/メモリ逼迫
  │    ├── メモリリーク → アプリケーション調査
  │    ├── 負荷増大 → オートスケール確認・スケールアウト
  │    └── バッチ処理影響 → スケジュール調整
  │
  └── DB性能劣化
       ├── ロック競合 → クエリ最適化
       ├── インデックス不足 → インデックス追加
       └── VACUUM不足 → 手動VACUUM実行
```

---

## 7. セキュリティ運用

### 7.1 日常セキュリティ確認

| 確認項目 | 頻度 | 担当 |
|---------|------|------|
| Microsoft Defender for Cloud確認 | 毎日 | L1サポート |
| 不審なログイン試行の確認 | 毎日 | L1サポート |
| WAFログの確認 | 毎日 | L2サポート |
| 脆弱性スキャン結果確認 | 毎日 | セキュリティ担当 |

### 7.2 シークレットローテーション

| シークレット | ローテーション周期 | 担当 | 手順 |
|------------|-----------------|------|------|
| DB接続パスワード | 90日 | DBA | Key Vault更新→アプリ再起動 |
| Redis接続パスワード | 90日 | インフラ | Key Vault更新→アプリ再起動 |
| JWT署名キー | 90日 | DevOps | Key Vault更新→段階的切替 |
| APIキー（外部サービス） | 365日 | DevOps | Key Vault更新→アプリ再起動 |
| SSL証明書 | 自動更新 | Azure | Azure管理 |

### 7.3 セキュリティインシデント発生時

```
→ 障害対応手順書（ITSCM-OP-003）のセキュリティインシデント対応セクションに従う
```

---

## 8. ユーザーサポート

### 8.1 問い合わせ対応フロー

```
ユーザー問い合わせ
  │
  ├── L1対応（即時〜30分）
  │    ├── FAQ確認・回答
  │    ├── 既知の問題の回答
  │    └── 操作方法のガイド
  │
  ├── L2エスカレーション（30分〜2時間）
  │    ├── 技術的調査
  │    ├── ログ分析
  │    └── 一時的回避策の提供
  │
  └── L3エスカレーション（2時間〜）
       ├── アプリケーションバグ調査
       ├── 根本原因分析
       └── 修正パッチの作成
```

### 8.2 問い合わせ分類

| カテゴリ | 対応レベル | 目標応答時間 | 目標解決時間 |
|---------|----------|------------|------------|
| 操作方法・FAQ | L1 | 30分以内 | 1時間以内 |
| 機能要望 | L1（記録） | 1時間以内 | バックログ登録 |
| 不具合報告（軽微） | L2 | 1時間以内 | 3営業日以内 |
| 不具合報告（重大） | L2/L3 | 30分以内 | 1営業日以内 |
| セキュリティ報告 | L3 | 即時 | 即時対応 |

---

## 関連文書

| 文書番号 | 文書名 |
|---------|--------|
| ITSCM-OP-002 | 監視設計書 |
| ITSCM-OP-003 | 障害対応手順書 |
| ITSCM-OP-004 | バックアップリストア手順書 |
| ITSCM-OP-005 | DR手順書 |
| ITSCM-RM-002 | リリース手順書 |
| ITSCM-RM-003 | ロールバック手順書 |

---

以上
