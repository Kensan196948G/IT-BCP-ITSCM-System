# IT-BCP-ITSCM-System

## IT事業継続管理システム（BCP/ITSCM統合プラットフォーム）

災害・サイバー攻撃時のIT復旧計画・BCP訓練・RTOダッシュボードを統合管理するプラットフォームです。

---

## 概要

| 項目 | 内容 |
|------|------|
| **プロジェクト名** | IT-BCP-ITSCM-System |
| **対象組織** | みらい建設工業 IT部門 |
| **準拠規格** | ISO20000 ITSCM / ISO27001 A.5.29・A.5.30 / NIST CSF RECOVER RC |
| **優先度** | 中 |

## 主要機能

### BCP/ITSCM計画管理
- IT復旧計画文書管理・バージョン管理
- システム別RTO/RPO目標値の管理・可視化
- 代替手段（フォールバック）管理
- 緊急連絡網・エスカレーション管理

### BCP訓練管理
- 訓練シナリオ管理
- テーブルトップ（机上）演習支援ツール
- 訓練結果記録・RTO達成状況トラッキング
- 訓練レポート自動生成

### インシデント対応（実災害時）
- 緊急対応指揮支援
- RTOダッシュボード（リアルタイム復旧状況表示）
- タスク割当・進捗管理
- 状況報告自動化

### ダッシュボード・レポート
- BCPレディネスダッシュボード
- RTO/RPOコンプライアンスレポート
- ISO20000 ITSCM準拠レポート

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | Next.js 14 / TypeScript / PWA対応 |
| バックエンド | Python FastAPI |
| データベース | PostgreSQL 16（Geo冗長） |
| キャッシュ | Redis 7 Cluster |
| タスクキュー | Celery |
| インフラ | Azure Container Apps（マルチリージョン） |
| CDN/LB | Azure Front Door |
| CI/CD | GitHub Actions |

## アーキテクチャ

```
[ユーザ] → [Azure Front Door] → [East Japan: Primary]
                                   ↕ レプリケーション
                                [West Japan: Standby]

フェイルオーバー: 最大90秒（RTO 15分要件を達成）
```

## ディレクトリ構成

```
IT-BCP-ITSCM-System/
├── docs/                    # プロジェクトドキュメント
│   ├── 01_計画管理/          # プロジェクト計画・ロードマップ
│   ├── 02_要件定義/          # 要件定義・BIA
│   ├── 03_設計/             # アーキテクチャ・DB・API設計
│   ├── 04_開発ガイド/        # 開発環境・コーディング規約
│   ├── 05_テスト/           # テスト計画・テストケース
│   ├── 06_リリース管理/      # リリース手順・変更管理
│   ├── 07_運用管理/          # 運用手順・監視・DR
│   └── 08_コンプライアンス/   # ISO/NIST準拠対応表
├── backend/                 # Python FastAPI バックエンド
├── frontend/                # Next.js 14 フロントエンド
├── infrastructure/          # Terraform / Docker
├── scripts/                 # ClaudeOS自動化スクリプト
└── .github/workflows/       # GitHub Actions CI/CD
```

## 開発環境

### 必要ソフトウェア
- Node.js 20.x
- Python 3.12
- PostgreSQL 16
- Redis 7
- Docker / Docker Compose

### セットアップ

```bash
# リポジトリクローン
git clone https://github.com/Kensan196948G/IT-BCP-ITSCM-System.git
cd IT-BCP-ITSCM-System

# 詳細な手順は docs/04_開発ガイド(Development-Guide)/ を参照
```

## ライセンス

MIT License

## 開発体制

ClaudeOS v4 Auto Development Pipeline による自律開発
