# コーディング規約 (Coding Standards)

| 項目 | 内容 |
|------|------|
| 文書番号 | DEV-CODE-002 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 作成者 | IT-BCP-ITSCM開発チーム |
| 分類 | 開発ガイド |
| 対象システム | IT事業継続管理システム (IT-BCP-ITSCM-System) |

---

## 1. 概要

本文書は、IT事業継続管理システムの開発におけるコーディング規約を定義する。全開発メンバーがこの規約に従うことで、コードの一貫性・可読性・保守性を確保し、品質の高いソフトウェアを効率的に開発することを目的とする。

### 1.1 適用範囲

- バックエンド（Python / FastAPI）
- フロントエンド（TypeScript / Next.js）
- データベース（PostgreSQL SQL）
- インフラ定義（Terraform / Docker）
- CI/CD 設定（GitHub Actions）
- Git 運用（コミットメッセージ、PR）

### 1.2 規約の優先順位

1. セキュリティ（脆弱性を生まないコード）
2. 可読性（チームメンバーが理解しやすいコード）
3. 保守性（変更が容易なコード）
4. パフォーマンス（効率的なコード）

---

## 2. Python コーディング規約

### 2.1 基本スタイル

| 項目 | 規約 |
|------|------|
| スタイルガイド | PEP 8 準拠 |
| フォーマッタ | Black（line-length: 88） |
| インポート整理 | isort（Black 互換プロファイル） |
| 型チェック | mypy（strict モード） |
| リンター | flake8 + flake8-bugbear |
| 最大行長 | 88文字（Black デフォルト） |
| インデント | スペース4つ |
| 文字コード | UTF-8 |

### 2.2 Black 設定

`pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ['py312']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.eggs
  | \.git
  | \.mypy_cache
  | \.venv
  | build
  | dist
  | alembic/versions
)/
'''
```

### 2.3 isort 設定

```toml
[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88
known_first_party = ["app"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]
```

### 2.4 mypy 設定

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
show_error_codes = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### 2.5 型アノテーション規約

全ての関数・メソッドに型アノテーションを付与すること。

```python
# 良い例
from typing import Optional
from datetime import datetime
from uuid import UUID

async def get_bcp_plan(
    plan_id: UUID,
    include_details: bool = False,
) -> Optional[BCPPlanResponse]:
    """BCP計画を取得する。

    Args:
        plan_id: BCP計画の一意識別子
        include_details: 詳細情報を含めるかどうか

    Returns:
        BCP計画レスポンスオブジェクト。存在しない場合はNone。

    Raises:
        PermissionDeniedError: アクセス権限がない場合
    """
    ...


# 悪い例（型アノテーションなし）
async def get_bcp_plan(plan_id, include_details=False):
    ...
```

### 2.6 FastAPI 規約

#### 2.6.1 ルーター定義

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.bcp_plan import BCPPlanCreate, BCPPlanResponse, BCPPlanUpdate
from app.services.bcp_plan import BCPPlanService
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/bcp-plans",
    tags=["BCP計画管理"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{plan_id}",
    response_model=BCPPlanResponse,
    summary="BCP計画の取得",
    description="指定されたIDのBCP計画を取得する。",
)
async def get_bcp_plan(
    plan_id: UUID,
    service: BCPPlanService = Depends(),
    current_user: User = Depends(get_current_user),
) -> BCPPlanResponse:
    plan = await service.get_by_id(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BCP計画 {plan_id} が見つかりません",
        )
    return plan
```

#### 2.6.2 Pydantic スキーマ

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from enum import Enum


class BCPPlanStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ACTIVE = "active"
    ARCHIVED = "archived"


class BCPPlanBase(BaseModel):
    """BCP計画の基本スキーマ"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="BCP計画のタイトル",
        examples=["東日本リージョン障害対応計画"],
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="BCP計画の説明",
    )
    target_rto_minutes: int = Field(
        ...,
        ge=0,
        le=525600,  # 365日
        description="目標RTO（分）",
    )
    target_rpo_minutes: int = Field(
        ...,
        ge=0,
        le=525600,
        description="目標RPO（分）",
    )


class BCPPlanCreate(BCPPlanBase):
    """BCP計画の作成スキーマ"""
    pass


class BCPPlanResponse(BCPPlanBase):
    """BCP計画のレスポンススキーマ"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: BCPPlanStatus
    created_at: datetime
    updated_at: datetime
    created_by: UUID
```

#### 2.6.3 サービス層

```python
from app.repositories.bcp_plan import BCPPlanRepository
from app.schemas.bcp_plan import BCPPlanCreate, BCPPlanUpdate


class BCPPlanService:
    """BCP計画のビジネスロジックを管理するサービス"""

    def __init__(
        self,
        repository: BCPPlanRepository = Depends(),
    ) -> None:
        self._repository = repository

    async def create(
        self,
        data: BCPPlanCreate,
        user_id: UUID,
    ) -> BCPPlan:
        """BCP計画を作成する"""
        ...
```

### 2.7 例外処理規約

```python
# カスタム例外クラスの定義
class ITBCPBaseException(Exception):
    """IT-BCP-ITSCMシステムの基底例外クラス"""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class ResourceNotFoundError(ITBCPBaseException):
    """リソースが見つからない場合の例外"""
    def __init__(self, resource_type: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource_type} (ID: {resource_id}) が見つかりません",
            code="RESOURCE_NOT_FOUND",
        )


class PermissionDeniedError(ITBCPBaseException):
    """権限不足の場合の例外"""
    def __init__(self, action: str) -> None:
        super().__init__(
            message=f"操作 '{action}' を実行する権限がありません",
            code="PERMISSION_DENIED",
        )
```

### 2.8 ロギング規約

```python
import structlog

logger = structlog.get_logger(__name__)

# 良い例（構造化ログ）
logger.info(
    "BCP計画を作成しました",
    plan_id=str(plan.id),
    title=plan.title,
    created_by=str(user.id),
)

# 悪い例（非構造化ログ）
logger.info(f"BCP計画 {plan.id} を作成しました")
```

### 2.9 テストコード規約

```python
import pytest
from httpx import AsyncClient
from uuid import uuid4

# テストクラスはTestプレフィックス、テスト関数はtest_プレフィックス
class TestBCPPlanAPI:
    """BCP計画APIのテスト"""

    @pytest.mark.asyncio
    async def test_create_bcp_plan_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """BCP計画を正常に作成できること"""
        # Arrange
        payload = {
            "title": "テスト計画",
            "description": "テスト用BCP計画",
            "target_rto_minutes": 60,
            "target_rpo_minutes": 30,
        }

        # Act
        response = await client.post(
            "/api/v1/bcp-plans",
            json=payload,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "テスト計画"
        assert data["target_rto_minutes"] == 60
```

---

## 3. TypeScript / Next.js コーディング規約

### 3.1 基本スタイル

| 項目 | 規約 |
|------|------|
| 言語 | TypeScript（strict モード） |
| フレームワーク | Next.js 14（App Router） |
| フォーマッタ | Prettier |
| リンター | ESLint（next/core-web-vitals） |
| スタイリング | Tailwind CSS |
| インデント | スペース2つ |
| セミコロン | あり |
| クォート | シングルクォート |
| 末尾カンマ | あり（trailing comma: all） |

### 3.2 ESLint 設定

`.eslintrc.json`:

```json
{
  "extends": [
    "next/core-web-vitals",
    "next/typescript",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/strict-boolean-expressions": "warn",
    "no-console": ["warn", { "allow": ["warn", "error"] }],
    "prefer-const": "error",
    "no-var": "error",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",
    "import/order": [
      "error",
      {
        "groups": [
          "builtin",
          "external",
          "internal",
          "parent",
          "sibling",
          "index"
        ],
        "newlines-between": "always",
        "alphabetize": { "order": "asc" }
      }
    ]
  }
}
```

### 3.3 Prettier 設定

`.prettierrc`:

```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf",
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

### 3.4 tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/lib/*": ["./src/lib/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/types/*": ["./src/types/*"],
      "@/services/*": ["./src/services/*"]
    }
  }
}
```

### 3.5 ディレクトリ構成規約

```
frontend/src/
  app/                           # Next.js App Router
    (auth)/                      # 認証グループ
      login/page.tsx
      layout.tsx
    (dashboard)/                 # ダッシュボードグループ
      dashboard/page.tsx
      bcp-plans/
        page.tsx                 # 一覧ページ
        [id]/page.tsx            # 詳細ページ
        new/page.tsx             # 作成ページ
      drills/
        page.tsx
        [id]/page.tsx
      incidents/
        page.tsx
        [id]/page.tsx
      bia/
        page.tsx
      rto-dashboard/
        page.tsx
      layout.tsx
    api/                         # API Routes
    layout.tsx                   # ルートレイアウト
    globals.css
  components/
    ui/                          # 汎用UIコンポーネント
      button.tsx
      card.tsx
      dialog.tsx
      data-table.tsx
    features/                    # 機能別コンポーネント
      bcp-plans/
        bcp-plan-form.tsx
        bcp-plan-list.tsx
        bcp-plan-detail.tsx
      drills/
      incidents/
      bia/
      rto-dashboard/
    layouts/                     # レイアウトコンポーネント
      header.tsx
      sidebar.tsx
      footer.tsx
  hooks/                         # カスタムフック
    use-bcp-plans.ts
    use-auth.ts
    use-websocket.ts
    use-offline.ts
  lib/                           # ユーティリティ
    api-client.ts
    utils.ts
    constants.ts
    validators.ts
  services/                      # API サービス
    bcp-plan.service.ts
    drill.service.ts
    incident.service.ts
  types/                         # 型定義
    bcp-plan.ts
    drill.ts
    incident.ts
    api.ts
  stores/                        # 状態管理
    auth.store.ts
    notification.store.ts
```

### 3.6 コンポーネント命名規則

| 種別 | 命名規則 | 例 |
|------|---------|-----|
| ページコンポーネント | PascalCase（page.tsx内） | `BCPPlanListPage` |
| UIコンポーネント | PascalCase | `Button`, `DataTable`, `Card` |
| 機能コンポーネント | PascalCase（機能名プレフィックス） | `BCPPlanForm`, `DrillScheduleCalendar` |
| カスタムフック | camelCase（useプレフィックス） | `useBCPPlans`, `useAuth` |
| ユーティリティ関数 | camelCase | `formatDate`, `calculateRTO` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RTO_MINUTES`, `API_BASE_URL` |
| 型/インターフェース | PascalCase | `BCPPlan`, `DrillResponse` |
| Enumの値 | PascalCase | `BCPPlanStatus.Active` |

### 3.7 コンポーネント実装規約

```tsx
'use client';

import { useState, useCallback } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useBCPPlans } from '@/hooks/use-bcp-plans';
import type { BCPPlan } from '@/types/bcp-plan';

/**
 * BCP計画一覧コンポーネント
 *
 * BCP計画の一覧表示、検索、フィルタリング機能を提供する。
 */

interface BCPPlanListProps {
  /** 初期フィルター条件 */
  initialFilter?: BCPPlanFilter;
  /** 計画選択時のコールバック */
  onSelect?: (plan: BCPPlan) => void;
}

export function BCPPlanList({
  initialFilter,
  onSelect,
}: BCPPlanListProps): React.ReactElement {
  const [filter, setFilter] = useState(initialFilter);
  const { data: plans, isLoading, error } = useBCPPlans(filter);

  const handleSelect = useCallback(
    (plan: BCPPlan): void => {
      onSelect?.(plan);
    },
    [onSelect],
  );

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return <ErrorDisplay error={error} />;
  }

  return (
    <div className="space-y-4">
      <BCPPlanFilterBar filter={filter} onChange={setFilter} />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {plans?.map((plan) => (
          <Card
            key={plan.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => handleSelect(plan)}
          >
            <BCPPlanCardContent plan={plan} />
          </Card>
        ))}
      </div>
    </div>
  );
}
```

### 3.8 Server Components / Client Components の使い分け

| 種別 | 使用場面 | 指示子 |
|------|---------|--------|
| Server Component | データフェッチ、SEO重要ページ、静的コンテンツ | デフォルト（指示子不要） |
| Client Component | インタラクティブUI、状態管理、ブラウザAPI使用 | `'use client'` |

```tsx
// Server Component（デフォルト）
// app/(dashboard)/bcp-plans/page.tsx
import { BCPPlanList } from '@/components/features/bcp-plans/bcp-plan-list';
import { getBCPPlans } from '@/services/bcp-plan.service';

export default async function BCPPlansPage(): Promise<React.ReactElement> {
  const plans = await getBCPPlans();

  return (
    <main className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">BCP計画一覧</h1>
      <BCPPlanList initialData={plans} />
    </main>
  );
}
```

### 3.9 API クライアント規約

```typescript
// lib/api-client.ts
import type { ApiResponse, ApiError } from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getAccessToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new ApiClientError(error.message, response.status, error.code);
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ... put, patch, delete メソッド
}

export const apiClient = new ApiClient();
```

### 3.10 XSS対策規約

フロントエンドでのユーザー入力表示時は、Reactのデフォルトエスケープ機構に依存すること。生のHTMLを直接挿入する手法（innerHTML等）は原則として禁止する。やむを得ず使用する場合は、DOMPurify等のサニタイザーライブラリで必ず無害化処理を行い、コードレビューでセキュリティチームの承認を得ること。

```typescript
// 良い例: Reactのデフォルトエスケープを使用
function SafeContent({ text }: { text: string }): React.ReactElement {
  return <p>{text}</p>; // 自動でエスケープされる
}

// やむを得ない場合: DOMPurifyで無害化
import DOMPurify from 'dompurify';

function SanitizedHTML({ html }: { html: string }): React.ReactElement {
  const sanitized = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}
```

### 3.11 PWA / オフライン対応規約

```typescript
// Service Worker の登録は next.config.js で next-pwa を使用
// オフラインデータは IndexedDB に保存

// hooks/use-offline.ts
import { useEffect, useState } from 'react';

export function useOffline(): {
  isOffline: boolean;
  pendingActions: number;
} {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [pendingActions, setPendingActions] = useState(0);

  useEffect(() => {
    const handleOnline = (): void => setIsOffline(false);
    const handleOffline = (): void => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return { isOffline, pendingActions };
}
```

---

## 4. SQL / データベース規約

### 4.1 テーブル命名規約

| 項目 | 規約 | 例 |
|------|------|-----|
| テーブル名 | snake_case（複数形） | `bcp_plans`, `drill_sessions` |
| カラム名 | snake_case | `target_rto_minutes`, `created_at` |
| 主キー | `id`（UUID v4） | `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` |
| 外部キー | `{参照テーブル単数形}_id` | `bcp_plan_id`, `user_id` |
| タイムスタンプ | `created_at`, `updated_at` | - |
| 論理削除 | `deleted_at` | `deleted_at TIMESTAMPTZ NULL` |
| ステータス | `status` | `status VARCHAR(20) NOT NULL DEFAULT 'draft'` |
| ブーリアン | `is_` プレフィックス | `is_active`, `is_template` |

### 4.2 インデックス命名規約

| 種別 | 命名パターン | 例 |
|------|------------|-----|
| 主キー | `pk_{table}` | `pk_bcp_plans` |
| ユニーク | `uq_{table}_{column(s)}` | `uq_users_email` |
| インデックス | `ix_{table}_{column(s)}` | `ix_bcp_plans_status` |
| 外部キー | `fk_{table}_{ref_table}` | `fk_bcp_plans_users` |
| 複合インデックス | `ix_{table}_{col1}_{col2}` | `ix_drill_sessions_plan_id_status` |

### 4.3 SQLAlchemy モデル規約

```python
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid


class BCPPlan(BaseModel):
    """BCP計画テーブル"""
    __tablename__ = "bcp_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    target_rto_minutes = Column(Integer, nullable=False)
    target_rpo_minutes = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    metadata_json = Column(JSONB, nullable=True)

    # リレーション
    created_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_by = relationship("User", back_populates="bcp_plans")
    procedures = relationship("BCPProcedure", back_populates="plan", lazy="selectin")
```

### 4.4 マイグレーション規約

- マイグレーションファイルには、必ず `upgrade()` と `downgrade()` の両方を実装すること
- データマイグレーション（DML）とスキーママイグレーション（DDL）は分離すること
- 破壊的変更（カラム削除等）は段階的に実施すること（deprecated -> remove）
- 本番適用前にステージング環境で検証を必須とすること

---

## 5. Git 規約

### 5.1 コミットメッセージ規約（Conventional Commits）

#### 5.1.1 フォーマット

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 5.1.2 Type 一覧

| Type | 説明 | 例 |
|------|------|-----|
| `feat` | 新機能 | `feat(bcp-plan): BCP計画のPDF出力機能を追加` |
| `fix` | バグ修正 | `fix(drill): 訓練スケジュールの日付計算エラーを修正` |
| `docs` | ドキュメント | `docs(api): Swagger UIの説明文を更新` |
| `style` | フォーマット | `style(backend): Black適用によるコード整形` |
| `refactor` | リファクタリング | `refactor(auth): 認証ミドルウェアの構造改善` |
| `perf` | パフォーマンス改善 | `perf(dashboard): RTOダッシュボードのクエリ最適化` |
| `test` | テスト | `test(bcp-plan): BCP計画作成のE2Eテスト追加` |
| `build` | ビルド設定 | `build(docker): マルチステージビルドの最適化` |
| `ci` | CI 設定 | `ci(github): セキュリティスキャンワークフロー追加` |
| `chore` | その他 | `chore(deps): 依存パッケージの更新` |
| `revert` | 取り消し | `revert: feat(bcp-plan)のPDF出力機能を取り消し` |

#### 5.1.3 Scope 一覧

| Scope | 対象 |
|-------|------|
| `bcp-plan` | BCP計画管理機能 |
| `drill` | 訓練管理機能 |
| `incident` | インシデント対応機能 |
| `bia` | ビジネスインパクト分析 |
| `rto-dashboard` | RTOダッシュボード |
| `auth` | 認証・認可 |
| `notification` | 通知機能 |
| `api` | API全般 |
| `ui` | UI共通 |
| `db` | データベース |
| `infra` | インフラ |
| `ci` | CI/CD |
| `deps` | 依存関係 |

#### 5.1.4 コミットメッセージの例

```
feat(bcp-plan): BCP計画のバージョン管理機能を実装

- 計画の版数管理と履歴追跡機能を追加
- 差分表示による変更内容の可視化
- 過去バージョンへのロールバック機能

Refs: #123
```

```
fix(rto-dashboard): WebSocket接続のメモリリークを修正

RTOダッシュボードのWebSocket接続がコンポーネントのアンマウント時に
正しくクリーンアップされておらず、メモリリークが発生していた問題を修正。

useEffectのクリーンアップ関数でWebSocket接続を明示的に閉じるようにした。

Fixes: #456
```

### 5.2 PR テンプレート

`.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## 概要
<!-- この PR で何を変更したか簡潔に記述 -->

## 変更種別
- [ ] 新機能 (feat)
- [ ] バグ修正 (fix)
- [ ] リファクタリング (refactor)
- [ ] パフォーマンス改善 (perf)
- [ ] テスト (test)
- [ ] ドキュメント (docs)
- [ ] CI/CD (ci)
- [ ] その他 (chore)

## 関連Issue
<!-- Closes #xxx -->

## 変更内容
<!-- 変更の詳細を記述 -->

## テスト方法
<!-- テストの実行方法を記述 -->
- [ ] ユニットテスト追加/更新
- [ ] 結合テスト追加/更新
- [ ] E2Eテスト追加/更新
- [ ] 手動テスト実施

## チェックリスト
- [ ] コーディング規約に準拠している
- [ ] 型アノテーションを付与している（Python/TypeScript）
- [ ] エラーハンドリングを実装している
- [ ] ログ出力を適切に追加している
- [ ] セキュリティ考慮事項を確認した
- [ ] マイグレーションファイルを作成した（DB変更がある場合）
- [ ] API ドキュメントを更新した（API変更がある場合）
- [ ] 環境変数の追加を .env.example に反映した

## スクリーンショット（UI変更がある場合）
<!-- スクリーンショットを添付 -->

## レビューポイント
<!-- レビュアーに特に見てほしいポイントを記述 -->
```

---

## 6. セキュリティコーディング規約

### 6.1 入力バリデーション

- 全ての外部入力は Pydantic スキーマで検証すること
- SQL インジェクション対策として、SQLAlchemy ORM または パラメータバインディングを必ず使用すること
- XSS 対策として、フロントエンドでのユーザー入力表示時は React のデフォルトエスケープに依存し、生HTML挿入は原則禁止とする（3.10節参照）

### 6.2 認証・認可

- JWT トークンの有効期限は 30 分以内とすること
- リフレッシュトークンはローテーションを実施すること
- API エンドポイントには必ず認可チェックを実装すること
- ロールベースアクセス制御（RBAC）を厳守すること

### 6.3 機密情報の取り扱い

- パスワードは bcrypt でハッシュ化すること
- API キー、シークレットはソースコードに含めないこと
- `.env` ファイルは `.gitignore` に必ず含めること
- ログに機密情報（パスワード、トークン、個人情報）を出力しないこと

### 6.4 依存関係のセキュリティ

- `pip-audit` / `npm audit` を定期的に実行すること
- 脆弱性が報告されたパッケージは速やかに更新すること
- CI パイプラインにセキュリティスキャンを組み込むこと

---

## 7. ドキュメント規約

### 7.1 Python Docstring

Google スタイルの docstring を使用する。

```python
def calculate_rto_achievement(
    target_rto: int,
    actual_rto: int,
) -> float:
    """RTOの達成率を計算する。

    目標RTOに対する実績RTOの達成率をパーセンテージで返す。
    100%以上の場合は目標未達を意味する。

    Args:
        target_rto: 目標RTO（分）
        actual_rto: 実績RTO（分）

    Returns:
        RTO達成率（パーセンテージ）。例: 80.0 は目標の80%の時間で復旧

    Raises:
        ValueError: target_rto が0以下の場合

    Examples:
        >>> calculate_rto_achievement(60, 48)
        80.0
        >>> calculate_rto_achievement(60, 72)
        120.0
    """
    if target_rto <= 0:
        raise ValueError("target_rto は正の値である必要があります")
    return (actual_rto / target_rto) * 100
```

### 7.2 TypeScript JSDoc

```typescript
/**
 * RTOの達成率を計算する
 *
 * @param targetRto - 目標RTO（分）
 * @param actualRto - 実績RTO（分）
 * @returns RTO達成率（パーセンテージ）
 * @throws {RangeError} targetRto が0以下の場合
 *
 * @example
 * ```ts
 * const rate = calculateRtoAchievement(60, 48);
 * console.log(rate); // 80.0
 * ```
 */
export function calculateRtoAchievement(
  targetRto: number,
  actualRto: number,
): number {
  if (targetRto <= 0) {
    throw new RangeError('targetRto は正の値である必要があります');
  }
  return (actualRto / targetRto) * 100;
}
```

---

## 8. コードレビュー基準

### 8.1 レビューチェックリスト

| カテゴリ | チェック項目 |
|---------|------------|
| 機能 | 要件を正しく満たしているか |
| 機能 | エッジケースが考慮されているか |
| 品質 | コーディング規約に準拠しているか |
| 品質 | 型アノテーションが適切か |
| 品質 | エラーハンドリングが適切か |
| 品質 | ログ出力が適切か |
| テスト | テストコードが追加されているか |
| テスト | テストカバレッジが十分か（80%以上） |
| セキュリティ | 入力バリデーションが適切か |
| セキュリティ | 認可チェックが実装されているか |
| セキュリティ | 機密情報がハードコードされていないか |
| パフォーマンス | N+1 クエリが発生していないか |
| パフォーマンス | 不要なリレンダリングがないか |

### 8.2 レビュー承認基準

- 最低 1 名の承認が必要（critical な変更は 2 名）
- CI パイプラインが全て成功していること
- コンフリクトが解決されていること
- 指摘事項が全て対応済みであること

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-03-27 | 初版作成 | IT-BCP-ITSCM開発チーム |
