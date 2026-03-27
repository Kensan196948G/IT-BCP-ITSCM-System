# 性能テスト仕様書 (Performance Test Specification)

| 項目 | 内容 |
|------|------|
| 文書番号 | TEST-PERF-004 |
| バージョン | 1.0.0 |
| 作成日 | 2026-03-27 |
| 最終更新日 | 2026-03-27 |
| 作成者 | IT-BCP-ITSCM開発チーム |
| 分類 | テスト |
| 対象システム | IT事業継続管理システム (IT-BCP-ITSCM-System) |

---

## 1. 概要

### 1.1 目的

本文書は、IT事業継続管理システムの性能テスト仕様を定義する。システムが想定される負荷条件下で要求されるレスポンスタイム、スループット、安定性を満たすことを検証する。特に、災害発生時に多数のユーザーが同時アクセスする状況を想定した負荷テスト、およびRTOダッシュボードのリアルタイム更新性能に重点を置く。

### 1.2 性能要件サマリー

| 項目 | 要件値 |
|------|--------|
| 同時接続ユーザー数（通常時） | 200 |
| 同時接続ユーザー数（災害時ピーク） | 500 |
| API レスポンスタイム（P50） | 200ms 以下 |
| API レスポンスタイム（P95） | 500ms 以下 |
| API レスポンスタイム（P99） | 1,000ms 以下 |
| スループット | 500 req/s 以上 |
| エラー率 | 0.1% 以下 |
| RTOダッシュボード更新遅延 | 3秒以下 |
| WebSocket同時接続数 | 200 |
| ページロード時間（初回） | 3秒以下 |
| ページロード時間（以降） | 1秒以下 |
| データベースクエリ時間（P95） | 100ms 以下 |

### 1.3 テストツール

| ツール | 用途 | バージョン |
|-------|------|-----------|
| k6 | 負荷テスト・ストレステスト | 最新 |
| Locust | 補助的な負荷テスト | 最新 |
| Lighthouse | フロントエンド性能測定 | 最新 |
| Azure Load Testing | クラウドベース負荷テスト | - |
| Application Insights | APM・モニタリング | - |
| pgbench | PostgreSQL ベンチマーク | PostgreSQL 16同梱 |

---

## 2. テスト環境

### 2.1 性能テスト環境構成

| コンポーネント | スペック | 備考 |
|--------------|---------|------|
| Container Apps (Backend) | 2vCPU / 4GBメモリ x 3レプリカ | 本番同等 |
| Container Apps (Frontend) | 1vCPU / 2GBメモリ x 3レプリカ | 本番同等 |
| PostgreSQL | Standard_D4ds_v4 (4vCPU/16GB) | 本番同等 |
| Redis | Premium P1 (6GB) | 本番同等 |
| Celery Worker | 2vCPU / 4GBメモリ x 2ワーカー | 本番同等 |
| 負荷生成器 | k6 Cloud / Azure Load Testing | 複数リージョン分散 |

### 2.2 テストデータ

| データ種別 | 件数 | 備考 |
|-----------|------|------|
| ユーザー | 1,000 | 各ロール均等配分 |
| BCP計画 | 500 | 各ステータス均等配分 |
| 訓練記録 | 2,000 | 過去2年分 |
| インシデント | 5,000 | 過去2年分 |
| BIA資産 | 1,000 | 依存関係含む |
| 監査ログ | 100,000 | 過去1年分 |

---

## 3. 負荷テスト

### 3.1 テストシナリオ一覧

| テストID | テスト名 | 同時ユーザー | 持続時間 | 目的 |
|---------|---------|------------|---------|------|
| PERF-LOAD-001 | 通常時負荷テスト | 200 | 30分 | 通常運用時の性能確認 |
| PERF-LOAD-002 | ピーク時負荷テスト | 500 | 15分 | 災害時ピーク負荷の性能確認 |
| PERF-LOAD-003 | ランプアップテスト | 0→500 | 30分 | 段階的負荷増加時の挙動確認 |
| PERF-LOAD-004 | 長時間持続テスト | 200 | 4時間 | 長時間稼働時のメモリリーク等検出 |
| PERF-LOAD-005 | バースト負荷テスト | 0→500→0 (繰返し) | 30分 | 急激な負荷変動への対応確認 |

### 3.2 PERF-LOAD-001: 通常時負荷テスト

#### 3.2.1 テスト概要

| 項目 | 内容 |
|------|------|
| テストID | PERF-LOAD-001 |
| テスト名 | 通常時負荷テスト |
| 目的 | 通常運用時（200同時ユーザー）にレスポンスタイム要件を満たすことを検証 |
| 同時ユーザー数 | 200 |
| ランプアップ | 0→200（5分間） |
| 定常状態 | 200ユーザー（25分間） |
| 合格基準 | P95 < 500ms, P99 < 1000ms, エラー率 < 0.1% |

#### 3.2.2 ユーザーシナリオ配分

| シナリオ | 比率 | 操作内容 |
|---------|------|---------|
| BCP計画閲覧 | 30% | ログイン → 一覧表示 → 詳細表示 → ログアウト |
| RTOダッシュボード監視 | 25% | ログイン → ダッシュボード表示 → WebSocket接続維持（5分） |
| 訓練管理操作 | 15% | ログイン → 訓練一覧 → 訓練詳細 → 評価入力 |
| インシデント登録 | 15% | ログイン → インシデント登録 → エスカレーション |
| BIA管理 | 10% | ログイン → 資産一覧 → 影響度評価 |
| 管理者操作 | 5% | ログイン → ユーザー管理 → 設定変更 |

#### 3.2.3 k6 テストスクリプト

```javascript
import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const apiResponseTime = new Trend('api_response_time', true);

export const options = {
  stages: [
    { duration: '5m', target: 200 },   // ランプアップ
    { duration: '25m', target: 200 },   // 定常状態
    { duration: '2m', target: 0 },      // ランプダウン
  ],
  thresholds: {
    http_req_duration: ['p(50)<200', 'p(95)<500', 'p(99)<1000'],
    errors: ['rate<0.001'],
    http_req_failed: ['rate<0.001'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'https://staging.itbcp-system.example.com';

// シナリオ: BCP計画閲覧
function bcpPlanBrowse(authToken) {
  // BCP計画一覧取得
  const listRes = http.get(`${BASE_URL}/api/v1/bcp-plans?page=1&per_page=20`, {
    headers: { 'Authorization': `Bearer ${authToken}` },
    tags: { name: 'BCP計画一覧' },
  });
  check(listRes, { 'BCP計画一覧 200': (r) => r.status === 200 });
  apiResponseTime.add(listRes.timings.duration);
  errorRate.add(listRes.status !== 200);

  sleep(2);

  // BCP計画詳細取得
  if (listRes.status === 200) {
    const plans = listRes.json('data');
    if (plans && plans.length > 0) {
      const planId = plans[Math.floor(Math.random() * plans.length)].id;
      const detailRes = http.get(`${BASE_URL}/api/v1/bcp-plans/${planId}`, {
        headers: { 'Authorization': `Bearer ${authToken}` },
        tags: { name: 'BCP計画詳細' },
      });
      check(detailRes, { 'BCP計画詳細 200': (r) => r.status === 200 });
      apiResponseTime.add(detailRes.timings.duration);
    }
  }

  sleep(3);
}

// シナリオ: RTOダッシュボード
function rtoDashboardMonitor(authToken) {
  // ダッシュボードAPI
  const dashRes = http.get(`${BASE_URL}/api/v1/rto-dashboard`, {
    headers: { 'Authorization': `Bearer ${authToken}` },
    tags: { name: 'RTOダッシュボード' },
  });
  check(dashRes, { 'RTOダッシュボード 200': (r) => r.status === 200 });
  apiResponseTime.add(dashRes.timings.duration);

  // WebSocket接続
  const wsUrl = BASE_URL.replace('https://', 'wss://') + '/ws/rto-dashboard';
  const wsRes = ws.connect(wsUrl, {
    headers: { 'Authorization': `Bearer ${authToken}` },
  }, function (socket) {
    socket.on('message', function (msg) {
      // RTOデータ受信の検証
      const data = JSON.parse(msg);
      check(data, { 'RTO更新データ受信': (d) => d.type === 'rto_update' });
    });

    socket.setTimeout(function () {
      socket.close();
    }, 300000); // 5分間接続維持
  });

  check(wsRes, { 'WebSocket接続成功': (r) => r && r.status === 101 });
}

// メインシナリオ
export default function () {
  // ログイン
  const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    email: `user${__VU}@test.example.com`,
    password: 'TestPassword123!',
  }), {
    headers: { 'Content-Type': 'application/json' },
    tags: { name: 'ログイン' },
  });
  check(loginRes, { 'ログイン成功': (r) => r.status === 200 });

  if (loginRes.status !== 200) {
    errorRate.add(true);
    return;
  }

  const authToken = loginRes.json('access_token');
  const scenario = Math.random();

  if (scenario < 0.30) {
    bcpPlanBrowse(authToken);
  } else if (scenario < 0.55) {
    rtoDashboardMonitor(authToken);
  } else if (scenario < 0.70) {
    // 訓練管理操作（省略）
    sleep(5);
  } else if (scenario < 0.85) {
    // インシデント登録（省略）
    sleep(5);
  } else if (scenario < 0.95) {
    // BIA管理（省略）
    sleep(5);
  } else {
    // 管理者操作（省略）
    sleep(5);
  }
}
```

#### 3.2.4 計測項目と合格基準

| 計測項目 | 合格基準 | 計測方法 |
|---------|---------|---------|
| HTTP レスポンスタイム P50 | 200ms 以下 | k6 メトリクス |
| HTTP レスポンスタイム P95 | 500ms 以下 | k6 メトリクス |
| HTTP レスポンスタイム P99 | 1,000ms 以下 | k6 メトリクス |
| エラー率 | 0.1% 以下 | k6 メトリクス |
| スループット | 500 req/s 以上 | k6 メトリクス |
| CPU使用率（Backend） | 70% 以下 | Azure Monitor |
| メモリ使用率（Backend） | 80% 以下 | Azure Monitor |
| DB接続プール使用率 | 70% 以下 | Application Insights |
| Redis メモリ使用率 | 60% 以下 | Azure Monitor |

### 3.3 PERF-LOAD-002: ピーク時負荷テスト

| 項目 | 内容 |
|------|------|
| テストID | PERF-LOAD-002 |
| テスト名 | ピーク時負荷テスト（災害時想定） |
| 目的 | 災害発生時の同時500ユーザーアクセスに耐えることを検証 |
| シナリオ | 災害発生直後、全ユーザーがRTOダッシュボードとBCP計画に集中アクセス |
| 同時ユーザー数 | 500 |
| ランプアップ | 0→500（2分間、急激な増加を再現） |
| 定常状態 | 500ユーザー（13分間） |
| 合格基準 | P95 < 1000ms, P99 < 2000ms, エラー率 < 0.5% |

#### 3.3.1 災害時シナリオ配分

| シナリオ | 比率 | 備考 |
|---------|------|------|
| RTOダッシュボード閲覧 | 50% | 災害時最優先 |
| BCP計画閲覧 | 30% | 復旧手順確認 |
| インシデント登録・更新 | 15% | 状況報告 |
| 緊急通知送信 | 5% | 管理者のみ |

#### 3.3.2 合格基準

| 計測項目 | 合格基準 |
|---------|---------|
| HTTP レスポンスタイム P95 | 1,000ms 以下 |
| HTTP レスポンスタイム P99 | 2,000ms 以下 |
| エラー率 | 0.5% 以下 |
| WebSocket接続成功率 | 99% 以上 |
| RTOダッシュボード更新遅延 | 5秒以下（通常時3秒以下） |
| 自動スケーリング応答 | 3分以内にスケールアウト開始 |

### 3.4 PERF-LOAD-003: ランプアップテスト

| 項目 | 内容 |
|------|------|
| テストID | PERF-LOAD-003 |
| テスト名 | ランプアップテスト |
| 目的 | 段階的な負荷増加時に性能劣化の閾値を特定 |
| パターン | 0→50→100→200→300→400→500（各段階5分間維持） |
| 合格基準 | 各段階での性能メトリクスを記録。劣化傾向を分析 |

#### 3.4.1 計測ポイント

各段階で以下のメトリクスを記録し、性能劣化カーブを分析する。

| 段階 | 同時ユーザー | P50目標 | P95目標 | P99目標 |
|------|------------|---------|---------|---------|
| 1 | 50 | 100ms | 200ms | 400ms |
| 2 | 100 | 120ms | 250ms | 500ms |
| 3 | 200 | 150ms | 350ms | 700ms |
| 4 | 300 | 200ms | 450ms | 900ms |
| 5 | 400 | 250ms | 600ms | 1200ms |
| 6 | 500 | 300ms | 800ms | 1500ms |

---

## 4. ストレステスト

### 4.1 テストシナリオ一覧

| テストID | テスト名 | 条件 | 持続時間 | 目的 |
|---------|---------|------|---------|------|
| PERF-STRESS-001 | 限界負荷テスト | 500→1000 | 15分 | システム限界の特定 |
| PERF-STRESS-002 | リソース枯渇テスト | DB接続プール上限超過 | 10分 | 接続プール枯渇時の挙動 |
| PERF-STRESS-003 | メモリ負荷テスト | 大量データ取得 | 30分 | メモリリークの検出 |
| PERF-STRESS-004 | 障害回復テスト | 高負荷→障害→回復 | 20分 | 障害後の回復能力 |

### 4.2 PERF-STRESS-001: 限界負荷テスト

| 項目 | 内容 |
|------|------|
| テストID | PERF-STRESS-001 |
| テスト名 | 限界負荷テスト |
| 目的 | システムのブレークポイント（性能が急激に劣化する負荷レベル）を特定 |
| パターン | 500→600→700→800→900→1000（各段階3分間） |
| 観測項目 | エラー率の急増、レスポンスタイムの急劣化、タイムアウト発生 |

#### 4.2.1 判定基準

| 指標 | ブレークポイント判定条件 |
|------|----------------------|
| エラー率 | 1% を超過した時点 |
| P99 レスポンスタイム | 5秒を超過した時点 |
| タイムアウト率 | 0.5% を超過した時点 |
| CPU使用率 | 90% を超過した時点 |
| メモリ使用率 | 90% を超過した時点 |

### 4.3 PERF-STRESS-002: リソース枯渇テスト

| 項目 | 内容 |
|------|------|
| テストID | PERF-STRESS-002 |
| テスト名 | データベース接続プール枯渇テスト |
| 目的 | DB接続プールが枯渇した際にシステムが適切にエラーハンドリングすることを検証 |
| 方法 | 接続プール上限を意図的に10に制限し、同時200ユーザーで負荷実行 |
| 合格基準 | 適切なエラーメッセージ（503）返却。システムクラッシュなし。プール回復後に正常復帰 |

#### 4.3.1 テスト手順

| ステップ | 操作 | 確認事項 |
|---------|------|---------|
| 1 | DB接続プール上限を10に設定 | 設定反映確認 |
| 2 | 200ユーザーで負荷開始 | 接続プール枯渇 |
| 3 | エラーレスポンスの確認 | 503 Service Temporarily Unavailable |
| 4 | エラーログの確認 | 接続プール枯渇の警告ログ |
| 5 | DB接続プール上限を100に復旧 | 設定変更 |
| 6 | 自動回復の確認 | 正常レスポンスに復帰 |
| 7 | 回復までの時間計測 | 30秒以内 |

### 4.4 PERF-STRESS-003: メモリ負荷テスト

| 項目 | 内容 |
|------|------|
| テストID | PERF-STRESS-003 |
| テスト名 | 長時間メモリ負荷テスト |
| 目的 | 長時間稼働時のメモリリークの有無を検出 |
| パターン | 200ユーザー定常負荷を4時間継続 |
| 合格基準 | メモリ使用量の線形増加が見られないこと（リーク無し） |

#### 4.4.1 計測項目

| 項目 | 計測間隔 | 判定基準 |
|------|---------|---------|
| Backend プロセスメモリ | 1分間隔 | 4時間で10%以上の増加でNG |
| Frontend プロセスメモリ | 1分間隔 | 4時間で10%以上の増加でNG |
| PostgreSQL メモリ | 1分間隔 | 安定していること |
| Redis メモリ | 1分間隔 | TTL設定通りにキー削除されること |
| Celery Worker メモリ | 1分間隔 | タスク完了後にメモリ解放されること |

---

## 5. RTOダッシュボードリアルタイム更新性能テスト

### 5.1 テストシナリオ一覧

| テストID | テスト名 | 条件 | 目的 |
|---------|---------|------|------|
| PERF-RTO-001 | WebSocket更新遅延テスト | 100接続 | リアルタイム更新の遅延測定 |
| PERF-RTO-002 | 大規模同時WebSocket接続 | 200接続 | 同時接続時の性能確認 |
| PERF-RTO-003 | 高頻度更新テスト | 100接続 + 1秒間隔更新 | 高頻度更新時の安定性 |
| PERF-RTO-004 | WebSocket再接続テスト | 100接続 + 断続的切断 | 再接続時の性能確認 |

### 5.2 PERF-RTO-001: WebSocket更新遅延テスト

| 項目 | 内容 |
|------|------|
| テストID | PERF-RTO-001 |
| テスト名 | RTOダッシュボードWebSocket更新遅延テスト |
| 目的 | RTO値の更新がWebSocket経由で3秒以内にクライアントに到達することを検証 |
| 前提条件 | 100クライアントがWebSocket接続中。10システムのRTO情報が対象 |
| 合格基準 | 更新遅延 P50 < 1秒、P95 < 3秒、P99 < 5秒 |

#### 5.2.1 テスト手順

| ステップ | 操作 | 確認事項 | 計測項目 |
|---------|------|---------|---------|
| 1 | 100クライアントをWebSocket接続 | 全接続成功 | 接続成功率 |
| 2 | バックエンドでRTO値を更新（API経由） | 更新成功 | API応答時間 |
| 3 | 更新がWebSocket経由で各クライアントに到達するまでの時間を計測 | 3秒以内 | 配信遅延 |
| 4 | 100回連続でRTO更新を実施（5秒間隔） | 全配信成功 | 配信成功率 |
| 5 | 更新遅延のパーセンタイル集計 | P95 < 3秒 | パーセンタイル値 |

#### 5.2.2 計測方法

```javascript
// k6 WebSocket 性能テストスクリプト
import ws from 'k6/ws';
import { Trend } from 'k6/metrics';

const wsLatency = new Trend('ws_message_latency', true);

export default function () {
  const url = 'wss://staging.itbcp-system.example.com/ws/rto-dashboard';

  ws.connect(url, {
    headers: { 'Authorization': `Bearer ${authToken}` },
  }, function (socket) {
    socket.on('message', function (msg) {
      const data = JSON.parse(msg);
      if (data.type === 'rto_update' && data.server_timestamp) {
        const latency = Date.now() - new Date(data.server_timestamp).getTime();
        wsLatency.add(latency);
      }
    });

    // テスト持続時間
    socket.setTimeout(function () {
      socket.close();
    }, 600000); // 10分
  });
}
```

#### 5.2.3 合格基準

| 計測項目 | 合格基準 |
|---------|---------|
| WebSocket 配信遅延 P50 | 1,000ms 以下 |
| WebSocket 配信遅延 P95 | 3,000ms 以下 |
| WebSocket 配信遅延 P99 | 5,000ms 以下 |
| WebSocket 接続成功率 | 99.9% 以上 |
| メッセージ配信成功率 | 99.9% 以上 |
| メッセージ順序保証 | 100%（順序逆転なし） |

### 5.3 PERF-RTO-002: 大規模同時WebSocket接続テスト

| 項目 | 内容 |
|------|------|
| テストID | PERF-RTO-002 |
| テスト名 | 大規模同時WebSocket接続テスト |
| 目的 | 200のWebSocket同時接続時にRTOダッシュボードが正常に機能することを検証 |
| 合格基準 | 全接続維持。メモリ使用量の安定。配信遅延5秒以内 |

#### 5.3.1 テスト手順

| ステップ | 操作 | 確認事項 |
|---------|------|---------|
| 1 | 200クライアントを段階的にWebSocket接続（10接続/秒） | 全接続成功 |
| 2 | 全クライアント接続後、5分間のRTO更新を実施 | 全クライアントにデータ配信 |
| 3 | サーバーリソース（CPU、メモリ、接続数）を監視 | 閾値以内 |
| 4 | 配信遅延の計測 | 5秒以内 |
| 5 | 10分間の安定稼働確認 | 接続断なし |

### 5.4 PERF-RTO-003: 高頻度更新テスト

| 項目 | 内容 |
|------|------|
| テストID | PERF-RTO-003 |
| テスト名 | 高頻度RTO更新テスト |
| 目的 | 1秒間隔のRTO更新が安定して配信されることを検証 |
| 条件 | 100接続、10システムのRTOを1秒間隔で更新（10分間） |
| 合格基準 | メッセージロスなし。配信遅延3秒以内 |

---

## 6. データベース性能テスト

### 6.1 テストシナリオ一覧

| テストID | テスト名 | 条件 | 目的 |
|---------|---------|------|------|
| PERF-DB-001 | 複雑クエリ性能テスト | BIA依存関係グラフ | 複雑なJOINクエリの性能 |
| PERF-DB-002 | 大量データ検索性能 | 10万件監査ログ検索 | インデックス効果の検証 |
| PERF-DB-003 | 書き込み性能テスト | 同時100件インシデント登録 | 書き込みスループット |
| PERF-DB-004 | pgbenchベンチマーク | 標準ベンチマーク | DB全体のベースライン |

### 6.2 PERF-DB-001: 複雑クエリ性能テスト

| 項目 | 内容 |
|------|------|
| テストID | PERF-DB-001 |
| テスト名 | BIA依存関係グラフクエリ性能 |
| 目的 | BIA資産間の依存関係を再帰的に取得するクエリの性能を検証 |
| 対象クエリ | 再帰CTE（WITH RECURSIVE）を使用した依存関係グラフ取得 |
| 合格基準 | 1000資産・5000依存関係で1秒以内 |

#### 6.2.1 対象クエリ例

```sql
WITH RECURSIVE dependency_graph AS (
    -- ベースケース
    SELECT
        a.id,
        a.name,
        a.category,
        a.impact_score,
        d.dependency_type,
        1 as depth,
        ARRAY[a.id] as path
    FROM bia_assets a
    JOIN bia_dependencies d ON a.id = d.dependent_asset_id
    WHERE d.source_asset_id = :target_asset_id

    UNION ALL

    -- 再帰ケース
    SELECT
        a.id,
        a.name,
        a.category,
        a.impact_score,
        d.dependency_type,
        dg.depth + 1,
        dg.path || a.id
    FROM bia_assets a
    JOIN bia_dependencies d ON a.id = d.dependent_asset_id
    JOIN dependency_graph dg ON d.source_asset_id = dg.id
    WHERE NOT a.id = ANY(dg.path)  -- 循環防止
    AND dg.depth < 10              -- 深さ制限
)
SELECT * FROM dependency_graph ORDER BY depth, impact_score DESC;
```

#### 6.2.2 計測項目

| データ規模 | 目標値 |
|-----------|--------|
| 100資産 / 500依存関係 | 100ms 以下 |
| 500資産 / 2,500依存関係 | 500ms 以下 |
| 1,000資産 / 5,000依存関係 | 1,000ms 以下 |

---

## 7. フロントエンド性能テスト

### 7.1 Lighthouse スコア基準

| メトリクス | 目標値 | 備考 |
|-----------|--------|------|
| Performance Score | 90 以上 | - |
| First Contentful Paint (FCP) | 1.8秒以下 | - |
| Largest Contentful Paint (LCP) | 2.5秒以下 | Core Web Vitals |
| Cumulative Layout Shift (CLS) | 0.1 以下 | Core Web Vitals |
| Interaction to Next Paint (INP) | 200ms 以下 | Core Web Vitals |
| Time to Interactive (TTI) | 3.8秒以下 | - |
| Total Blocking Time (TBT) | 200ms 以下 | - |

### 7.2 ページ別性能基準

| ページ | LCP目標 | TTI目標 | バンドルサイズ目標 |
|-------|---------|---------|-----------------|
| ログイン画面 | 1.5秒 | 2.0秒 | 100KB以下 |
| ダッシュボード | 2.5秒 | 3.5秒 | 200KB以下 |
| BCP計画一覧 | 2.0秒 | 3.0秒 | 150KB以下 |
| BCP計画詳細 | 2.0秒 | 3.0秒 | 180KB以下 |
| RTOダッシュボード | 2.5秒 | 3.5秒 | 250KB以下 |
| BIA依存関係マップ | 3.0秒 | 4.0秒 | 300KB以下 |

---

## 8. テスト結果報告テンプレート

### 8.1 性能テスト結果報告書

```markdown
# 性能テスト結果報告書

## 実施概要
- テスト日時: YYYY-MM-DD HH:MM - HH:MM
- テスト種別: [負荷/ストレス/RTO性能/DB性能/フロントエンド]
- テスト環境: staging / DR専用
- テストツール: k6 / Locust / Lighthouse
- 実施者: [氏名]

## テスト結果サマリー
| テストID | テスト名 | 結果 | P50 | P95 | P99 | エラー率 | 判定 |
|---------|---------|------|-----|-----|-----|---------|------|

## リソース使用状況
| リソース | ピーク値 | 基準値 | 判定 |
|---------|---------|--------|------|

## ボトルネック分析
[特定されたボトルネックと改善提案]

## 推奨事項
[性能改善のための推奨事項]
```

---

## 9. テスト実施スケジュール

| テスト種別 | 頻度 | 実施タイミング |
|-----------|------|-------------|
| 負荷テスト（通常） | リリース前 | staging環境デプロイ後 |
| 負荷テスト（ピーク） | リリース前 | staging環境デプロイ後 |
| ストレステスト | 四半期 | 計画的メンテナンス時 |
| RTOダッシュボード性能 | 月次 | 定期テスト |
| DB性能テスト | リリース前（スキーマ変更時） | マイグレーション後 |
| フロントエンド性能 | リリース前 | ビルド後 |
| 長時間持続テスト | 四半期 | 計画的メンテナンス時 |

---

## 改訂履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|-----------|------|---------|--------|
| 1.0.0 | 2026-03-27 | 初版作成 | IT-BCP-ITSCM開発チーム |
