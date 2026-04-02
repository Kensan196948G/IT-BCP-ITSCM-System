# Phase 1: 基盤構築 (Foundation)

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-DEV-PHASE-001 |
| フェーズ期間 | 2026-03-22 ～ 2026-04-18 (4週間 / W01-W04) |
| ステータス | 🟡 進行中 (75% 完了) |
| マイルストーン | M1: 開発基盤確立 (2026-04-18) |

---

## 1. フェーズ目標

開発の土台を確立し、全後続フェーズが安全・高速に進められる環境を整備する。

```
目標:
  ✅ CI/CDパイプライン完全稼働
  ✅ 認証基盤（Azure AD / FastAPI）
  ✅ DBスキーマ確定・マイグレーション自動化
  ✅ テスト基盤（pytest / coverage ≥ 90%）
  🔄 Azureインフラ本番環境構築（進行中）
```

---

## 2. 週次タスク計画

### Week 1 (2026-03-22 ～ 2026-03-28) ✅ 完了

| タスク | 担当 | 成果物 | 状態 |
|-------|------|--------|------|
| GitHub リポジトリ初期構築 | Dev | リポジトリ・ブランチ戦略 | ✅ |
| GitHub Actions CI/CD 構築 | Dev | `.github/workflows/ci.yml` | ✅ |
| コードフォーマッター設定 (black/isort/flake8) | Dev | `pyproject.toml` / `.flake8` | ✅ |
| Pydantic スキーマ全体設計 | Dev | `apps/schemas.py` | ✅ |
| SQLAlchemy モデル定義 (11エンティティ) | Dev | `apps/models.py` | ✅ |
| FastAPI アプリ骨格構築 | Dev | `main.py` / `apps/routers/` | ✅ |
| pytest 基盤構築 | Dev | `tests/conftest.py` | ✅ |

### Week 2 (2026-03-29 ～ 2026-04-04) 🔄 進行中

| タスク | 担当 | 成果物 | 状態 |
|-------|------|--------|------|
| テストカバレッジ 99% 達成 | Dev | `tests/*.py` (471テスト) | ✅ |
| セキュリティ脆弱性対応 (FastAPI CVE) | Dev | FastAPI 0.120.4 アップグレード | ✅ |
| Next.js 14→16 アップグレード | Dev | `frontend/package.json` | ✅ |
| TypeScript 6.0 アップグレード | Dev | 型エラー修正 | ✅ |
| mypy strict モード対応 | Dev | 型エラー 7→0 | ✅ |
| テストカバレッジ 100% 達成 | Dev | 残り14行のカバレッジ | 🔄 |
| CORS/APIスキーマ不整合修正 | Dev | 14ページ動作確認 | ✅ |

### Week 3 (2026-04-05 ～ 2026-04-11) 📋 予定

| タスク | 担当 | 成果物 | 状態 |
|-------|------|--------|------|
| Azure AD 認証ミドルウェア実装 | Dev | `apps/auth.py` | ⏳ |
| RBAC (ロールベースアクセス制御) 実装 | Dev | ロール定義・権限テーブル | ⏳ |
| Alembic マイグレーション整備 | Dev | `alembic/versions/` | ⏳ |
| PostgreSQL 接続プール最適化 | Dev | `database.py` チューニング | ⏳ |
| Redis キャッシュ基盤実装 | Dev | キャッシュモジュール | ⏳ |
| Next.js 認証フロー (NextAuth.js) | Dev | 認証コンポーネント | ⏳ |
| E2Eテスト基盤構築 (Playwright) | Dev | `tests/e2e/` | ⏳ |

### Week 4 (2026-04-12 ～ 2026-04-18) 📋 予定

| タスク | 担当 | 成果物 | 状態 |
|-------|------|--------|------|
| Azure Container Apps 環境構築 | DevOps | インフラ定義 (Terraform/Bicep) | ⏳ |
| Azure Database for PostgreSQL 本番構築 | DevOps | DB 本番接続設定 | ⏳ |
| Azure Front Door / WAF 設定 | DevOps | CDN・セキュリティ設定 | ⏳ |
| GitHub Actions → Azure CD パイプライン | DevOps | `deploy.yml` | ⏳ |
| 監視基盤 (Azure Monitor / App Insights) | DevOps | アラート設定 | ⏳ |
| Phase 1 完了レビュー・M1 判定 | PM | Phase 1 完了報告書 | ⏳ |

---

## 3. 完了定義 (Definition of Done)

### M1 判定条件 (2026-04-18)

```
必須条件:
  □ pytest: 全テスト PASS
  □ flake8: エラー 0
  □ mypy --strict: エラー 0
  □ black: フォーマット適合
  □ テストカバレッジ: ≥ 95%
  □ GitHub Actions CI: 全ジョブ GREEN
  □ Azure 本番環境: Container Apps デプロイ成功
  □ 認証: Azure AD ログイン動作確認
  □ DB: マイグレーション自動適用確認
  □ セキュリティ: Critical/High CVE = 0
```

---

## 4. 現在の達成状況

```
開発環境・CI/CD     ████████████████ 100%
テスト基盤         ██████████████░░  90% (カバレッジ99%, 100%目標)
APIスキーマ・モデル ████████████████ 100%
フロントエンド基盤  ██████████████░░  88% (認証フロー未実装)
Azureインフラ      ████░░░░░░░░░░░░  25% (本番環境未構築)
認証・RBAC基盤     ░░░░░░░░░░░░░░░░   0% (Week3対象)
```

---

## 5. 技術的決定事項

| 決定 | 内容 | 根拠 |
|------|------|------|
| FastAPI async | 全エンドポイントを async/await で実装 | PostgreSQL async接続との整合性 |
| Pydantic v2 | `@field_validator` / `model_validator` 使用 | 型安全性・パフォーマンス向上 |
| mypy strict | 全モジュールで厳格型チェック | バグ早期発見・可読性向上 |
| black line-length=120 | プロジェクト標準フォーマット | 長い型アノテーションへの対応 |
| Next.js App Router | `app/` ディレクトリ構造 | Server Components活用 |
| pytest-asyncio | 非同期テストフレームワーク | FastAPI TestClient との統合 |

---

## 6. リスクと対策

| リスク | 発生確率 | 影響 | 対策 |
|-------|---------|------|------|
| Azure インフラ構築遅延 | 中 | 高 | Week4に集中、IaC (Terraform) で自動化 |
| 認証実装の複雑化 | 中 | 高 | NextAuth.js + Azure AD の組み合わせで実績パターン使用 |
| Week2以降の技術的負債 | 低 | 中 | Improvement ループで定期的に解消 |

---

_更新: 2026-04-02 | ClaudeOS Improvement Loop_
