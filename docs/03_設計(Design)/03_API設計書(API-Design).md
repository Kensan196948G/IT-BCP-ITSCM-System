# API設計書 (API Design)

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-DES-API-003 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 分類 | 設計文書 |
| 準拠規格 | ISO20000 ITSCM / ISO27001 / NIST CSF RECOVER RC |

---

## 目次

1. [概要](#1-概要)
2. [API共通仕様](#2-api共通仕様)
3. [認証・認可](#3-認証認可)
4. [REST API一覧](#4-rest-api一覧)
5. [REST APIエンドポイント詳細](#5-rest-apiエンドポイント詳細)
6. [WebSocket API](#6-websocket-api)
7. [エラーハンドリング](#7-エラーハンドリング)
8. [レート制限](#8-レート制限)
9. [変更履歴](#9-変更履歴)

---

## 1. 概要

### 1.1 基本情報

| 項目 | 値 |
|------|-----|
| ベースURL | `https://api.itscm.example.com/api/v1` |
| プロトコル | HTTPS (TLS 1.3) |
| 認証方式 | Bearer Token (JWT) / Microsoft Entra ID |
| データ形式 | JSON (application/json) |
| 文字コード | UTF-8 |
| APIバージョニング | URLパスベース (`/api/v1/`) |
| OpenAPI仕様 | OpenAPI 3.1 |

### 1.2 設計原則

- RESTful設計に準拠（リソース指向、適切なHTTPメソッド使用）
- ページネーション: カーソルベースを標準採用（大量データのパフォーマンス確保）
- フィルタリング: クエリパラメータによるフィルタリング
- ソート: `sort_by`、`sort_order`パラメータによるソート
- 部分レスポンス: `fields`パラメータによるフィールド選択
- HATEOAS: リンク情報を含むレスポンス

---

## 2. API共通仕様

### 2.1 リクエストヘッダー

| ヘッダー | 必須 | 説明 | 例 |
|---------|------|------|-----|
| Authorization | YES | Bearer トークン | `Bearer eyJhbGci...` |
| Content-Type | YES (POST/PUT/PATCH) | コンテンツタイプ | `application/json` |
| Accept | NO | レスポンス形式 | `application/json` |
| X-Request-ID | NO | リクエスト追跡ID | `550e8400-e29b-41d4-a716-446655440000` |
| Accept-Language | NO | 言語設定 | `ja` |

### 2.2 レスポンスヘッダー

| ヘッダー | 説明 | 例 |
|---------|------|-----|
| X-Request-ID | リクエスト追跡ID | `550e8400-e29b-41d4-a716-446655440000` |
| X-RateLimit-Limit | レート制限上限 | `100` |
| X-RateLimit-Remaining | 残りリクエスト数 | `95` |
| X-RateLimit-Reset | リセット時刻（Unix timestamp） | `1711500000` |

### 2.3 ページネーション共通レスポンス

```json
{
    "data": [...],
    "pagination": {
        "total_count": 150,
        "page_size": 20,
        "has_next": true,
        "has_prev": false,
        "next_cursor": "eyJpZCI6IjEyMzQ1In0=",
        "prev_cursor": null
    },
    "links": {
        "self": "/api/v1/resource?cursor=abc&limit=20",
        "next": "/api/v1/resource?cursor=eyJpZCI6IjEyMzQ1In0=&limit=20",
        "prev": null
    }
}
```

### 2.4 共通クエリパラメータ

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| cursor | string | null | ページネーションカーソル |
| limit | integer | 20 | 1ページあたりの件数（最大100） |
| sort_by | string | created_at | ソートカラム |
| sort_order | string | desc | ソート順（asc/desc） |
| fields | string | null | 取得フィールド（カンマ区切り） |
| search | string | null | 全文検索クエリ |

---

## 3. 認証・認可

### 3.1 認証フロー

```
ユーザー
  │
  │ ① Microsoft Entra IDへリダイレクト
  ▼
Entra ID ログイン画面
  │
  │ ② 認証成功 → Authorization Code発行
  ▼
フロントエンド
  │
  │ ③ Authorization Codeをバックエンドに送信
  ▼
FastAPI Backend
  │
  │ ④ Entra IDに対してToken Exchange
  │ ⑤ IDトークン検証 + ユーザー情報取得
  │ ⑥ 内部JWT発行（アクセストークン + リフレッシュトークン）
  ▼
フロントエンド（JWT保持）
```

### 3.2 トークン仕様

| 項目 | アクセストークン | リフレッシュトークン |
|------|----------------|-------------------|
| 有効期限 | 15分 | 7日 |
| 形式 | JWT (RS256) | Opaque Token |
| 保存場所 | メモリ（フロントエンド） | HttpOnly Secure Cookie |
| リフレッシュ | リフレッシュトークンで再発行 | 使用時にローテーション |

### 3.3 JWTペイロード

```json
{
    "sub": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "山田太郎",
    "role": "bcp_manager",
    "department": "IT戦略部",
    "permissions": ["incidents:read", "incidents:write", "exercises:manage"],
    "iat": 1711500000,
    "exp": 1711500900,
    "iss": "itscm-api",
    "aud": "itscm-frontend"
}
```

### 3.4 RBAC権限マトリクス

| リソース | system_admin | bcp_manager | incident_commander | exercise_facilitator | operator | viewer |
|---------|-------------|-------------|-------------------|---------------------|----------|--------|
| ユーザー管理 | CRUD | R | R | R | R | R |
| ITシステム | CRUD | CRUD | R | R | R | R |
| シナリオ | CRUD | CRUD | R | CRUD | R | R |
| 演習 | CRUD | CRUD | R | CRUD | R | R |
| インシデント | CRUD | CRUD | CRUD | R | CRU | R |
| 復旧手順 | CRUD | CRUD | RU | R | R | R |
| ベンダー | CRUD | CRUD | R | R | R | R |
| ダッシュボード | R | R | R | R | R | R |
| 監査ログ | R | R | - | - | - | - |
| エスカレーション | CRUD | CRU | CRU | R | CRU | R |

---

## 4. REST API一覧

### 4.1 認証系

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| POST | /api/v1/auth/login | ログイン（Entra ID Code Exchange） | 不要 |
| POST | /api/v1/auth/refresh | トークンリフレッシュ | リフレッシュトークン |
| POST | /api/v1/auth/logout | ログアウト | 必要 |
| GET | /api/v1/auth/me | 自分の情報取得 | 必要 |

### 4.2 ユーザー管理

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/users | ユーザー一覧取得 | 全ロール |
| GET | /api/v1/users/{id} | ユーザー詳細取得 | 全ロール |
| POST | /api/v1/users | ユーザー作成 | system_admin |
| PUT | /api/v1/users/{id} | ユーザー更新 | system_admin |
| DELETE | /api/v1/users/{id} | ユーザー論理削除 | system_admin |
| PATCH | /api/v1/users/{id}/preferences | 通知設定更新 | 本人 / system_admin |

### 4.3 ITシステム管理

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/systems | ITシステム一覧取得 | 全ロール |
| GET | /api/v1/systems/{id} | ITシステム詳細取得 | 全ロール |
| POST | /api/v1/systems | ITシステム登録 | system_admin, bcp_manager |
| PUT | /api/v1/systems/{id} | ITシステム更新 | system_admin, bcp_manager |
| DELETE | /api/v1/systems/{id} | ITシステム論理削除 | system_admin, bcp_manager |
| GET | /api/v1/systems/{id}/procedures | 復旧手順一覧取得 | 全ロール |
| GET | /api/v1/systems/{id}/dependencies | 依存関係取得 | 全ロール |
| GET | /api/v1/systems/{id}/incidents | 関連インシデント取得 | 全ロール |
| GET | /api/v1/systems/{id}/rto-history | RTO履歴取得 | 全ロール |

### 4.4 BCPシナリオ

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/scenarios | シナリオ一覧取得 | 全ロール |
| GET | /api/v1/scenarios/{id} | シナリオ詳細取得 | 全ロール |
| POST | /api/v1/scenarios | シナリオ作成 | system_admin, bcp_manager, exercise_facilitator |
| PUT | /api/v1/scenarios/{id} | シナリオ更新 | system_admin, bcp_manager, exercise_facilitator |
| DELETE | /api/v1/scenarios/{id} | シナリオ論理削除 | system_admin, bcp_manager |
| POST | /api/v1/scenarios/{id}/duplicate | シナリオ複製 | system_admin, bcp_manager, exercise_facilitator |

### 4.5 BCP演習

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/exercises | 演習一覧取得 | 全ロール |
| GET | /api/v1/exercises/{id} | 演習詳細取得 | 全ロール |
| POST | /api/v1/exercises | 演習作成 | system_admin, bcp_manager, exercise_facilitator |
| PUT | /api/v1/exercises/{id} | 演習更新 | system_admin, bcp_manager, exercise_facilitator |
| DELETE | /api/v1/exercises/{id} | 演習論理削除 | system_admin, bcp_manager |
| POST | /api/v1/exercises/{id}/start | 演習開始 | exercise_facilitator |
| POST | /api/v1/exercises/{id}/inject | シナリオインジェクション実行 | exercise_facilitator |
| POST | /api/v1/exercises/{id}/end | 演習終了 | exercise_facilitator |
| GET | /api/v1/exercises/{id}/rto-records | RTO記録取得 | 全ロール |
| PUT | /api/v1/exercises/{id}/rto-records/{record_id} | RTO記録更新 | exercise_facilitator, operator |
| GET | /api/v1/exercises/{id}/report | 演習レポート取得 | 全ロール |

### 4.6 インシデント管理

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/incidents | インシデント一覧取得 | 全ロール |
| GET | /api/v1/incidents/{id} | インシデント詳細取得 | 全ロール |
| POST | /api/v1/incidents | インシデント作成 | system_admin, bcp_manager, incident_commander, operator |
| PUT | /api/v1/incidents/{id} | インシデント更新 | system_admin, bcp_manager, incident_commander, operator |
| PATCH | /api/v1/incidents/{id}/status | ステータス更新 | system_admin, bcp_manager, incident_commander, operator |
| POST | /api/v1/incidents/{id}/activate-bcp | BCP発動 | system_admin, bcp_manager, incident_commander |
| POST | /api/v1/incidents/{id}/escalate | エスカレーション実行 | system_admin, bcp_manager, incident_commander, operator |
| GET | /api/v1/incidents/{id}/affected-systems | 影響システム一覧 | 全ロール |
| POST | /api/v1/incidents/{id}/affected-systems | 影響システム追加 | incident_commander, operator |
| PUT | /api/v1/incidents/{id}/affected-systems/{system_id} | 影響システム状態更新 | incident_commander, operator |
| GET | /api/v1/incidents/{id}/escalation-logs | エスカレーション履歴 | 全ロール（viewer除く） |
| GET | /api/v1/incidents/{id}/timeline | タイムライン取得 | 全ロール |
| POST | /api/v1/incidents/{id}/timeline | タイムラインエントリ追加 | incident_commander, operator |

### 4.7 復旧手順

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/procedures | 復旧手順一覧取得 | 全ロール |
| GET | /api/v1/procedures/{id} | 復旧手順詳細取得 | 全ロール |
| POST | /api/v1/procedures | 復旧手順作成 | system_admin, bcp_manager |
| PUT | /api/v1/procedures/{id} | 復旧手順更新 | system_admin, bcp_manager, incident_commander |
| DELETE | /api/v1/procedures/{id} | 復旧手順論理削除 | system_admin, bcp_manager |
| POST | /api/v1/procedures/reorder | 手順順序変更 | system_admin, bcp_manager |

### 4.8 ベンダー管理

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/vendors | ベンダー一覧取得 | 全ロール |
| GET | /api/v1/vendors/{id} | ベンダー詳細取得 | 全ロール |
| POST | /api/v1/vendors | ベンダー作成 | system_admin, bcp_manager |
| PUT | /api/v1/vendors/{id} | ベンダー更新 | system_admin, bcp_manager |
| DELETE | /api/v1/vendors/{id} | ベンダー論理削除 | system_admin, bcp_manager |

### 4.9 RTOダッシュボード

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/dashboard/rto-overview | RTO概要取得 | 全ロール |
| GET | /api/v1/dashboard/rto-by-tier | ティア別RTO状態 | 全ロール |
| GET | /api/v1/dashboard/active-incidents-summary | アクティブインシデント概要 | 全ロール |
| GET | /api/v1/dashboard/exercise-statistics | 演習統計 | 全ロール |
| GET | /api/v1/dashboard/system-health | システムヘルス概要 | 全ロール |
| GET | /api/v1/dashboard/compliance-status | コンプライアンス状態 | system_admin, bcp_manager |

### 4.10 監査ログ

| メソッド | パス | 説明 | 権限 |
|---------|------|------|------|
| GET | /api/v1/audit-logs | 監査ログ一覧取得 | system_admin, bcp_manager |
| GET | /api/v1/audit-logs/{id} | 監査ログ詳細取得 | system_admin, bcp_manager |
| GET | /api/v1/audit-logs/export | 監査ログエクスポート | system_admin |

### 4.11 ヘルスチェック

| メソッド | パス | 説明 | 認証 |
|---------|------|------|------|
| GET | /health | ヘルスチェック（簡易） | 不要 |
| GET | /health/detailed | ヘルスチェック（詳細） | system_admin |
| GET | /health/ready | レディネスプローブ | 不要 |
| GET | /health/live | ライブネスプローブ | 不要 |

---

## 5. REST APIエンドポイント詳細

### 5.1 POST /api/v1/auth/login - ログイン

**説明**: Microsoft Entra IDの認可コードを使用してログインし、JWTトークンを取得する。

**リクエスト**:

```json
{
    "authorization_code": "0.AXYA...",
    "redirect_uri": "https://itscm.example.com/auth/callback",
    "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
}
```

**レスポンス (200 OK)**:

```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "yamada@example.com",
        "display_name": "山田太郎",
        "role": "bcp_manager",
        "department": "IT戦略部"
    }
}
```

### 5.2 GET /api/v1/systems - ITシステム一覧取得

**説明**: BCP管理対象のITシステム一覧を取得する。

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| cursor | string | NO | ページネーションカーソル |
| limit | integer | NO | 件数（デフォルト20、最大100） |
| criticality_tier | string | NO | 重要度フィルタ |
| rto_status | string | NO | RTO状態フィルタ |
| owner_department | string | NO | 所管部署フィルタ |
| search | string | NO | 検索クエリ（システム名、コード） |
| sort_by | string | NO | ソートカラム（デフォルト: recovery_priority） |
| sort_order | string | NO | ソート順（デフォルト: asc） |

**レスポンス (200 OK)**:

```json
{
    "data": [
        {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "system_code": "SYS-001",
            "system_name": "基幹業務システム",
            "criticality_tier": "tier_1_mission_critical",
            "rto_target_minutes": 60,
            "rpo_target_minutes": 0,
            "current_rto_status": "on_track",
            "owner_department": "業務推進部",
            "recovery_priority": 1,
            "last_tested_at": "2026-02-15T10:00:00Z",
            "created_at": "2026-01-10T09:00:00Z",
            "updated_at": "2026-03-20T14:30:00Z",
            "links": {
                "self": "/api/v1/systems/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "procedures": "/api/v1/systems/a1b2c3d4-e5f6-7890-abcd-ef1234567890/procedures",
                "dependencies": "/api/v1/systems/a1b2c3d4-e5f6-7890-abcd-ef1234567890/dependencies"
            }
        }
    ],
    "pagination": {
        "total_count": 45,
        "page_size": 20,
        "has_next": true,
        "has_prev": false,
        "next_cursor": "eyJpZCI6ImExYjJjM2Q0In0=",
        "prev_cursor": null
    }
}
```

### 5.3 POST /api/v1/systems - ITシステム登録

**説明**: 新しいBCP管理対象ITシステムを登録する。

**リクエスト**:

```json
{
    "system_code": "SYS-046",
    "system_name": "顧客管理システム（CRM）",
    "system_description": "顧客情報および営業活動の管理システム。Salesforceベース。",
    "criticality_tier": "tier_2_business_critical",
    "rto_target_minutes": 120,
    "rpo_target_minutes": 15,
    "owner_department": "営業推進部",
    "owner_contact_id": "550e8400-e29b-41d4-a716-446655440000",
    "technical_contact_id": "660f9511-f3a0-52e5-b827-557766551111",
    "recovery_priority": 15,
    "infrastructure_type": "SaaS",
    "hosting_location": "Salesforce Cloud (Tokyo)",
    "dependencies": [
        {
            "system_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "dependency_type": "required",
            "description": "認証連携（SSO）"
        }
    ],
    "documentation_url": "https://wiki.example.com/crm-bcp"
}
```

**レスポンス (201 Created)**:

```json
{
    "data": {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "system_code": "SYS-046",
        "system_name": "顧客管理システム（CRM）",
        "criticality_tier": "tier_2_business_critical",
        "rto_target_minutes": 120,
        "rpo_target_minutes": 15,
        "current_rto_status": "not_started",
        "owner_department": "営業推進部",
        "recovery_priority": 15,
        "created_at": "2026-03-27T10:00:00Z",
        "links": {
            "self": "/api/v1/systems/b2c3d4e5-f6a7-8901-bcde-f12345678901"
        }
    }
}
```

### 5.4 POST /api/v1/incidents - インシデント作成

**説明**: 新しいインシデントを登録する。

**リクエスト**:

```json
{
    "incident_title": "東日本データセンター電源障害",
    "incident_type": "infrastructure_failure",
    "description": "東日本DCの電源系統に障害が発生。UPSに切替後、発電機の起動に失敗。影響範囲調査中。",
    "severity": "critical",
    "affected_systems": [
        {
            "system_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "impact_level": "total_outage"
        },
        {
            "system_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
            "impact_level": "partial_outage"
        }
    ],
    "tags": ["datacenter", "power", "east-japan"]
}
```

**レスポンス (201 Created)**:

```json
{
    "data": {
        "id": "d4e5f6a7-b8c9-0123-def0-123456789abc",
        "incident_code": "INC-2026-0042",
        "incident_title": "東日本データセンター電源障害",
        "incident_type": "infrastructure_failure",
        "severity": "critical",
        "status": "detected",
        "bcp_activation_level": "none",
        "reported_by": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "display_name": "山田太郎"
        },
        "detected_at": "2026-03-27T14:30:00Z",
        "affected_systems": [
            {
                "system_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "system_name": "基幹業務システム",
                "impact_level": "total_outage",
                "rto_status": "not_started",
                "target_rto_minutes": 60
            }
        ],
        "created_at": "2026-03-27T14:30:00Z",
        "links": {
            "self": "/api/v1/incidents/d4e5f6a7-b8c9-0123-def0-123456789abc",
            "affected_systems": "/api/v1/incidents/d4e5f6a7-b8c9-0123-def0-123456789abc/affected-systems",
            "timeline": "/api/v1/incidents/d4e5f6a7-b8c9-0123-def0-123456789abc/timeline"
        }
    }
}
```

### 5.5 POST /api/v1/incidents/{id}/activate-bcp - BCP発動

**説明**: インシデントに対してBCPを発動する。発動レベルに応じたエスカレーションが自動実行される。

**リクエスト**:

```json
{
    "activation_level": "p1_full_bcp",
    "reason": "東日本DC電源障害により主要3システムが停止。全社BCP発動が必要。",
    "incident_commander_id": "770a0622-a4b1-63f6-c938-668877662222",
    "notification_channels": ["teams", "sms", "email"],
    "additional_message": "全BCPチームメンバーは直ちにTeams会議に参加してください。"
}
```

**レスポンス (200 OK)**:

```json
{
    "data": {
        "id": "d4e5f6a7-b8c9-0123-def0-123456789abc",
        "incident_code": "INC-2026-0042",
        "status": "bcp_activated",
        "bcp_activation_level": "p1_full_bcp",
        "bcp_activated_at": "2026-03-27T14:35:00Z",
        "incident_commander": {
            "id": "770a0622-a4b1-63f6-c938-668877662222",
            "display_name": "佐藤花子"
        },
        "escalation_results": [
            {
                "channel": "teams",
                "status": "sent",
                "recipients_count": 25
            },
            {
                "channel": "sms",
                "status": "sent",
                "recipients_count": 12
            },
            {
                "channel": "email",
                "status": "sent",
                "recipients_count": 50
            }
        ]
    }
}
```

### 5.6 POST /api/v1/exercises/{id}/start - 演習開始

**説明**: BCP演習を開始する。テーブルトップ演習のシナリオインジェクションエンジンが起動する。

**リクエスト**:

```json
{
    "actual_participants": [
        {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "role_in_exercise": "incident_commander"
        },
        {
            "user_id": "660f9511-f3a0-52e5-b827-557766551111",
            "role_in_exercise": "communication_lead"
        }
    ],
    "notes": "年度末テーブルトップ演習開始"
}
```

**レスポンス (200 OK)**:

```json
{
    "data": {
        "id": "e5f6a7b8-c9d0-1234-ef01-23456789abcd",
        "exercise_code": "EX-2026-008",
        "status": "in_progress",
        "actual_start_at": "2026-03-27T10:00:00Z",
        "scenario": {
            "id": "f6a7b8c9-d0e1-2345-f012-3456789abcde",
            "scenario_name": "大規模サイバー攻撃シナリオ",
            "total_injection_steps": 5
        },
        "current_injection_step": 0,
        "rto_records": [
            {
                "system_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "system_name": "基幹業務システム",
                "target_rto_minutes": 60,
                "rto_status": "not_started"
            }
        ],
        "message": "演習を開始しました。最初のインジェクションを実行してください。"
    }
}
```

### 5.7 POST /api/v1/exercises/{id}/inject - シナリオインジェクション

**説明**: テーブルトップ演習中にシナリオインジェクション（状況変化の注入）を実行する。

**リクエスト**:

```json
{
    "step_number": 1,
    "facilitator_notes": "参加者の初動対応を観察する。5分以内の検知報告を期待。",
    "additional_context": "実際のシステム監視画面のスクリーンショットを投影"
}
```

**レスポンス (200 OK)**:

```json
{
    "data": {
        "exercise_id": "e5f6a7b8-c9d0-1234-ef01-23456789abcd",
        "current_injection_step": 1,
        "injection": {
            "step": 1,
            "title": "初期障害検知",
            "description": "データセンターの電源系統に異常を検知。UPSに切替。",
            "inject_type": "notification",
            "expected_response_minutes": 5,
            "injected_at": "2026-03-27T10:05:00Z"
        },
        "next_step": {
            "step": 2,
            "title": "障害拡大",
            "recommended_delay_minutes": 15
        }
    }
}
```

### 5.8 GET /api/v1/dashboard/rto-overview - RTOダッシュボード概要

**説明**: RTOダッシュボードの概要データを取得する。

**レスポンス (200 OK)**:

```json
{
    "data": {
        "timestamp": "2026-03-27T15:00:00Z",
        "summary": {
            "total_systems": 45,
            "on_track": 38,
            "at_risk": 3,
            "overdue": 1,
            "recovered": 2,
            "not_started": 1
        },
        "active_incidents": {
            "total": 1,
            "critical": 1,
            "high": 0,
            "bcp_activated": true,
            "bcp_level": "p1_full_bcp"
        },
        "by_tier": [
            {
                "tier": "tier_1_mission_critical",
                "total": 8,
                "on_track": 6,
                "at_risk": 1,
                "overdue": 1,
                "recovered": 0,
                "not_started": 0
            },
            {
                "tier": "tier_2_business_critical",
                "total": 12,
                "on_track": 10,
                "at_risk": 1,
                "overdue": 0,
                "recovered": 1,
                "not_started": 0
            },
            {
                "tier": "tier_3_business_operational",
                "total": 15,
                "on_track": 14,
                "at_risk": 1,
                "overdue": 0,
                "recovered": 0,
                "not_started": 0
            },
            {
                "tier": "tier_4_administrative",
                "total": 10,
                "on_track": 8,
                "at_risk": 0,
                "overdue": 0,
                "recovered": 1,
                "not_started": 1
            }
        ],
        "worst_rto_systems": [
            {
                "system_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "system_name": "基幹業務システム",
                "rto_target_minutes": 60,
                "elapsed_minutes": 75,
                "rto_status": "overdue",
                "gap_percentage": 25.0
            }
        ]
    }
}
```

### 5.9 POST /api/v1/incidents/{id}/escalate - エスカレーション実行

**説明**: インシデントに対してエスカレーションを実行する。

**リクエスト**:

```json
{
    "escalation_level": 2,
    "channels": ["teams", "sms", "email"],
    "recipients": {
        "roles": ["bcp_manager", "incident_commander"],
        "additional_user_ids": ["880b1733-b5c2-74g7-d049-779988773333"],
        "vendor_ids": ["990c2844-c6d3-85h8-e150-880099884444"]
    },
    "message": "BCP発動レベル2に伴い、全BCPチームメンバーの参集を要請します。",
    "urgency": "immediate"
}
```

**レスポンス (200 OK)**:

```json
{
    "data": {
        "escalation_id": "aabbccdd-1122-3344-5566-778899001122",
        "incident_id": "d4e5f6a7-b8c9-0123-def0-123456789abc",
        "escalation_level": 2,
        "results": [
            {
                "channel": "teams",
                "status": "sent",
                "recipients_count": 15,
                "sent_at": "2026-03-27T14:40:00Z"
            },
            {
                "channel": "sms",
                "status": "sent",
                "recipients_count": 8,
                "sent_at": "2026-03-27T14:40:02Z"
            },
            {
                "channel": "email",
                "status": "sent",
                "recipients_count": 30,
                "sent_at": "2026-03-27T14:40:03Z"
            }
        ],
        "total_recipients": 53,
        "message": "エスカレーション（レベル2）を送信しました。"
    }
}
```

### 5.10 GET /health - ヘルスチェック

**説明**: システムのヘルスチェック。Front Doorのヘルスプローブに使用。

**レスポンス (200 OK)**:

```json
{
    "status": "healthy",
    "timestamp": "2026-03-27T15:00:00Z",
    "version": "1.0.0"
}
```

**GET /health/detailed レスポンス (200 OK)**:

```json
{
    "status": "healthy",
    "timestamp": "2026-03-27T15:00:00Z",
    "version": "1.0.0",
    "components": {
        "database": {
            "status": "healthy",
            "latency_ms": 5,
            "connection_pool": {
                "active": 3,
                "idle": 7,
                "max": 20
            }
        },
        "redis": {
            "status": "healthy",
            "latency_ms": 1,
            "memory_usage_mb": 256
        },
        "celery": {
            "status": "healthy",
            "active_workers": 2,
            "queued_tasks": 0
        },
        "external_services": {
            "teams_api": {"status": "healthy", "latency_ms": 120},
            "twilio_api": {"status": "healthy", "latency_ms": 85},
            "sendgrid_api": {"status": "healthy", "latency_ms": 95},
            "itsm_api": {"status": "healthy", "latency_ms": 200}
        }
    }
}
```

---

## 6. WebSocket API

### 6.1 概要

WebSocket APIは、RTOダッシュボードのリアルタイム更新およびインシデント状態のライブ通知に使用する。

| 項目 | 値 |
|------|-----|
| エンドポイント | `wss://api.itscm.example.com/ws/v1` |
| プロトコル | WebSocket over TLS 1.3 |
| 認証 | 接続時にJWTトークンをクエリパラメータまたは初回メッセージで送信 |
| ハートビート | 30秒間隔のping/pong |
| 再接続 | 指数バックオフ（1s, 2s, 4s, 8s, 最大30s） |

### 6.2 接続

```
wss://api.itscm.example.com/ws/v1?token=eyJhbGci...
```

**接続成功メッセージ**:

```json
{
    "type": "connection_established",
    "connection_id": "ws-conn-12345",
    "timestamp": "2026-03-27T15:00:00Z",
    "message": "WebSocket接続が確立されました"
}
```

### 6.3 チャネル購読

クライアントは特定のチャネルを購読してリアルタイム更新を受信する。

**購読リクエスト**:

```json
{
    "type": "subscribe",
    "channels": [
        "rto_dashboard",
        "incident_updates",
        "exercise_live"
    ]
}
```

**購読確認**:

```json
{
    "type": "subscription_confirmed",
    "channels": ["rto_dashboard", "incident_updates", "exercise_live"],
    "timestamp": "2026-03-27T15:00:01Z"
}
```

### 6.4 チャネル一覧

| チャネル | 説明 | 更新頻度 |
|---------|------|---------|
| `rto_dashboard` | RTOステータスのリアルタイム更新 | 10秒間隔 / イベント発生時 |
| `incident_updates` | インシデント状態変更通知 | イベント発生時 |
| `incident_{id}` | 特定インシデントの詳細更新 | イベント発生時 |
| `exercise_live` | アクティブ演習のライブ更新 | イベント発生時 |
| `exercise_{id}` | 特定演習の詳細更新 | イベント発生時 |
| `escalation_alerts` | エスカレーション通知 | イベント発生時 |
| `system_health` | システムヘルス状態変更 | 30秒間隔 |

### 6.5 メッセージ形式

#### 6.5.1 RTO更新メッセージ

```json
{
    "type": "rto_update",
    "channel": "rto_dashboard",
    "timestamp": "2026-03-27T15:01:00Z",
    "data": {
        "system_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "system_name": "基幹業務システム",
        "previous_status": "at_risk",
        "current_status": "overdue",
        "rto_target_minutes": 60,
        "elapsed_minutes": 65,
        "incident_id": "d4e5f6a7-b8c9-0123-def0-123456789abc"
    }
}
```

#### 6.5.2 インシデント更新メッセージ

```json
{
    "type": "incident_update",
    "channel": "incident_updates",
    "timestamp": "2026-03-27T15:02:00Z",
    "data": {
        "incident_id": "d4e5f6a7-b8c9-0123-def0-123456789abc",
        "incident_code": "INC-2026-0042",
        "event": "status_changed",
        "previous_status": "detected",
        "current_status": "bcp_activated",
        "bcp_activation_level": "p1_full_bcp",
        "updated_by": {
            "id": "770a0622-a4b1-63f6-c938-668877662222",
            "display_name": "佐藤花子"
        }
    }
}
```

#### 6.5.3 エスカレーション通知メッセージ

```json
{
    "type": "escalation_alert",
    "channel": "escalation_alerts",
    "timestamp": "2026-03-27T15:03:00Z",
    "data": {
        "incident_id": "d4e5f6a7-b8c9-0123-def0-123456789abc",
        "incident_code": "INC-2026-0042",
        "escalation_level": 2,
        "message": "BCP発動レベル2: 全BCPチームメンバーの参集を要請します",
        "channels_used": ["teams", "sms", "email"],
        "requires_acknowledgment": true
    }
}
```

#### 6.5.4 演習ライブ更新メッセージ

```json
{
    "type": "exercise_update",
    "channel": "exercise_live",
    "timestamp": "2026-03-27T10:05:00Z",
    "data": {
        "exercise_id": "e5f6a7b8-c9d0-1234-ef01-23456789abcd",
        "exercise_code": "EX-2026-008",
        "event": "injection_executed",
        "injection_step": 1,
        "injection_title": "初期障害検知",
        "rto_records_updated": [
            {
                "system_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "rto_status": "on_track",
                "elapsed_minutes": 5
            }
        ]
    }
}
```

### 6.6 エラーメッセージ

```json
{
    "type": "error",
    "code": "UNAUTHORIZED",
    "message": "認証トークンが無効または期限切れです",
    "timestamp": "2026-03-27T15:00:00Z"
}
```

---

## 7. エラーハンドリング

### 7.1 エラーレスポンス形式

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "入力値が不正です",
        "details": [
            {
                "field": "rto_target_minutes",
                "message": "1以上の整数を指定してください",
                "value": -5
            }
        ],
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2026-03-27T15:00:00Z"
    }
}
```

### 7.2 エラーコード一覧

| HTTPステータス | エラーコード | 説明 |
|--------------|------------|------|
| 400 | VALIDATION_ERROR | バリデーションエラー |
| 400 | INVALID_REQUEST | リクエスト形式不正 |
| 401 | UNAUTHORIZED | 認証エラー |
| 401 | TOKEN_EXPIRED | トークン期限切れ |
| 403 | FORBIDDEN | 権限不足 |
| 404 | NOT_FOUND | リソースが見つからない |
| 409 | CONFLICT | 競合（同時更新等） |
| 422 | UNPROCESSABLE_ENTITY | 処理不能（ビジネスロジックエラー） |
| 429 | RATE_LIMITED | レート制限超過 |
| 500 | INTERNAL_ERROR | 内部サーバーエラー |
| 502 | BAD_GATEWAY | バックエンド通信エラー |
| 503 | SERVICE_UNAVAILABLE | サービス一時停止 |

---

## 8. レート制限

### 8.1 レート制限設定

| エンドポイントカテゴリ | 制限値 | ウィンドウ | 備考 |
|---------------------|--------|-----------|------|
| 認証系 | 10 req | 1分 | ブルートフォース対策 |
| 一般API（GET） | 100 req | 1分 | ユーザーごと |
| 一般API（POST/PUT/DELETE） | 30 req | 1分 | ユーザーごと |
| ダッシュボードAPI | 60 req | 1分 | ポーリング対応 |
| WebSocket メッセージ | 30 msg | 1分 | 接続ごと |
| エクスポートAPI | 5 req | 10分 | 負荷制限 |

### 8.2 レート制限超過レスポンス

```json
{
    "error": {
        "code": "RATE_LIMITED",
        "message": "リクエスト制限を超過しました。しばらく待ってから再試行してください。",
        "retry_after_seconds": 30,
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2026-03-27T15:00:00Z"
    }
}
```

---

## 9. 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-03-27 | - | 初版作成 |
