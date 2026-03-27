# Contributing to IT-BCP-ITSCM-System

IT事業継続管理システムへの貢献ガイドです。

## 開発環境セットアップ

```bash
# バックエンド
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# フロントエンド
cd frontend
npm install
npm run dev
```

## ブランチ戦略

| ブランチ | 用途 |
|:---------|:-----|
| `main` | 本番ブランチ（直接push禁止） |
| `feature/*` | 新機能開発 |
| `fix/*` | バグ修正 |
| `improvement/*` | 品質改善・リファクタリング |

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) に準拠:

```
feat: 新機能追加
fix: バグ修正
improve: 品質改善
docs: ドキュメント更新
test: テスト追加
```

## PR作成前チェックリスト

```bash
# バックエンド
cd backend
python3 -m black .
python3 -m flake8 . --max-line-length=120
python3 -m pytest tests/ -v

# フロントエンド
cd frontend
npm run lint
npm run build
```

## テスト

- バックエンド: pytest（DB不要のモックテスト）
- カバレッジ目標: 80%以上（現在92%）
- CI品質ゲート: `--cov-fail-under=80`

## コーディング規約

- Python: Black (line-length=120) + flake8 + isort
- TypeScript: ESLint (next/core-web-vitals) + Prettier
- 型アノテーション必須（Python/TypeScript共に）

## ライセンス

MIT License
