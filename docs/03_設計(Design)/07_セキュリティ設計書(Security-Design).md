# セキュリティ設計書 (Security Design)

| 項目 | 内容 |
|------|------|
| 文書番号 | ITSCM-DES-SEC-007 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 分類 | 設計文書 |
| 準拠規格 | ISO20000 ITSCM / ISO27001 / NIST CSF RECOVER RC |

---

## 目次

1. [概要](#1-概要)
2. [認証設計](#2-認証設計)
3. [認可設計](#3-認可設計)
4. [通信暗号化](#4-通信暗号化)
5. [データ暗号化](#5-データ暗号化)
6. [監査ログ](#6-監査ログ)
7. [脆弱性対策](#7-脆弱性対策)
8. [シークレット管理](#8-シークレット管理)
9. [セキュリティ監視](#9-セキュリティ監視)
10. [インシデントレスポンス](#10-インシデントレスポンス)
11. [コンプライアンス対応](#11-コンプライアンス対応)
12. [変更履歴](#12-変更履歴)

---

## 1. 概要

### 1.1 セキュリティ設計方針

| 方針 | 説明 |
|------|------|
| ゼロトラスト | 全通信を検証。内部ネットワークも信頼しない |
| 多層防御 | WAF、ネットワーク、アプリケーション、データの各層で防御 |
| 最小権限 | 必要最小限のアクセス権のみ付与 |
| 暗号化 | 通信中・保存中のデータをすべて暗号化 |
| 監査可能性 | 全操作を記録し、追跡可能な状態を維持 |
| セキュリティ・バイ・デザイン | 設計段階からセキュリティを組み込む |

### 1.2 セキュリティ境界

```
                    ┌─ インターネット境界 ─────────────────────┐
                    │                                        │
                    │  Azure Front Door (WAF)                │
                    │  ・DDoS Protection                     │
                    │  ・OWASP Rule Set                      │
                    │  ・Bot Protection                      │
                    │  ・Rate Limiting                       │
                    │  ・Geo Filtering                       │
                    │                                        │
                    └──────────────┬─────────────────────────┘
                                   │
                    ┌─ アプリケーション境界 ──────────────────┐
                    │                                        │
                    │  Container Apps (mTLS)                 │
                    │  ・JWT認証                             │
                    │  ・RBAC認可                            │
                    │  ・入力バリデーション                    │
                    │  ・CORS                                │
                    │  ・CSP                                 │
                    │                                        │
                    └──────────────┬─────────────────────────┘
                                   │
                    ┌─ データ境界 ────────────────────────────┐
                    │                                        │
                    │  Private Endpoint (VNet内部のみ)       │
                    │  ・PostgreSQL (TLS + 暗号化保存)       │
                    │  ・Redis (TLS + 暗号化保存)            │
                    │  ・Blob Storage (暗号化保存)           │
                    │                                        │
                    └────────────────────────────────────────┘
```

---

## 2. 認証設計

### 2.1 Microsoft Entra ID SSO

| 項目 | 設定 |
|------|------|
| 認証プロトコル | OpenID Connect (OIDC) |
| 認可コードフロー | Authorization Code Flow with PKCE |
| テナント | シングルテナント（自組織のみ） |
| アプリ登録 | Azure Entra ID App Registration |
| リダイレクトURI | `https://itscm.example.com/auth/callback` |
| ログアウトURI | `https://itscm.example.com/login` |
| トークン構成 | ID Token + Access Token |

### 2.2 認証フロー詳細

```
ユーザー (ブラウザ)
  │
  │ ① https://itscm.example.com/ アクセス
  ▼
Next.js Frontend
  │
  │ ② 認証状態チェック → 未認証
  │ ③ PKCE code_verifier 生成 + code_challenge 計算
  │ ④ Entra ID認可エンドポイントへリダイレクト
  │    https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize
  │    ?client_id={client_id}
  │    &response_type=code
  │    &redirect_uri=https://itscm.example.com/auth/callback
  │    &scope=openid profile email
  │    &code_challenge={code_challenge}
  │    &code_challenge_method=S256
  │    &state={random_state}
  │    &nonce={random_nonce}
  ▼
Microsoft Entra ID
  │
  │ ⑤ ユーザー認証（MFA含む）
  │ ⑥ 認可コード発行 → コールバックURLにリダイレクト
  ▼
Next.js Frontend (/auth/callback)
  │
  │ ⑦ state検証
  │ ⑧ authorization_code + code_verifier をバックエンドに送信
  ▼
FastAPI Backend (/api/v1/auth/login)
  │
  │ ⑨ Entra IDトークンエンドポイントにToken Exchange
  │    POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
  │ ⑩ ID Token検証（署名、issuer、audience、nonce）
  │ ⑪ ユーザー情報取得/作成（DBに初回登録 or 更新）
  │ ⑫ 内部JWT Access Token生成 (15分有効)
  │ ⑬ Refresh Token生成 (7日有効、HttpOnly Cookie)
  ▼
フロントエンド
  │
  │ ⑭ Access TokenをメモリにState保存
  │ ⑮ ダッシュボードにリダイレクト
  ▼
認証完了
```

### 2.3 トークン管理

| トークン | 保存場所 | 有効期限 | リフレッシュ | 説明 |
|---------|---------|---------|------------|------|
| Access Token (JWT) | フロントエンドメモリ (Zustand) | 15分 | Refresh Tokenで再発行 | API呼び出し用。XSSでも取得困難 |
| Refresh Token | HttpOnly Secure SameSite Cookie | 7日 | 使用時にローテーション | セッション維持用。JSからアクセス不可 |
| CSRF Token | HTTPヘッダー (X-CSRF-Token) | リクエストごと | 自動 | CSRF対策 |

### 2.4 MFA（多要素認証）

| 項目 | 設定 |
|------|------|
| MFA要件 | Entra ID条件付きアクセスで強制 |
| 対象 | 全ユーザー |
| 方法 | Microsoft Authenticator / SMS / 電話 |
| 条件 | 新デバイス / 新ロケーション / リスク検知時は必ず要求 |

### 2.5 セッション管理

| 項目 | 値 |
|------|-----|
| セッションタイムアウト | 30分（アイドル状態） |
| 最大セッション時間 | 8時間 |
| 同時セッション | 最大3端末 |
| セッション無効化 | ログアウト / パスワード変更 / 管理者による強制無効化 |
| セッションストレージ | Redis (暗号化、TTL設定) |

---

## 3. 認可設計

### 3.1 RBAC（ロールベースアクセス制御）

#### ロール定義

| ロール | 説明 | 想定ユーザー数 |
|--------|------|-------------|
| system_admin | システム全体の管理権限 | 2-3名 |
| bcp_manager | BCP管理（シナリオ、演習、システム登録） | 5-10名 |
| incident_commander | インシデント対応指揮 | 10-15名 |
| exercise_facilitator | 演習のファシリテーション | 5-10名 |
| operator | インシデント登録・更新操作 | 20-30名 |
| viewer | 閲覧のみ | 50-100名 |

#### 権限の詳細定義

```python
# permissions.py

PERMISSIONS = {
    "system_admin": [
        "users:create", "users:read", "users:update", "users:delete",
        "systems:create", "systems:read", "systems:update", "systems:delete",
        "scenarios:create", "scenarios:read", "scenarios:update", "scenarios:delete",
        "exercises:create", "exercises:read", "exercises:update", "exercises:delete",
        "exercises:execute",
        "incidents:create", "incidents:read", "incidents:update", "incidents:delete",
        "incidents:activate_bcp", "incidents:escalate",
        "procedures:create", "procedures:read", "procedures:update", "procedures:delete",
        "vendors:create", "vendors:read", "vendors:update", "vendors:delete",
        "audit_logs:read", "audit_logs:export",
        "dashboard:read",
        "admin:access",
    ],
    "bcp_manager": [
        "systems:create", "systems:read", "systems:update", "systems:delete",
        "scenarios:create", "scenarios:read", "scenarios:update", "scenarios:delete",
        "exercises:create", "exercises:read", "exercises:update", "exercises:delete",
        "incidents:create", "incidents:read", "incidents:update",
        "incidents:activate_bcp", "incidents:escalate",
        "procedures:create", "procedures:read", "procedures:update", "procedures:delete",
        "vendors:create", "vendors:read", "vendors:update", "vendors:delete",
        "audit_logs:read",
        "dashboard:read",
        "users:read",
    ],
    "incident_commander": [
        "incidents:create", "incidents:read", "incidents:update",
        "incidents:activate_bcp", "incidents:escalate",
        "procedures:read", "procedures:update",
        "systems:read",
        "scenarios:read",
        "exercises:read",
        "vendors:read",
        "dashboard:read",
        "users:read",
    ],
    "exercise_facilitator": [
        "exercises:create", "exercises:read", "exercises:update",
        "exercises:execute",
        "scenarios:create", "scenarios:read", "scenarios:update",
        "systems:read",
        "incidents:read",
        "procedures:read",
        "vendors:read",
        "dashboard:read",
        "users:read",
    ],
    "operator": [
        "incidents:create", "incidents:read", "incidents:update",
        "incidents:escalate",
        "systems:read",
        "procedures:read",
        "vendors:read",
        "exercises:read",
        "scenarios:read",
        "dashboard:read",
        "users:read",
    ],
    "viewer": [
        "systems:read",
        "procedures:read",
        "vendors:read",
        "incidents:read",
        "exercises:read",
        "scenarios:read",
        "dashboard:read",
        "users:read",
    ],
}
```

### 3.2 認可ミドルウェア

```python
# middleware/authorization.py

from fastapi import Depends, HTTPException, status

async def require_permission(permission: str):
    async def _check(current_user: User = Depends(get_current_user)):
        user_permissions = PERMISSIONS.get(current_user.role, [])
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"権限が不足しています: {permission}"
            )
        return current_user
    return _check

# 使用例
@router.post("/incidents")
async def create_incident(
    body: CreateIncidentRequest,
    user: User = Depends(require_permission("incidents:create"))
):
    ...
```

### 3.3 データレベルアクセス制御

| ルール | 説明 |
|--------|------|
| 部署フィルタリング | viewerは自部署関連のシステムのみ閲覧可能（オプション設定） |
| インシデント機密レベル | 重大インシデントの詳細は incident_commander以上のみ閲覧可能 |
| 監査ログ | system_admin と bcp_manager のみ閲覧可能 |

---

## 4. 通信暗号化

### 4.1 TLS設定

| 通信経路 | TLSバージョン | 暗号スイート |
|---------|-------------|------------|
| ユーザー → Front Door | TLS 1.3 | TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256 |
| Front Door → Container Apps | TLS 1.2+ (mTLS) | ECDHE-RSA-AES256-GCM-SHA384 |
| Container Apps → PostgreSQL | TLS 1.2+ | ECDHE-RSA-AES256-GCM-SHA384 |
| Container Apps → Redis | TLS 1.2+ | ECDHE-RSA-AES256-GCM-SHA384 |
| Container Apps → External API | TLS 1.2+ | 接続先に依存 |
| Container Apps間 | mTLS (自動) | Container Apps環境が管理 |

### 4.2 証明書管理

| 証明書 | 種別 | 発行者 | 自動更新 |
|--------|------|--------|---------|
| Front Door (itscm.example.com) | Azure Managed Certificate | DigiCert | はい (自動) |
| Container Apps Ingress | Azure Managed Certificate | Let's Encrypt | はい (自動) |
| PostgreSQL SSL | Azure Managed | Azure | はい (自動) |
| Redis TLS | Azure Managed | Azure | はい (自動) |

### 4.3 HSTS設定

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

---

## 5. データ暗号化

### 5.1 保存データの暗号化

| データストア | 暗号化方式 | 鍵管理 |
|------------|-----------|--------|
| PostgreSQL | AES-256 (TDE) | Azure管理キー (デフォルト) |
| Redis | AES-256 | Azure管理キー |
| Blob Storage | AES-256 | Azure管理キー |
| Key Vault | HSM保護 | Azure管理キー |

### 5.2 アプリケーションレベル暗号化

機密性の高いデータに対して、Azure管理の暗号化に加えてアプリケーションレベルの暗号化を実施する。

| データ | 暗号化方式 | 鍵 |
|--------|-----------|-----|
| ユーザー電話番号 | AES-256-GCM | Key Vaultに保管するアプリケーション鍵 |
| ベンダー緊急連絡先 | AES-256-GCM | Key Vaultに保管するアプリケーション鍵 |
| SMS送信内容 | AES-256-GCM | Key Vaultに保管するアプリケーション鍵 |

```python
# crypto/encryption.py

from cryptography.fernet import Fernet
from azure.keyvault.secrets import SecretClient

class FieldEncryptor:
    def __init__(self, key_vault_url: str, secret_name: str):
        client = SecretClient(vault_url=key_vault_url, credential=DefaultAzureCredential())
        key = client.get_secret(secret_name).value
        self.fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.fernet.decrypt(ciphertext.encode()).decode()
```

### 5.3 PWAキャッシュデータの暗号化

| データ種別 | キャッシュ先 | 暗号化 |
|-----------|-----------|--------|
| BCP手順書（公開範囲データ） | Cache API | 不要（認証チェック済み） |
| 連絡先（機密） | IndexedDB | Web Crypto API (AES-GCM) |
| オフライン操作キュー | IndexedDB | Web Crypto API (AES-GCM) |
| 認証情報 | メモリ / HttpOnly Cookie | JWTは署名付き、Cookieは暗号化 |

```typescript
// crypto/indexedDbEncryption.ts

async function generateKey(): Promise<CryptoKey> {
    return await crypto.subtle.generateKey(
        { name: "AES-GCM", length: 256 },
        true,
        ["encrypt", "decrypt"]
    );
}

async function encryptData(key: CryptoKey, data: string): Promise<ArrayBuffer> {
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encrypted = await crypto.subtle.encrypt(
        { name: "AES-GCM", iv },
        key,
        new TextEncoder().encode(data)
    );
    // IV + encrypted data を結合して返却
    const result = new Uint8Array(iv.length + encrypted.byteLength);
    result.set(iv);
    result.set(new Uint8Array(encrypted), iv.length);
    return result.buffer;
}
```

---

## 6. 監査ログ

### 6.1 監査ログ記録対象

| カテゴリ | 記録イベント |
|---------|------------|
| 認証 | ログイン成功/失敗、ログアウト、トークンリフレッシュ、MFA実行 |
| ユーザー管理 | 作成、更新、削除、ロール変更 |
| ITシステム管理 | 作成、更新、削除、RTO変更 |
| インシデント | 作成、更新、ステータス変更、BCP発動、エスカレーション |
| 演習 | 作成、開始、インジェクション、終了、スコア入力 |
| シナリオ | 作成、更新、削除 |
| 復旧手順 | 作成、更新、削除、順序変更 |
| ベンダー | 作成、更新、削除 |
| データエクスポート | CSV/PDFエクスポート実行 |
| 設定変更 | 通知設定変更、システム設定変更 |
| API呼び出し | 全APIリクエスト（メソッド、パス、ステータスコード、レスポンス時間） |

### 6.2 監査ログフォーマット

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-03-27T14:30:00.000Z",
    "user_id": "660f9511-f3a0-52e5-b827-557766551111",
    "user_email": "yamada@example.com",
    "user_role": "bcp_manager",
    "action": "UPDATE",
    "resource_type": "incident",
    "resource_id": "d4e5f6a7-b8c9-0123-def0-123456789abc",
    "description": "インシデント INC-2026-0042 のステータスを 'detected' から 'bcp_activated' に変更",
    "old_value": {
        "status": "detected",
        "bcp_activation_level": "none"
    },
    "new_value": {
        "status": "bcp_activated",
        "bcp_activation_level": "p1_full_bcp"
    },
    "ip_address": "203.0.113.50",
    "user_agent": "Mozilla/5.0 ...",
    "request_id": "req-abc12345",
    "session_id": "sess-def67890",
    "request_method": "PATCH",
    "request_path": "/api/v1/incidents/d4e5f6a7/status",
    "response_status": 200,
    "response_time_ms": 45
}
```

### 6.3 監査ログ実装

```python
# middleware/audit.py

from fastapi import Request
import uuid
from datetime import datetime, timezone

class AuditMiddleware:
    async def __call__(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = datetime.now(timezone.utc)

        response = await call_next(request)

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        # 非同期で監査ログを記録（レスポンスをブロックしない）
        await audit_logger.log_async(
            request_id=request_id,
            user_id=getattr(request.state, 'user_id', None),
            action=self._map_method_to_action(request.method),
            resource_type=self._extract_resource_type(request.url.path),
            resource_id=self._extract_resource_id(request.url.path),
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent'),
            request_method=request.method,
            request_path=request.url.path,
            response_status=response.status_code,
            response_time_ms=elapsed,
        )

        response.headers['X-Request-ID'] = request_id
        return response
```

### 6.4 監査ログの保護

| 対策 | 説明 |
|------|------|
| 改竄防止 | 監査ログは追記のみ。UPDATE/DELETE不可 |
| アクセス制限 | system_admin と bcp_manager のみ閲覧可能 |
| 暗号化 | Azure Blob Storage (Archive tier) で暗号化保存 |
| 保持期間 | 7年間（ISO27001要件） |
| バックアップ | GRSによる地理冗長バックアップ |
| 整合性チェック | ハッシュチェーンによる改竄検知（オプション） |

---

## 7. 脆弱性対策

### 7.1 OWASP Top 10 対策

| 脆弱性 | 対策 |
|--------|------|
| A01 アクセス制御の不備 | RBAC実装、APIレベルの認可チェック、オブジェクトレベル認可 |
| A02 暗号化の失敗 | TLS 1.3強制、AES-256暗号化、安全な鍵管理 |
| A03 インジェクション | パラメータバインディング（SQLAlchemy ORM）、入力バリデーション（Pydantic/Zod）、WAF |
| A04 安全でない設計 | 脅威モデリング実施、セキュアコーディングガイドライン遵守 |
| A05 セキュリティ設定ミス | Terraform/IaCによる構成管理、セキュリティベースライン適用、不要ポート閉鎖 |
| A06 脆弱で古いコンポーネント | Dependabot自動更新、Snykスキャン、コンテナイメージスキャン（Trivy） |
| A07 認証の不備 | Entra ID SSO + MFA、パスワードレス推奨、セッション管理 |
| A08 データの完全性の不備 | CSRF対策（SameSite Cookie + CSRFトークン）、CI/CDパイプラインの署名検証 |
| A09 ログとモニタリングの失敗 | 包括的監査ログ、リアルタイムアラート、SIEM連携 |
| A10 SSRF | 外部URL検証、内部ネットワークへのリクエストブロック |

### 7.2 フロントエンドセキュリティ

#### Content Security Policy (CSP)

```
Content-Security-Policy:
    default-src 'self';
    script-src 'self' 'nonce-{random}';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https://graph.microsoft.com;
    font-src 'self';
    connect-src 'self' https://api.itscm.example.com wss://api.itscm.example.com https://login.microsoftonline.com;
    frame-ancestors 'none';
    form-action 'self';
    base-uri 'self';
    object-src 'none';
```

#### その他のセキュリティヘッダー

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
```

### 7.3 CORS設定

```python
# FastAPI CORS設定
origins = [
    "https://itscm.example.com",
    "https://www.itscm.example.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=3600,
)
```

### 7.4 入力バリデーション

```python
# バックエンド: Pydantic によるバリデーション
from pydantic import BaseModel, field_validator, constr
import re

class CreateIncidentRequest(BaseModel):
    incident_title: constr(min_length=1, max_length=500)
    incident_type: constr(pattern=r'^[a-z_]+$')
    description: constr(min_length=10, max_length=10000)
    severity: Literal['critical', 'high', 'medium', 'low']

    @field_validator('incident_title')
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        # HTMLタグの除去
        return re.sub(r'<[^>]*>', '', v).strip()
```

```typescript
// フロントエンド: Zod によるバリデーション
import { z } from 'zod';

const createIncidentSchema = z.object({
    incident_title: z.string().min(1).max(500).transform(val =>
        val.replace(/<[^>]*>/g, '').trim()
    ),
    incident_type: z.string().regex(/^[a-z_]+$/),
    description: z.string().min(10).max(10000),
    severity: z.enum(['critical', 'high', 'medium', 'low']),
});
```

### 7.5 コンテナセキュリティ

| 対策 | 実装 |
|------|------|
| ベースイメージ | 公式slim/distrolessイメージ使用 |
| rootユーザー禁止 | Dockerfileで非rootユーザー指定 |
| イメージスキャン | CI/CDでTrivy実行（CRITICAL/HIGH検出で失敗） |
| 依存関係スキャン | Snyk / GitHub Dependabot |
| イメージ署名 | Notation (Notary v2) によるイメージ署名 |
| ランタイム保護 | Azure Defender for Containers |

```dockerfile
# Dockerfileのセキュリティ対策例
FROM python:3.12-slim AS base

# 非rootユーザー作成
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app
COPY --chown=appuser:appgroup . .

RUN pip install --no-cache-dir -r requirements.txt

USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.6 セキュリティスキャン体制

| スキャン種別 | ツール | 頻度 | 対象 |
|------------|--------|------|------|
| SAST（静的解析） | CodeQL, Bandit (Python), ESLint Security | 全PR | ソースコード |
| DAST（動的解析） | OWASP ZAP | 週次 | ステージング環境 |
| SCA（依存関係スキャン） | Snyk, Dependabot | 全PR + 日次 | パッケージ依存関係 |
| コンテナスキャン | Trivy | 全PR + 日次 | Dockerイメージ |
| インフラスキャン | Checkov, tfsec | 全PR | Terraformコード |
| ペネトレーションテスト | 外部委託 | 年次 | 本番環境 |

---

## 8. シークレット管理

### 8.1 Azure Key Vault構成

| 項目 | 値 |
|------|-----|
| Key Vault名 | kv-itscm-prod-eastjp-001 |
| SKU | Premium (HSM保護) |
| アクセスポリシー | RBAC (Azure RBAC) |
| ネットワーク | Private Endpoint経由のみ |
| 論理削除 | 有効 (90日保持) |
| パージ保護 | 有効 |

### 8.2 シークレット一覧

| シークレット名 | 用途 | ローテーション |
|-------------|------|-------------|
| database-connection-string | PostgreSQL接続文字列 | 90日ごと |
| redis-connection-string | Redis接続文字列 | 90日ごと |
| entra-client-secret | Entra IDクライアントシークレット | 180日ごと |
| jwt-signing-key | JWT署名鍵 (RSA 2048) | 365日ごと |
| app-encryption-key | アプリケーション暗号化鍵 | 365日ごと |
| twilio-api-key | Twilio SMS API鍵 | 180日ごと |
| sendgrid-api-key | SendGrid Email API鍵 | 180日ごと |
| teams-webhook-url | Teams Webhook URL | 変更時 |
| itsm-api-key | ITSM連携API鍵 | 180日ごと |

### 8.3 シークレットローテーション

```
シークレット期限アラート（30日前）
  │
  │ ① Azure Monitor アラート発火
  │ ② 運用チームに通知
  ▼
シークレットローテーション実行
  │
  │ ③ 新シークレットをKey Vaultに追加（新バージョン）
  │ ④ Container Appsがシークレット参照を更新
  │ ⑤ 旧シークレットを一定期間（7日）並行運用
  │ ⑥ 旧シークレットを無効化
  ▼
完了
```

---

## 9. セキュリティ監視

### 9.1 リアルタイム監視

| 監視項目 | 検知条件 | アクション |
|---------|---------|----------|
| ブルートフォース攻撃 | 同一IPから10回連続ログイン失敗 | IPブロック + アラート |
| 不正アクセス | 権限のないリソースへのアクセス試行 | ログ記録 + アラート |
| 異常ログイン | 通常と異なるロケーション/時間帯 | MFA再要求 + アラート |
| API乱用 | レート制限超過 | 一時ブロック + アラート |
| データエクスフィルトレーション | 大量データのエクスポート | アラート + 承認要求 |
| SQLインジェクション試行 | WAFルール検知 | ブロック + アラート |
| XSS試行 | WAFルール検知 | ブロック + アラート |

### 9.2 Azure Defender統合

| サービス | 機能 |
|---------|------|
| Microsoft Defender for Cloud | セキュリティスコア、推奨事項 |
| Defender for Containers | コンテナランタイム脅威検知 |
| Defender for Key Vault | 不審なアクセスパターン検知 |
| Defender for Resource Manager | 不審な管理操作検知 |
| Defender for PostgreSQL | 不審なDBアクセス検知 |

---

## 10. インシデントレスポンス

### 10.1 セキュリティインシデント対応フロー

```
セキュリティイベント検知
  │
  │ ① Defender / WAF / 監査ログからの検知
  ▼
トリアージ（15分以内）
  │
  │ ② 重大度判定（Critical / High / Medium / Low）
  │ ③ 影響範囲の初期評価
  ▼
封じ込め（1時間以内）
  │
  │ ④ 必要に応じてアクセスブロック
  │ ⑤ 影響を受けたアカウントのセッション無効化
  │ ⑥ 関連システムの隔離判断
  ▼
調査（24時間以内）
  │
  │ ⑦ ログ分析（監査ログ、WAFログ、Azureアクティビティログ）
  │ ⑧ 影響範囲の確定
  │ ⑨ 根本原因の特定
  ▼
復旧
  │
  │ ⑩ 脆弱性の修正
  │ ⑪ パッチ適用
  │ ⑫ サービス復旧
  ▼
事後対応
  │
  │ ⑬ インシデントレポート作成
  │ ⑭ 再発防止策の実施
  │ ⑮ セキュリティポリシーの見直し
  ▼
完了
```

---

## 11. コンプライアンス対応

### 11.1 ISO27001対応

| 管理策 | 対応状況 |
|--------|---------|
| A.5 情報セキュリティ方針 | セキュリティ設計方針として策定 |
| A.6 情報セキュリティの組織 | RBAC + 責任分離 |
| A.7 人的資源のセキュリティ | Entra ID SSO + MFA |
| A.8 資産管理 | 全ITシステムのit_systems_bcpテーブルで管理 |
| A.9 アクセス制御 | RBAC + 最小権限 + 監査ログ |
| A.10 暗号化 | TLS 1.3 + AES-256 |
| A.12 運用セキュリティ | ログ監視 + 脆弱性管理 + バックアップ |
| A.16 インシデント管理 | 監査ログ + アラート + インシデントレスポンス |
| A.18 コンプライアンス | 監査ログ7年保持 + 定期レビュー |

### 11.2 NIST CSF RECOVER RC対応

| カテゴリ | 対応 |
|---------|------|
| RC.RP（復旧計画） | recovery_proceduresテーブルによる復旧手順管理 |
| RC.IM（改善） | 演習結果のaction_itemsによる継続的改善 |
| RC.CO（コミュニケーション） | エスカレーション機能による関係者への迅速な通知 |

---

## 12. 変更履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|-----------|------|--------|---------|
| 1.0.0 | 2026-03-27 | - | 初版作成 |
