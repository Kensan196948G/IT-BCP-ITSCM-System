# データベース設計書 (Database Design)

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-DES-DB-002 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 分類 | 設計文書 |
| 準拠規格 | ISO20000 ITSCM / ISO27001 / NIST CSF RECOVER RC |

---

## 目次

1. [概要](#1-概要)
2. [ER図](#2-er図)
3. [テーブル定義](#3-テーブル定義)
4. [インデックス設計](#4-インデックス設計)
5. [パーティション戦略](#5-パーティション戦略)
6. [Geo冗長レプリケーション設計](#6-geo冗長レプリケーション設計)
7. [データライフサイクル管理](#7-データライフサイクル管理)
8. [変更履歴](#8-変更履歴)

---

## 1. 概要

### 1.1 データベース基本情報

| 項目 | 値 |
|------|-----|
| RDBMS | PostgreSQL 16 |
| ホスティング | Azure Database for PostgreSQL Flexible Server |
| プライマリリージョン | East Japan |
| スタンバイリージョン | West Japan |
| 文字コード | UTF-8 |
| 照合順序 | ja_JP.utf8 |
| タイムゾーン | UTC（アプリケーション層でJST変換） |
| スキーマ名 | itscm |

### 1.2 設計方針

- 全テーブルに `created_at`、`updated_at`、`created_by`、`updated_by` の監査カラムを付与
- 論理削除（`deleted_at`）を採用し、物理削除は行わない
- UUID v7をプライマリキーに使用（時系列ソート可能）
- ENUM型はPostgreSQLカスタム型として定義
- 外部キー制約を必ず設定し、参照整合性を保証
- パーティショニングにより大量データのクエリ性能を確保

---

## 2. ER図

### 2.1 全体ER図（テキスト表現）

```
┌─────────────────┐       ┌─────────────────────┐
│     users        │       │   it_systems_bcp     │
│─────────────────│       │─────────────────────│
│ PK id           │       │ PK id                │
│    email         │       │ FK created_by → users│
│    display_name  │◄──┐  │    system_name       │
│    role          │   │  │    criticality_tier  │
│    department    │   │  │    rto_target        │
│    phone         │   │  │    rpo_target        │
│    is_active     │   │  │    current_rto_status│
└─────────────────┘   │  │    owner_department  │
                       │  │    recovery_priority │
                       │  └──────────┬──────────┘
                       │             │
                       │             │ 1:N
                       │             ▼
                       │  ┌─────────────────────┐
                       │  │ recovery_procedures  │
                       │  │─────────────────────│
                       │  │ PK id                │
                       │  │ FK system_id          │
                       │  │    step_number        │
                       │  │    procedure_title    │
                       │  │    procedure_detail   │
                       │  │    estimated_minutes  │
                       │  │    responsible_role   │
                       │  └─────────────────────┘
                       │
                       │  ┌─────────────────────┐       ┌─────────────────────┐
                       │  │  bcp_exercises       │       │  bcp_scenarios      │
                       │  │─────────────────────│       │─────────────────────│
                       │  │ PK id                │       │ PK id                │
                       ├──│ FK facilitator_id     │  ┌──│    scenario_name     │
                       │  │ FK scenario_id ───────┼──┘  │    scenario_type     │
                       │  │    exercise_name     │       │    description       │
                       │  │    exercise_type     │       │    severity_level    │
                       │  │    status            │       │    target_systems    │
                       │  │    scheduled_date    │       │    injection_steps   │
                       │  │    actual_start      │       │    expected_rto      │
                       │  │    actual_end        │       └─────────────────────┘
                       │  └──────────┬──────────┘
                       │             │
                       │             │ 1:N
                       │             ▼
                       │  ┌─────────────────────────────┐
                       │  │ exercise_rto_records         │
                       │  │─────────────────────────────│
                       │  │ PK id                        │
                       │  │ FK exercise_id                │
                       │  │ FK system_id → it_systems_bcp│
                       │  │    target_rto_minutes        │
                       │  │    actual_rto_minutes        │
                       │  │    rto_status                │
                       │  │    recovery_start_time       │
                       │  │    recovery_end_time         │
                       │  └─────────────────────────────┘
                       │
                       │  ┌─────────────────────┐
                       │  │  active_incidents    │
                       │  │─────────────────────│
                       ├──│ FK reported_by        │
                       ├──│ FK incident_commander │
                       │  │ PK id                │
                       │  │    incident_title    │
                       │  │    incident_type     │
                       │  │    severity          │
                       │  │    status            │
                       │  │    bcp_activation_level│
                       │  │    detected_at       │
                       │  │    resolved_at       │
                       │  └──────────┬──────────┘
                       │             │
                       │             │ 1:N
                       │             ▼
                       │  ┌─────────────────────────────┐
                       │  │ incident_affected_systems    │
                       │  │─────────────────────────────│
                       │  │ PK id                        │
                       │  │ FK incident_id                │
                       │  │ FK system_id → it_systems_bcp│
                       │  │    impact_level              │
                       │  │    rto_status                │
                       │  │    recovery_start            │
                       │  │    recovery_end              │
                       │  └─────────────────────────────┘
                       │
                       │  ┌─────────────────────┐
                       │  │ escalation_logs      │
                       │  │─────────────────────│
                       │  │ PK id                │
                       │  │ FK incident_id        │
                       ├──│ FK escalated_by       │
                       │  │    escalation_level  │
                       │  │    channel           │
                       │  │    recipients        │
                       │  │    message           │
                       │  │    sent_at           │
                       │  │    delivery_status   │
                       │  └─────────────────────┘
                       │
                       │  ┌─────────────────────┐
                       │  │  vendor_contacts     │
                       │  │─────────────────────│
                       │  │ PK id                │
                       │  │    vendor_name       │
                       │  │    contact_name      │
                       │  │    contact_email     │
                       │  │    contact_phone     │
                       │  │    contract_type     │
                       │  │    sla_response_hours│
                       │  │    escalation_path   │
                       │  └─────────────────────┘
                       │
                       │  ┌─────────────────────┐
                       │  │  audit_logs          │
                       │  │─────────────────────│
                       │  │ PK id                │
                       └──│ FK user_id            │
                          │    action            │
                          │    resource_type     │
                          │    resource_id       │
                          │    old_value         │
                          │    new_value         │
                          │    ip_address        │
                          │    user_agent        │
                          │    timestamp         │
                          └─────────────────────┘
```

---

## 3. テーブル定義

### 3.1 カスタム型定義

```sql
-- ユーザーロール
CREATE TYPE itscm.user_role AS ENUM (
    'system_admin',      -- システム管理者
    'bcp_manager',       -- BCP管理者
    'incident_commander',-- インシデントコマンダー
    'exercise_facilitator', -- 演習ファシリテーター
    'operator',          -- オペレーター
    'viewer'             -- 閲覧者
);

-- システム重要度
CREATE TYPE itscm.criticality_tier AS ENUM (
    'tier_1_mission_critical',  -- ミッションクリティカル
    'tier_2_business_critical', -- ビジネスクリティカル
    'tier_3_business_operational', -- 業務運用
    'tier_4_administrative'     -- 管理系
);

-- RTO状態
CREATE TYPE itscm.rto_status AS ENUM (
    'not_started',  -- 未開始（グレー）
    'on_track',     -- 順調（緑）
    'at_risk',      -- リスクあり（黄）
    'overdue',      -- 超過（赤）
    'recovered'     -- 復旧済（青）
);

-- インシデント重大度
CREATE TYPE itscm.severity_level AS ENUM (
    'critical',  -- P1: 重大
    'high',      -- P2: 高
    'medium',    -- P3: 中
    'low'        -- P4: 低
);

-- インシデント状態
CREATE TYPE itscm.incident_status AS ENUM (
    'detected',       -- 検知
    'triaged',        -- トリアージ済
    'bcp_activated',  -- BCP発動
    'recovering',     -- 復旧中
    'recovered',      -- 復旧済
    'post_mortem',    -- ポストモーテム
    'closed'          -- クローズ
);

-- BCP発動レベル
CREATE TYPE itscm.bcp_activation_level AS ENUM (
    'none',             -- 未発動
    'p2_partial_bcp',   -- P2: 部分BCP発動
    'p1_full_bcp'       -- P1: 全面BCP発動
);

-- 演習種別
CREATE TYPE itscm.exercise_type AS ENUM (
    'tabletop',       -- テーブルトップ演習
    'walkthrough',    -- ウォークスルー演習
    'simulation',     -- シミュレーション演習
    'full_exercise'   -- 全体演習
);

-- 演習状態
CREATE TYPE itscm.exercise_status AS ENUM (
    'draft',        -- 下書き
    'scheduled',    -- 予定
    'in_progress',  -- 実施中
    'completed',    -- 完了
    'cancelled'     -- 中止
);

-- 通知チャネル
CREATE TYPE itscm.notification_channel AS ENUM (
    'teams',    -- Microsoft Teams
    'sms',      -- SMS
    'email',    -- Email
    'phone'     -- 電話
);

-- 配信状態
CREATE TYPE itscm.delivery_status AS ENUM (
    'pending',    -- 送信待ち
    'sent',       -- 送信済
    'delivered',  -- 配信済
    'failed',     -- 失敗
    'retrying'    -- リトライ中
);
```

### 3.2 users テーブル

ユーザー情報を管理するテーブル。Entra ID SSOと連携し、認証はEntra IDで行う。

```sql
CREATE TABLE itscm.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entra_id        VARCHAR(255) NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    display_name    VARCHAR(255) NOT NULL,
    role            itscm.user_role NOT NULL DEFAULT 'viewer',
    department      VARCHAR(255),
    phone           VARCHAR(50),
    secondary_phone VARCHAR(50),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    profile_image_url VARCHAR(500),
    notification_preferences JSONB NOT NULL DEFAULT '{
        "teams": true,
        "sms": true,
        "email": true,
        "phone": false
    }'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID REFERENCES itscm.users(id),
    updated_by      UUID REFERENCES itscm.users(id),
    deleted_at      TIMESTAMPTZ
);

COMMENT ON TABLE itscm.users IS 'ユーザー管理テーブル。Entra ID SSOと連携';
COMMENT ON COLUMN itscm.users.entra_id IS 'Microsoft Entra IDのオブジェクトID';
COMMENT ON COLUMN itscm.users.role IS 'ユーザーロール（RBAC）';
COMMENT ON COLUMN itscm.users.notification_preferences IS '通知設定（チャネル別ON/OFF）';
```

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|------|------|-----------|------|
| id | UUID | NO | gen_random_uuid() | プライマリキー |
| entra_id | VARCHAR(255) | NO | - | Entra IDオブジェクトID |
| email | VARCHAR(255) | NO | - | メールアドレス |
| display_name | VARCHAR(255) | NO | - | 表示名 |
| role | user_role | NO | 'viewer' | ロール |
| department | VARCHAR(255) | YES | - | 所属部署 |
| phone | VARCHAR(50) | YES | - | 電話番号（主） |
| secondary_phone | VARCHAR(50) | YES | - | 電話番号（副） |
| is_active | BOOLEAN | NO | TRUE | アクティブフラグ |
| last_login_at | TIMESTAMPTZ | YES | - | 最終ログイン日時 |
| profile_image_url | VARCHAR(500) | YES | - | プロフィール画像URL |
| notification_preferences | JSONB | NO | (JSON) | 通知設定 |
| created_at | TIMESTAMPTZ | NO | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | NOW() | 更新日時 |
| created_by | UUID (FK) | YES | - | 作成者 |
| updated_by | UUID (FK) | YES | - | 更新者 |
| deleted_at | TIMESTAMPTZ | YES | - | 論理削除日時 |

### 3.3 it_systems_bcp テーブル

BCP管理対象のITシステムを管理するテーブル。

```sql
CREATE TABLE itscm.it_systems_bcp (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_code         VARCHAR(50) NOT NULL UNIQUE,
    system_name         VARCHAR(255) NOT NULL,
    system_description  TEXT,
    criticality_tier    itscm.criticality_tier NOT NULL,
    rto_target_minutes  INTEGER NOT NULL CHECK (rto_target_minutes > 0),
    rpo_target_minutes  INTEGER NOT NULL CHECK (rpo_target_minutes >= 0),
    current_rto_status  itscm.rto_status NOT NULL DEFAULT 'not_started',
    owner_department    VARCHAR(255) NOT NULL,
    owner_contact_id    UUID REFERENCES itscm.users(id),
    technical_contact_id UUID REFERENCES itscm.users(id),
    recovery_priority   INTEGER NOT NULL CHECK (recovery_priority BETWEEN 1 AND 100),
    infrastructure_type VARCHAR(100),
    hosting_location    VARCHAR(255),
    dependencies        JSONB NOT NULL DEFAULT '[]'::jsonb,
    vendor_ids          UUID[] DEFAULT '{}',
    documentation_url   VARCHAR(500),
    last_tested_at      TIMESTAMPTZ,
    last_incident_at    TIMESTAMPTZ,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID NOT NULL REFERENCES itscm.users(id),
    updated_by          UUID REFERENCES itscm.users(id),
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE itscm.it_systems_bcp IS 'BCP管理対象ITシステムテーブル';
COMMENT ON COLUMN itscm.it_systems_bcp.criticality_tier IS 'システム重要度（Tier1が最も重要）';
COMMENT ON COLUMN itscm.it_systems_bcp.rto_target_minutes IS 'RTO目標（分）';
COMMENT ON COLUMN itscm.it_systems_bcp.rpo_target_minutes IS 'RPO目標（分）';
COMMENT ON COLUMN itscm.it_systems_bcp.recovery_priority IS '復旧優先度（1が最高、100が最低）';
COMMENT ON COLUMN itscm.it_systems_bcp.dependencies IS '依存システムID一覧（JSON配列）';
```

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|------|------|-----------|------|
| id | UUID | NO | gen_random_uuid() | プライマリキー |
| system_code | VARCHAR(50) | NO | - | システムコード（一意） |
| system_name | VARCHAR(255) | NO | - | システム名称 |
| system_description | TEXT | YES | - | システム説明 |
| criticality_tier | criticality_tier | NO | - | 重要度ティア |
| rto_target_minutes | INTEGER | NO | - | RTO目標（分） |
| rpo_target_minutes | INTEGER | NO | - | RPO目標（分） |
| current_rto_status | rto_status | NO | 'not_started' | 現在のRTO状態 |
| owner_department | VARCHAR(255) | NO | - | 所管部署 |
| owner_contact_id | UUID (FK) | YES | - | 所管担当者 |
| technical_contact_id | UUID (FK) | YES | - | 技術担当者 |
| recovery_priority | INTEGER | NO | - | 復旧優先度(1-100) |
| infrastructure_type | VARCHAR(100) | YES | - | インフラ種別 |
| hosting_location | VARCHAR(255) | YES | - | ホスティング場所 |
| dependencies | JSONB | NO | '[]' | 依存システム |
| vendor_ids | UUID[] | YES | '{}' | 関連ベンダーID |
| documentation_url | VARCHAR(500) | YES | - | ドキュメントURL |
| last_tested_at | TIMESTAMPTZ | YES | - | 最終テスト日時 |
| last_incident_at | TIMESTAMPTZ | YES | - | 最終インシデント日時 |
| is_active | BOOLEAN | NO | TRUE | アクティブフラグ |
| metadata | JSONB | NO | '{}' | メタデータ |
| created_at | TIMESTAMPTZ | NO | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | NOW() | 更新日時 |
| created_by | UUID (FK) | NO | - | 作成者 |
| updated_by | UUID (FK) | YES | - | 更新者 |
| deleted_at | TIMESTAMPTZ | YES | - | 論理削除日時 |

### 3.4 bcp_scenarios テーブル

BCP訓練シナリオを管理するテーブル。テーブルトップ演習のシナリオテンプレートを格納する。

```sql
CREATE TABLE itscm.bcp_scenarios (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_code       VARCHAR(50) NOT NULL UNIQUE,
    scenario_name       VARCHAR(255) NOT NULL,
    scenario_type       VARCHAR(100) NOT NULL,
    description         TEXT NOT NULL,
    severity_level      itscm.severity_level NOT NULL,
    target_systems      UUID[] NOT NULL DEFAULT '{}',
    injection_steps     JSONB NOT NULL DEFAULT '[]'::jsonb,
    expected_rto_minutes INTEGER,
    expected_actions    JSONB NOT NULL DEFAULT '[]'::jsonb,
    evaluation_criteria JSONB NOT NULL DEFAULT '[]'::jsonb,
    prerequisites       TEXT,
    estimated_duration_minutes INTEGER NOT NULL DEFAULT 120,
    difficulty_level    VARCHAR(20) NOT NULL DEFAULT 'medium'
        CHECK (difficulty_level IN ('easy', 'medium', 'hard', 'expert')),
    tags                VARCHAR(100)[] DEFAULT '{}',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    version             INTEGER NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID NOT NULL REFERENCES itscm.users(id),
    updated_by          UUID REFERENCES itscm.users(id),
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE itscm.bcp_scenarios IS 'BCPシナリオテーブル。テーブルトップ演習のシナリオテンプレート';
COMMENT ON COLUMN itscm.bcp_scenarios.injection_steps IS '段階的シナリオインジェクション手順（JSON配列）';
COMMENT ON COLUMN itscm.bcp_scenarios.evaluation_criteria IS '評価基準（JSON配列）';
```

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|------|------|-----------|------|
| id | UUID | NO | gen_random_uuid() | プライマリキー |
| scenario_code | VARCHAR(50) | NO | - | シナリオコード（一意） |
| scenario_name | VARCHAR(255) | NO | - | シナリオ名称 |
| scenario_type | VARCHAR(100) | NO | - | シナリオ種別（災害/サイバー攻撃/停電等） |
| description | TEXT | NO | - | シナリオ概要説明 |
| severity_level | severity_level | NO | - | 想定重大度 |
| target_systems | UUID[] | NO | '{}' | 対象システムID配列 |
| injection_steps | JSONB | NO | '[]' | インジェクションステップ（JSON） |
| expected_rto_minutes | INTEGER | YES | - | 想定RTO（分） |
| expected_actions | JSONB | NO | '[]' | 期待されるアクション（JSON） |
| evaluation_criteria | JSONB | NO | '[]' | 評価基準（JSON） |
| prerequisites | TEXT | YES | - | 前提条件 |
| estimated_duration_minutes | INTEGER | NO | 120 | 想定所要時間（分） |
| difficulty_level | VARCHAR(20) | NO | 'medium' | 難易度 |
| tags | VARCHAR(100)[] | YES | '{}' | タグ |
| is_active | BOOLEAN | NO | TRUE | アクティブフラグ |
| version | INTEGER | NO | 1 | バージョン番号 |
| created_at | TIMESTAMPTZ | NO | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | NOW() | 更新日時 |
| created_by | UUID (FK) | NO | - | 作成者 |
| updated_by | UUID (FK) | YES | - | 更新者 |
| deleted_at | TIMESTAMPTZ | YES | - | 論理削除日時 |

**injection_stepsのJSON構造例**:

```json
[
    {
        "step": 1,
        "time_offset_minutes": 0,
        "title": "初期障害検知",
        "description": "データセンターの電源系統に異常を検知。UPSに切替",
        "inject_type": "notification",
        "expected_response_minutes": 5
    },
    {
        "step": 2,
        "time_offset_minutes": 15,
        "title": "障害拡大",
        "description": "UPSバッテリー残量低下。発電機の起動失敗",
        "inject_type": "escalation",
        "expected_response_minutes": 10
    },
    {
        "step": 3,
        "time_offset_minutes": 30,
        "title": "サービス影響拡大",
        "description": "主要3システムがダウン。顧客影響が発生",
        "inject_type": "decision_point",
        "expected_response_minutes": 15
    }
]
```

### 3.5 bcp_exercises テーブル

BCP訓練（演習）の実施記録を管理するテーブル。

```sql
CREATE TABLE itscm.bcp_exercises (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_code       VARCHAR(50) NOT NULL UNIQUE,
    exercise_name       VARCHAR(255) NOT NULL,
    exercise_type       itscm.exercise_type NOT NULL,
    scenario_id         UUID NOT NULL REFERENCES itscm.bcp_scenarios(id),
    facilitator_id      UUID NOT NULL REFERENCES itscm.users(id),
    status              itscm.exercise_status NOT NULL DEFAULT 'draft',
    scheduled_date      DATE NOT NULL,
    scheduled_start_time TIME,
    scheduled_end_time  TIME,
    actual_start_at     TIMESTAMPTZ,
    actual_end_at       TIMESTAMPTZ,
    participants        JSONB NOT NULL DEFAULT '[]'::jsonb,
    observer_notes      TEXT,
    lessons_learned     TEXT,
    action_items        JSONB NOT NULL DEFAULT '[]'::jsonb,
    overall_score       DECIMAL(5,2) CHECK (overall_score BETWEEN 0 AND 100),
    scoring_details     JSONB NOT NULL DEFAULT '{}'::jsonb,
    current_injection_step INTEGER NOT NULL DEFAULT 0,
    attachments         JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID NOT NULL REFERENCES itscm.users(id),
    updated_by          UUID REFERENCES itscm.users(id),
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE itscm.bcp_exercises IS 'BCP演習テーブル。訓練の計画・実施・評価を管理';
COMMENT ON COLUMN itscm.bcp_exercises.current_injection_step IS '現在のシナリオインジェクションステップ番号';
COMMENT ON COLUMN itscm.bcp_exercises.action_items IS '改善事項（JSON配列）';
```

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|------|------|-----------|------|
| id | UUID | NO | gen_random_uuid() | プライマリキー |
| exercise_code | VARCHAR(50) | NO | - | 演習コード（一意） |
| exercise_name | VARCHAR(255) | NO | - | 演習名称 |
| exercise_type | exercise_type | NO | - | 演習種別 |
| scenario_id | UUID (FK) | NO | - | 使用シナリオ |
| facilitator_id | UUID (FK) | NO | - | ファシリテーター |
| status | exercise_status | NO | 'draft' | 演習状態 |
| scheduled_date | DATE | NO | - | 予定日 |
| scheduled_start_time | TIME | YES | - | 予定開始時刻 |
| scheduled_end_time | TIME | YES | - | 予定終了時刻 |
| actual_start_at | TIMESTAMPTZ | YES | - | 実際の開始日時 |
| actual_end_at | TIMESTAMPTZ | YES | - | 実際の終了日時 |
| participants | JSONB | NO | '[]' | 参加者情報（JSON） |
| observer_notes | TEXT | YES | - | オブザーバーメモ |
| lessons_learned | TEXT | YES | - | 教訓・気付き |
| action_items | JSONB | NO | '[]' | 改善事項 |
| overall_score | DECIMAL(5,2) | YES | - | 総合スコア(0-100) |
| scoring_details | JSONB | NO | '{}' | スコア詳細 |
| current_injection_step | INTEGER | NO | 0 | 現在のインジェクションステップ |
| attachments | JSONB | NO | '[]' | 添付ファイル情報 |
| created_at | TIMESTAMPTZ | NO | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | NOW() | 更新日時 |
| created_by | UUID (FK) | NO | - | 作成者 |
| updated_by | UUID (FK) | YES | - | 更新者 |
| deleted_at | TIMESTAMPTZ | YES | - | 論理削除日時 |

### 3.6 active_incidents テーブル

アクティブなインシデント情報を管理するテーブル。

```sql
CREATE TABLE itscm.active_incidents (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_code           VARCHAR(50) NOT NULL UNIQUE,
    incident_title          VARCHAR(500) NOT NULL,
    incident_type           VARCHAR(100) NOT NULL,
    description             TEXT NOT NULL,
    severity                itscm.severity_level NOT NULL,
    status                  itscm.incident_status NOT NULL DEFAULT 'detected',
    bcp_activation_level    itscm.bcp_activation_level NOT NULL DEFAULT 'none',
    reported_by             UUID NOT NULL REFERENCES itscm.users(id),
    incident_commander_id   UUID REFERENCES itscm.users(id),
    detected_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    triaged_at              TIMESTAMPTZ,
    bcp_activated_at        TIMESTAMPTZ,
    resolved_at             TIMESTAMPTZ,
    closed_at               TIMESTAMPTZ,
    root_cause              TEXT,
    impact_summary          TEXT,
    affected_users_count    INTEGER DEFAULT 0,
    affected_regions        VARCHAR(100)[] DEFAULT '{}',
    communication_log       JSONB NOT NULL DEFAULT '[]'::jsonb,
    timeline                JSONB NOT NULL DEFAULT '[]'::jsonb,
    post_mortem_url         VARCHAR(500),
    external_ticket_id      VARCHAR(100),
    external_ticket_url     VARCHAR(500),
    tags                    VARCHAR(100)[] DEFAULT '{}',
    metadata                JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by              UUID NOT NULL REFERENCES itscm.users(id),
    updated_by              UUID REFERENCES itscm.users(id),
    deleted_at              TIMESTAMPTZ
) PARTITION BY RANGE (detected_at);

COMMENT ON TABLE itscm.active_incidents IS 'インシデント管理テーブル。パーティション（月単位）';
COMMENT ON COLUMN itscm.active_incidents.bcp_activation_level IS 'BCP発動レベル';
COMMENT ON COLUMN itscm.active_incidents.timeline IS 'インシデントタイムライン（JSON配列）';
```

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|------|------|-----------|------|
| id | UUID | NO | gen_random_uuid() | プライマリキー |
| incident_code | VARCHAR(50) | NO | - | インシデントコード（一意） |
| incident_title | VARCHAR(500) | NO | - | インシデントタイトル |
| incident_type | VARCHAR(100) | NO | - | インシデント種別 |
| description | TEXT | NO | - | 詳細説明 |
| severity | severity_level | NO | - | 重大度 |
| status | incident_status | NO | 'detected' | ステータス |
| bcp_activation_level | bcp_activation_level | NO | 'none' | BCP発動レベル |
| reported_by | UUID (FK) | NO | - | 報告者 |
| incident_commander_id | UUID (FK) | YES | - | インシデントコマンダー |
| detected_at | TIMESTAMPTZ | NO | NOW() | 検知日時 |
| triaged_at | TIMESTAMPTZ | YES | - | トリアージ日時 |
| bcp_activated_at | TIMESTAMPTZ | YES | - | BCP発動日時 |
| resolved_at | TIMESTAMPTZ | YES | - | 解決日時 |
| closed_at | TIMESTAMPTZ | YES | - | クローズ日時 |
| root_cause | TEXT | YES | - | 根本原因 |
| impact_summary | TEXT | YES | - | 影響概要 |
| affected_users_count | INTEGER | YES | 0 | 影響ユーザー数 |
| affected_regions | VARCHAR(100)[] | YES | '{}' | 影響リージョン |
| communication_log | JSONB | NO | '[]' | コミュニケーションログ |
| timeline | JSONB | NO | '[]' | タイムライン |
| post_mortem_url | VARCHAR(500) | YES | - | ポストモーテムURL |
| external_ticket_id | VARCHAR(100) | YES | - | 外部チケットID |
| external_ticket_url | VARCHAR(500) | YES | - | 外部チケットURL |
| tags | VARCHAR(100)[] | YES | '{}' | タグ |
| metadata | JSONB | NO | '{}' | メタデータ |
| created_at | TIMESTAMPTZ | NO | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | NOW() | 更新日時 |
| created_by | UUID (FK) | NO | - | 作成者 |
| updated_by | UUID (FK) | YES | - | 更新者 |
| deleted_at | TIMESTAMPTZ | YES | - | 論理削除日時 |

### 3.7 recovery_procedures テーブル

ITシステムの復旧手順を管理するテーブル。

```sql
CREATE TABLE itscm.recovery_procedures (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id           UUID NOT NULL REFERENCES itscm.it_systems_bcp(id),
    step_number         INTEGER NOT NULL CHECK (step_number > 0),
    procedure_title     VARCHAR(255) NOT NULL,
    procedure_detail    TEXT NOT NULL,
    estimated_minutes   INTEGER NOT NULL CHECK (estimated_minutes > 0),
    responsible_role    itscm.user_role NOT NULL,
    responsible_team    VARCHAR(255),
    prerequisites       TEXT,
    verification_steps  TEXT,
    rollback_steps      TEXT,
    automation_script_url VARCHAR(500),
    is_automated        BOOLEAN NOT NULL DEFAULT FALSE,
    notes               TEXT,
    version             INTEGER NOT NULL DEFAULT 1,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID NOT NULL REFERENCES itscm.users(id),
    updated_by          UUID REFERENCES itscm.users(id),
    deleted_at          TIMESTAMPTZ,
    UNIQUE (system_id, step_number, version)
);

COMMENT ON TABLE itscm.recovery_procedures IS '復旧手順テーブル。システムごとの段階的復旧手順を管理';
COMMENT ON COLUMN itscm.recovery_procedures.step_number IS '手順のステップ番号（実行順序）';
COMMENT ON COLUMN itscm.recovery_procedures.is_automated IS '自動化済みフラグ';
```

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|------|------|-----------|------|
| id | UUID | NO | gen_random_uuid() | プライマリキー |
| system_id | UUID (FK) | NO | - | 対象システム |
| step_number | INTEGER | NO | - | ステップ番号 |
| procedure_title | VARCHAR(255) | NO | - | 手順タイトル |
| procedure_detail | TEXT | NO | - | 手順詳細 |
| estimated_minutes | INTEGER | NO | - | 想定所要時間（分） |
| responsible_role | user_role | NO | - | 実行担当ロール |
| responsible_team | VARCHAR(255) | YES | - | 実行担当チーム |
| prerequisites | TEXT | YES | - | 前提条件 |
| verification_steps | TEXT | YES | - | 確認手順 |
| rollback_steps | TEXT | YES | - | ロールバック手順 |
| automation_script_url | VARCHAR(500) | YES | - | 自動化スクリプトURL |
| is_automated | BOOLEAN | NO | FALSE | 自動化済み |
| notes | TEXT | YES | - | 備考 |
| version | INTEGER | NO | 1 | バージョン |
| is_active | BOOLEAN | NO | TRUE | アクティブフラグ |
| created_at | TIMESTAMPTZ | NO | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | NOW() | 更新日時 |
| created_by | UUID (FK) | NO | - | 作成者 |
| updated_by | UUID (FK) | YES | - | 更新者 |
| deleted_at | TIMESTAMPTZ | YES | - | 論理削除日時 |

### 3.8 vendor_contacts テーブル

ベンダー連絡先情報を管理するテーブル。

```sql
CREATE TABLE itscm.vendor_contacts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_code         VARCHAR(50) NOT NULL UNIQUE,
    vendor_name         VARCHAR(255) NOT NULL,
    vendor_type         VARCHAR(100) NOT NULL,
    contact_name        VARCHAR(255) NOT NULL,
    contact_title       VARCHAR(255),
    contact_email       VARCHAR(255) NOT NULL,
    contact_phone       VARCHAR(50) NOT NULL,
    secondary_phone     VARCHAR(50),
    emergency_phone     VARCHAR(50),
    contract_type       VARCHAR(100) NOT NULL,
    contract_number     VARCHAR(100),
    contract_start_date DATE,
    contract_end_date   DATE,
    sla_response_hours  DECIMAL(5,2) NOT NULL CHECK (sla_response_hours > 0),
    sla_resolution_hours DECIMAL(5,2),
    escalation_path     JSONB NOT NULL DEFAULT '[]'::jsonb,
    support_hours       VARCHAR(100) NOT NULL DEFAULT '24/7',
    support_scope       TEXT,
    related_systems     UUID[] DEFAULT '{}',
    notes               TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by          UUID NOT NULL REFERENCES itscm.users(id),
    updated_by          UUID REFERENCES itscm.users(id),
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE itscm.vendor_contacts IS 'ベンダー連絡先テーブル。緊急時の連絡先管理';
COMMENT ON COLUMN itscm.vendor_contacts.escalation_path IS 'エスカレーションパス（JSON配列）';
COMMENT ON COLUMN itscm.vendor_contacts.sla_response_hours IS 'SLA応答時間（時間）';
```

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|------|------|-----------|------|
| id | UUID | NO | gen_random_uuid() | プライマリキー |
| vendor_code | VARCHAR(50) | NO | - | ベンダーコード（一意） |
| vendor_name | VARCHAR(255) | NO | - | ベンダー名 |
| vendor_type | VARCHAR(100) | NO | - | ベンダー種別 |
| contact_name | VARCHAR(255) | NO | - | 担当者名 |
| contact_title | VARCHAR(255) | YES | - | 担当者役職 |
| contact_email | VARCHAR(255) | NO | - | メールアドレス |
| contact_phone | VARCHAR(50) | NO | - | 電話番号 |
| secondary_phone | VARCHAR(50) | YES | - | 副電話番号 |
| emergency_phone | VARCHAR(50) | YES | - | 緊急電話番号 |
| contract_type | VARCHAR(100) | NO | - | 契約種別 |
| contract_number | VARCHAR(100) | YES | - | 契約番号 |
| contract_start_date | DATE | YES | - | 契約開始日 |
| contract_end_date | DATE | YES | - | 契約終了日 |
| sla_response_hours | DECIMAL(5,2) | NO | - | SLA応答時間（時間） |
| sla_resolution_hours | DECIMAL(5,2) | YES | - | SLA解決時間（時間） |
| escalation_path | JSONB | NO | '[]' | エスカレーションパス |
| support_hours | VARCHAR(100) | NO | '24/7' | サポート対応時間 |
| support_scope | TEXT | YES | - | サポート範囲 |
| related_systems | UUID[] | YES | '{}' | 関連システムID |
| notes | TEXT | YES | - | 備考 |
| is_active | BOOLEAN | NO | TRUE | アクティブフラグ |
| created_at | TIMESTAMPTZ | NO | NOW() | 作成日時 |
| updated_at | TIMESTAMPTZ | NO | NOW() | 更新日時 |
| created_by | UUID (FK) | NO | - | 作成者 |
| updated_by | UUID (FK) | YES | - | 更新者 |
| deleted_at | TIMESTAMPTZ | YES | - | 論理削除日時 |

### 3.9 incident_affected_systems テーブル

インシデントで影響を受けたシステムの関連テーブル。

```sql
CREATE TABLE itscm.incident_affected_systems (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id         UUID NOT NULL REFERENCES itscm.active_incidents(id),
    system_id           UUID NOT NULL REFERENCES itscm.it_systems_bcp(id),
    impact_level        VARCHAR(20) NOT NULL
        CHECK (impact_level IN ('total_outage', 'partial_outage', 'degraded', 'minor')),
    rto_status          itscm.rto_status NOT NULL DEFAULT 'not_started',
    target_rto_minutes  INTEGER NOT NULL,
    actual_rto_minutes  INTEGER,
    recovery_start_at   TIMESTAMPTZ,
    recovery_end_at     TIMESTAMPTZ,
    current_step_number INTEGER DEFAULT 0,
    recovery_notes      TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (incident_id, system_id)
);

COMMENT ON TABLE itscm.incident_affected_systems IS 'インシデント影響システム関連テーブル';
```

### 3.10 exercise_rto_records テーブル

演習時のRTO記録テーブル。

```sql
CREATE TABLE itscm.exercise_rto_records (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id             UUID NOT NULL REFERENCES itscm.bcp_exercises(id),
    system_id               UUID NOT NULL REFERENCES itscm.it_systems_bcp(id),
    target_rto_minutes      INTEGER NOT NULL,
    actual_rto_minutes      INTEGER,
    rto_status              itscm.rto_status NOT NULL DEFAULT 'not_started',
    recovery_start_time     TIMESTAMPTZ,
    recovery_end_time       TIMESTAMPTZ,
    steps_completed         INTEGER NOT NULL DEFAULT 0,
    steps_total             INTEGER NOT NULL DEFAULT 0,
    bottleneck_description  TEXT,
    improvement_suggestions TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (exercise_id, system_id)
);

COMMENT ON TABLE itscm.exercise_rto_records IS '演習RTO記録テーブル。演習中の各システムRTO達成状況を記録';
```

### 3.11 escalation_logs テーブル

エスカレーション履歴を記録するテーブル。

```sql
CREATE TABLE itscm.escalation_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id         UUID NOT NULL REFERENCES itscm.active_incidents(id),
    escalation_level    INTEGER NOT NULL CHECK (escalation_level BETWEEN 1 AND 4),
    escalation_type     itscm.bcp_activation_level NOT NULL,
    channel             itscm.notification_channel NOT NULL,
    recipients          JSONB NOT NULL DEFAULT '[]'::jsonb,
    message_subject     VARCHAR(500),
    message_body        TEXT NOT NULL,
    sent_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at        TIMESTAMPTZ,
    delivery_status     itscm.delivery_status NOT NULL DEFAULT 'pending',
    failure_reason      TEXT,
    retry_count         INTEGER NOT NULL DEFAULT 0,
    max_retries         INTEGER NOT NULL DEFAULT 3,
    escalated_by        UUID NOT NULL REFERENCES itscm.users(id),
    acknowledged_by     UUID REFERENCES itscm.users(id),
    acknowledged_at     TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (sent_at);

COMMENT ON TABLE itscm.escalation_logs IS 'エスカレーションログテーブル。パーティション（月単位）';
```

### 3.12 audit_logs テーブル

監査ログテーブル。全操作を記録する。

```sql
CREATE TABLE itscm.audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES itscm.users(id),
    action          VARCHAR(50) NOT NULL,
    resource_type   VARCHAR(100) NOT NULL,
    resource_id     UUID,
    old_value       JSONB,
    new_value       JSONB,
    ip_address      INET,
    user_agent      TEXT,
    request_id      UUID,
    session_id      VARCHAR(255),
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

COMMENT ON TABLE itscm.audit_logs IS '監査ログテーブル。全操作を記録。パーティション（月単位）';
COMMENT ON COLUMN itscm.audit_logs.action IS '操作種別（CREATE/READ/UPDATE/DELETE/LOGIN/LOGOUT等）';
```

---

## 4. インデックス設計

### 4.1 主要インデックス一覧

```sql
-- users テーブル
CREATE INDEX idx_users_entra_id ON itscm.users(entra_id);
CREATE INDEX idx_users_email ON itscm.users(email);
CREATE INDEX idx_users_role ON itscm.users(role) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_department ON itscm.users(department) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_is_active ON itscm.users(is_active) WHERE deleted_at IS NULL;

-- it_systems_bcp テーブル
CREATE INDEX idx_systems_code ON itscm.it_systems_bcp(system_code);
CREATE INDEX idx_systems_criticality ON itscm.it_systems_bcp(criticality_tier) WHERE deleted_at IS NULL;
CREATE INDEX idx_systems_rto_status ON itscm.it_systems_bcp(current_rto_status) WHERE deleted_at IS NULL;
CREATE INDEX idx_systems_priority ON itscm.it_systems_bcp(recovery_priority) WHERE deleted_at IS NULL;
CREATE INDEX idx_systems_owner_dept ON itscm.it_systems_bcp(owner_department) WHERE deleted_at IS NULL;
CREATE INDEX idx_systems_owner_contact ON itscm.it_systems_bcp(owner_contact_id) WHERE deleted_at IS NULL;

-- bcp_scenarios テーブル
CREATE INDEX idx_scenarios_code ON itscm.bcp_scenarios(scenario_code);
CREATE INDEX idx_scenarios_type ON itscm.bcp_scenarios(scenario_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_scenarios_severity ON itscm.bcp_scenarios(severity_level) WHERE deleted_at IS NULL;
CREATE INDEX idx_scenarios_tags ON itscm.bcp_scenarios USING GIN(tags) WHERE deleted_at IS NULL;

-- bcp_exercises テーブル
CREATE INDEX idx_exercises_code ON itscm.bcp_exercises(exercise_code);
CREATE INDEX idx_exercises_status ON itscm.bcp_exercises(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_exercises_scheduled ON itscm.bcp_exercises(scheduled_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_exercises_scenario ON itscm.bcp_exercises(scenario_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_exercises_facilitator ON itscm.bcp_exercises(facilitator_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_exercises_type_status ON itscm.bcp_exercises(exercise_type, status) WHERE deleted_at IS NULL;

-- active_incidents テーブル
CREATE INDEX idx_incidents_code ON itscm.active_incidents(incident_code);
CREATE INDEX idx_incidents_severity ON itscm.active_incidents(severity);
CREATE INDEX idx_incidents_status ON itscm.active_incidents(status);
CREATE INDEX idx_incidents_bcp_level ON itscm.active_incidents(bcp_activation_level);
CREATE INDEX idx_incidents_detected ON itscm.active_incidents(detected_at DESC);
CREATE INDEX idx_incidents_commander ON itscm.active_incidents(incident_commander_id);
CREATE INDEX idx_incidents_active ON itscm.active_incidents(status, severity)
    WHERE status NOT IN ('closed');
CREATE INDEX idx_incidents_tags ON itscm.active_incidents USING GIN(tags);

-- recovery_procedures テーブル
CREATE INDEX idx_procedures_system ON itscm.recovery_procedures(system_id, step_number)
    WHERE deleted_at IS NULL AND is_active = TRUE;
CREATE INDEX idx_procedures_role ON itscm.recovery_procedures(responsible_role) WHERE deleted_at IS NULL;

-- vendor_contacts テーブル
CREATE INDEX idx_vendors_code ON itscm.vendor_contacts(vendor_code);
CREATE INDEX idx_vendors_type ON itscm.vendor_contacts(vendor_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_vendors_contract_end ON itscm.vendor_contacts(contract_end_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_vendors_related_systems ON itscm.vendor_contacts USING GIN(related_systems)
    WHERE deleted_at IS NULL;

-- incident_affected_systems テーブル
CREATE INDEX idx_affected_incident ON itscm.incident_affected_systems(incident_id);
CREATE INDEX idx_affected_system ON itscm.incident_affected_systems(system_id);
CREATE INDEX idx_affected_rto_status ON itscm.incident_affected_systems(rto_status);

-- exercise_rto_records テーブル
CREATE INDEX idx_rto_records_exercise ON itscm.exercise_rto_records(exercise_id);
CREATE INDEX idx_rto_records_system ON itscm.exercise_rto_records(system_id);
CREATE INDEX idx_rto_records_status ON itscm.exercise_rto_records(rto_status);

-- escalation_logs テーブル
CREATE INDEX idx_escalation_incident ON itscm.escalation_logs(incident_id);
CREATE INDEX idx_escalation_status ON itscm.escalation_logs(delivery_status);
CREATE INDEX idx_escalation_channel ON itscm.escalation_logs(channel);
CREATE INDEX idx_escalation_sent ON itscm.escalation_logs(sent_at DESC);

-- audit_logs テーブル
CREATE INDEX idx_audit_user ON itscm.audit_logs(user_id);
CREATE INDEX idx_audit_action ON itscm.audit_logs(action);
CREATE INDEX idx_audit_resource ON itscm.audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_timestamp ON itscm.audit_logs(timestamp DESC);
CREATE INDEX idx_audit_request ON itscm.audit_logs(request_id);
```

### 4.2 インデックス設計方針

| 方針 | 説明 |
|------|------|
| 部分インデックス | `WHERE deleted_at IS NULL`で論理削除済みレコードを除外し、インデックスサイズを削減 |
| 複合インデックス | 頻繁に同時に使用されるカラムの組み合わせに複合インデックスを設定 |
| GINインデックス | 配列型（tags, related_systems）にGINインデックスを使用 |
| 降順インデックス | 日時カラム（detected_at, timestamp等）は降順で最新データの検索を高速化 |
| カバリングインデックス | 必要に応じてINCLUDE句でカバリングインデックスを検討 |

---

## 5. パーティション戦略

### 5.1 パーティション対象テーブル

| テーブル | パーティション方式 | パーティションキー | 粒度 |
|---------|------------------|-------------------|------|
| active_incidents | RANGE | detected_at | 月単位 |
| escalation_logs | RANGE | sent_at | 月単位 |
| audit_logs | RANGE | timestamp | 月単位 |

### 5.2 パーティション作成DDL例

```sql
-- active_incidents パーティション作成（2026年度）
CREATE TABLE itscm.active_incidents_2026_04
    PARTITION OF itscm.active_incidents
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE TABLE itscm.active_incidents_2026_05
    PARTITION OF itscm.active_incidents
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

-- ... 以降も月単位で作成

-- escalation_logs パーティション（同様に月単位）
CREATE TABLE itscm.escalation_logs_2026_04
    PARTITION OF itscm.escalation_logs
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

-- audit_logs パーティション（同様に月単位）
CREATE TABLE itscm.audit_logs_2026_04
    PARTITION OF itscm.audit_logs
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
```

### 5.3 パーティション自動管理

```sql
-- pg_partmanを使用した自動パーティション管理
-- 3ヶ月先までのパーティションを事前作成
-- 13ヶ月以上前のパーティションはdetachしてアーカイブ

SELECT partman.create_parent(
    p_parent_table := 'itscm.active_incidents',
    p_control := 'detected_at',
    p_type := 'native',
    p_interval := '1 month',
    p_premake := 3
);

SELECT partman.create_parent(
    p_parent_table := 'itscm.escalation_logs',
    p_control := 'sent_at',
    p_type := 'native',
    p_interval := '1 month',
    p_premake := 3
);

SELECT partman.create_parent(
    p_parent_table := 'itscm.audit_logs',
    p_control := 'timestamp',
    p_type := 'native',
    p_interval := '1 month',
    p_premake := 3
);
```

### 5.4 アーカイブ戦略

| データ種別 | アクティブ保持期間 | アーカイブ先 | アーカイブ保持期間 |
|-----------|-----------------|------------|-----------------|
| active_incidents | 13ヶ月 | Azure Blob Storage (Cool) | 7年 |
| escalation_logs | 13ヶ月 | Azure Blob Storage (Cool) | 7年 |
| audit_logs | 13ヶ月 | Azure Blob Storage (Archive) | 7年 |

---

## 6. Geo冗長レプリケーション設計

### 6.1 レプリケーション構成

```
┌──────────────────────────────┐     ┌──────────────────────────────┐
│     East Japan (Primary)      │     │     West Japan (Standby)      │
│                              │     │                              │
│  ┌────────────────────────┐  │     │  ┌────────────────────────┐  │
│  │ PostgreSQL Primary     │  │     │  │ PostgreSQL Standby     │  │
│  │                        │──┼─────┼─▶│                        │  │
│  │ Read / Write           │  │ 同期 │  │ Read Only              │  │
│  │                        │  │ レプリカ│                        │  │
│  └────────────────────────┘  │     │  └────────────────────────┘  │
│                              │     │                              │
│  ┌────────────────────────┐  │     │  ┌────────────────────────┐  │
│  │ Read Replica           │  │     │  │ Read Replica           │  │
│  │ (参照分離用)            │  │     │  │ (フェイルオーバー後用)   │  │
│  └────────────────────────┘  │     │  └────────────────────────┘  │
└──────────────────────────────┘     └──────────────────────────────┘
```

### 6.2 レプリケーション設定

| 項目 | 設定値 |
|------|--------|
| レプリケーション方式 | 同期ストリーミングレプリケーション |
| レプリケーションスロット | 使用（WALの保証） |
| WAL保持期間 | 24時間 |
| max_wal_senders | 10 |
| synchronous_commit | remote_apply |
| recovery_target_timeline | latest |
| wal_level | logical（将来の拡張性） |

### 6.3 フェイルオーバーグループ設定

| 項目 | 設定値 |
|------|--------|
| フェイルオーバーモード | 自動 |
| 猶予期間 | 60秒 |
| フェイルオーバーポリシー | データ損失なし（同期レプリカのため） |
| DNS TTL | 30秒 |
| 読み取りエンドポイント | `<server>-read.postgres.database.azure.com` |
| 書き込みエンドポイント | `<server>.postgres.database.azure.com` |

### 6.4 接続文字列の管理

アプリケーションはフェイルオーバーグループのエンドポイントを使用し、個別サーバーへの直接接続は行わない。

```python
# 書き込み用接続
WRITE_DB_URL = "postgresql://user:pass@itscm-fg.postgres.database.azure.com:5432/itscm"

# 読み取り用接続
READ_DB_URL = "postgresql://user:pass@itscm-fg-read.postgres.database.azure.com:5432/itscm"
```

---

## 7. データライフサイクル管理

### 7.1 データ分類と保持ポリシー

| データ分類 | テーブル | オンライン保持 | アーカイブ保持 | 法的要件 |
|-----------|---------|-------------|-------------|---------|
| インシデント | active_incidents | 13ヶ月 | 7年 | ISO27001 |
| エスカレーション | escalation_logs | 13ヶ月 | 7年 | ISO27001 |
| 監査ログ | audit_logs | 13ヶ月 | 7年 | ISO27001/NIST CSF |
| システム情報 | it_systems_bcp | 永続 | - | ISO20000 |
| 演習記録 | bcp_exercises | 永続 | - | ISO20000 |
| シナリオ | bcp_scenarios | 永続 | - | - |
| 復旧手順 | recovery_procedures | 永続 | - | ISO20000 |
| ベンダー情報 | vendor_contacts | 永続 | - | - |
| ユーザー | users | 永続 | - | - |

### 7.2 バックアップ戦略

| バックアップ種別 | 頻度 | 保持期間 | 方式 |
|----------------|------|---------|------|
| 連続バックアップ（PITR） | リアルタイム | 35日 | Azure自動管理 |
| 日次フルバックアップ | 毎日 01:00 UTC | 35日 | Azure自動管理 |
| 週次論理バックアップ | 毎週日曜 03:00 UTC | 90日 | Celery定期タスク (pg_dump) |
| 月次論理バックアップ | 毎月1日 03:00 UTC | 1年 | Celery定期タスク (pg_dump) |

---

## 8. 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-03-27 | - | 初版作成 |
