# 詳細設計仕様書
## IT事業継続管理システム（IT-BCP-ITSCM-System）

| 項目 | 内容 |
|------|------|
| **文書番号** | DES-BCP-001 |
| **バージョン** | 1.0.0 |
| **作成日** | 2026-03-22 |
| **対象リポジトリ** | Kensan196948G/IT-BCP-ITSCM-System |

---

## 1. システムアーキテクチャ

### 1.1 全体構成（高可用性設計）

```
┌──────────────────────────────────────────────────────────────────┐
│                    フロントエンド（PWA対応）                        │
│  Next.js 14 / TypeScript / Service Worker（オフライン対応）        │
│  BCPダッシュボード / RTOモニタリング / 訓練管理 / 緊急対応UI        │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼───────────────────────────────────────┐
│              バックエンドAPI（高可用性・マルチリージョン）           │
│  Python FastAPI / Azure Container Apps (East Japan + West Japan) │
└───────┬──────────┬──────────┬──────────┬────────────────────────┘
        │          │          │          │
┌───────▼──┐  ┌────▼──┐  ┌───▼────┐  ┌──▼─────────────────────┐
│PostgreSQL │  │Redis  │  │Celery  │  │  外部連携              │
│（Geo冗長）│  │Cluster│  │Worker  │  │  ITSM/Teams/SMS/Email  │
└──────────┘  └───────┘  └────────┘  └────────────────────────┘
```

### 1.2 高可用性・DR設計

```
[ユーザ] → [Azure Front Door] → [East Japan: Primary]
                                  ↕ レプリケーション（リアルタイム）
                               [West Japan: Standby]

フェイルオーバー:
- Primary障害検知: 30秒
- DNSフェイルオーバー: 60秒
- 合計: 最大90秒（RTO 15分の要件を大幅に達成）
```

### 1.3 ディレクトリ構成

```
IT-BCP-ITSCM-System/
├── backend/
│   ├── apps/
│   │   ├── plans/                   # BCP/ITSCM計画管理
│   │   │   ├── models.py            # 計画・手順・RTO/RPO
│   │   │   ├── views.py
│   │   │   └── services/
│   │   │       └── plan_service.py
│   │   ├── exercises/               # BCP訓練管理
│   │   │   ├── tabletop/            # テーブルトップ演習
│   │   │   └── realtest/            # 実機テスト管理
│   │   ├── incidents/               # 実災害時対応管理
│   │   │   ├── command_center.py    # 指揮支援
│   │   │   └── rto_tracker.py       # RTOトラッキング
│   │   ├── bia/                     # ビジネスインパクト分析
│   │   ├── contacts/                # 緊急連絡網
│   │   └── reports/                 # レポート生成
│   └── tests/
├── frontend/
│   ├── app/
│   │   ├── dashboard/               # BCPダッシュボード
│   │   ├── plans/                   # 計画管理
│   │   ├── exercises/               # 訓練管理
│   │   ├── command/                 # 緊急指揮センター
│   │   ├── contacts/                # 緊急連絡網
│   │   └── rto-monitor/             # RTOモニタリング
│   ├── public/
│   │   └── sw.js                    # Service Worker（オフライン）
│   └── offline/
│       └── critical-procedures/     # オフライン保存手順書
├── infrastructure/
│   ├── terraform/
│   │   ├── east_japan/              # 東日本リージョン
│   │   └── west_japan/              # 西日本リージョン（DR）
│   └── docker-compose.yml
└── docs/
```

---

## 2. データベース設計

### 2.1 主要テーブル

#### it_systems_bcp（ITシステムBCP設定）テーブル
```sql
CREATE TABLE it_systems_bcp (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_name     VARCHAR(100) UNIQUE NOT NULL,
    system_type     VARCHAR(30) NOT NULL,               -- onprem/cloud/hybrid
    criticality     VARCHAR(20) NOT NULL,               -- tier1/tier2/tier3/tier4
    
    -- RTO/RPO目標値
    rto_target_hours DECIMAL(5,1) NOT NULL,             -- 目標復旧時間（時間）
    rpo_target_hours DECIMAL(5,1) NOT NULL,             -- 目標復旧時点（時間）
    mtpd_hours      DECIMAL(5,1),                       -- 最大許容停止時間
    
    -- 復旧手順
    recovery_procedure_id UUID REFERENCES recovery_procedures(id),
    fallback_system VARCHAR(100),                       -- 代替手段
    fallback_procedure TEXT,
    
    -- 依存関係
    depends_on      VARCHAR(100)[],                     -- 依存システム
    supports        VARCHAR(100)[],                     -- 上位サービス
    
    -- 担当者
    primary_owner_id   UUID REFERENCES users(id),
    secondary_owner_id UUID REFERENCES users(id),
    vendor_contact_id  UUID REFERENCES vendor_contacts(id),
    
    -- 最終テスト
    last_dr_test    DATE,
    last_test_rto   DECIMAL(5,1),                       -- 直近テストの実測RTO
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### bcp_exercises（BCP訓練）テーブル
```sql
CREATE TABLE bcp_exercises (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id     VARCHAR(20) UNIQUE NOT NULL,        -- EX-2026-001
    title           VARCHAR(200) NOT NULL,
    exercise_type   VARCHAR(30) NOT NULL,               -- tabletop/functional/full_scale
    scenario_id     UUID REFERENCES bcp_scenarios(id),
    
    -- 日程
    scheduled_date  TIMESTAMPTZ NOT NULL,
    actual_date     TIMESTAMPTZ,
    duration_hours  DECIMAL(4,1),
    
    -- 参加者
    participants    UUID[],
    facilitator_id  UUID REFERENCES users(id),
    
    -- 結果
    status          VARCHAR(20) DEFAULT 'planned',      -- planned/in_progress/completed
    overall_result  VARCHAR(20),                        -- pass/partial_pass/fail
    
    -- RTO達成状況
    systems_tested  JSONB,
    -- [{system_name, rto_target, rto_actual, achieved: bool}]
    
    -- 所見・改善
    findings        JSONB,                              -- 課題リスト
    improvements    JSONB,                              -- 改善アクションリスト
    lessons_learned TEXT,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### active_incidents（実対応インシデント）テーブル
```sql
CREATE TABLE active_incidents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     VARCHAR(20) UNIQUE NOT NULL,        -- BCP-2026-001
    title           VARCHAR(300) NOT NULL,
    scenario_type   VARCHAR(50) NOT NULL,               -- earthquake/ransomware/dc_failure/etc
    severity        VARCHAR(20) NOT NULL,               -- p1/p2/p3
    
    -- 発生・検知
    occurred_at     TIMESTAMPTZ NOT NULL,
    detected_at     TIMESTAMPTZ NOT NULL,
    declared_at     TIMESTAMPTZ,                        -- BCP発動宣言時刻
    
    -- 指揮官
    incident_commander_id UUID REFERENCES users(id),
    
    -- 状況
    status          VARCHAR(20) DEFAULT 'active',       -- active/recovering/resolved
    situation_report TEXT,                              -- 最新状況サマリ
    
    -- 影響
    affected_systems VARCHAR(100)[],
    affected_users   INTEGER,
    estimated_impact TEXT,
    
    -- 復旧状況
    recovery_tasks   JSONB,                             -- タスクリスト
    rto_status       JSONB,                             -- システム別RTO達成状況
    
    resolved_at     TIMESTAMPTZ,
    actual_rto_hours DECIMAL(5,1),
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. RTOダッシュボード設計

### 3.1 RTOステータス計算

```python
# apps/incidents/rto_tracker.py

class RTOTracker:
    """実災害時のRTOリアルタイム追跡"""
    
    STATUS_COLORS = {
        'on_track': '#22c55e',       # 緑: RTO達成見込み
        'at_risk': '#eab308',        # 黄: RTO達成リスクあり
        'overdue': '#dc2626',        # 赤: RTO超過
        'recovered': '#2563eb',      # 青: 復旧完了
        'not_started': '#94a3b8'     # グレー: 未着手
    }
    
    def calculate_status(self, system_name: str, 
                          incident_start: datetime,
                          rto_hours: float,
                          is_recovered: bool) -> dict:
        """RTOステータス計算"""
        
        now = datetime.utcnow()
        elapsed_hours = (now - incident_start).total_seconds() / 3600
        
        if is_recovered:
            actual_rto = elapsed_hours
            return {
                'status': 'recovered',
                'color': self.STATUS_COLORS['recovered'],
                'elapsed_hours': round(elapsed_hours, 1),
                'actual_rto': round(actual_rto, 1),
                'rto_target': rto_hours,
                'achieved': actual_rto <= rto_hours
            }
        
        remaining_hours = rto_hours - elapsed_hours
        
        if remaining_hours > rto_hours * 0.3:
            status = 'on_track'
        elif remaining_hours > 0:
            status = 'at_risk'
        else:
            status = 'overdue'
        
        return {
            'status': status,
            'color': self.STATUS_COLORS[status],
            'elapsed_hours': round(elapsed_hours, 1),
            'remaining_hours': round(max(0, remaining_hours), 1),
            'rto_target': rto_hours,
            'overdue_hours': round(max(0, -remaining_hours), 1)
        }
    
    def get_overall_dashboard(self, incident_id: str) -> dict:
        """全システムRTO一覧ダッシュボード"""
        incident = ActiveIncident.objects.get(id=incident_id)
        systems = ITSystemBCP.objects.filter(
            system_name__in=incident.affected_systems
        ).order_by('criticality')
        
        dashboard = []
        for system in systems:
            is_recovered = self._check_recovery_status(system.system_name, incident)
            status = self.calculate_status(
                system.system_name,
                incident.occurred_at,
                float(system.rto_target_hours),
                is_recovered
            )
            dashboard.append({
                'system_name': system.system_name,
                'criticality': system.criticality,
                'owner': system.primary_owner.display_name,
                **status
            })
        
        return {
            'incident_id': str(incident_id),
            'elapsed_hours': round(
                (datetime.utcnow() - incident.occurred_at).total_seconds() / 3600, 1
            ),
            'systems': dashboard,
            'summary': self._summary(dashboard)
        }
```

---

## 4. テーブルトップ演習エンジン

### 4.1 演習進行管理

```python
# apps/exercises/tabletop/engine.py

class TabletopExerciseEngine:
    """テーブルトップ演習の進行管理エンジン"""
    
    def start_exercise(self, exercise_id: str) -> dict:
        """演習開始 - 全参加者に通知"""
        exercise = BCPExercise.objects.get(id=exercise_id)
        scenario = exercise.scenario
        
        # 演習タイマー開始
        exercise.actual_date = datetime.utcnow()
        exercise.status = 'in_progress'
        exercise.save()
        
        # 参加者に通知
        self._notify_participants(exercise, "演習開始", {
            "scenario": scenario.title,
            "description": scenario.initial_inject,
            "dashboard_url": f"/exercises/{exercise_id}/live"
        })
        
        # 自動インジェクション（段階的シナリオ展開）
        for inject in scenario.injects:
            schedule_inject.apply_async(
                args=[exercise_id, inject],
                countdown=inject['offset_minutes'] * 60
            )
        
        return {"status": "started", "exercise_id": str(exercise_id)}
    
    def record_rto(self, exercise_id: str, system_name: str, 
                    elapsed_minutes: float) -> dict:
        """訓練中のRTO達成記録"""
        exercise = BCPExercise.objects.get(id=exercise_id)
        system = ITSystemBCP.objects.get(system_name=system_name)
        
        elapsed_hours = elapsed_minutes / 60
        achieved = elapsed_hours <= float(system.rto_target_hours)
        
        # 結果記録
        rto_results = exercise.systems_tested or {}
        rto_results[system_name] = {
            'rto_target': float(system.rto_target_hours),
            'rto_actual': elapsed_hours,
            'achieved': achieved,
            'recorded_at': datetime.utcnow().isoformat()
        }
        exercise.systems_tested = rto_results
        exercise.save()
        
        return {
            'system': system_name,
            'achieved': achieved,
            'actual_hours': round(elapsed_hours, 2),
            'target_hours': float(system.rto_target_hours)
        }
```

---

## 5. PWA・オフライン設計

### 5.1 Service Worker設計

```javascript
// frontend/public/sw.js

const CACHE_NAME = 'bcp-itscm-v1';
const CRITICAL_ASSETS = [
  '/',
  '/offline',
  '/plans/recovery-procedures',    // IT復旧手順書
  '/contacts/emergency',           // 緊急連絡網
  '/command/quick-start',          // 初動対応チェックリスト
];

// インストール時: 重要アセットをキャッシュ
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(CRITICAL_ASSETS);
    })
  );
});

// フェッチ: キャッシュファースト戦略（BCP資料）
self.addEventListener('fetch', event => {
  if (isCriticalBCPResource(event.request.url)) {
    // BCP重要資料: キャッシュ優先 → ネットワークフォールバック
    event.respondWith(
      caches.match(event.request).then(cached => {
        return cached || fetch(event.request).then(response => {
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, response.clone()));
          return response;
        });
      })
    );
  } else {
    // 通常リソース: ネットワーク優先 → キャッシュフォールバック
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  }
});

function isCriticalBCPResource(url) {
  return ['/plans/', '/contacts/', '/command/'].some(p => url.includes(p));
}
```

---

## 6. 緊急連絡網設計

### 6.1 エスカレーション設計

```python
# apps/contacts/escalation.py

class EmergencyEscalation:
    """BCP発動時の緊急連絡・エスカレーション"""
    
    # エスカレーション経路定義
    ESCALATION_MATRIX = {
        'P1_FULL_BCP': [
            {'role': '対応チーム', 'notify_after': 0, 'channels': ['teams', 'sms']},
            {'role': 'IT部門長', 'notify_after': 5, 'channels': ['teams', 'sms', 'phone']},
            {'role': '経営層（CISO・CEO）', 'notify_after': 15, 'channels': ['sms', 'phone']},
            {'role': '全部門長', 'notify_after': 30, 'channels': ['teams', 'email']},
        ],
        'P2_PARTIAL_BCP': [
            {'role': '対応チーム', 'notify_after': 0, 'channels': ['teams']},
            {'role': 'IT部門長', 'notify_after': 15, 'channels': ['teams', 'email']},
        ],
    }
    
    async def trigger_escalation(self, incident_id: str, 
                                  severity: str) -> None:
        """BCP発動時の自動エスカレーション開始"""
        incident = await ActiveIncident.aget(id=incident_id)
        matrix = self.ESCALATION_MATRIX.get(severity, self.ESCALATION_MATRIX['P2_PARTIAL_BCP'])
        
        for level in matrix:
            await asyncio.sleep(level['notify_after'] * 60)
            contacts = await self._get_role_contacts(level['role'])
            
            for channel in level['channels']:
                if channel == 'sms':
                    await self._send_sms(contacts, incident)
                elif channel == 'teams':
                    await self._send_teams(contacts, incident)
                elif channel == 'email':
                    await self._send_email(contacts, incident)
```

---

## 7. インフラ設計（マルチリージョン）

### 7.1 Terraform（東日本・西日本）

```hcl
# infrastructure/terraform/main.tf

module "east_japan" {
  source = "./modules/region"
  
  location         = "japaneast"
  resource_prefix  = "bcp-east"
  is_primary       = true
  
  # 東日本: プライマリ
  container_apps_replicas = 3
  postgres_sku            = "GeneralPurpose_Standard_D4s_v3"
  redis_sku               = "Premium"
}

module "west_japan" {
  source = "./modules/region"
  
  location         = "japanwest"
  resource_prefix  = "bcp-west"
  is_primary       = false
  
  # 西日本: スタンバイ（DR）
  container_apps_replicas = 2
  postgres_sku            = "GeneralPurpose_Standard_D2s_v3"
  redis_sku               = "Standard"
}

# Azure Front Door（グローバル負荷分散・フェイルオーバー）
resource "azurerm_cdn_frontdoor_profile" "main" {
  name                = "bcp-frontdoor"
  resource_group_name = var.resource_group_name
  sku_name            = "Premium_AzureFrontDoor"
}
```

---

## 8. テスト仕様

### 8.1 DRテストシナリオ

| テスト | 内容 | 期待結果 |
|--------|------|---------|
| フェイルオーバーテスト | East Japan停止→West Japan切替 | 90秒以内に切替完了 |
| オフライン動作テスト | ネットワーク断絶時PWA動作確認 | 重要資料の参照可能 |
| RTOトラッカーテスト | 模擬インシデント発生時の表示確認 | リアルタイム更新確認 |
| 通知テスト | エスカレーション自動発動確認 | 各チャネルへの通知確認 |

---

*文書管理：本文書はバージョン管理対象。*
