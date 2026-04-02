# Phase 3: 高度機能開発 (Advanced Features)

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-DEV-PHASE-003 |
| フェーズ期間 | 2026-06-14 ～ 2026-07-25 (6週間 / W13-W18) |
| ステータス | ⏳ 未開始 |
| マイルストーン | M3: β版完成 (2026-07-25) |

---

## 1. フェーズ目標

α版のコア機能を土台に、ISO20000-1 / ISO27001 準拠に必要な高度機能を追加し、β版として完成させる。

```
目標:
  - BCP 訓練管理機能（計画・実施・評価サイクル）
  - 自動エスカレーション（インシデント重大度連動）
  - 多言語対応（日本語/英語）
  - PDF レポート自動生成
  - 外部システム連携（メール/Slack/Teams）
  - 監査ログ・コンプライアンス証跡
  - バルク操作（CSV インポート/エクスポート）
```

---

## 2. 機能スコープ

### 2.1 BCP 訓練管理

| 機能 | 説明 | 優先度 |
|------|------|--------|
| 訓練計画作成 | 訓練シナリオ・日程・参加者管理 | 高 |
| 訓練実施記録 | チェックリスト・証跡記録 | 高 |
| 訓練評価・レポート | RTO/RPO 達成率・改善点 | 高 |
| 訓練履歴管理 | 過去訓練データ・トレンド分析 | 中 |

### 2.2 エスカレーション・通知

| 機能 | 説明 | 優先度 |
|------|------|--------|
| 自動エスカレーション | RTO 超過時の自動通知 | 高 |
| メール通知 | SendGrid / Azure Communication Services | 高 |
| Slack 通知 | Webhook 連携 | 中 |
| Microsoft Teams 通知 | Incoming Webhook | 中 |
| エスカレーションルール設定 | 閾値・宛先カスタマイズ | 中 |

### 2.3 レポート・エクスポート

| 機能 | 説明 | 優先度 |
|------|------|--------|
| PDF レポート自動生成 | ReportLab / WeasyPrint | 高 |
| CSV エクスポート | 全エンティティ対応 | 中 |
| CSV インポート | 一括登録 | 中 |
| Excel エクスポート | openpyxl | 低 |

### 2.4 監査・コンプライアンス

| 機能 | 説明 | 優先度 |
|------|------|--------|
| 操作ログ記録 | 全 CRUD 操作の証跡 | 高 |
| 変更履歴管理 | エンティティ変更差分 | 中 |
| ISO20000-1 準拠レポート | 規格要求事項マッピング | 高 |
| ISO27001 A.5.29/A.5.30 対応 | 事業継続計画確認項目 | 高 |

---

## 3. 週次タスク計画

### Week 13-14 (2026-06-14 ～ 2026-06-27) 訓練管理

| タスク | 成果物 | 優先度 |
|-------|--------|--------|
| `DrillExercise` モデル・スキーマ設計 | `apps/models.py` 追加 | 高 |
| 訓練管理 API 実装 | `apps/routers/drills.py` | 高 |
| 訓練実施記録 CRUD | DB マイグレーション | 高 |
| 訓練ページ UI 実装 | `app/drills/` | 高 |
| Alembic マイグレーション作成 | `alembic/versions/` | 高 |

### Week 15-16 (2026-06-28 ～ 2026-07-11) 通知・エスカレーション

| タスク | 成果物 | 優先度 |
|-------|--------|--------|
| エスカレーションエンジン強化 | `apps/escalation_engine.py` | 高 |
| メール通知実装 | `apps/notification_service.py` | 高 |
| Slack Webhook 連携 | 通知サービス拡張 | 中 |
| 通知設定 UI | `/settings` ページ拡張 | 中 |
| エスカレーションルール管理 API | `apps/routers/escalation.py` | 中 |

### Week 17-18 (2026-07-12 ～ 2026-07-25) レポート・監査

| タスク | 成果物 | 優先度 |
|-------|--------|--------|
| PDF レポート生成エンジン | `apps/pdf_generator.py` | 高 |
| CSV インポート/エクスポート | バルク操作 API | 中 |
| 監査ログ機能実装 | `apps/audit_log.py` | 高 |
| ISO20000-1 準拠レポートテンプレート | PDF テンプレート | 高 |
| β版内部デモ・M3 判定 | 完了報告書 | 高 |

---

## 4. 完了定義 (Definition of Done)

### M3 判定条件 (2026-07-25)

```
必須条件:
  □ 訓練管理: 計画→実施→評価サイクルが完全動作
  □ 通知: メール通知 E2E 動作確認
  □ PDF レポート: ISO20000-1 準拠フォーマット生成
  □ 監査ログ: 全 CRUD 操作が記録される
  □ テスト: 全テスト PASS / カバレッジ ≥ 95%
  □ CI: 全ジョブ GREEN
  □ 内部デモ: ステークホルダー承認
```

---

## 5. 新規 DB モデル（予定）

```python
# 訓練管理
class DrillExercise(Base):
    id: UUID
    drill_id: str          # DR-2026-001
    scenario_type: str     # dc_failure / cyber_attack
    planned_date: date
    actual_date: date | None
    participants: list[str]
    rto_achieved_hours: float | None
    evaluation_score: int  # 1-100
    status: str            # planned / in_progress / completed

# 監査ログ
class AuditLog(Base):
    id: UUID
    user_id: str
    action: str            # CREATE / UPDATE / DELETE
    entity_type: str       # ITSystemBCP / Incident / ...
    entity_id: UUID
    before_value: dict | None
    after_value: dict | None
    timestamp: datetime
    ip_address: str
```

---

## 6. リスクと対策

| リスク | 対策 |
|-------|------|
| PDF ライブラリの日本語フォント対応 | Noto Sans CJK フォント同梱 |
| メール送信の SPF/DKIM 設定 | Azure Communication Services 使用 |
| DB スキーマ変更の後方互換性 | Alembic の downgrade スクリプト作成 |
| 訓練機能スコープクリープ | Phase 3 で基本機能のみ、高度化は Phase 4 以降 |

---

_更新: 2026-04-02 | ClaudeOS Improvement Loop_
