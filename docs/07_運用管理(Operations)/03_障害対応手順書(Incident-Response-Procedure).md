# 障害対応手順書（Incident Response Procedure）

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-OP-003 |
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
2. [障害レベル定義](#2-障害レベル定義)
3. [エスカレーションフロー](#3-エスカレーションフロー)
4. [障害対応プロセス](#4-障害対応プロセス)
5. [障害パターン別対応手順](#5-障害パターン別対応手順)
6. [セキュリティインシデント対応](#6-セキュリティインシデント対応)
7. [障害報告・分析](#7-障害報告分析)

---

## 1. 概要

### 1.1 目的

本文書は、IT-BCP-ITSCMシステムに発生する障害（インシデント）に対して迅速かつ適切に対応し、サービスへの影響を最小限に抑えるための手順を定義する。

### 1.2 障害対応の原則

| 原則 | 内容 |
|------|------|
| 迅速な検知 | 監視システムによる自動検知、ユーザー報告の即時受付 |
| サービス復旧優先 | 根本原因分析より先にサービス復旧を優先 |
| 適切なエスカレーション | 障害レベルに応じた適切なエスカレーション |
| 正確な記録 | 全対応内容の時系列での正確な記録 |
| 再発防止 | ポストモーテムによる根本原因分析と再発防止策の策定 |

---

## 2. 障害レベル定義

### 2.1 障害レベル一覧

| レベル | 名称 | 定義 | 対応時間目標 | 復旧時間目標 |
|--------|------|------|------------|------------|
| P1 | Critical | サービス全停止、データ損失リスク、セキュリティ侵害 | 即時（5分以内） | 1時間以内 |
| P2 | High | 主要機能停止、大多数のユーザーに影響 | 15分以内 | 4時間以内 |
| P3 | Medium | 一部機能障害、回避策あり、一部ユーザーに影響 | 1時間以内 | 8時間以内 |
| P4 | Low | 軽微な不具合、ユーザー影響軽微 | 4時間以内 | 次営業日 |

### 2.2 障害レベル判定基準

#### P1 (Critical) の条件

- サービス全体がアクセス不能
- 両リージョン（East/West Japan）が同時停止
- データベースへの書き込み不可、データ損失リスク
- セキュリティ侵害（不正アクセス、データ漏洩）
- フェイルオーバーが機能しない状態
- 全ユーザーに影響

#### P2 (High) の条件

- 主要機能（認証、BCP計画管理、RTOダッシュボード）が利用不可
- APIエラーレートが5%以上
- 応答時間がSLA基準の5倍以上
- Primaryリージョンが停止（Standbyで稼働中）
- 大多数のユーザー（50%以上）に影響

#### P3 (Medium) の条件

- 一部機能が利用不可だが回避策あり
- APIエラーレートが1%〜5%
- パフォーマンスが目標値を下回るが利用可能
- バッチ処理の遅延
- 一部ユーザー（50%未満）に影響

#### P4 (Low) の条件

- UIの表示崩れ、誤字等
- 特定条件でのみ発生する不具合
- パフォーマンスの軽微な劣化
- ログの警告増加（サービスへの影響なし）

---

## 3. エスカレーションフロー

### 3.1 エスカレーションマトリクス

```
        P1 (Critical)           P2 (High)              P3 (Medium)         P4 (Low)
        │                       │                      │                   │
 検知   │ 即時                   │ 即時                  │ 1時間以内          │ 次営業日
        │                       │                      │                   │
 L1     ├→ トリアージ(5分)       ├→ トリアージ(15分)      ├→ 調査開始          ├→ チケット作成
        │                       │                      │                   │
 L2     ├→ 即時アサイン          ├→ 15分以内アサイン      ├→ 1時間以内         │  (L1で対応)
        │                       │                      │  アサイン           │
 L3     ├→ 即時召集             ├→ 必要に応じて          │  (必要に応じて)      │
        │                       │                      │                   │
 管理者  ├→ 即時通知             ├→ 30分以内通知         │  (レポートで報告)    │
        │                       │                      │                   │
 CTO    ├→ 15分以内通知         │  (1時間レポート)       │                   │
        │                       │                      │                   │
 外部   ├→ 必要に応じて          │                      │                   │
        │  (Azureサポート等)      │                      │                   │
```

### 3.2 エスカレーション連絡先

| レベル | 担当/チーム | 連絡方法 | 連絡先 |
|--------|----------|---------|--------|
| L1 | 運用サポート | Slack | #ops-itscm |
| L2 | 運用エンジニア | PagerDuty | Schedule: ops-l2-oncall |
| L3 | 開発チーム | PagerDuty | Schedule: dev-oncall |
| L3-DB | DBA | PagerDuty | Schedule: dba-oncall |
| L3-Infra | インフラチーム | PagerDuty | Schedule: infra-oncall |
| L3-Security | セキュリティチーム | PagerDuty | Schedule: security-oncall |
| 運用マネージャー | 運用部門長 | 電話 + Slack | （直通番号） |
| CTO | 技術責任者 | 電話 | （直通番号） |
| Azureサポート | Microsoft | Azureポータル | サポートリクエスト（Severity A） |

### 3.3 エスカレーションタイマー

| 経過時間 | P1対応 | P2対応 |
|---------|--------|--------|
| 0分 | 検知、L1トリアージ開始 | 検知、L1トリアージ開始 |
| 5分 | L2アサイン、調査開始 | |
| 15分 | L3召集、運用マネージャー通知 | L2アサイン |
| 30分 | CTO通知、戦略判断 | 運用マネージャー通知 |
| 60分 | 未復旧の場合: Azureサポート起票 | L3召集（必要に応じて） |
| 120分 | 経営報告 | |
| 240分 | | CTO通知（未復旧の場合） |

---

## 4. 障害対応プロセス

### 4.1 障害対応フロー全体像

```
検知 → トリアージ → 初動対応 → 調査・診断 → 復旧 → 確認 → クローズ → ポストモーテム

Phase 1: 検知・トリアージ（0-15分）
  ├── 障害の検知（監視アラート/ユーザー報告）
  ├── 障害レベルの判定
  ├── インシデントチケット作成
  └── エスカレーション

Phase 2: 初動対応（15-60分）
  ├── 影響範囲の特定
  ├── 暫定対処（回避策、フェイルオーバー等）
  └── ステークホルダーへの状況報告

Phase 3: 調査・復旧（60分-）
  ├── 根本原因の調査
  ├── 復旧作業の実施
  └── 復旧確認

Phase 4: クローズ・分析（復旧後）
  ├── サービス復旧確認
  ├── インシデントレポート作成
  └── ポストモーテム実施
```

### 4.2 インシデントチケット作成

```markdown
## インシデントチケット

### 基本情報
- インシデント番号: INC-YYYY-NNNN（自動採番）
- 検知日時: YYYY-MM-DD HH:MM:SS
- 検知方法: 監視アラート / ユーザー報告 / その他
- 障害レベル: P1 / P2 / P3 / P4
- ステータス: Open / Investigating / Identified / Recovering / Resolved / Closed
- 担当者:
- 影響範囲:

### タイムライン
| 時刻 | アクション | 担当 |
|------|----------|------|
| | | |

### 影響
- 影響サービス:
- 影響ユーザー数:
- ビジネスへの影響:

### 対応内容
（対応の詳細）

### 根本原因
（判明後記載）

### 再発防止策
（ポストモーテム後記載）
```

### 4.3 コミュニケーションテンプレート

#### 初報テンプレート

```
[INCIDENT] IT-BCP-ITSCM System - P{レベル} インシデント発生

発生日時: YYYY-MM-DD HH:MM
影響: {影響の概要}
現在の状況: 調査中
次回更新: {時刻}

対応チーム: {担当者名}
```

#### 中間報告テンプレート

```
[UPDATE] INC-YYYY-NNNN - P{レベル} インシデント 更新

ステータス: {ステータス}
経過: {前回更新からの経過}
現在の状況: {現在の状況}
見込み: {復旧見込み}
次回更新: {時刻}
```

#### 復旧報告テンプレート

```
[RESOLVED] INC-YYYY-NNNN - P{レベル} インシデント 復旧

復旧日時: YYYY-MM-DD HH:MM
影響時間: XX分
原因: {原因の概要}
対処: {対処内容}
備考: ポストモーテムを{日付}に実施予定
```

---

## 5. 障害パターン別対応手順

### 5.1 アプリケーション障害

#### 5.1.1 API全体停止

**症状**: 全APIエンドポイントが応答しない
**レベル**: P1

```
対応手順:
1. コンテナの状態確認
   az containerapp show \
     --name itscm-api-prod \
     --resource-group rg-itscm-prod-eastjp \
     --query "properties.runningStatus"

2. レプリカの確認
   az containerapp revision list \
     --name itscm-api-prod \
     --resource-group rg-itscm-prod-eastjp \
     --query "[?properties.active].{name:name,replicas:properties.replicas}"

3. ログ確認
   az containerapp logs show \
     --name itscm-api-prod \
     --resource-group rg-itscm-prod-eastjp \
     --tail 100

4. 対処:
   a. レプリカ数が0の場合 → スケール設定確認、手動スケール
      az containerapp update \
        --name itscm-api-prod \
        --resource-group rg-itscm-prod-eastjp \
        --min-replicas 3

   b. コンテナ起動エラーの場合 → ログ確認、前バージョンへのロールバック
      → ロールバック手順書（ITSCM-RM-003）に従う

   c. East Japanのみ障害 → West Japanへのフェイルオーバー
      → DR手順書（ITSCM-OP-005）に従う
```

#### 5.1.2 認証障害

**症状**: ログインができない
**レベル**: P2

```
対応手順:
1. Azure AD状態確認
   - Azure AD Health: https://status.azure.com/
   - Azure AD Sign-in ログ確認

2. 認証関連ログ確認
   # Application Insightsで認証エラーの確認
   AppRequests
   | where Url contains "/api/auth"
   | where ResultCode >= 400
   | project TimeGenerated, ResultCode, DurationMs
   | order by TimeGenerated desc

3. 対処:
   a. Azure AD障害の場合 → Azure状態ページ確認、復旧待ち、ユーザー通知
   b. トークン検証エラー → JWTシークレット確認、Key Vault確認
   c. CORS設定エラー → 環境変数CORS_ORIGINS確認
   d. セッションストア障害 → Redis接続確認
```

#### 5.1.3 パフォーマンス劣化

**症状**: API応答時間がSLA基準を超過
**レベル**: P2-P3

```
対応手順:
1. ボトルネック特定
   # Application Insightsでの分析
   AppRequests
   | where TimeGenerated > ago(30m)
   | where DurationMs > 200
   | summarize count(), avg(DurationMs), percentile(DurationMs, 95) by Name
   | order by avg_DurationMs desc

2. 依存関係の確認
   AppDependencies
   | where TimeGenerated > ago(30m)
   | summarize avg(DurationMs), count() by DependencyType
   | order by avg_DurationMs desc

3. 対処:
   a. DBスロークエリ → クエリ最適化、インデックス追加
   b. Redis応答遅延 → Redis状態確認、接続数確認
   c. リソース不足 → スケールアウト
   d. 外部依存遅延 → サーキットブレーカー確認、タイムアウト調整
```

### 5.2 インフラストラクチャ障害

#### 5.2.1 データベース障害

**症状**: PostgreSQL接続エラー
**レベル**: P1

```
対応手順:
1. DB状態確認
   az postgres flexible-server show \
     --name itscm-db-prod-eastjp \
     --resource-group rg-itscm-prod-eastjp \
     --query "{state:state,availabilityZone:availabilityZone}"

2. 接続テスト
   az containerapp exec \
     --name itscm-api-prod \
     --resource-group rg-itscm-prod-eastjp \
     --command "python -c \"import psycopg2; conn=psycopg2.connect('$DATABASE_URL'); print('OK')\""

3. 対処:
   a. DB停止 → Azure状態確認、Azureサポート起票
   b. 接続プール枯渇 → アプリ再起動、プールサイズ調整
      az containerapp revision restart \
        --name itscm-api-prod \
        --resource-group rg-itscm-prod-eastjp
   c. ディスク容量不足 → ストレージ拡張
   d. レプリケーション断 → レプリカ状態確認、再構築
```

#### 5.2.2 Redis障害

**症状**: Redisキャッシュ接続エラー
**レベル**: P2

```
対応手順:
1. Redis状態確認
   az redis show \
     --name itscm-redis-prod-eastjp \
     --resource-group rg-itscm-prod-eastjp \
     --query "{provisioningState:provisioningState,hostName:hostName}"

2. 対処:
   a. Redis停止 → Azureサポート確認
   b. メモリ不足 → エビクションポリシー確認、メモリ拡張
   c. 接続数超過 → 接続数設定確認、アプリ側の接続数削減
   d. 一時的な回避策: アプリケーション側でキャッシュバイパス
      → 環境変数 REDIS_ENABLED=false に設定
```

#### 5.2.3 Azure Front Door障害

**症状**: フロントドアの応答異常
**レベル**: P1-P2

```
対応手順:
1. Front Door状態確認
   az network front-door show \
     --name itscm-frontdoor \
     --resource-group rg-itscm-global \
     --query "frontendEndpoints[].{name:name,enabled:enabledState}"

2. バックエンドヘルス確認
   az network front-door backend-pool backend list \
     --front-door-name itscm-frontdoor \
     --resource-group rg-itscm-global \
     --pool-name itscm-backend-pool

3. 対処:
   a. 全バックエンド異常 → 各リージョンの直接確認
   b. Front Door自体の障害 → Azure状態確認、DNSでの直接ルーティング
   c. WAFブロック → WAFログ確認、ルール調整
   d. 証明書エラー → 証明書状態確認、手動更新
```

### 5.3 ネットワーク障害

#### 5.3.1 リージョン間接続障害

**症状**: East-West Japan間の通信障害
**レベル**: P2

```
対応手順:
1. 各リージョンの単独疎通確認
   curl -sf https://eastjp.itscm.example.com/api/health
   curl -sf https://westjp.itscm.example.com/api/health

2. レプリケーション状態確認
   # DBレプリケーション
   az postgres flexible-server replica list ...
   # Redisレプリケーション
   az redis show ...

3. 対処:
   a. 片方のリージョン停止 → DR手順書に従いフェイルオーバー
   b. レプリケーション遅延 → 許容範囲内か判断、必要に応じてアラート更新
   c. VNet接続障害 → Azure Networkingチームと連携
```

### 5.4 Celery Worker障害

**症状**: バックグラウンドタスクが実行されない
**レベル**: P3

```
対応手順:
1. Worker状態確認
   az containerapp show \
     --name itscm-worker-prod \
     --resource-group rg-itscm-prod-eastjp \
     --query "properties.runningStatus"

2. キュー状態確認
   # Flower ダッシュボード確認
   https://flower.itscm.example.com

3. ログ確認
   az containerapp logs show \
     --name itscm-worker-prod \
     --resource-group rg-itscm-prod-eastjp \
     --tail 100

4. 対処:
   a. Worker停止 → 再起動
   b. キュー滞留 → Worker数の増加（スケールアウト）
   c. タスク失敗 → 失敗タスクのログ確認、リトライ
   d. Redis接続エラー → Redis接続確認（Brokerとして使用）
```

---

## 6. セキュリティインシデント対応

### 6.1 セキュリティインシデント分類

| 分類 | 例 | レベル |
|------|-----|--------|
| データ漏洩 | 個人情報・機密情報の外部流出 | P1 |
| 不正アクセス | 権限のないアクセス、アカウント乗っ取り | P1 |
| マルウェア感染 | コンテナへのマルウェア混入 | P1 |
| DDoS攻撃 | 大量トラフィックによるサービス妨害 | P1-P2 |
| 脆弱性悪用 | 既知/未知の脆弱性の悪用試行 | P1-P2 |
| 内部不正 | 内部者による不正操作 | P1 |

### 6.2 セキュリティインシデント対応フロー

```
検知 → 封じ込め → 根絶 → 復旧 → 事後対応

Phase 1: 検知・初期評価（0-15分）
  ├── インシデントの検知・報告
  ├── CISOへの即時報告
  ├── 影響範囲の初期評価
  └── セキュリティチーム召集

Phase 2: 封じ込め（15-60分）
  ├── 被害の拡大防止
  │    ├── 不正アクセス元のIPブロック
  │    ├── 侵害されたアカウントの無効化
  │    ├── 影響システムの隔離
  │    └── ネットワークセグメントの遮断
  └── エビデンスの保全

Phase 3: 根絶（1-24時間）
  ├── 侵入経路の特定・遮断
  ├── マルウェアの除去
  ├── 脆弱性の修正
  └── 認証情報の全更新

Phase 4: 復旧（根絶後）
  ├── システムの復旧
  ├── セキュリティ強化策の適用
  ├── 監視の強化
  └── サービス再開

Phase 5: 事後対応
  ├── インシデント報告書作成
  ├── 法的対応（情報漏洩の場合）
  ├── 関係機関への報告
  ├── 再発防止策の策定・実施
  └── セキュリティ監査
```

### 6.3 封じ込め手順

```bash
# 不正アクセス元IPのブロック（WAF）
az network front-door waf-policy managed-rule-override add \
  --policy-name itscm-waf-policy \
  --resource-group rg-itscm-global \
  --type Microsoft_DefaultRuleSet \
  --rule-group-id IPBlock \
  --rule-id custom-block-1 \
  --action Block

# 侵害アカウントの無効化
az ad user update \
  --id "{user-object-id}" \
  --account-enabled false

# 全セッションの無効化（Redis）
az containerapp exec \
  --name itscm-api-prod \
  --resource-group rg-itscm-prod-eastjp \
  --command "redis-cli -h $REDIS_HOST FLUSHDB"

# JWTシークレットの即時ローテーション
az keyvault secret set \
  --vault-name kv-itscm-prod-eastjp \
  --name "JWT-SECRET-KEY" \
  --value "$(openssl rand -base64 64)"
```

---

## 7. 障害報告・分析

### 7.1 インシデントレポート

全P1/P2インシデントについて、復旧後24時間以内にインシデントレポートを作成する。

```markdown
## インシデントレポート

### 基本情報
- インシデント番号: INC-YYYY-NNNN
- 発生日時: YYYY-MM-DD HH:MM
- 復旧日時: YYYY-MM-DD HH:MM
- 影響時間: XX分
- 障害レベル: P{レベル}

### 影響
- 影響サービス:
- 影響ユーザー数:
- SLAへの影響:

### タイムライン
| 時刻 | イベント | 担当 |
|------|---------|------|
| | | |

### 原因
（原因の詳細）

### 対応内容
（実施した対応の詳細）

### 暫定対策
（実施した暫定対策）

### 恒久対策
| 対策 | 担当 | 期限 | ステータス |
|------|------|------|----------|
| | | | |
```

### 7.2 ポストモーテム

全P1/P2インシデントについて、復旧後5営業日以内にポストモーテムを実施する。

**参加者**: インシデント対応メンバー全員 + 運用マネージャー + 関連チームリーダー

**議題**:
1. タイムラインのレビュー
2. 根本原因分析（5 Whys / Fishbone Diagram）
3. 対応の振り返り（良かった点、改善点）
4. 再発防止策の策定
5. アクションアイテムの確認

### 7.3 障害管理KPI

| KPI | 目標値 | 測定方法 |
|-----|--------|---------|
| MTBF（平均故障間隔） | > 720時間 | インシデント間の平均時間 |
| MTTR（平均復旧時間） | P1: < 1時間, P2: < 4時間 | 検知から復旧までの平均時間 |
| 検知時間 | < 5分 | 障害発生から検知までの時間 |
| インシデント数 | P1: 0件/月, P2: < 2件/月 | 月間インシデント件数 |
| 再発率 | < 5% | 同一原因のインシデント再発率 |
| エスカレーション適切率 | > 95% | 適切にエスカレーションされた割合 |

---

## 関連文書

| 文書番号 | 文書名 |
|---------|--------|
| ITSCM-OP-001 | 運用手順書 |
| ITSCM-OP-002 | 監視設計書 |
| ITSCM-OP-004 | バックアップリストア手順書 |
| ITSCM-OP-005 | DR手順書 |
| ITSCM-RM-003 | ロールバック手順書 |

---

以上
