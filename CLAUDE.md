# CLAUDE.md - IT-BCP-ITSCM-System

## プロジェクト概要
IT事業継続管理システム（BCP/ITSCM統合プラットフォーム）
災害・サイバー攻撃時のIT復旧計画・BCP訓練・RTOダッシュボード統合プラットフォーム

## 準拠規格
- ISO20000-1:2018 ITサービス継続管理（必須）
- ISO27001:2022 A.5.29/A.5.30
- NIST CSF 2.0 RECOVER RC

## 技術スタック
- **バックエンド**: Python 3.12 / FastAPI 0.115 / SQLAlchemy (async) / Alembic
- **フロントエンド**: Next.js 16 / TypeScript / Tailwind CSS v4
- **データベース**: PostgreSQL 16 / Redis 7
- **インフラ**: Azure Container Apps / Azure Front Door
- **CI/CD**: GitHub Actions

## 開発規約

### Python
- フォーマッター: Black (line-length=120)
- リンター: flake8 (max-line-length=120)
- ソートル: isort (profile=black)
- 型チェック: mypy (strict)
- テスト: pytest

### TypeScript
- フォーマッター: Prettier
- リンター: ESLint (next/core-web-vitals)
- スタイル: Tailwind CSS v4 (postcss)

### Git
- mainへの直接push禁止
- feature/fix/improve ブランチで作業
- コミットメッセージ: Conventional Commits
- PRはCI通過後にマージ

## ディレクトリ構造
```
backend/           # FastAPI バックエンド
  apps/            # アプリケーションモジュール
    models.py      # SQLAlchemy モデル
    schemas.py     # Pydantic スキーマ
    crud.py        # CRUD操作
    rto_tracker.py # RTOトラッカー
    routers/       # APIルーター
  tests/           # pytest テスト
  main.py          # エントリポイント
  config.py        # 設定
  database.py      # DB接続

frontend/          # Next.js 16 フロントエンド
  app/             # App Router ページ
  public/          # 静的ファイル・PWA

docs/              # プロジェクトドキュメント（46ファイル）
scripts/           # 自動化スクリプト
```

## テスト実行
```bash
# バックエンド
cd backend && python3 -m pytest tests/ -v

# フロントエンド
cd frontend && npm run lint && npm run build
```

## CI/CD
- GitHub Actions: lint → test → build
- STABLE判定: CI連続N回成功（小規模N=2, 通常N=3, 重要N=5）

## GitHub Project
- Project #13: https://github.com/users/Kensan196948G/projects/13
- Status: Inbox → Backlog → Ready → Design → Development → Verify → Deploy Gate → Done → Blocked
