"""Runbook module: operational procedures as code.

Provides deployment checklists, rollback procedures,
DR failover steps, and incident response playbooks.
"""

from datetime import datetime, timezone


class Runbook:
    """Operational runbook for IT-BCP-ITSCM-System."""

    @staticmethod
    def get_deployment_checklist() -> dict:
        """Return pre-deployment checklist with 12 verification items."""
        return {
            "title": "デプロイ前チェックリスト",
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "items": [
                {
                    "id": 1,
                    "category": "テスト",
                    "item": "全ユニットテストがパスしていること",
                    "required": True,
                },
                {
                    "id": 2,
                    "category": "テスト",
                    "item": "E2Eテストがパスしていること",
                    "required": True,
                },
                {
                    "id": 3,
                    "category": "品質",
                    "item": "Lintチェック(black/flake8)が通過していること",
                    "required": True,
                },
                {
                    "id": 4,
                    "category": "品質",
                    "item": "フロントエンドビルドが成功していること",
                    "required": True,
                },
                {
                    "id": 5,
                    "category": "セキュリティ",
                    "item": "セキュリティスキャン(依存関係)が完了していること",
                    "required": True,
                },
                {
                    "id": 6,
                    "category": "セキュリティ",
                    "item": "シークレット漏洩チェックが完了していること",
                    "required": True,
                },
                {
                    "id": 7,
                    "category": "データベース",
                    "item": "DBマイグレーションが確認済みであること",
                    "required": True,
                },
                {
                    "id": 8,
                    "category": "データベース",
                    "item": "DBバックアップが取得済みであること",
                    "required": True,
                },
                {
                    "id": 9,
                    "category": "インフラ",
                    "item": "Terraformプランがレビュー済みであること",
                    "required": True,
                },
                {
                    "id": 10,
                    "category": "インフラ",
                    "item": "ロールバック手順が準備されていること",
                    "required": True,
                },
                {
                    "id": 11,
                    "category": "承認",
                    "item": "変更管理チケットが承認済みであること",
                    "required": True,
                },
                {
                    "id": 12,
                    "category": "承認",
                    "item": "関係者への事前通知が完了していること",
                    "required": False,
                },
            ],
            "total_items": 12,
        }

    @staticmethod
    def get_rollback_procedure() -> dict:
        """Return rollback procedure with 8 steps."""
        return {
            "title": "ロールバック手順",
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "steps": [
                {
                    "step": 1,
                    "action": "異常検知・ロールバック判断",
                    "description": "監視アラートまたは手動確認により異常を検知し、ロールバックの実施を判断する。",
                    "responsible": "インシデントコマンダー",
                    "estimated_minutes": 5,
                },
                {
                    "step": 2,
                    "action": "関係者への通知",
                    "description": "ロールバック開始をTeams/メールで関係者に通知する。",
                    "responsible": "運用チーム",
                    "estimated_minutes": 3,
                },
                {
                    "step": 3,
                    "action": "トラフィック遮断",
                    "description": "Front Doorまたはロードバランサーでトラフィックをメンテナンスページへ切替。",
                    "responsible": "インフラチーム",
                    "estimated_minutes": 2,
                },
                {
                    "step": 4,
                    "action": "コンテナイメージの切り戻し",
                    "description": "Container Appsのイメージタグを前バージョンに変更してデプロイ。",
                    "responsible": "インフラチーム",
                    "estimated_minutes": 10,
                },
                {
                    "step": 5,
                    "action": "DBマイグレーションのロールバック",
                    "description": "必要に応じてDBマイグレーションを逆方向に実行、またはバックアップからリストア。",
                    "responsible": "DBAチーム",
                    "estimated_minutes": 15,
                },
                {
                    "step": 6,
                    "action": "動作確認",
                    "description": "ヘルスチェックエンドポイント、主要機能の動作確認を実施。",
                    "responsible": "QAチーム",
                    "estimated_minutes": 10,
                },
                {
                    "step": 7,
                    "action": "トラフィック復旧",
                    "description": "Front Doorのルーティングを本番アプリケーションに戻す。",
                    "responsible": "インフラチーム",
                    "estimated_minutes": 2,
                },
                {
                    "step": 8,
                    "action": "事後報告・原因分析",
                    "description": "ロールバック完了を通知し、根本原因分析(RCA)のチケットを作成する。",
                    "responsible": "運用チーム",
                    "estimated_minutes": 30,
                },
            ],
            "total_steps": 8,
            "estimated_total_minutes": 77,
        }

    @staticmethod
    def get_dr_failover_steps() -> dict:
        """Return DR failover procedure with 10 steps."""
        return {
            "title": "DRフェイルオーバー手順",
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "steps": [
                {
                    "step": 1,
                    "action": "災害発生の確認",
                    "description": "プライマリリージョン(東日本)の障害を確認し、DRフェイルオーバーの発動を判断。",
                    "responsible": "インシデントコマンダー",
                    "estimated_minutes": 10,
                },
                {
                    "step": 2,
                    "action": "DR発動宣言",
                    "description": "経営層・関係者にDR発動を宣言し、戦況室(War Room)を開設。",
                    "responsible": "CIO/CISO",
                    "estimated_minutes": 5,
                },
                {
                    "step": 3,
                    "action": "DRサイト(西日本)の状態確認",
                    "description": "西日本リージョンのインフラ・アプリケーション・DBレプリカの状態を確認。",
                    "responsible": "インフラチーム",
                    "estimated_minutes": 10,
                },
                {
                    "step": 4,
                    "action": "DBフェイルオーバー実行",
                    "description": "PostgreSQLのリードレプリカを昇格し、書き込み可能なプライマリに切替。",
                    "responsible": "DBAチーム",
                    "estimated_minutes": 15,
                },
                {
                    "step": 5,
                    "action": "アプリケーションスケールアップ",
                    "description": "西日本のContainer Appsレプリカ数を本番相当(3台)に増加。",
                    "responsible": "インフラチーム",
                    "estimated_minutes": 10,
                },
                {
                    "step": 6,
                    "action": "DNS/Front Door切替",
                    "description": "Azure Front Doorのオリジンを西日本に切替、またはDNSフェイルオーバーを実行。",
                    "responsible": "インフラチーム",
                    "estimated_minutes": 5,
                },
                {
                    "step": 7,
                    "action": "接続テスト・動作確認",
                    "description": "主要エンドポイントへのアクセス確認、データ整合性チェック。",
                    "responsible": "QAチーム",
                    "estimated_minutes": 15,
                },
                {
                    "step": 8,
                    "action": "外部連携の切替確認",
                    "description": "外部API・メール・通知サービス等の接続先が正しいことを確認。",
                    "responsible": "アプリチーム",
                    "estimated_minutes": 10,
                },
                {
                    "step": 9,
                    "action": "ユーザーへの通知",
                    "description": "サービス復旧（DR切替完了）をユーザー・顧客に通知。",
                    "responsible": "広報/CS",
                    "estimated_minutes": 5,
                },
                {
                    "step": 10,
                    "action": "監視強化・状況報告",
                    "description": "DRサイトの監視を強化し、30分間隔で状況報告を実施。フェイルバック計画を策定。",
                    "responsible": "運用チーム",
                    "estimated_minutes": 30,
                },
            ],
            "total_steps": 10,
            "estimated_total_minutes": 115,
        }

    @staticmethod
    def get_incident_response_playbook(scenario_type: str) -> dict:
        """Return incident response playbook for a given scenario.

        Supported scenarios: earthquake, ransomware, dc_failure.
        """
        playbooks: dict[str, dict] = {
            "earthquake": {
                "title": "地震発生時インシデント対応プレイブック",
                "scenario_type": "earthquake",
                "severity": "P1",
                "steps": [
                    {
                        "step": 1,
                        "action": "安全確認",
                        "description": "全従業員の安全確認を実施。安否確認システムで回答を収集。",
                    },
                    {
                        "step": 2,
                        "action": "被害状況の把握",
                        "description": "データセンター・オフィスの物理的被害状況を確認。",
                    },
                    {
                        "step": 3,
                        "action": "インシデント宣言",
                        "description": "BCPインシデントを宣言し、インシデントコマンダーを任命。",
                    },
                    {
                        "step": 4,
                        "action": "システム影響範囲の特定",
                        "description": "影響を受けたITシステムの一覧を作成し、優先順位を決定。",
                    },
                    {
                        "step": 5,
                        "action": "DRサイト切替判断",
                        "description": "プライマリサイトの復旧見込みを評価し、DR切替の要否を判断。",
                    },
                    {
                        "step": 6,
                        "action": "復旧作業の実施",
                        "description": "RTOに基づきTier1システムから順次復旧。DRフェイルオーバーまたは現地復旧。",
                    },
                    {
                        "step": 7,
                        "action": "復旧確認・事後対応",
                        "description": "全システムの復旧を確認。事後レビュー(Post-mortem)を実施。",
                    },
                ],
                "total_steps": 7,
            },
            "ransomware": {
                "title": "ランサムウェア感染時インシデント対応プレイブック",
                "scenario_type": "ransomware",
                "severity": "P1",
                "steps": [
                    {
                        "step": 1,
                        "action": "検知・初動対応",
                        "description": "ランサムウェア感染を検知し、感染端末を即座にネットワークから隔離。",
                    },
                    {
                        "step": 2,
                        "action": "感染範囲の特定",
                        "description": "EDR/SIEMログを分析し、感染の横展開範囲を特定。",
                    },
                    {
                        "step": 3,
                        "action": "インシデント宣言・エスカレーション",
                        "description": "セキュリティインシデントを宣言。CSIRT・外部フォレンジック業者に連絡。",
                    },
                    {
                        "step": 4,
                        "action": "証拠保全",
                        "description": "感染端末のメモリダンプ・ディスクイメージを取得し、証拠を保全。",
                    },
                    {
                        "step": 5,
                        "action": "封じ込め",
                        "description": "感染経路を遮断。不正なC2通信をファイアウォールでブロック。",
                    },
                    {
                        "step": 6,
                        "action": "クリーンバックアップからの復旧",
                        "description": "感染前のバックアップを特定し、クリーンな環境へリストア。",
                    },
                    {
                        "step": 7,
                        "action": "システム検証",
                        "description": "復旧したシステムのマルウェアスキャン・整合性チェックを実施。",
                    },
                    {
                        "step": 8,
                        "action": "再発防止・事後報告",
                        "description": "根本原因を分析し、パッチ適用・ポリシー強化等の再発防止策を実施。",
                    },
                ],
                "total_steps": 8,
            },
            "dc_failure": {
                "title": "データセンター障害時インシデント対応プレイブック",
                "scenario_type": "dc_failure",
                "severity": "P1",
                "steps": [
                    {
                        "step": 1,
                        "action": "障害検知・初期評価",
                        "description": "データセンターの障害(電源/ネットワーク/空調)を検知し、影響範囲を評価。",
                    },
                    {
                        "step": 2,
                        "action": "インシデント宣言",
                        "description": "BCPインシデントを宣言し、War Roomを開設。DC事業者と連絡。",
                    },
                    {
                        "step": 3,
                        "action": "復旧見込みの確認",
                        "description": "DC事業者から復旧見込み時間を取得し、DRフェイルオーバーの要否を判断。",
                    },
                    {
                        "step": 4,
                        "action": "DRフェイルオーバー実行",
                        "description": "復旧見込みがRTOを超える場合、DRフェイルオーバー手順を実行。",
                    },
                    {
                        "step": 5,
                        "action": "サービス復旧確認",
                        "description": "DRサイトでのサービス稼働を確認。ユーザーへ復旧通知を送信。",
                    },
                    {
                        "step": 6,
                        "action": "フェイルバック計画・事後対応",
                        "description": "プライマリDC復旧後のフェイルバック計画を策定。事後レビューを実施。",
                    },
                ],
                "total_steps": 6,
            },
        }

        if scenario_type not in playbooks:
            return {
                "error": f"Unknown scenario type: {scenario_type}",
                "available_scenarios": list(playbooks.keys()),
            }

        result = playbooks[scenario_type]
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        return result
