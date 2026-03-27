<p align="center">
  <h1 align="center">🛡️ IT-BCP-ITSCM-System</h1>
  <p align="center">
    <strong>IT事業継続管理システム（BCP/ITSCM統合プラットフォーム）</strong>
  </p>
  <p align="center">
    災害・サイバー攻撃時のIT復旧計画・BCP訓練・RTOダッシュボード統合プラットフォーム
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ISO20000-ITSCM-blue?style=flat-square" alt="ISO20000">
  <img src="https://img.shields.io/badge/ISO27001-A.5.29%2FA.5.30-green?style=flat-square" alt="ISO27001">
  <img src="https://img.shields.io/badge/NIST_CSF-RECOVER_RC-orange?style=flat-square" alt="NIST CSF">
  <img src="https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Azure-Container_Apps-0078D4?style=flat-square&logo=microsoftazure" alt="Azure">
  <img src="https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=github-actions" alt="CI">
</p>

---

## 📋 プロジェクト概要

| 項目 | 内容 |
|:-----|:-----|
| 🏢 **対象組織** | みらい建設工業 IT部門 |
| 📦 **リポジトリ** | `Kensan196948G/IT-BCP-ITSCM-System` |
| 📜 **準拠規格** | ISO20000 ITSCM / ISO27001 A.5.29・A.5.30 / NIST CSF 2.0 RECOVER RC |
| 🟡 **優先度** | 中 |
| 🤖 **開発方式** | ClaudeOS v4 Auto Development Pipeline |

---

## 🏗️ システムアーキテクチャ

```mermaid
graph TB
    subgraph Users["👤 ユーザー"]
        PC["🖥️ デスクトップ"]
        Mobile["📱 モバイル（PWA）"]
    end

    subgraph Azure["☁️ Azure Cloud"]
        FD["🌐 Azure Front Door<br/>CDN + WAF + LB"]

        subgraph East["🗾 East Japan（Primary）"]
            CA_E["📦 Container Apps x3"]
            PG_E["🐘 PostgreSQL Primary"]
            RD_E["⚡ Redis Primary"]
        end

        subgraph West["🗾 West Japan（Standby）"]
            CA_W["📦 Container Apps x2"]
            PG_W["🐘 PostgreSQL Replica"]
            RD_W["⚡ Redis Replica"]
        end
    end

    subgraph External["🔗 外部連携"]
        Teams["💬 Microsoft Teams"]
        SMS["📨 SMS Gateway"]
        ITSM["🎫 ITSM-System"]
    end

    PC --> FD
    Mobile --> FD
    FD --> CA_E
    FD -.-> CA_W
    CA_E --> PG_E
    CA_E --> RD_E
    PG_E <-..-> PG_W
    RD_E <-..-> RD_W
    CA_E --> Teams
    CA_E --> SMS
    CA_E --> ITSM

    style East fill:#dbeafe,stroke:#3b82f6
    style West fill:#fef3c7,stroke:#f59e0b
    style FD fill:#e0f2fe,stroke:#0284c7
```

### ⚡ フェイルオーバー性能

| 指標 | 目標値 | 設計値 |
|:-----|:------:|:------:|
| 🔄 フェイルオーバー時間 | 15分以内 | **90秒以内** |
| 🔍 障害検知 | - | 30秒 |
| 🌐 DNS切替 | - | 60秒 |
| 💾 データ同期遅延 | 5分以内 | **5秒以内** |
| 📶 オフライン動作 | 必須 | PWA対応 |

---

## ✨ 主要機能

### 📋 BCP/ITSCM計画管理
| 機能 | 説明 | 要件ID |
|:-----|:-----|:------:|
| 📄 IT復旧計画文書管理 | シナリオ別復旧手順書の管理・バージョン管理 | PLAN-001 |
| ⏱️ RTO/RPO管理 | システム別目標復旧時間の管理・可視化 | PLAN-002 |
| 🔄 代替手段管理 | フォールバック手段の登録・管理 | PLAN-003 |
| 📞 緊急連絡網管理 | エスカレーション経路の管理 | PLAN-004 |
| 📊 優先復旧順序管理 | BIAに基づく復旧優先順位 | PLAN-005 |
| 🏢 ベンダー連絡先管理 | IT関連ベンダーの緊急連絡先・SLA情報 | PLAN-006 |

### 🏋️ BCP訓練管理
| 機能 | 説明 | 要件ID |
|:-----|:-----|:------:|
| 🎬 訓練シナリオ管理 | 年次BCP訓練シナリオの作成・管理 | TRN-001 |
| 🗣️ テーブルトップ演習 | シナリオベースの机上演習ツール | TRN-002 |
| 📝 訓練結果記録 | 実施結果・課題・改善事項の記録 | TRN-003 |
| ⏱️ タイムトラッキング | RTO達成状況のリアルタイム記録 | TRN-004 |

### 🚨 インシデント対応（実災害時）
| 機能 | 説明 | 要件ID |
|:-----|:-----|:------:|
| 🎯 緊急対応指揮支援 | 対応状況管理・指揮系統支援 | INC-001 |
| 📊 RTOダッシュボード | 復旧状況のリアルタイム表示 | INC-002 |
| ✅ タスク割当・進捗管理 | 復旧作業のタスク追跡 | INC-003 |
| 📨 状況報告自動化 | 経営層への定期状況報告 | INC-004 |

### 📈 ダッシュボード
| 機能 | 説明 | 要件ID |
|:-----|:-----|:------:|
| 🎯 BCPレディネス | BCP準備状況の総合スコア | RPT-001 |
| 📊 RTO/RPOコンプライアンス | 目標値vs実績値の比較 | RPT-002 |
| 📈 訓練履歴・改善トレンド | 経年変化・改善状況 | RPT-003 |
| 📋 ISO20000準拠レポート | ITSCM要件準拠状況 | RPT-004 |

---

## 🛠️ 技術スタック

| レイヤー | 技術 | バージョン |
|:---------|:-----|:----------|
| 🖥️ フロントエンド | Next.js / TypeScript / Tailwind CSS | 14.x |
| ⚡ バックエンド | Python FastAPI | 0.115.x |
| 🐘 データベース | PostgreSQL（Geo冗長） | 16 |
| ⚡ キャッシュ | Redis Cluster | 7 |
| 📦 タスクキュー | Celery | 5.4 |
| ☁️ インフラ | Azure Container Apps（マルチリージョン） | - |
| 🌐 CDN/LB | Azure Front Door Premium | - |
| 🔧 IaC | Terraform | - |
| 🔄 CI/CD | GitHub Actions | - |
| 📱 PWA | Service Worker + IndexedDB | - |

---

## 📊 対象システムRTO/RPO定義

| システム | RTO目標 | RPO目標 | 重要度 | ステータス |
|:---------|:-------:|:-------:|:------:|:----------:|
| 🔐 Active Directory | 4時間 | 1時間 | 🔴 最高 | 🟢 定義済 |
| ☁️ Entra ID / M365 | SLA依存 | SLA依存 | 🔴 最高 | 🟢 定義済 |
| 📧 Exchange Online | SLA依存 | SLA依存 | 🟠 高 | 🟢 定義済 |
| 📁 ファイルサーバ | 8時間 | 24時間 | 🟠 高 | 🟢 定義済 |
| 📋 DeskNet's Neo | 24時間 | 24時間 | 🟡 中 | 🟢 定義済 |
| 📊 AppSuite | 48時間 | 24時間 | 🟡 中 | 🟢 定義済 |
| 🎫 ITSM-System | 8時間 | 4時間 | 🟠 高 | 🟢 定義済 |
| 🔍 SIEM Platform | 8時間 | 4時間 | 🟠 高 | 🟢 定義済 |

---

## 🚀 開発ロードマップ

```mermaid
gantt
    title IT-BCP-ITSCM-System 開発ロードマップ
    dateFormat  YYYY-MM-DD
    axisFormat  %m/%d

    section Phase 1: 基盤構築
    環境構築・認証基盤         :done, p1a, 2026-03-27, 2d
    バックエンドAPI基盤        :done, p1b, 2026-03-27, 1d
    フロントエンド基盤         :done, p1c, 2026-03-27, 1d
    DB設計・マイグレーション    :done, p1d, 2026-03-27, 1d
    API接続・動的表示          :done, p1e, 2026-03-27, 1d
    セキュリティ強化           :done, p1f, 2026-03-27, 1d
    Docker環境                :done, p1g, 2026-03-27, 1d

    section Phase 2: コア機能
    BCP計画管理               :p2a, after p1d, 21d
    RTO/RPO管理               :p2b, after p1d, 14d
    訓練管理                  :p2c, after p2a, 14d

    section Phase 3: 高度機能
    WebSocket RTOダッシュボード :done, p3a, 2026-03-27, 1d
    PWAオフライン(IndexedDB)   :done, p3b, 2026-03-27, 1d
    通知連携(Teams/Email)      :done, p3c, 2026-03-27, 1d

    section Phase 4: DR・本番
    Terraform マルチリージョン  :done, p4a, 2026-03-27, 1d
    デプロイWF+監視基盤        :done, p4b, 2026-03-27, 1d
    運用ランブック+E2Eテスト    :done, p4c, 2026-03-27, 1d
    JWT認証+監査ログ           :done, p4d, 2026-03-27, 1d
```

### 📌 フェーズ進捗

| フェーズ | 期間 | 進捗 | ステータス |
|:---------|:-----|:----:|:----------:|
| 🏗️ Phase 1: 基盤構築 | 2ヶ月 | ██████████ 100% | ✅ 完了 |
| ⚙️ Phase 2: コア機能 | 3ヶ月 | ██████████ 100% | ✅ 完了 |
| 🚀 Phase 3: 高度機能 | 2ヶ月 | ██████████ 100% | ✅ 完了 |
| 🌐 Phase 4: DR・本番 | 1ヶ月 | ██████████ 100% | ✅ 完了 |

---

## 📂 ディレクトリ構成

```
IT-BCP-ITSCM-System/
├── 📁 docs/                          # プロジェクトドキュメント（46ファイル）
│   ├── 01_計画管理(Planning)/         # プロジェクト計画・ロードマップ（8件）
│   ├── 02_要件定義(Requirements)/     # 要件定義・BIA（5件）
│   ├── 03_設計(Design)/              # アーキテクチャ・DB・API設計（8件）
│   ├── 04_開発ガイド(Development)/    # 環境構築・コーディング規約（4件）
│   ├── 05_テスト(Testing)/           # テスト計画・テストケース（5件）
│   ├── 06_リリース管理(Release)/      # リリース手順・変更管理（6件）
│   ├── 07_運用管理(Operations)/       # 運用手順・監視・DR（5件）
│   └── 08_コンプライアンス(Compliance)/ # ISO/NIST準拠対応表（4件）
├── 📁 backend/                        # Python FastAPI バックエンド
│   ├── apps/                          # アプリケーションモジュール
│   │   ├── models.py                  # SQLAlchemy モデル（3テーブル）
│   │   ├── schemas.py                 # Pydantic スキーマ（バリデーション強化）
│   │   ├── crud.py                    # CRUD操作（ページネーション対応）
│   │   ├── rto_tracker.py             # RTOトラッカー（5ステータス判定）
│   │   └── routers/                   # APIルーター（4ルーター）
│   ├── alembic/                       # DBマイグレーション
│   ├── scripts/                       # シードデータ投入
│   ├── tests/                         # テスト（61件）
│   ├── main.py                        # FastAPI + セキュリティミドルウェア
│   ├── config.py                      # 環境設定
│   ├── database.py                    # DB接続（AsyncSession）
│   └── Dockerfile                     # コンテナビルド
├── 📁 frontend/                       # Next.js 14 フロントエンド
│   ├── app/                           # App Router ページ（7ページ）
│   │   ├── page.tsx                   # ダッシュボード
│   │   ├── plans/                     # BCP計画管理
│   │   ├── exercises/                 # 訓練管理
│   │   ├── incidents/                 # インシデント管理
│   │   ├── rto-monitor/               # RTOモニタリング
│   │   └── components/                # 共通コンポーネント
│   ├── lib/                           # API接続・型定義・フック
│   ├── public/                        # PWA（manifest.json + sw.js）
│   └── Dockerfile                     # コンテナビルド
├── 📁 infrastructure/                 # Terraform IaC
│   └── terraform/                     # Azure マルチリージョン構成
│       ├── main.tf                    # Front Door + East/West Japan
│       └── modules/region/            # リージョンモジュール
├── 📁 scripts/                        # ClaudeOS自動化スクリプト
│   ├── project-sync.sh                # GitHub Project状態同期
│   ├── create-issue.sh                # Issue自動生成
│   └── create-pr.sh                   # PR自動生成
└── 📁 .github/workflows/             # GitHub Actions CI/CD
    └── claudeos-ci.yml                # lint → test → build パイプライン
```

---

## 🔄 CI/CD パイプライン

```mermaid
graph LR
    A["📝 Push/PR"] --> B["🔍 Lint"]
    B --> C["🧪 Test"]
    C --> D["🏗️ Build"]
    D --> E{"✅ STABLE?"}
    E -->|Yes| F["🚀 Deploy"]
    E -->|No| G["🔧 Auto Repair"]
    G --> A

    style A fill:#e0f2fe
    style B fill:#fef3c7
    style C fill:#fef3c7
    style D fill:#fef3c7
    style E fill:#dbeafe
    style F fill:#dcfce7
    style G fill:#fee2e2
```

| ステージ | ツール | 内容 |
|:---------|:-------|:-----|
| 🔍 Lint | ESLint + flake8 + black | コード品質チェック |
| 🧪 Test | pytest + Jest | ユニット・結合テスト |
| 🏗️ Build | next build | フロントエンドビルド |
| ✅ STABLE | ClaudeOS判定 | N回連続CI成功で判定 |

---

## ⚙️ 開発環境セットアップ

### 必要ソフトウェア

| ソフトウェア | バージョン | 用途 |
|:------------|:----------|:-----|
| 🟩 Node.js | 20.x | フロントエンド |
| 🐍 Python | 3.12 | バックエンド |
| 🐘 PostgreSQL | 16 | データベース |
| ⚡ Redis | 7 | キャッシュ |
| 🐳 Docker | latest | コンテナ |

### クイックスタート

```bash
# リポジトリクローン
git clone https://github.com/Kensan196948G/IT-BCP-ITSCM-System.git
cd IT-BCP-ITSCM-System

# バックエンド
cd backend && pip install -r requirements.txt
uvicorn main:app --reload

# フロントエンド
cd frontend && npm install
npm run dev
```

> 📖 詳細な手順は [開発環境構築手順](docs/04_開発ガイド(Development-Guide)/01_開発環境構築手順(Development-Setup).md) を参照してください。

---

## 📜 準拠規格

| 規格 | 対象条項 | 準拠状況 |
|:-----|:---------|:--------:|
| 📘 **ISO20000-1:2018** | ITサービス継続管理 8.7 | 🟢 対応済 |
| 📗 **ISO27001:2022** | A.5.29 事業継続 / A.5.30 ICT継続 | 🟢 対応済 |
| 📙 **NIST CSF 2.0** | RECOVER RC（復旧計画・改善） | 🟢 対応済 |
| 📕 **ITIL v4** | ITサービス継続管理 | 🟢 対応済 |

---

## 📊 GitHub Project

🔗 [IT-BCP-ITSCM-System Project Board](https://github.com/users/Kensan196948G/projects/13)

### ステータスフロー

```mermaid
graph LR
    A["📥 Inbox"] --> B["📋 Backlog"]
    B --> C["✅ Ready"]
    C --> D["🎨 Design"]
    D --> E["💻 Development"]
    E --> F["🧪 Verify"]
    F --> G["🚀 Deploy Gate"]
    G --> H["✅ Done"]
    E -.-> I["🚫 Blocked"]
    I -.-> E

    style A fill:#f3f4f6
    style B fill:#f3f4f6
    style C fill:#dbeafe
    style D fill:#e9d5ff
    style E fill:#fed7aa
    style F fill:#fef08a
    style G fill:#bbf7d0
    style H fill:#bbf7d0
    style I fill:#fecaca
```

---

## 📄 ライセンス

MIT License

---

## 🤖 開発体制

**ClaudeOS v4 Auto Development Pipeline** による自律開発

| ループ | 間隔 | 役割 |
|:-------|:----:|:-----|
| 🔍 Monitor | 1h | Projects/Issues/PR/Actions状態監視 |
| 💻 Development | 2h | 設計・実装タスク実行 |
| 🧪 Verify | 2h | テスト/CI/STABLE判定 |
| 🔧 Improvement | 3h | 品質・アーキテクチャ改善 |

---

<p align="center">
  <sub>Built with ❤️ by ClaudeOS v4 Auto Development Pipeline</sub>
</p>
