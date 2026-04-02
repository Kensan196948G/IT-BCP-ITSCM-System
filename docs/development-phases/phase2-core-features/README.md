# Phase 2: コア機能開発 (Core Features)

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-DEV-PHASE-002 |
| フェーズ期間 | 2026-04-19 ～ 2026-06-13 (8週間 / W05-W12) |
| ステータス | 🟡 一部先行実装済み (約60%) |
| マイルストーン | M2: α版完成 (2026-06-13) |

---

## 1. フェーズ目標

BCP/ITSCM システムの主要機能をすべて実装し、α版として動作するシステムを完成させる。

```
目標:
  - 全 API エンドポイント完全実装・認証付き
  - フロントエンド全 14 ページ完成
  - BIA 計算エンジン精度向上
  - RTO トラッカー リアルタイム動作
  - WebSocket によるリアルタイム通知
  - ダッシュボード集計機能完成
```

---

## 2. 機能スコープ

### 2.1 バックエンド API

| モジュール | エンドポイント | 実装状態 |
|-----------|--------------|---------|
| IT システム管理 | `GET/POST /api/systems`, `GET/PUT/DELETE /api/systems/{id}` | ✅ 実装済み |
| 復旧手順管理 | `GET/POST /api/procedures`, `GET/PUT/DELETE /api/procedures/{id}` | ✅ 実装済み |
| シナリオ管理 | `GET/POST /api/scenarios`, `GET/PUT/DELETE /api/scenarios/{id}` | ✅ 実装済み |
| インシデント管理 | `GET/POST /api/incidents`, `GET/PUT/DELETE /api/incidents/{id}` | ✅ 実装済み |
| BIA 評価 | `GET/POST /api/bia`, `GET/PUT/DELETE /api/bia/{id}` | ✅ 実装済み |
| 連絡先管理 | `GET/POST /api/contacts`, `GET/PUT/DELETE /api/contacts/{id}` | ✅ 実装済み |
| レポート | `GET/POST /api/reports`, `GET /api/reports/{id}` | ✅ 実装済み |
| ダッシュボード | `GET /api/dashboard/readiness`, `GET /api/dashboard/rto-overview` | ✅ 実装済み |
| RTO ダッシュボード | `GET /api/incidents/{id}/rto-dashboard` | ✅ 実装済み |
| WebSocket | `WS /ws/incidents/{id}` | ✅ 実装済み |
| 認証付き API | 全エンドポイントに JWT/Azure AD 認証 | ⏳ Week5-6 |

### 2.2 フロントエンドページ

| ページ | URL | 実装状態 |
|--------|-----|---------|
| ダッシュボード | `/dashboard` | ✅ 実装済み |
| BCP 計画一覧 | `/plans` | ✅ 実装済み |
| IT システム一覧 | `/systems` | ✅ 実装済み |
| 復旧手順 | `/procedures` | ✅ 実装済み |
| シナリオ管理 | `/scenarios` | ✅ 実装済み |
| インシデント管理 | `/incidents` | ✅ 実装済み |
| BIA 評価 | `/bia` | ✅ 実装済み |
| 連絡先管理 | `/contacts` | ✅ 実装済み |
| レポート | `/reports` | ✅ 実装済み |
| RTO モニター | `/rto-monitor` | ✅ 実装済み |
| システムステータス | `/system-status` | ✅ 実装済み |
| ランブック | `/runbook` | ✅ 実装済み |
| 設定 | `/settings` | ✅ 実装済み |
| ログイン | `/login` | ✅ 実装済み |

---

## 3. 週次タスク計画

### Week 5-6 (2026-04-19 ～ 2026-05-02) 認証統合

| タスク | 成果物 | 優先度 |
|-------|--------|--------|
| 全 API エンドポイントへの認証ミドルウェア適用 | 認証付き API 仕様 | 高 |
| フロントエンド認証フロー完成 | ログイン/ログアウト/セッション管理 | 高 |
| RBAC: ロール別アクセス制御実装 | 管理者/一般ユーザー/閲覧者ロール | 高 |
| API ドキュメント更新 (認証スキーマ追記) | OpenAPI spec 更新 | 中 |

### Week 7-8 (2026-05-03 ～ 2026-05-16) BIA・RTO精度向上

| タスク | 成果物 | 優先度 |
|-------|--------|--------|
| BIA 計算エンジン精度向上 | `apps/bia_calculator.py` 改善 | 高 |
| RTO トラッカー リアルタイム連携 | `apps/rto_tracker.py` 改善 | 高 |
| インシデント → RTO 自動紐付け | 自動計算ロジック | 高 |
| Pydantic バリデーション強化 | `apps/schemas.py` 改善 | 中 |
| エラーハンドリング標準化 | 全エンドポイント統一エラーレスポンス | 中 |

### Week 9-10 (2026-05-17 ～ 2026-05-30) ダッシュボード強化

| タスク | 成果物 | 優先度 |
|-------|--------|--------|
| ダッシュボード集計ロジック最適化 | N+1 クエリ解消 | 高 |
| WebSocket リアルタイム更新 | インシデント状態リアルタイム反映 | 高 |
| フロントエンドグラフ・チャート実装 | Chart.js / Recharts 統合 | 中 |
| ページネーション・フィルタリング | 一覧ページ全体 | 中 |
| モバイル対応 (Responsive) | Tailwind CSS 調整 | 低 |

### Week 11-12 (2026-05-31 ～ 2026-06-13) α版完成・レビュー

| タスク | 成果物 | 優先度 |
|-------|--------|--------|
| α版内部デモ実施 | デモ資料・フィードバック収集 | 高 |
| フィードバック対応・バグ修正 | 修正 PR | 高 |
| API ドキュメント完成 | OpenAPI / Swagger UI | 中 |
| パフォーマンスベースライン測定 | 応答時間・DB クエリ数 | 中 |
| M2 判定・Phase 2 完了報告 | 完了報告書 | 高 |

---

## 4. 完了定義 (Definition of Done)

### M2 判定条件 (2026-06-13)

```
必須条件:
  □ 全 API エンドポイント: 認証付きで動作
  □ フロントエンド 14 ページ: 全ページ正常動作
  □ BIA 計算: 金融影響・リスクスコアが正確に計算
  □ RTO トラッカー: インシデント発生からリアルタイム追跡
  □ WebSocket: インシデント更新がリアルタイム反映
  □ テスト: 全テスト PASS / カバレッジ ≥ 95%
  □ CI: 全ジョブ GREEN
  □ 内部デモ: ステークホルダー承認
```

---

## 5. 依存関係

```
Phase 1 完了が前提:
  - Azure AD 認証基盤 (Week3-4)
  - PostgreSQL 本番環境 (Week4)
  - CI/CD パイプライン完全稼働 (Week1-2 ✅)
```

---

## 6. 技術的考慮事項

| 項目 | 対策 |
|------|------|
| N+1 クエリ問題 | SQLAlchemy `selectinload()` / `joinedload()` 使用 |
| WebSocket 接続管理 | `websocket_manager.py` コネクションプール管理 |
| 認証トークン管理 | Redis セッションストア + リフレッシュトークン |
| 型安全性 | TypeScript strict モード + Pydantic v2 |

---

_更新: 2026-04-02 | ClaudeOS Improvement Loop_
