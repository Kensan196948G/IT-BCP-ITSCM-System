# テスト計画書 (Test Plan)

| 項目 | 内容 |
|------|------|
| 文書番号 | TEST-PLAN-001 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 作成者 | IT-BCP-ITSCM開発チーム |
| 分類 | テスト |
| 対象システム | IT事業継続管理システム (IT-BCP-ITSCM-System) |

---

## 1. 概要

### 1.1 目的

本文書は、IT事業継続管理システム（IT-BCP-ITSCM-System）のテスト計画を定義する。本システムは災害・サイバー攻撃時のIT復旧計画、BCP訓練管理、RTOダッシュボードを統合したプラットフォームであり、高い信頼性・可用性が求められる。テスト計画は、システムが要求仕様を満たし、安全かつ安定的に動作することを検証するための戦略・手順・基準を網羅する。

### 1.2 対象システム

| 項目 | 内容 |
|------|------|
| システム名 | IT事業継続管理システム (IT-BCP-ITSCM-System) |
| フロントエンド | Next.js 14 / TypeScript / PWA |
| バックエンド | Python FastAPI / PostgreSQL 16 / Redis 7 / Celery 5 |
| インフラ | Azure Container Apps マルチリージョン（東日本 + 西日本） |
| 準拠規格 | ISO 20000, ISO 27001, NIST CSF |

### 1.3 テスト範囲

| 機能カテゴリ | サブ機能 | テスト対象 |
|------------|---------|-----------|
| BCP計画管理 | CRUD、バージョン管理、承認ワークフロー、PDF出力 | バックエンド + フロントエンド |
| 訓練管理 | スケジュール、実行、評価、レポート | バックエンド + フロントエンド |
| インシデント対応 | 検知、エスカレーション、対応記録、事後分析 | バックエンド + フロントエンド |
| BIA（ビジネスインパクト分析） | 資産登録、影響度評価、依存関係マッピング | バックエンド + フロントエンド |
| RTOダッシュボード | リアルタイム監視、RTO/RPOトラッキング、アラート | バックエンド + WebSocket + フロントエンド |
| 認証・認可 | Azure AD SSO、RBAC、JWT管理 | バックエンド + フロントエンド |
| 通知 | メール、Slack、SMS、Teams | バックエンド（Celery） |
| PWA / オフライン | Service Worker、IndexedDB、同期 | フロントエンド |
| DR（災害復旧） | フェイルオーバー、マルチリージョン | インフラ |

### 1.4 テスト範囲外

- 外部サービス（Azure AD、Slack、Teams）の内部動作テスト
- ハードウェアレベルのインフラテスト
- Azure プラットフォーム自体の可用性テスト

---

## 2. テスト戦略

### 2.1 テストピラミッド

```
        /\
       /  \        E2E テスト（10%）
      /    \       UI操作、シナリオベース
     /------\
    /        \     結合テスト（20%）
   /          \    API、サービス間連携
  /------------\
 /              \  ユニットテスト（70%）
/________________\ 関数、クラス、モジュール単位
```

### 2.2 テストレベル定義

#### 2.2.1 ユニットテスト

| 項目 | 内容 |
|------|------|
| 目的 | 個々の関数・メソッド・コンポーネントの正確性を検証 |
| 対象 | サービス層、リポジトリ層、ユーティリティ、React コンポーネント |
| ツール（バックエンド） | pytest, pytest-asyncio, pytest-cov, factory-boy |
| ツール（フロントエンド） | Jest, React Testing Library |
| カバレッジ目標 | バックエンド: 80%以上、フロントエンド: 75%以上 |
| 実行タイミング | コミット時、PR 作成時（CI） |
| 担当 | 開発者 |

#### 2.2.2 結合テスト

| 項目 | 内容 |
|------|------|
| 目的 | コンポーネント間の連携が正しく機能することを検証 |
| 対象 | API エンドポイント、DB アクセス、Redis キャッシュ、Celery タスク |
| ツール | pytest（テスト用DB）, httpx（AsyncClient） |
| 実行タイミング | PR 作成時（CI） |
| 担当 | 開発者 + QA |

#### 2.2.3 E2E テスト

| 項目 | 内容 |
|------|------|
| 目的 | ユーザーシナリオに基づいたシステム全体の動作を検証 |
| 対象 | BCP計画の作成から承認まで、訓練の計画から評価まで等 |
| ツール | Playwright |
| 実行タイミング | develop マージ時（CI）、リリース前 |
| 担当 | QA チーム |

#### 2.2.4 性能テスト

| 項目 | 内容 |
|------|------|
| 目的 | 負荷条件下でのシステム応答性能・安定性を検証 |
| 対象 | API レスポンスタイム、同時接続数、WebSocket 性能 |
| ツール | k6, Locust |
| 実行タイミング | リリース前、月次 |
| 担当 | インフラチーム + QA |

#### 2.2.5 セキュリティテスト

| 項目 | 内容 |
|------|------|
| 目的 | セキュリティ脆弱性の検出と対策の検証 |
| 対象 | OWASP Top 10、認証・認可、暗号化、入力検証 |
| ツール | OWASP ZAP, Bandit, Trivy, CodeQL |
| 実行タイミング | PR 時（SAST）、リリース前（DAST）、四半期（ペネトレーション） |
| 担当 | セキュリティチーム + 外部ベンダー |

#### 2.2.6 DR テスト

| 項目 | 内容 |
|------|------|
| 目的 | 災害復旧手順の有効性と RTO/RPO の達成を検証 |
| 対象 | リージョン間フェイルオーバー、データ復旧、オフライン動作 |
| ツール | Azure Chaos Studio, カスタムスクリプト |
| 実行タイミング | 月次（自動）、四半期（手動） |
| 担当 | インフラチーム + BCP管理者 |

---

## 3. テスト環境

### 3.1 テスト環境一覧

| 環境名 | 用途 | インフラ | データ |
|-------|------|---------|-------|
| ローカル開発環境 | ユニットテスト、開発時テスト | Docker Compose | テスト用ダミーデータ |
| CI 環境 | 自動テスト（ユニット、結合、E2E） | GitHub Actions Runner | テスト用ダミーデータ |
| dev 環境 | 開発チームの統合テスト | Azure Container Apps（東日本） | サンプルデータ |
| staging 環境 | リリース前テスト、性能テスト | Azure Container Apps（東日本） | 本番相当データ（匿名化） |
| DR テスト環境 | DR テスト専用 | Azure Container Apps（東日本 + 西日本） | 本番相当データ（匿名化） |

### 3.2 テストデータ管理

| データ種別 | 用途 | 管理方法 |
|-----------|------|---------|
| ファクトリーデータ | ユニットテスト | factory-boy / faker |
| フィクスチャ | 結合テスト | JSON/YAML フィクスチャファイル |
| シードデータ | E2E テスト | シードスクリプト |
| 匿名化データ | 性能・DR テスト | 本番データの匿名化スクリプト |

### 3.3 テスト環境のセットアップ

```bash
# ローカルテスト環境
docker compose -f docker-compose.test.yml up -d
cd backend && pytest
cd frontend && pnpm test

# E2E テスト環境
docker compose -f docker-compose.test.yml up -d
cd frontend && pnpm exec playwright test
```

---

## 4. テストスケジュール

### 4.1 テストフェーズ

| フェーズ | 期間 | テスト種別 | 完了基準 |
|---------|------|-----------|---------|
| Phase 1: ユニットテスト | 各スプリント内 | ユニットテスト | カバレッジ80%以上 |
| Phase 2: 結合テスト | 各スプリント終了時 | API結合テスト | 全APIエンドポイントテスト完了 |
| Phase 3: E2Eテスト | リリース候補確定後 | E2Eテスト | 全シナリオパス |
| Phase 4: 性能テスト | リリース候補確定後 | 負荷テスト、ストレステスト | 性能基準達成 |
| Phase 5: セキュリティテスト | リリース候補確定後 | SAST、DAST、ペネトレーション | CRITICAL/HIGH脆弱性0件 |
| Phase 6: DR テスト | リリース前 | フェイルオーバー、復旧テスト | RTO/RPO基準達成 |
| Phase 7: 受入テスト | リリース前 | ユーザー受入テスト | 業務担当者承認 |

### 4.2 継続的テスト

| テスト | 頻度 | 自動/手動 |
|-------|------|----------|
| ユニットテスト | PR 毎 | 自動（CI） |
| 結合テスト | PR 毎 | 自動（CI） |
| E2E テスト | develop マージ毎 | 自動（CI） |
| セキュリティスキャン | 毎日 + PR 毎 | 自動（CI） |
| 性能テスト | リリース前 + 月次 | 自動 + 手動 |
| DR テスト | 月次 | 自動 + 手動 |

---

## 5. 合格基準

### 5.1 リリース判定基準

| 項目 | 基準 | 重要度 |
|------|------|--------|
| ユニットテストカバレッジ（バックエンド） | 80% 以上 | 必須 |
| ユニットテストカバレッジ（フロントエンド） | 75% 以上 | 必須 |
| 結合テスト合格率 | 100% | 必須 |
| E2E テスト合格率 | 100%（クリティカルパス） | 必須 |
| E2E テスト合格率 | 95% 以上（全体） | 必須 |
| セキュリティ脆弱性（CRITICAL） | 0 件 | 必須 |
| セキュリティ脆弱性（HIGH） | 0 件 | 必須 |
| セキュリティ脆弱性（MEDIUM） | 5 件以下（対応計画あり） | 推奨 |
| API レスポンスタイム（P95） | 500ms 以下 | 必須 |
| API レスポンスタイム（P99） | 1000ms 以下 | 必須 |
| 同時接続 500 ユーザー | エラー率 0.1% 以下 | 必須 |
| RTO ダッシュボード更新遅延 | 3 秒以下 | 必須 |
| フェイルオーバー完了時間 | 90 秒以内 | 必須 |
| オフライン動作 | 基本操作可能 | 必須 |
| 未解決バグ（Critical） | 0 件 | 必須 |
| 未解決バグ（High） | 0 件 | 必須 |
| 未解決バグ（Medium） | 5 件以下（対応計画あり） | 推奨 |

### 5.2 バグ重要度定義

| 重要度 | 定義 | SLA |
|--------|------|-----|
| Critical | システム停止、データ損失、セキュリティ侵害 | 即時対応（4時間以内に修正） |
| High | 主要機能の障害、ワークアラウンドなし | 24時間以内に修正 |
| Medium | 機能の一部障害、ワークアラウンドあり | 次スプリントで修正 |
| Low | UIの軽微な不具合、改善要望 | バックログに登録 |

---

## 6. テストツールと設定

### 6.1 バックエンドテスト設定

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
]
markers = [
    "unit: ユニットテスト",
    "integration: 結合テスト",
    "e2e: E2Eテスト",
    "slow: 実行時間の長いテスト",
    "security: セキュリティテスト",
    "dr: DRテスト",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning",
]
```

### 6.2 フロントエンドテスト設定

`jest.config.ts`:

```typescript
import type { Config } from 'jest';
import nextJest from 'next/jest';

const createJestConfig = nextJest({ dir: './' });

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterSetup: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  coverageProvider: 'v8',
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 75,
      lines: 75,
      statements: 75,
    },
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
    '!src/types/**',
  ],
};

export default createJestConfig(config);
```

### 6.3 Playwright 設定

`playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 2,
  workers: 4,
  reporter: [
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'test-results/e2e-results.xml' }],
  ],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
});
```

---

## 7. テスト体制

### 7.1 役割と責任

| 役割 | 責任 | 担当者数 |
|------|------|---------|
| テストリード | テスト計画策定、進捗管理、品質判定 | 1名 |
| QA エンジニア | テストケース設計、E2E テスト実行、バグ報告 | 2名 |
| 開発者 | ユニットテスト作成、結合テスト作成、バグ修正 | 各開発者 |
| セキュリティエンジニア | セキュリティテスト設計・実行 | 1名 |
| インフラエンジニア | 性能テスト・DR テスト設計・実行 | 1名 |

### 7.2 バグ管理プロセス

```
検出 → 報告（GitHub Issue）→ トリアージ → 修正 → 検証 → クローズ
```

| ステップ | 担当 | ツール |
|---------|------|-------|
| 検出 | 全メンバー / CI | テスト実行、手動テスト |
| 報告 | 検出者 | GitHub Issues（バグテンプレート使用） |
| トリアージ | テストリード | GitHub Projects |
| 修正 | 開発者 | - |
| 検証 | QA / 報告者 | テスト再実行 |
| クローズ | テストリード | GitHub Issues |

---

## 8. リスクと対策

| リスク | 影響 | 対策 |
|-------|------|------|
| テスト環境の不安定 | テスト実行の遅延 | Docker による環境の再現性確保 |
| テストデータの不足 | テストカバレッジの低下 | ファクトリーパターンによるデータ生成 |
| 外部サービスの不安定 | 結合テストの失敗 | モック/スタブの活用 |
| 性能テスト環境の本番差異 | 性能問題の見落とし | staging 環境を本番同等スペックに |
| セキュリティテスト漏れ | 脆弱性の見落とし | 自動スキャン + 定期的なペネトレーションテスト |
| DR テスト環境のコスト | テスト頻度の制限 | 自動化による効率化、必要時のみ環境起動 |

---

## 9. 成果物

| 成果物 | 形式 | 保管場所 |
|-------|------|---------|
| テスト計画書（本文書） | Markdown | リポジトリ docs/ |
| テストケース一覧 | Markdown | リポジトリ docs/ |
| テスト結果レポート | HTML / XML | CI アーティファクト |
| カバレッジレポート | HTML | Codecov |
| セキュリティスキャン結果 | SARIF / JSON | GitHub Security タブ |
| 性能テスト結果 | HTML | CI アーティファクト |
| バグ一覧 | GitHub Issues | GitHub |
| リリース判定書 | Markdown | リポジトリ docs/ |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-03-27 | 初版作成 | IT-BCP-ITSCM開発チーム |
