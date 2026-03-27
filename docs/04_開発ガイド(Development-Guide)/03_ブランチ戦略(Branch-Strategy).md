# ブランチ戦略 (Branch Strategy)

| 項目 | 内容 |
|------|------|
| 文書番号 | DEV-BRANCH-003 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 作成者 | IT-BCP-ITSCM開発チーム |
| 分類 | 開発ガイド |
| 対象システム | IT事業継続管理システム (IT-BCP-ITSCM-System) |

---

## 1. 概要

本文書は、IT事業継続管理システムの開発における Git ブランチ戦略を定義する。Git Flow をベースとしたブランチモデルを採用し、安定したリリースプロセスと並行開発の効率化を実現する。

### 1.1 採用モデル

Git Flow ベースのブランチモデルを採用する。ただし、本システムの特性（BCP/ITSCM という高可用性要件）に合わせてカスタマイズを行っている。

### 1.2 基本原則

1. `main` ブランチは常に本番リリース可能な状態を維持すること
2. `develop` ブランチは次回リリースの統合ブランチとして機能すること
3. 直接 `main` / `develop` へのプッシュは禁止（PR 必須）
4. 全てのマージは CI パイプラインの成功を条件とすること
5. コンフリクトは機能ブランチ側で解決すること

---

## 2. ブランチ構成

### 2.1 ブランチ種別一覧

| ブランチ種別 | 命名パターン | ライフサイクル | マージ先 | 用途 |
|-------------|------------|--------------|---------|------|
| main | `main` | 永続 | - | 本番リリース用 |
| develop | `develop` | 永続 | main | 次回リリース統合用 |
| feature | `feature/<scope>/<description>` | 一時的 | develop | 新機能開発 |
| release | `release/<version>` | 一時的 | main, develop | リリース準備 |
| hotfix | `hotfix/<description>` | 一時的 | main, develop | 緊急修正 |
| bugfix | `bugfix/<scope>/<description>` | 一時的 | develop | バグ修正 |
| docs | `docs/<description>` | 一時的 | develop | ドキュメント |
| refactor | `refactor/<scope>/<description>` | 一時的 | develop | リファクタリング |

### 2.2 ブランチ図

```
main        ──●─────────────────●─────────────●──
               \               / \           / \
release         \       ●──●──●   \   ●──●──●   \
                 \     /           \ /             \
develop    ──●────●───●────●────●───●────●────●────●──
              \  / \     / \      / \     /
feature        ●    ●───●   ●───●   ●───●
                    feature/  feature/ feature/
                    bcp-plan  drill    bia
```

---

## 3. ブランチ命名規則

### 3.1 命名フォーマット

```
<type>/<scope>/<short-description>
```

- **type**: ブランチ種別（feature, bugfix, hotfix, release, docs, refactor）
- **scope**: 機能スコープ（オプション。feature, bugfix, refactor では推奨）
- **short-description**: 簡潔な説明（kebab-case、英語）

### 3.2 命名例

| 種別 | 命名例 | 説明 |
|------|--------|------|
| feature | `feature/bcp-plan/version-management` | BCP計画のバージョン管理機能 |
| feature | `feature/drill/schedule-calendar` | 訓練スケジュールカレンダー機能 |
| feature | `feature/rto-dashboard/realtime-chart` | RTOダッシュボードリアルタイムチャート |
| feature | `feature/incident/auto-escalation` | インシデント自動エスカレーション |
| feature | `feature/bia/impact-assessment` | BIAインパクト評価機能 |
| feature | `feature/auth/azure-ad-integration` | Azure AD認証統合 |
| feature | `feature/notification/multi-channel` | マルチチャネル通知 |
| feature | `feature/pwa/offline-sync` | PWAオフライン同期 |
| bugfix | `bugfix/drill/date-calculation-error` | 訓練日付計算エラーの修正 |
| bugfix | `bugfix/rto-dashboard/websocket-leak` | WebSocketメモリリーク修正 |
| hotfix | `hotfix/security-patch-jwt` | JWT脆弱性の緊急修正 |
| hotfix | `hotfix/db-connection-pool-exhaustion` | DB接続プール枯渇の修正 |
| release | `release/1.0.0` | バージョン1.0.0リリース |
| release | `release/1.1.0` | バージョン1.1.0リリース |
| docs | `docs/api-specification-update` | API仕様書の更新 |
| refactor | `refactor/auth/middleware-restructure` | 認証ミドルウェアの構造改善 |

### 3.3 命名の禁止事項

- 日本語は使用しないこと
- スペースは使用しないこと（kebab-case を使用）
- 大文字は使用しないこと（全て小文字）
- 個人名は含めないこと（例: `feature/tanaka/xxx` は不可）
- Issue番号のみのブランチ名は不可（例: `feature/123` は不可）

---

## 4. ブランチワークフロー

### 4.1 feature ブランチワークフロー

#### 4.1.1 作成から完了まで

```bash
# 1. develop ブランチを最新化
git checkout develop
git pull origin develop

# 2. feature ブランチを作成
git checkout -b feature/bcp-plan/version-management

# 3. 開発作業（コミット）
git add .
git commit -m "feat(bcp-plan): バージョン管理のDBスキーマを追加"

git add .
git commit -m "feat(bcp-plan): バージョン管理のAPI実装"

git add .
git commit -m "feat(bcp-plan): バージョン管理のUIコンポーネント実装"

git add .
git commit -m "test(bcp-plan): バージョン管理のユニットテスト追加"

# 4. develop の最新変更を取り込み
git fetch origin
git rebase origin/develop

# 5. リモートにプッシュ
git push origin feature/bcp-plan/version-management

# 6. GitHub で PR を作成（develop ← feature）
# 7. コードレビュー
# 8. CI パイプライン確認
# 9. マージ（Squash and Merge 推奨）
# 10. feature ブランチ削除（自動）
```

#### 4.1.2 長期開発 feature ブランチの管理

長期間にわたる feature ブランチ（2週間以上）の場合:

```bash
# 定期的に develop の変更を取り込む（最低週1回）
git checkout feature/bcp-plan/version-management
git fetch origin
git rebase origin/develop

# コンフリクトが発生した場合は解決してから続行
git rebase --continue
```

### 4.2 release ブランチワークフロー

```bash
# 1. develop から release ブランチを作成
git checkout develop
git pull origin develop
git checkout -b release/1.0.0

# 2. バージョン番号の更新
# package.json, pyproject.toml 等のバージョンを更新
git commit -m "chore(release): バージョン1.0.0に更新"

# 3. リリース前の修正（バグ修正のみ）
git commit -m "fix(drill): リリース前バグ修正"

# 4. main にマージ
git checkout main
git merge --no-ff release/1.0.0

# 5. タグ付け
git tag -a v1.0.0 -m "Release v1.0.0"

# 6. develop にマージバック
git checkout develop
git merge --no-ff release/1.0.0

# 7. release ブランチ削除
git branch -d release/1.0.0

# 8. プッシュ
git push origin main develop --tags
```

### 4.3 hotfix ブランチワークフロー

```bash
# 1. main から hotfix ブランチを作成
git checkout main
git pull origin main
git checkout -b hotfix/security-patch-jwt

# 2. 緊急修正の実施
git commit -m "fix(auth): JWT署名検証の脆弱性を修正"

# 3. テストの追加・実行
git commit -m "test(auth): JWT検証のセキュリティテスト追加"

# 4. main にマージ
git checkout main
git merge --no-ff hotfix/security-patch-jwt

# 5. タグ付け
git tag -a v1.0.1 -m "Hotfix v1.0.1: JWT security patch"

# 6. develop にマージバック
git checkout develop
git merge --no-ff hotfix/security-patch-jwt

# 7. hotfix ブランチ削除
git branch -d hotfix/security-patch-jwt

# 8. プッシュ
git push origin main develop --tags
```

---

## 5. マージ戦略

### 5.1 マージ方法の使い分け

| マージ元 → マージ先 | マージ方法 | 理由 |
|--------------------|-----------|------|
| feature → develop | Squash and Merge | コミット履歴を整理 |
| bugfix → develop | Squash and Merge | コミット履歴を整理 |
| release → main | Merge Commit (--no-ff) | マージポイントを明示 |
| release → develop | Merge Commit (--no-ff) | マージポイントを明示 |
| hotfix → main | Merge Commit (--no-ff) | マージポイントを明示 |
| hotfix → develop | Merge Commit (--no-ff) | マージポイントを明示 |

### 5.2 Squash and Merge のルール

feature ブランチから develop へのマージ時は Squash and Merge を使用する。

- マージ後のコミットメッセージは Conventional Commits 形式に従うこと
- 複数機能が含まれる場合は、feature ブランチを分割すること

```
feat(bcp-plan): BCP計画のバージョン管理機能を実装 (#123)

- 計画の版数管理と履歴追跡機能を追加
- 差分表示による変更内容の可視化
- 過去バージョンへのロールバック機能
- ユニットテスト・E2Eテスト追加
```

### 5.3 マージ条件（Branch Protection Rules）

#### 5.3.1 main ブランチ保護ルール

| 項目 | 設定 |
|------|------|
| Require pull request | 有効 |
| Required approvals | 2 |
| Dismiss stale reviews | 有効 |
| Require status checks | 有効 |
| Required checks | `lint`, `test-backend`, `test-frontend`, `build`, `security-scan` |
| Require branches to be up to date | 有効 |
| Require signed commits | 有効 |
| Include administrators | 有効 |
| Allow force pushes | 無効 |
| Allow deletions | 無効 |

#### 5.3.2 develop ブランチ保護ルール

| 項目 | 設定 |
|------|------|
| Require pull request | 有効 |
| Required approvals | 1 |
| Dismiss stale reviews | 有効 |
| Require status checks | 有効 |
| Required checks | `lint`, `test-backend`, `test-frontend`, `build` |
| Require branches to be up to date | 有効 |
| Allow force pushes | 無効 |
| Allow deletions | 無効 |

---

## 6. コンフリクト解決手順

### 6.1 基本方針

- コンフリクトは常に feature/bugfix ブランチ側で解決すること
- develop や main ブランチ上では解決しないこと
- 不明な箇所は関連する開発者と相談して解決すること

### 6.2 解決手順

```bash
# 1. develop の最新を取得
git fetch origin

# 2. rebase でコンフリクトを検出
git rebase origin/develop

# 3. コンフリクトが発生した場合
# コンフリクトファイルを確認
git status

# 4. コンフリクトを手動で解決
# エディタでコンフリクトマーカーを解消

# 5. 解決済みファイルをステージング
git add <resolved-file>

# 6. rebase を続行
git rebase --continue

# 7. 全てのコンフリクトが解決されるまで 3-6 を繰り返す

# 8. force push（rebase 後のため必要）
git push --force-with-lease origin feature/bcp-plan/version-management
```

### 6.3 コンフリクト解決のベストプラクティス

| 項目 | 推奨事項 |
|------|---------|
| 頻度 | develop からの取り込みを最低週1回実施 |
| 粒度 | feature ブランチは小さく保つ（1-2週間で完了する規模） |
| ツール | VS Code の Git マージエディタを活用 |
| 確認 | 解決後に必ずテストを実行して動作確認 |
| 記録 | 重大なコンフリクトは PR コメントに解決方法を記録 |

### 6.4 `--force-with-lease` の使用

`git push --force` の代わりに `git push --force-with-lease` を使用すること。これにより、他者がプッシュした変更を意図せず上書きすることを防げる。

```bash
# 推奨
git push --force-with-lease origin feature/bcp-plan/version-management

# 禁止（--force の直接使用）
git push --force origin feature/bcp-plan/version-management
```

---

## 7. バージョニング

### 7.1 セマンティックバージョニング

[Semantic Versioning 2.0.0](https://semver.org/) に準拠する。

```
MAJOR.MINOR.PATCH
```

| 要素 | 条件 | 例 |
|------|------|-----|
| MAJOR | 後方互換性のない変更 | API の破壊的変更 |
| MINOR | 後方互換性のある機能追加 | 新機能の追加 |
| PATCH | 後方互換性のあるバグ修正 | バグ修正、セキュリティパッチ |

### 7.2 バージョン計画

| バージョン | 内容 | 予定時期 |
|-----------|------|---------|
| 0.1.0 | MVP（BCP計画管理基本機能） | - |
| 0.2.0 | 訓練管理機能 | - |
| 0.3.0 | インシデント対応機能 | - |
| 0.4.0 | BIA モジュール | - |
| 0.5.0 | RTO ダッシュボード | - |
| 0.6.0 | PWA / オフライン対応 | - |
| 0.7.0 | 通知・エスカレーション | - |
| 0.8.0 | DR マルチリージョン | - |
| 1.0.0 | 正式リリース | - |

### 7.3 タグ規約

```bash
# リリースタグ
git tag -a v1.0.0 -m "Release v1.0.0: 正式リリース"

# プレリリースタグ
git tag -a v1.0.0-rc.1 -m "Release Candidate 1 for v1.0.0"
git tag -a v1.0.0-beta.1 -m "Beta 1 for v1.0.0"
git tag -a v1.0.0-alpha.1 -m "Alpha 1 for v1.0.0"
```

---

## 8. ワークフロー図

### 8.1 通常の機能開発フロー

```
開発者                    GitHub                      CI/CD
  |                        |                           |
  |-- feature ブランチ作成 ->|                           |
  |-- コミット & プッシュ --->|                           |
  |-- PR 作成 ------------->|                           |
  |                        |-- CI トリガー ------------->|
  |                        |                           |-- lint
  |                        |                           |-- test
  |                        |                           |-- build
  |                        |<-- CI 結果 ----------------|
  |<-- レビュー依頼 --------|                           |
  |-- レビュー対応 -------->|                           |
  |                        |-- CI 再実行 -------------->|
  |                        |<-- CI 成功 ----------------|
  |                        |-- Squash & Merge -------->|
  |                        |-- ブランチ自動削除 ------->|
  |<-- 通知 ----------------|                           |
```

### 8.2 リリースフロー

```
リリース管理者              GitHub                      CI/CD                 Azure
  |                        |                           |                      |
  |-- release ブランチ作成 ->|                           |                      |
  |-- バージョン更新 ------->|                           |                      |
  |-- PR 作成 (→main) ----->|                           |                      |
  |                        |-- CI トリガー ------------->|                      |
  |                        |                           |-- 全テスト実行         |
  |                        |                           |-- セキュリティスキャン  |
  |                        |                           |-- ビルド              |
  |                        |<-- CI 成功 ----------------|                      |
  |-- 承認 (2名) ---------->|                           |                      |
  |                        |-- main にマージ ---------->|                      |
  |                        |-- タグ作成 --------------->|                      |
  |                        |                           |-- staging デプロイ --->|
  |                        |                           |                      |-- 動作確認
  |-- 本番デプロイ承認 ----->|                           |-- production デプロイ->|
  |                        |-- develop にマージバック -->|                      |
  |                        |-- release ブランチ削除 --->|                      |
```

### 8.3 Hotfix フロー

```
開発者                    GitHub                      CI/CD                 Azure
  |                        |                           |                      |
  |-- hotfix ブランチ作成 -->|                           |                      |
  |   (main から分岐)       |                           |                      |
  |-- 修正コミット -------->|                           |                      |
  |-- PR 作成 (→main) ----->|                           |                      |
  |                        |-- CI トリガー ------------->|                      |
  |                        |<-- CI 成功 ----------------|                      |
  |-- 緊急承認 (2名) ------>|                           |                      |
  |                        |-- main にマージ ---------->|                      |
  |                        |-- タグ作成 (patch) ------->|                      |
  |                        |                           |-- 緊急デプロイ ------->|
  |                        |-- develop にマージバック -->|                      |
  |                        |-- hotfix ブランチ削除 ---->|                      |
```

---

## 9. よくある質問（FAQ）

### Q1: feature ブランチで作業中に develop が大きく変わった場合は？

A: `git rebase origin/develop` で最新の変更を取り込むこと。コンフリクトが大きい場合はチームリードに相談し、段階的に解決すること。

### Q2: 複数人で同じ feature ブランチを使って良いか？

A: 原則として避けること。大きな機能は sub-feature ブランチに分割し、feature ブランチにマージする方式を推奨する。

```
feature/bcp-plan/version-management     (統合ブランチ)
  ├── feature/bcp-plan/version-db-schema  (サブブランチ1)
  ├── feature/bcp-plan/version-api        (サブブランチ2)
  └── feature/bcp-plan/version-ui         (サブブランチ3)
```

### Q3: rebase と merge のどちらを使うべきか？

A: feature ブランチでの develop 取り込みは `rebase`、develop / main への統合は `merge`（PR 経由）を使用する。

### Q4: コミットの粒度はどの程度が適切か？

A: 1つのコミットで1つの論理的な変更を表すこと。「動作する最小単位」を目安にする。ただし、WIP（Work In Progress）コミットは PR マージ時に Squash される。

### Q5: hotfix を develop にマージバックし忘れた場合は？

A: 発見次第、速やかに develop にマージバックすること。CI が通ることを確認した上で PR を作成する。

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-03-27 | 初版作成 | IT-BCP-ITSCM開発チーム |
