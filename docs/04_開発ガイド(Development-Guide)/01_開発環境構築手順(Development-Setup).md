# 開発環境構築手順 (Development Setup)

| 項目 | 内容 |
|------|------|
| 文書番号 | DEV-SETUP-001 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 作成者 | IT-BCP-ITSCM開発チーム |
| 分類 | 開発ガイド |
| 対象システム | IT事業継続管理システム (IT-BCP-ITSCM-System) |

---

## 1. 概要

本文書は、IT事業継続管理システム（IT-BCP-ITSCM-System）の開発環境を構築するための手順を詳細に記述したものである。新規参画メンバーがこの手順に従うことで、ローカル開発環境を迅速かつ正確にセットアップできることを目的とする。

### 1.1 システム構成概要

| レイヤー | 技術スタック |
|----------|-------------|
| フロントエンド | Next.js 14 / TypeScript / Tailwind CSS / PWA |
| バックエンド | Python FastAPI / SQLAlchemy / Alembic |
| データベース | PostgreSQL 16 |
| キャッシュ / メッセージブローカー | Redis 7 |
| タスクキュー | Celery 5 |
| コンテナ | Docker / Docker Compose |
| インフラ | Azure Container Apps（東日本 + 西日本マルチリージョン） |
| CI/CD | GitHub Actions |

---

## 2. 必要ソフトウェア

### 2.1 必須ソフトウェア一覧

| ソフトウェア | バージョン | 用途 | 備考 |
|-------------|-----------|------|------|
| Node.js | 20.x LTS | フロントエンド開発 | nvm での管理を推奨 |
| npm / pnpm | 10.x / 9.x | パッケージマネージャ | pnpm を推奨 |
| Python | 3.12.x | バックエンド開発 | pyenv での管理を推奨 |
| PostgreSQL | 16.x | リレーショナルデータベース | Docker 利用可 |
| Redis | 7.x | キャッシュ / メッセージブローカー | Docker 利用可 |
| Docker | 24.x 以上 | コンテナ実行環境 | Docker Desktop または Docker Engine |
| Docker Compose | 2.20 以上 | マルチコンテナオーケストレーション | Docker Desktop に同梱 |
| Git | 2.40 以上 | バージョン管理 | - |

### 2.2 推奨ソフトウェア一覧

| ソフトウェア | バージョン | 用途 | 備考 |
|-------------|-----------|------|------|
| Visual Studio Code | 最新 | 統合開発環境 | 推奨拡張機能は後述 |
| nvm | 最新 | Node.js バージョン管理 | - |
| pyenv | 最新 | Python バージョン管理 | - |
| Poetry | 1.8.x | Python 依存関係管理 | pip でのインストールも可 |
| DBeaver | 最新 | データベースクライアント | - |
| Postman | 最新 | API テストクライアント | - |
| Azure CLI | 最新 | Azure リソース操作 | - |

### 2.3 VS Code 推奨拡張機能

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.isort",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-azuretools.vscode-docker",
    "GitHub.copilot",
    "ms-vscode.vscode-typescript-next",
    "eamodio.gitlens",
    "usernamehw.errorlens",
    "ms-azuretools.vscode-azurefunctions"
  ]
}
```

---

## 3. 開発環境セットアップ手順

### 3.1 リポジトリクローン

```bash
# リポジトリのクローン
git clone https://github.com/<organization>/IT-BCP-ITSCM-System.git
cd IT-BCP-ITSCM-System

# サブモジュールの初期化（存在する場合）
git submodule update --init --recursive
```

### 3.2 環境変数設定

#### 3.2.1 バックエンド環境変数

プロジェクトルートの `backend/` ディレクトリに `.env` ファイルを作成する。

```bash
cp backend/.env.example backend/.env
```

`.env` ファイルの内容:

```env
# アプリケーション設定
APP_NAME=IT-BCP-ITSCM-System
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key-here-change-in-production
APP_HOST=0.0.0.0
APP_PORT=8000

# データベース設定
DATABASE_URL=postgresql+asyncpg://itbcp_user:itbcp_password@localhost:5432/itbcp_db
DATABASE_ECHO=true

# Redis 設定
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_DB=1
REDIS_CELERY_DB=2

# Celery 設定
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# 認証設定
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Azure 設定（ローカル開発では空でも可）
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_STORAGE_CONNECTION_STRING=

# メール設定（ローカル開発では MailHog 使用）
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@itbcp-system.local

# ログ設定
LOG_LEVEL=DEBUG
LOG_FORMAT=json

# CORS 設定
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### 3.2.2 フロントエンド環境変数

`frontend/` ディレクトリに `.env.local` ファイルを作成する。

```bash
cp frontend/.env.example frontend/.env.local
```

`.env.local` ファイルの内容:

```env
# API エンドポイント
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# アプリケーション設定
NEXT_PUBLIC_APP_NAME=IT-BCP-ITSCM System
NEXT_PUBLIC_APP_VERSION=1.0.0

# PWA 設定
NEXT_PUBLIC_PWA_ENABLED=true

# Azure AD 認証（ローカル開発）
NEXT_PUBLIC_AZURE_AD_CLIENT_ID=
NEXT_PUBLIC_AZURE_AD_TENANT_ID=
NEXTAUTH_SECRET=your-nextauth-secret-here
NEXTAUTH_URL=http://localhost:3000

# 機能フラグ
NEXT_PUBLIC_FEATURE_OFFLINE_MODE=true
NEXT_PUBLIC_FEATURE_RTO_DASHBOARD=true
NEXT_PUBLIC_FEATURE_BIA_MODULE=true
```

---

### 3.3 バックエンドセットアップ

#### 3.3.1 Python 環境構築

```bash
# Python 3.12 のインストール（pyenv 使用）
pyenv install 3.12.4
pyenv local 3.12.4

# 仮想環境の作成と有効化
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# pip のアップグレード
pip install --upgrade pip
```

#### 3.3.2 Poetry を使用した依存関係インストール

```bash
# Poetry のインストール（未インストールの場合）
curl -sSL https://install.python-poetry.org | python3 -

# 依存関係のインストール
cd backend
poetry install

# 開発用依存関係も含めてインストール
poetry install --with dev,test
```

#### 3.3.3 pip を使用した依存関係インストール（Poetry を使用しない場合）

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 3.3.4 バックエンドの起動確認

```bash
cd backend

# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API ドキュメント確認
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
# ヘルスチェック: http://localhost:8000/api/v1/health
```

---

### 3.4 フロントエンドセットアップ

#### 3.4.1 Node.js 環境構築

```bash
# Node.js 20 のインストール（nvm 使用）
nvm install 20
nvm use 20

# pnpm のインストール（推奨）
npm install -g pnpm@9
```

#### 3.4.2 依存関係のインストール

```bash
cd frontend

# pnpm を使用する場合
pnpm install

# npm を使用する場合
npm install
```

#### 3.4.3 フロントエンドの起動確認

```bash
cd frontend

# 開発サーバー起動
pnpm dev
# または
npm run dev

# ブラウザで確認: http://localhost:3000
```

---

## 4. Docker Compose によるローカル開発環境構築

### 4.1 Docker Compose 構成

プロジェクトルートの `docker-compose.yml` を使用して、全サービスを一括で起動できる。

#### 4.1.1 サービス構成

| サービス名 | イメージ | ポート | 用途 |
|-----------|---------|-------|------|
| postgres | postgres:16-alpine | 5432 | メインデータベース |
| redis | redis:7-alpine | 6379 | キャッシュ / メッセージブローカー |
| backend | カスタムビルド | 8000 | FastAPI アプリケーション |
| frontend | カスタムビルド | 3000 | Next.js アプリケーション |
| celery-worker | カスタムビルド | - | 非同期タスクワーカー |
| celery-beat | カスタムビルド | - | 定期タスクスケジューラ |
| mailhog | mailhog/mailhog | 1025, 8025 | メールテスト |
| pgadmin | dpage/pgadmin4 | 5050 | データベース管理UI |

#### 4.1.2 docker-compose.yml の例

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    container_name: itbcp-postgres
    environment:
      POSTGRES_DB: itbcp_db
      POSTGRES_USER: itbcp_user
      POSTGRES_PASSWORD: itbcp_password
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --locale=ja_JP.UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U itbcp_user -d itbcp_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: itbcp-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: itbcp-backend
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: itbcp-frontend
    env_file:
      - ./frontend/.env.local
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    command: pnpm dev

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: itbcp-celery-worker
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: itbcp-celery-beat
    env_file:
      - ./backend/.env
    volumes:
      - ./backend:/app
    depends_on:
      - celery-worker
    command: celery -A app.celery_app beat --loglevel=info

  mailhog:
    image: mailhog/mailhog
    container_name: itbcp-mailhog
    ports:
      - "1025:1025"
      - "8025:8025"

  pgadmin:
    image: dpage/pgadmin4
    container_name: itbcp-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@itbcp.local
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

volumes:
  postgres_data:
  redis_data:
```

### 4.2 Docker Compose 起動手順

```bash
# 全サービスの起動
docker compose up -d

# 起動状態の確認
docker compose ps

# ログの確認
docker compose logs -f backend
docker compose logs -f frontend

# 全サービスの停止
docker compose down

# ボリュームも含めて完全削除（データベースリセット時）
docker compose down -v
```

### 4.3 個別サービスの起動

```bash
# インフラサービスのみ起動（PostgreSQL, Redis, MailHog）
docker compose up -d postgres redis mailhog

# バックエンドのみローカル実行する場合
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# フロントエンドのみローカル実行する場合
cd frontend
pnpm dev
```

---

## 5. データベースマイグレーション

### 5.1 Alembic によるマイグレーション管理

```bash
cd backend

# マイグレーションの初期化（初回のみ）
alembic init alembic

# 現在のマイグレーション状態確認
alembic current

# マイグレーションファイルの自動生成
alembic revision --autogenerate -m "説明文"

# マイグレーションの実行（最新まで適用）
alembic upgrade head

# 1つ前のバージョンにロールバック
alembic downgrade -1

# 特定のバージョンまでロールバック
alembic downgrade <revision_id>

# マイグレーション履歴の確認
alembic history --verbose
```

### 5.2 マイグレーションファイルの構成

```
backend/
  alembic/
    versions/
      001_create_users_table.py
      002_create_bcp_plans_table.py
      003_create_drills_table.py
      004_create_incidents_table.py
      005_create_bia_table.py
      006_create_rto_tracking_table.py
      007_create_notifications_table.py
      008_create_audit_logs_table.py
    env.py
    script.py.mako
  alembic.ini
```

### 5.3 Docker 環境でのマイグレーション実行

```bash
# Docker コンテナ内でマイグレーション実行
docker compose exec backend alembic upgrade head

# マイグレーション状態の確認
docker compose exec backend alembic current
```

---

## 6. 初期データ投入

### 6.1 シードデータの投入

```bash
cd backend

# 初期マスターデータの投入
python -m app.scripts.seed_master_data

# テスト用サンプルデータの投入
python -m app.scripts.seed_sample_data

# 全シードデータの投入（マスター + サンプル）
python -m app.scripts.seed_all
```

### 6.2 Docker 環境でのシードデータ投入

```bash
docker compose exec backend python -m app.scripts.seed_master_data
docker compose exec backend python -m app.scripts.seed_sample_data
```

### 6.3 投入されるマスターデータ

| カテゴリ | データ内容 | 件数目安 |
|---------|-----------|---------|
| ユーザーロール | システム管理者、BCP管理者、訓練管理者、一般ユーザー、閲覧者 | 5 |
| 組織マスタ | 部門、チーム階層構造 | 20 |
| システム分類 | 業務システムカテゴリ（基幹、情報、インフラ等） | 10 |
| RTO/RPO テンプレート | 業界標準の RTO/RPO 値テンプレート | 15 |
| 災害シナリオ | 地震、風水害、パンデミック、サイバー攻撃等 | 12 |
| BCP テンプレート | 標準 BCP 計画テンプレート | 5 |
| 訓練シナリオ | 標準訓練シナリオテンプレート | 8 |
| 通知テンプレート | メール・SMS 通知テンプレート | 20 |
| チェックリスト | 初動対応チェックリストテンプレート | 10 |
| 評価基準 | BIA 影響度評価基準マスタ | 5 |

### 6.4 テスト用管理者アカウント

| 項目 | 値 |
|------|-----|
| メールアドレス | admin@itbcp-system.local |
| パスワード | Admin@12345 |
| ロール | システム管理者 |

> **注意**: このアカウントはローカル開発環境専用である。本番環境では Azure AD 認証を使用する。

---

## 7. 開発ツールのセットアップ

### 7.1 pre-commit フックの設定

```bash
cd backend

# pre-commit のインストール
pip install pre-commit

# フックのインストール
pre-commit install

# 全ファイルに対して手動実行
pre-commit run --all-files
```

`.pre-commit-config.yaml` で設定されるフック:

| フック | 用途 |
|-------|------|
| black | Python コードフォーマット |
| isort | Python インポート整理 |
| flake8 | Python リント |
| mypy | Python 型チェック |
| eslint | TypeScript/JavaScript リント |
| prettier | フロントエンドコードフォーマット |

### 7.2 Makefile コマンド

```bash
# よく使用するコマンドの一覧
make help

# 開発環境の完全セットアップ（初回用）
make setup

# バックエンドテスト実行
make test-backend

# フロントエンドテスト実行
make test-frontend

# 全テスト実行
make test-all

# リント実行
make lint

# フォーマット実行
make format

# データベースマイグレーション
make migrate

# シードデータ投入
make seed

# Docker 環境起動
make up

# Docker 環境停止
make down

# Docker 環境リセット（データ含む）
make reset
```

---

## 8. トラブルシューティング

### 8.1 よくある問題と解決方法

#### PostgreSQL 接続エラー

```
原因: PostgreSQL サービスが起動していない、またはポート競合
解決方法:
1. docker compose ps で PostgreSQL の状態を確認
2. ローカルにインストールされた PostgreSQL がポート 5432 を使用していないか確認
3. docker compose logs postgres でエラーログを確認
```

#### Redis 接続エラー

```
原因: Redis サービスが起動していない
解決方法:
1. docker compose ps で Redis の状態を確認
2. redis-cli ping でレスポンスを確認
```

#### Node.js バージョン不整合

```
原因: プロジェクトが要求する Node.js バージョンと異なるバージョンが使用されている
解決方法:
1. nvm use 20 で正しいバージョンに切り替え
2. node --version で確認
3. pnpm install を再実行
```

#### Python パッケージインストールエラー

```
原因: psycopg2 等のネイティブパッケージのビルドに必要なライブラリが不足
解決方法:
# Ubuntu/Debian
sudo apt-get install libpq-dev python3-dev build-essential

# macOS
brew install postgresql

# または psycopg2-binary を使用
pip install psycopg2-binary
```

#### マイグレーションエラー

```
原因: データベーススキーマとマイグレーションファイルの不整合
解決方法:
1. alembic current で現在の状態を確認
2. alembic history で履歴を確認
3. 必要に応じて alembic stamp head でリセット
4. データベースを完全リセットする場合: docker compose down -v && docker compose up -d
```

#### ポート競合

```
原因: 別プロセスが同じポートを使用している
解決方法:
# 使用中のポートを確認
lsof -i :3000  # フロントエンド
lsof -i :8000  # バックエンド
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# プロセスを終了
kill -9 <PID>
```

### 8.2 ログの確認方法

```bash
# バックエンドログ
docker compose logs -f backend

# フロントエンドログ
docker compose logs -f frontend

# 全サービスのログ
docker compose logs -f

# 特定時間のログ
docker compose logs --since 30m backend
```

---

## 9. ネットワーク構成（ローカル開発時）

| サービス | URL | 用途 |
|---------|-----|------|
| フロントエンド | http://localhost:3000 | Next.js アプリケーション |
| バックエンド API | http://localhost:8000 | FastAPI エンドポイント |
| Swagger UI | http://localhost:8000/docs | API ドキュメント |
| ReDoc | http://localhost:8000/redoc | API ドキュメント（別形式） |
| pgAdmin | http://localhost:5050 | PostgreSQL 管理 UI |
| MailHog | http://localhost:8025 | メールテスト UI |
| WebSocket | ws://localhost:8000/ws | リアルタイム通信 |

---

## 10. 次のステップ

環境構築が完了したら、以下のドキュメントを参照すること。

| ドキュメント | 内容 |
|------------|------|
| [02_コーディング規約](./02_コーディング規約(Coding-Standards).md) | コーディングルールとスタイルガイド |
| [03_ブランチ戦略](./03_ブランチ戦略(Branch-Strategy).md) | Git ブランチ運用ルール |
| [04_CI-CD設定](./04_CI-CD設定(CI-CD-Configuration).md) | CI/CD パイプライン設定 |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-03-27 | 初版作成 | IT-BCP-ITSCM開発チーム |
