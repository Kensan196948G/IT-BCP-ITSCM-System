# CI/CD 設定 (CI-CD Configuration)

| 項目 | 内容 |
|------|------|
| 文書番号 | DEV-CICD-004 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 作成者 | IT-BCP-ITSCM開発チーム |
| 分類 | 開発ガイド |
| 対象システム | IT事業継続管理システム (IT-BCP-ITSCM-System) |

---

## 1. 概要

本文書は、IT事業継続管理システムの CI/CD（継続的インテグレーション / 継続的デリバリー）パイプラインの設計と設定を定義する。GitHub Actions を使用し、コードの品質保証から本番デプロイまでを自動化する。

### 1.1 CI/CD の目的

- コード品質の自動検証（リント、型チェック、テスト）
- セキュリティ脆弱性の早期検出
- ビルド・デプロイプロセスの自動化
- 環境間の一貫性確保
- リリースサイクルの短縮

### 1.2 CI/CD ツール

| ツール | 用途 |
|-------|------|
| GitHub Actions | CI/CD パイプライン実行基盤 |
| Docker | コンテナビルド |
| Azure Container Registry (ACR) | コンテナイメージレジストリ |
| Azure Container Apps | アプリケーションホスティング |
| Trivy | コンテナセキュリティスキャン |
| SonarQube | コード品質分析 |
| k6 | 負荷テスト |

---

## 2. ステージ構成

### 2.1 環境一覧

| 環境 | 用途 | URL | トリガー |
|------|------|-----|---------|
| dev | 開発環境 | `dev.itbcp-system.example.com` | develop ブランチへのマージ |
| staging | ステージング環境 | `staging.itbcp-system.example.com` | release ブランチの作成 |
| production | 本番環境 | `itbcp-system.example.com` | main ブランチへのマージ + 手動承認 |

### 2.2 環境構成の詳細

| 項目 | dev | staging | production |
|------|-----|---------|------------|
| Azure リージョン | 東日本のみ | 東日本のみ | 東日本 + 西日本 |
| Container Apps レプリカ数 | 1 | 2 | 3-10（自動スケーリング） |
| PostgreSQL | Basic (2vCores) | Standard (4vCores) | Premium (8vCores, HA) |
| Redis | Basic (C0) | Standard (C1) | Premium (P1, クラスター) |
| SSL/TLS | Let's Encrypt | Let's Encrypt | Azure Managed Certificate |
| ログレベル | DEBUG | INFO | WARNING |
| 監視 | 基本メトリクス | 基本メトリクス + アラート | フル監視 + オンコール |

### 2.3 環境間の昇格フロー

```
開発者PC → dev環境 → staging環境 → production環境
  (PR)     (自動)     (自動+承認)    (手動承認)
```

---

## 3. GitHub Actions ワークフロー設計

### 3.1 ワークフロー一覧

| ワークフロー | ファイル | トリガー | 用途 |
|------------|---------|---------|------|
| CI | `ci.yml` | PR作成/更新 | リント、テスト、ビルド確認 |
| Deploy Dev | `deploy-dev.yml` | develop マージ | dev 環境デプロイ |
| Deploy Staging | `deploy-staging.yml` | release ブランチ | staging 環境デプロイ |
| Deploy Production | `deploy-production.yml` | main マージ | production 環境デプロイ |
| Security Scan | `security-scan.yml` | 毎日 + PR | セキュリティスキャン |
| Dependency Update | `dependency-update.yml` | 毎週月曜 | 依存パッケージ更新 |
| DR Test | `dr-test.yml` | 毎月1日 + 手動 | DR テスト自動実行 |

### 3.2 CI ワークフロー（ci.yml）

```yaml
name: CI Pipeline

on:
  pull_request:
    branches: [develop, main]
    types: [opened, synchronize, reopened]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '20'
  PNPM_VERSION: '9'

jobs:
  # ===================================
  # 変更検出
  # ===================================
  changes:
    name: 変更ファイル検出
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.filter.outputs.backend }}
      frontend: ${{ steps.filter.outputs.frontend }}
      infra: ${{ steps.filter.outputs.infra }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            backend:
              - 'backend/**'
              - 'pyproject.toml'
              - 'poetry.lock'
            frontend:
              - 'frontend/**'
              - 'pnpm-lock.yaml'
            infra:
              - 'infra/**'
              - 'docker-compose*.yml'
              - 'Dockerfile*'

  # ===================================
  # バックエンド CI
  # ===================================
  lint-backend:
    name: バックエンド リント
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Python セットアップ
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: 依存関係キャッシュ
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: pip-${{ runner.os }}-${{ hashFiles('backend/requirements*.txt') }}

      - name: 依存関係インストール
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt

      - name: Black フォーマットチェック
        run: cd backend && black --check .

      - name: isort チェック
        run: cd backend && isort --check-only .

      - name: flake8 リント
        run: cd backend && flake8 .

      - name: mypy 型チェック
        run: cd backend && mypy app/

  test-backend:
    name: バックエンド テスト
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: itbcp_test_db
          POSTGRES_USER: itbcp_test_user
          POSTGRES_PASSWORD: itbcp_test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4

      - name: Python セットアップ
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: 依存関係インストール
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt

      - name: マイグレーション実行
        env:
          DATABASE_URL: postgresql+asyncpg://itbcp_test_user:itbcp_test_password@localhost:5432/itbcp_test_db
        run: cd backend && alembic upgrade head

      - name: テスト実行
        env:
          DATABASE_URL: postgresql+asyncpg://itbcp_test_user:itbcp_test_password@localhost:5432/itbcp_test_db
          REDIS_URL: redis://localhost:6379/0
          APP_ENV: testing
        run: |
          cd backend
          pytest \
            --cov=app \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=80 \
            --junitxml=test-results.xml \
            -v

      - name: テスト結果アップロード
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: backend-test-results
          path: |
            backend/test-results.xml
            backend/htmlcov/

      - name: カバレッジレポート
        uses: codecov/codecov-action@v4
        with:
          files: backend/coverage.xml
          flags: backend
          fail_ci_if_error: true

  # ===================================
  # フロントエンド CI
  # ===================================
  lint-frontend:
    name: フロントエンド リント
    needs: changes
    if: needs.changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: pnpm セットアップ
        uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}

      - name: Node.js セットアップ
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
          cache-dependency-path: frontend/pnpm-lock.yaml

      - name: 依存関係インストール
        run: cd frontend && pnpm install --frozen-lockfile

      - name: ESLint
        run: cd frontend && pnpm lint

      - name: Prettier チェック
        run: cd frontend && pnpm prettier --check .

      - name: TypeScript 型チェック
        run: cd frontend && pnpm type-check

  test-frontend:
    name: フロントエンド テスト
    needs: changes
    if: needs.changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: pnpm セットアップ
        uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}

      - name: Node.js セットアップ
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
          cache-dependency-path: frontend/pnpm-lock.yaml

      - name: 依存関係インストール
        run: cd frontend && pnpm install --frozen-lockfile

      - name: ユニットテスト
        run: |
          cd frontend
          pnpm test -- \
            --coverage \
            --coverageReporters=text \
            --coverageReporters=lcov \
            --ci

      - name: カバレッジレポート
        uses: codecov/codecov-action@v4
        with:
          files: frontend/coverage/lcov.info
          flags: frontend
          fail_ci_if_error: true

  build-frontend:
    name: フロントエンド ビルド
    needs: [lint-frontend, test-frontend]
    if: needs.changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: pnpm セットアップ
        uses: pnpm/action-setup@v4
        with:
          version: ${{ env.PNPM_VERSION }}

      - name: Node.js セットアップ
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'
          cache-dependency-path: frontend/pnpm-lock.yaml

      - name: 依存関係インストール
        run: cd frontend && pnpm install --frozen-lockfile

      - name: プロダクションビルド
        run: cd frontend && pnpm build

      - name: ビルド成果物アップロード
        uses: actions/upload-artifact@v4
        with:
          name: frontend-build
          path: frontend/.next/

  # ===================================
  # セキュリティスキャン
  # ===================================
  security-scan:
    name: セキュリティスキャン
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Python 依存関係の脆弱性チェック
        run: |
          pip install pip-audit
          cd backend && pip-audit -r requirements.txt

      - name: Node.js 依存関係の脆弱性チェック
        run: |
          cd frontend && npm audit --audit-level=high

      - name: Trivy ファイルシステムスキャン
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      - name: CodeQL 分析
        uses: github/codeql-action/analyze@v3

  # ===================================
  # Docker ビルドテスト
  # ===================================
  docker-build:
    name: Docker ビルドテスト
    needs: changes
    if: needs.changes.outputs.backend == 'true' || needs.changes.outputs.frontend == 'true' || needs.changes.outputs.infra == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [backend, frontend]
    steps:
      - uses: actions/checkout@v4

      - name: Docker Buildx セットアップ
        uses: docker/setup-buildx-action@v3

      - name: Docker ビルド (${{ matrix.service }})
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service }}
          push: false
          tags: itbcp-${{ matrix.service }}:test
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Trivy イメージスキャン
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: itbcp-${{ matrix.service }}:test
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

  # ===================================
  # E2E テスト
  # ===================================
  e2e-test:
    name: E2E テスト
    needs: [test-backend, build-frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Docker Compose で環境起動
        run: |
          docker compose -f docker-compose.test.yml up -d
          docker compose -f docker-compose.test.yml exec -T backend alembic upgrade head
          docker compose -f docker-compose.test.yml exec -T backend python -m app.scripts.seed_master_data

      - name: Playwright セットアップ
        run: |
          cd frontend
          pnpm install --frozen-lockfile
          pnpm exec playwright install --with-deps chromium

      - name: E2E テスト実行
        run: |
          cd frontend
          pnpm exec playwright test --project=chromium
        env:
          PLAYWRIGHT_BASE_URL: http://localhost:3000

      - name: テスト結果アップロード
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: e2e-test-results
          path: frontend/playwright-report/

      - name: 環境停止
        if: always()
        run: docker compose -f docker-compose.test.yml down -v

  # ===================================
  # 品質ゲート
  # ===================================
  quality-gate:
    name: 品質ゲート
    needs: [lint-backend, test-backend, lint-frontend, test-frontend, build-frontend, security-scan, docker-build, e2e-test]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: 品質ゲート判定
        run: |
          echo "=== 品質ゲート結果 ==="
          echo "バックエンドリント: ${{ needs.lint-backend.result }}"
          echo "バックエンドテスト: ${{ needs.test-backend.result }}"
          echo "フロントエンドリント: ${{ needs.lint-frontend.result }}"
          echo "フロントエンドテスト: ${{ needs.test-frontend.result }}"
          echo "フロントエンドビルド: ${{ needs.build-frontend.result }}"
          echo "セキュリティスキャン: ${{ needs.security-scan.result }}"
          echo "Dockerビルド: ${{ needs.docker-build.result }}"
          echo "E2Eテスト: ${{ needs.e2e-test.result }}"

          if [[ "${{ needs.lint-backend.result }}" == "failure" ]] || \
             [[ "${{ needs.test-backend.result }}" == "failure" ]] || \
             [[ "${{ needs.lint-frontend.result }}" == "failure" ]] || \
             [[ "${{ needs.test-frontend.result }}" == "failure" ]] || \
             [[ "${{ needs.build-frontend.result }}" == "failure" ]] || \
             [[ "${{ needs.security-scan.result }}" == "failure" ]] || \
             [[ "${{ needs.docker-build.result }}" == "failure" ]] || \
             [[ "${{ needs.e2e-test.result }}" == "failure" ]]; then
            echo "品質ゲート: FAILED"
            exit 1
          fi
          echo "品質ゲート: PASSED"
```

### 3.3 Deploy Dev ワークフロー（deploy-dev.yml）

```yaml
name: Deploy to Dev

on:
  push:
    branches: [develop]

concurrency:
  group: deploy-dev
  cancel-in-progress: false

env:
  AZURE_RESOURCE_GROUP: rg-itbcp-dev
  AZURE_CONTAINER_REGISTRY: acritbcpdev
  AZURE_CONTAINER_APP_BACKEND: ca-itbcp-backend-dev
  AZURE_CONTAINER_APP_FRONTEND: ca-itbcp-frontend-dev

jobs:
  build-and-push:
    name: ビルド & プッシュ
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [backend, frontend]
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4

      - name: Azure ログイン
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS_DEV }}

      - name: ACR ログイン
        uses: azure/docker-login@v2
        with:
          login-server: ${{ env.AZURE_CONTAINER_REGISTRY }}.azurecr.io
          username: ${{ secrets.ACR_USERNAME_DEV }}
          password: ${{ secrets.ACR_PASSWORD_DEV }}

      - name: Docker メタデータ
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.AZURE_CONTAINER_REGISTRY }}.azurecr.io/itbcp-${{ matrix.service }}
          tags: |
            type=sha,prefix=dev-
            type=raw,value=dev-latest

      - name: Docker ビルド & プッシュ
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    name: dev 環境デプロイ
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v4

      - name: Azure ログイン
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS_DEV }}

      - name: バックエンドデプロイ
        uses: azure/container-apps-deploy-action@v2
        with:
          resourceGroup: ${{ env.AZURE_RESOURCE_GROUP }}
          containerAppName: ${{ env.AZURE_CONTAINER_APP_BACKEND }}
          imageToDeploy: ${{ env.AZURE_CONTAINER_REGISTRY }}.azurecr.io/itbcp-backend:dev-latest

      - name: フロントエンドデプロイ
        uses: azure/container-apps-deploy-action@v2
        with:
          resourceGroup: ${{ env.AZURE_RESOURCE_GROUP }}
          containerAppName: ${{ env.AZURE_CONTAINER_APP_FRONTEND }}
          imageToDeploy: ${{ env.AZURE_CONTAINER_REGISTRY }}.azurecr.io/itbcp-frontend:dev-latest

      - name: マイグレーション実行
        run: |
          az containerapp exec \
            --name ${{ env.AZURE_CONTAINER_APP_BACKEND }} \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --command "alembic upgrade head"

      - name: ヘルスチェック
        run: |
          for i in {1..30}; do
            STATUS=$(curl -s -o /dev/null -w '%{http_code}' https://dev.itbcp-system.example.com/api/v1/health)
            if [ "$STATUS" == "200" ]; then
              echo "ヘルスチェック成功"
              exit 0
            fi
            echo "待機中... ($i/30)"
            sleep 10
          done
          echo "ヘルスチェック失敗"
          exit 1

      - name: デプロイ通知（Slack）
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Dev環境デプロイ: ${{ job.status }}\nコミット: ${{ github.sha }}\n実行者: ${{ github.actor }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 3.4 Deploy Production ワークフロー（deploy-production.yml）

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

concurrency:
  group: deploy-production
  cancel-in-progress: false

env:
  AZURE_RESOURCE_GROUP_EAST: rg-itbcp-prod-japaneast
  AZURE_RESOURCE_GROUP_WEST: rg-itbcp-prod-japanwest
  AZURE_CONTAINER_REGISTRY: acritbcpprod

jobs:
  build-and-push:
    name: プロダクションビルド
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [backend, frontend]
    steps:
      - uses: actions/checkout@v4

      - name: Azure ログイン
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS_PROD }}

      - name: ACR ログイン
        uses: azure/docker-login@v2
        with:
          login-server: ${{ env.AZURE_CONTAINER_REGISTRY }}.azurecr.io
          username: ${{ secrets.ACR_USERNAME_PROD }}
          password: ${{ secrets.ACR_PASSWORD_PROD }}

      - name: Docker メタデータ
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.AZURE_CONTAINER_REGISTRY }}.azurecr.io/itbcp-${{ matrix.service }}
          tags: |
            type=semver,pattern={{version}}
            type=sha,prefix=prod-
            type=raw,value=prod-latest

      - name: Docker ビルド & プッシュ
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}

  deploy-east:
    name: 東日本リージョンデプロイ
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: production-east
    steps:
      - uses: actions/checkout@v4

      - name: Azure ログイン
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS_PROD }}

      - name: 東日本リージョンデプロイ
        uses: azure/container-apps-deploy-action@v2
        with:
          resourceGroup: ${{ env.AZURE_RESOURCE_GROUP_EAST }}
          containerAppName: ca-itbcp-backend-prod-east
          imageToDeploy: ${{ env.AZURE_CONTAINER_REGISTRY }}.azurecr.io/itbcp-backend:prod-latest

      - name: マイグレーション実行（東日本）
        run: |
          az containerapp exec \
            --name ca-itbcp-backend-prod-east \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP_EAST }} \
            --command "alembic upgrade head"

      - name: ヘルスチェック（東日本）
        run: |
          for i in {1..30}; do
            STATUS=$(curl -s -o /dev/null -w '%{http_code}' https://east.itbcp-system.example.com/api/v1/health)
            if [ "$STATUS" == "200" ]; then
              echo "東日本ヘルスチェック成功"
              exit 0
            fi
            sleep 10
          done
          exit 1

  deploy-west:
    name: 西日本リージョンデプロイ
    needs: deploy-east
    runs-on: ubuntu-latest
    environment: production-west
    steps:
      - uses: actions/checkout@v4

      - name: Azure ログイン
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS_PROD }}

      - name: 西日本リージョンデプロイ
        uses: azure/container-apps-deploy-action@v2
        with:
          resourceGroup: ${{ env.AZURE_RESOURCE_GROUP_WEST }}
          containerAppName: ca-itbcp-backend-prod-west
          imageToDeploy: ${{ env.AZURE_CONTAINER_REGISTRY }}.azurecr.io/itbcp-backend:prod-latest

      - name: ヘルスチェック（西日本）
        run: |
          for i in {1..30}; do
            STATUS=$(curl -s -o /dev/null -w '%{http_code}' https://west.itbcp-system.example.com/api/v1/health)
            if [ "$STATUS" == "200" ]; then
              echo "西日本ヘルスチェック成功"
              exit 0
            fi
            sleep 10
          done
          exit 1

  smoke-test:
    name: スモークテスト
    needs: [deploy-east, deploy-west]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: API スモークテスト
        run: |
          echo "=== スモークテスト開始 ==="

          # ヘルスチェック
          curl -sf https://itbcp-system.example.com/api/v1/health

          # 認証エンドポイント
          curl -sf https://itbcp-system.example.com/api/v1/auth/status

          # BCP計画一覧（認証なし→401確認）
          STATUS=$(curl -s -o /dev/null -w '%{http_code}' https://itbcp-system.example.com/api/v1/bcp-plans)
          if [ "$STATUS" != "401" ]; then
            echo "認証バイパスの可能性あり: $STATUS"
            exit 1
          fi

          echo "=== スモークテスト完了 ==="

      - name: リリース通知
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "本番デプロイ: ${{ job.status }}\nバージョン: ${{ github.ref_name }}\n実行者: ${{ github.actor }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### 3.5 セキュリティスキャンワークフロー（security-scan.yml）

```yaml
name: Security Scan

on:
  schedule:
    - cron: '0 2 * * *'  # 毎日午前2時（UTC）
  pull_request:
    branches: [develop, main]

jobs:
  dependency-scan:
    name: 依存関係脆弱性スキャン
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Python 依存関係スキャン
        run: |
          pip install pip-audit safety
          cd backend
          pip-audit -r requirements.txt --output json > pip-audit-results.json
          safety check -r requirements.txt --json > safety-results.json

      - name: Node.js 依存関係スキャン
        run: |
          cd frontend
          npm audit --json > npm-audit-results.json || true

      - name: 結果アップロード
        uses: actions/upload-artifact@v4
        with:
          name: dependency-scan-results
          path: |
            backend/pip-audit-results.json
            backend/safety-results.json
            frontend/npm-audit-results.json

  container-scan:
    name: コンテナイメージスキャン
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [backend, frontend]
    steps:
      - uses: actions/checkout@v4

      - name: Docker ビルド
        run: docker build -t itbcp-${{ matrix.service }}:scan ./${{ matrix.service }}

      - name: Trivy スキャン
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: itbcp-${{ matrix.service }}:scan
          format: 'sarif'
          output: trivy-results-${{ matrix.service }}.sarif
          severity: 'CRITICAL,HIGH,MEDIUM'

      - name: SARIF アップロード
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results-${{ matrix.service }}.sarif

  sast:
    name: SAST（静的アプリケーションセキュリティテスト）
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: CodeQL 初期化
        uses: github/codeql-action/init@v3
        with:
          languages: python, javascript

      - name: CodeQL 分析
        uses: github/codeql-action/analyze@v3

      - name: Bandit（Python SAST）
        run: |
          pip install bandit
          cd backend && bandit -r app/ -f json -o bandit-results.json || true

      - name: 結果アップロード
        uses: actions/upload-artifact@v4
        with:
          name: sast-results
          path: backend/bandit-results.json

  secret-scan:
    name: シークレットスキャン
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Gitleaks スキャン
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 4. 品質ゲート

### 4.1 品質ゲート基準

| 項目 | 基準 | 必須/推奨 |
|------|------|----------|
| バックエンドテストカバレッジ | 80% 以上 | 必須 |
| フロントエンドテストカバレッジ | 75% 以上 | 必須 |
| リント違反 | 0件 | 必須 |
| 型チェックエラー | 0件 | 必須 |
| セキュリティ脆弱性（CRITICAL） | 0件 | 必須 |
| セキュリティ脆弱性（HIGH） | 0件 | 必須 |
| セキュリティ脆弱性（MEDIUM） | 5件以下 | 推奨 |
| E2E テスト | 全パス | 必須 |
| Docker ビルド | 成功 | 必須 |
| コードレビュー承認 | develop: 1名 / main: 2名 | 必須 |

### 4.2 品質ゲートの適用タイミング

| タイミング | ゲート内容 |
|-----------|-----------|
| PR 作成時 | リント + テスト + セキュリティスキャン + ビルド |
| develop マージ時 | 上記 + E2E テスト + コードレビュー1名 |
| main マージ時 | 上記 + 負荷テスト + コードレビュー2名 + 手動承認 |
| production デプロイ時 | 上記 + スモークテスト + ヘルスチェック |

---

## 5. 自動デプロイ設定

### 5.1 ロールバック戦略

| 環境 | ロールバック方法 | 所要時間目安 |
|------|----------------|------------|
| dev | 前のイメージにリビジョン切り替え | 2分以内 |
| staging | 前のイメージにリビジョン切り替え | 2分以内 |
| production | Blue/Green デプロイメントによる切り替え | 5分以内 |

### 5.2 ロールバック手順

```bash
# Azure Container Apps のリビジョン一覧確認
az containerapp revision list \
  --name ca-itbcp-backend-prod-east \
  --resource-group rg-itbcp-prod-japaneast \
  --output table

# 前のリビジョンにトラフィックを100%切り替え
az containerapp ingress traffic set \
  --name ca-itbcp-backend-prod-east \
  --resource-group rg-itbcp-prod-japaneast \
  --revision-weight <previous-revision>=100
```

### 5.3 カナリアデプロイ（production）

```yaml
# production では段階的なトラフィック移行を実施
# 10% → 25% → 50% → 100% の4段階

- name: カナリアデプロイ (10%)
  run: |
    az containerapp ingress traffic set \
      --name ${{ env.CONTAINER_APP }} \
      --resource-group ${{ env.RESOURCE_GROUP }} \
      --revision-weight $NEW_REVISION=10 $OLD_REVISION=90

- name: メトリクス監視 (5分)
  run: |
    sleep 300
    # エラーレート確認
    ERROR_RATE=$(az monitor metrics list ...)
    if [ "$ERROR_RATE" -gt "1" ]; then
      echo "エラーレート超過 - ロールバック"
      exit 1
    fi
```

---

## 6. シークレット管理

### 6.1 GitHub Secrets 一覧

| Secret 名 | 説明 | 使用環境 |
|-----------|------|---------|
| `AZURE_CREDENTIALS_DEV` | Azure サービスプリンシパル（dev） | dev |
| `AZURE_CREDENTIALS_PROD` | Azure サービスプリンシパル（prod） | staging, production |
| `ACR_USERNAME_DEV` | ACR ユーザー名（dev） | dev |
| `ACR_PASSWORD_DEV` | ACR パスワード（dev） | dev |
| `ACR_USERNAME_PROD` | ACR ユーザー名（prod） | staging, production |
| `ACR_PASSWORD_PROD` | ACR パスワード（prod） | staging, production |
| `SLACK_WEBHOOK_URL` | Slack 通知用 Webhook | 全環境 |
| `CODECOV_TOKEN` | Codecov トークン | CI |
| `SONARQUBE_TOKEN` | SonarQube トークン | CI |

### 6.2 環境変数の管理

- ランタイムの環境変数は Azure Container Apps の環境変数設定で管理する
- シークレットは Azure Key Vault に格納し、Container Apps から参照する
- `.env` ファイルは CI/CD パイプラインで生成し、イメージに含めない

---

## 7. 監視・通知

### 7.1 CI/CD 通知設定

| イベント | 通知先 | 条件 |
|---------|-------|------|
| CI 失敗 | Slack #ci-alerts | 全失敗 |
| デプロイ成功 | Slack #deployments | 全環境 |
| デプロイ失敗 | Slack #ci-alerts + PagerDuty | staging, production |
| セキュリティ脆弱性検出 | Slack #security-alerts | CRITICAL, HIGH |
| 本番ロールバック | Slack #incidents + PagerDuty | production |

### 7.2 ダッシュボード

| ダッシュボード | 用途 | URL |
|-------------|------|-----|
| GitHub Actions | CI/CD パイプライン状況 | GitHub リポジトリの Actions タブ |
| Codecov | テストカバレッジ推移 | codecov.io |
| Azure Portal | インフラリソース監視 | portal.azure.com |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-03-27 | 初版作成 | IT-BCP-ITSCM開発チーム |
