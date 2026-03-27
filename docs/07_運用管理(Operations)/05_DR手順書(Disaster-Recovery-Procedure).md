# DR手順書（Disaster Recovery Procedure）
## IT事業継続管理システム（IT-BCP-ITSCM-System）

| 項目 | 内容 |
|------|------|
| **文書番号** | OPS-005 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-27 |
| **最終更新日** | 2026-03-27 |
| **作成者** | ClaudeOS Auto Dev |
| **承認者** | IT部門長 |

---

## 1. 目的

本ドキュメントは、IT事業継続管理システム自体のDR（災害復旧）手順を定義する。マルチリージョン構成（East Japan Primary / West Japan Standby）におけるフェイルオーバー・フェイルバック手順を明確化し、システムRTO 15分以内を確実に達成する。

---

## 2. DR構成概要

### 2.1 アーキテクチャ

```
[ユーザ] → [Azure Front Door (グローバル)]
               │
         ┌─────┴─────┐
         ▼           ▼
  [East Japan]  [West Japan]
   Primary       Standby
   Active        Hot Standby
```

### 2.2 リージョン構成

| コンポーネント | East Japan（Primary） | West Japan（Standby） |
|--------------|---------------------|---------------------|
| Container Apps | 3レプリカ（Active） | 2レプリカ（Hot Standby） |
| PostgreSQL | Primary（読み書き） | Read Replica（読み取り専用） |
| Redis | Primary Cluster | Replica Cluster |
| Blob Storage | プライマリ | GRS（Geo冗長） |

### 2.3 RTO/RPO目標

| 項目 | 目標値 |
|------|--------|
| **RTO（本システム）** | 15分以内 |
| **RPO（本システム）** | 5分以内 |
| **フェイルオーバー時間** | 90秒以内 |
| **データ同期遅延** | 最大5秒 |

---

## 3. フェイルオーバー手順

### 3.1 自動フェイルオーバー

Azure Front Door による自動フェイルオーバーが標準動作。

#### 検知〜切替フロー

```
1. Health Probe失敗検知     （0〜30秒）
2. Front Door判定            （30秒）
3. DNS切替実行               （30秒）
4. West Japanへトラフィック転送  （即時）
─────────────────────────────────
合計: 最大90秒
```

#### 自動フェイルオーバー条件

| 条件 | 閾値 |
|------|------|
| Health Probe連続失敗 | 3回（30秒間隔） |
| レスポンスタイムアウト | 10秒 |
| HTTP エラー率 | 50%以上（1分間） |

### 3.2 手動フェイルオーバー手順

自動フェイルオーバーが機能しない場合、または計画的なフェイルオーバーの場合。

#### Step 1: 状況確認

```bash
# East Japan の状態確認
az containerapp show --name bcp-east-app \
  --resource-group bcp-east-rg \
  --query "properties.runningStatus"

# PostgreSQL レプリケーション状態確認
az postgres flexible-server show --name bcp-east-pg \
  --resource-group bcp-east-rg \
  --query "replicationRole"

# Front Door の正常性確認
az afd endpoint show --endpoint-name bcp-endpoint \
  --profile-name bcp-frontdoor \
  --resource-group bcp-global-rg
```

#### Step 2: West Japan の昇格準備

```bash
# PostgreSQL: Read ReplicaをPrimaryに昇格
az postgres flexible-server replica stop-replication \
  --name bcp-west-pg \
  --resource-group bcp-west-rg

# Redis: Replicaの昇格確認
az redis update --name bcp-west-redis \
  --resource-group bcp-west-rg \
  --set replicasPerMaster=0
```

#### Step 3: Front Door ルーティング変更

```bash
# East Japan のオリジンを無効化
az afd origin update --origin-name east-origin \
  --origin-group-name bcp-origins \
  --profile-name bcp-frontdoor \
  --resource-group bcp-global-rg \
  --enabled-state Disabled

# West Japan のオリジンを優先に設定
az afd origin update --origin-name west-origin \
  --origin-group-name bcp-origins \
  --profile-name bcp-frontdoor \
  --resource-group bcp-global-rg \
  --priority 1 \
  --weight 1000
```

#### Step 4: 動作確認

```bash
# エンドポイント疎通確認
curl -s -o /dev/null -w "%{http_code}" https://bcp.example.com/api/health

# データ整合性確認
curl -s https://bcp.example.com/api/health/db

# WebSocket接続確認
wscat -c wss://bcp.example.com/ws/rto-dashboard
```

#### Step 5: 通知

```bash
# 関係者への通知
./scripts/notify-dr-event.sh "FAILOVER_COMPLETE" "West Japan now serving as Primary"
```

---

## 4. フェイルバック手順

### 4.1 前提条件

- East Japan リージョンが完全に復旧済み
- ネットワーク接続が安定（30分以上の無障害確認）
- データ同期が完了

### 4.2 手順

#### Step 1: East Japan 復旧確認

```bash
# インフラ状態確認
az containerapp show --name bcp-east-app \
  --resource-group bcp-east-rg

# ネットワーク接続テスト
az network watcher test-ip-flow --direction Inbound \
  --resource-group bcp-east-rg \
  --vm bcp-east-jumpbox \
  --protocol TCP --local 10.0.0.4:443 --remote 0.0.0.0:0
```

#### Step 2: データ再同期

```bash
# PostgreSQL: West Japan → East Japan のレプリケーション設定
az postgres flexible-server replica create \
  --source-server bcp-west-pg \
  --replica-name bcp-east-pg \
  --resource-group bcp-east-rg \
  --location japaneast

# レプリケーション遅延確認（0に近づくまで待機）
az postgres flexible-server show --name bcp-east-pg \
  --resource-group bcp-east-rg \
  --query "replicationRole"
```

#### Step 3: 段階的トラフィック切り戻し

```bash
# Phase 1: 10%のトラフィックをEast Japanへ
az afd origin update --origin-name east-origin \
  --origin-group-name bcp-origins \
  --profile-name bcp-frontdoor \
  --resource-group bcp-global-rg \
  --enabled-state Enabled \
  --weight 100

# 15分間の監視（エラー率確認）
sleep 900

# Phase 2: 50%のトラフィックをEast Japanへ
az afd origin update --origin-name east-origin \
  --origin-group-name bcp-origins \
  --profile-name bcp-frontdoor \
  --resource-group bcp-global-rg \
  --weight 500

# 15分間の監視
sleep 900

# Phase 3: East Japanをプライマリに復帰
az afd origin update --origin-name east-origin \
  --origin-group-name bcp-origins \
  --profile-name bcp-frontdoor \
  --resource-group bcp-global-rg \
  --priority 1 \
  --weight 1000

az afd origin update --origin-name west-origin \
  --origin-group-name bcp-origins \
  --profile-name bcp-frontdoor \
  --resource-group bcp-global-rg \
  --priority 2 \
  --weight 1
```

#### Step 4: PostgreSQL ロール復帰

```bash
# East Japan を Primary に昇格
az postgres flexible-server replica stop-replication \
  --name bcp-east-pg \
  --resource-group bcp-east-rg

# West Japan を Read Replica に戻す
az postgres flexible-server replica create \
  --source-server bcp-east-pg \
  --replica-name bcp-west-pg \
  --resource-group bcp-west-rg \
  --location japanwest
```

#### Step 5: 完了確認・通知

```bash
# フェイルバック完了通知
./scripts/notify-dr-event.sh "FAILBACK_COMPLETE" "East Japan restored as Primary"
```

---

## 5. DR訓練計画

### 5.1 訓練スケジュール

| 訓練種別 | 頻度 | 内容 |
|---------|------|------|
| テーブルトップ演習 | 四半期 | DR手順の机上確認・ロールプレイ |
| 部分フェイルオーバー | 半年 | 非業務時間のフェイルオーバーテスト |
| 完全DR訓練 | 年1回 | 完全フェイルオーバー＋フェイルバック |
| オフライン動作テスト | 四半期 | PWAオフライン動作確認 |

### 5.2 訓練実施手順

1. **事前準備**: 訓練計画書作成、関係者通知（2週間前）
2. **実施**: フェイルオーバー実行、RTO計測、動作確認
3. **記録**: 実施結果、RTO達成状況、発見課題
4. **改善**: 課題の改善アクション策定、手順書更新

### 5.3 訓練判定基準

| 判定項目 | 合格基準 |
|---------|---------|
| フェイルオーバー完了時間 | 90秒以内 |
| システム復旧時間 | 15分以内 |
| データ損失 | RPO 5分以内 |
| 全機能動作確認 | 100%正常 |
| オフライン動作 | 重要資料参照可能 |

---

## 6. 連絡体制

### 6.1 DR発動時の連絡フロー

```
障害検知
  ↓
自動通知（Azure Monitor → Teams/Email）
  ↓
IT部門長 判断
  ↓
DR発動宣言
  ↓
関係者一斉通知
  ├── 対応チーム（即時）
  ├── 経営層（5分以内）
  └── 利用部門（15分以内）
```

### 6.2 緊急連絡先

| 役割 | 連絡先 | 手段 |
|------|--------|------|
| IT部門長 | （社内連絡網参照） | 電話 / Teams |
| インフラ担当 | （社内連絡網参照） | 電話 / Teams |
| Azure サポート | Premier Support | Azure Portal |
| ネットワーク保守 | （契約先連絡網参照） | 電話 |

---

## 7. 事後対応

### 7.1 インシデントレビュー

DR発動後、72時間以内に以下を実施：

1. **タイムライン作成**: 障害検知〜復旧完了の時系列整理
2. **RTO/RPO評価**: 目標値との比較・達成状況
3. **根本原因分析**: 5 Why分析、原因の特定
4. **改善策策定**: 再発防止策、手順改善点
5. **報告書作成**: 経営層向け報告書

### 7.2 手順書更新

インシデントレビュー結果に基づき、本手順書を更新する。

---

## 更新履歴

| 日付 | バージョン | 変更内容 | 更新者 |
|------|-----------|---------|--------|
| 2026-03-27 | 1.0.0 | 初版作成 | ClaudeOS Auto Dev |

---

*本文書はバージョン管理対象です。DR訓練実施後は必ず見直しを行ってください。*
