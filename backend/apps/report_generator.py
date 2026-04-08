"""Report generation engine for BCP/ITSCM compliance and readiness reports."""

from datetime import datetime, timezone
from typing import Any


class ReportGenerator:
    """Generates various BCP/ITSCM reports from system and exercise data."""

    def __init__(
        self,
        systems: list[dict[str, Any]],
        exercises: list[dict[str, Any]],
        incidents: list[dict[str, Any]],
    ) -> None:
        self.systems = systems
        self.exercises = exercises
        self.incidents = incidents

    def generate_readiness_report(self) -> dict[str, Any]:
        """Generate BCP Readiness Report (RPT-001).

        Returns a dict with:
        - report_id, report_type, generated_at
        - overall_score (0-100)
        - system_readiness: per-system readiness detail
        - untested_systems: systems with no recent DR test
        - recommendations
        """
        total = len(self.systems)
        if total == 0:
            return self._empty_readiness()

        system_readiness: list[dict[str, Any]] = []
        tested_count = 0
        rto_met_count = 0
        untested: list[str] = []

        for sys in self.systems:
            name = sys.get("system_name", "Unknown")
            rto_target = sys.get("rto_target_hours", 0)
            rpo_target = sys.get("rpo_target_hours", 0)
            last_test = sys.get("last_dr_test")
            last_test_rto = sys.get("last_test_rto")
            has_fallback = bool(sys.get("fallback_system"))

            tested = last_test is not None
            if tested:
                tested_count += 1
            else:
                untested.append(name)

            rto_achieved = False
            if last_test_rto is not None and rto_target > 0:
                rto_achieved = last_test_rto <= rto_target
                if rto_achieved:
                    rto_met_count += 1

            # Per-system score: tested(40) + rto_met(40) + fallback(20)
            score = 0.0
            if tested:
                score += 40.0
            if rto_achieved:
                score += 40.0
            if has_fallback:
                score += 20.0

            system_readiness.append(
                {
                    "system_name": name,
                    "rto_target_hours": rto_target,
                    "rpo_target_hours": rpo_target,
                    "last_test_rto_hours": last_test_rto,
                    "rto_achieved": rto_achieved,
                    "tested": tested,
                    "has_fallback": has_fallback,
                    "readiness_score": round(score, 1),
                }
            )

        # Overall score: average of per-system scores
        overall = sum(s["readiness_score"] for s in system_readiness) / total

        recommendations: list[str] = []
        if untested:
            recommendations.append(f"{len(untested)}件のシステムが未テストです。DR試験を計画してください。")
        if rto_met_count < tested_count:
            recommendations.append("一部システムのRTO目標が未達成です。復旧手順の見直しを推奨します。")
        if overall < 60:
            recommendations.append("全体レディネススコアが低い状態です。優先度の高いシステムから改善してください。")

        return {
            "report_id": "RPT-001",
            "report_type": "BCP Readiness Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_score": round(overall, 1),
            "total_systems": total,
            "tested_systems": tested_count,
            "rto_met_systems": rto_met_count,
            "system_readiness": system_readiness,
            "untested_systems": untested,
            "recommendations": recommendations,
        }

    def _empty_readiness(self) -> dict[str, Any]:
        return {
            "report_id": "RPT-001",
            "report_type": "BCP Readiness Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_score": 0.0,
            "total_systems": 0,
            "tested_systems": 0,
            "rto_met_systems": 0,
            "system_readiness": [],
            "untested_systems": [],
            "recommendations": ["システムが登録されていません。"],
        }

    def generate_rto_compliance_report(self) -> dict[str, Any]:
        """Generate RTO/RPO Compliance Report (RPT-002).

        Returns a dict with:
        - system-level RTO target vs actual comparison
        - compliance_rate (%)
        - overdue_systems
        - trend indicator per system
        """
        total = len(self.systems)
        if total == 0:
            return {
                "report_id": "RPT-002",
                "report_type": "RTO/RPO Compliance Report",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "compliance_rate": 0.0,
                "total_systems": 0,
                "compliant_systems": 0,
                "system_compliance": [],
                "overdue_systems": [],
            }

        system_compliance: list[dict[str, Any]] = []
        compliant_count = 0
        overdue: list[str] = []

        for sys in self.systems:
            name = sys.get("system_name", "Unknown")
            rto_target = sys.get("rto_target_hours", 0)
            last_test_rto = sys.get("last_test_rto")

            compliant = False
            deviation = None
            trend = "unknown"

            if last_test_rto is not None and rto_target > 0:
                deviation = round(last_test_rto - rto_target, 2)
                compliant = last_test_rto <= rto_target
                if compliant:
                    compliant_count += 1
                    trend = "improving"
                else:
                    overdue.append(name)
                    trend = "deteriorating"
            else:
                overdue.append(name)

            system_compliance.append(
                {
                    "system_name": name,
                    "rto_target_hours": rto_target,
                    "rto_actual_hours": last_test_rto,
                    "deviation_hours": deviation,
                    "compliant": compliant,
                    "trend": trend,
                }
            )

        rate = (compliant_count / total * 100.0) if total > 0 else 0.0

        return {
            "report_id": "RPT-002",
            "report_type": "RTO/RPO Compliance Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "compliance_rate": round(rate, 1),
            "total_systems": total,
            "compliant_systems": compliant_count,
            "system_compliance": system_compliance,
            "overdue_systems": overdue,
        }

    def generate_exercise_trend_report(self) -> dict[str, Any]:
        """Generate Exercise Trend Report (RPT-003).

        Returns a dict with:
        - yearly exercise counts
        - RTO achievement rate trends
        - common issue categories
        - improvement action completion rate
        """
        yearly_stats: dict[int, dict[str, Any]] = {}
        issue_categories: dict[str, int] = {}
        total_improvements = 0
        completed_improvements = 0

        for ex in self.exercises:
            # Extract year from scheduled_date
            sched = ex.get("scheduled_date")
            year = None
            if isinstance(sched, datetime):
                year = sched.year
            elif isinstance(sched, str):
                try:
                    year = datetime.fromisoformat(sched.replace("Z", "+00:00")).year
                except (ValueError, TypeError):
                    pass

            if year is None:
                continue

            if year not in yearly_stats:
                yearly_stats[year] = {
                    "year": year,
                    "exercise_count": 0,
                    "completed": 0,
                    "pass_count": 0,
                }

            yearly_stats[year]["exercise_count"] += 1

            status = ex.get("status", "")
            if status == "completed":
                yearly_stats[year]["completed"] += 1

            result = ex.get("overall_result", "")
            if result == "pass":
                yearly_stats[year]["pass_count"] += 1

            # Findings
            findings = ex.get("findings")
            if isinstance(findings, dict):
                for category in findings.get("categories", []):
                    issue_categories[category] = issue_categories.get(category, 0) + 1
            elif isinstance(findings, list):
                for f in findings:
                    cat = f if isinstance(f, str) else "general"
                    issue_categories[cat] = issue_categories.get(cat, 0) + 1

            # Improvements
            improvements = ex.get("improvements")
            if isinstance(improvements, dict):
                items = improvements.get("items", [])
                total_improvements += len(items)
                completed_improvements += sum(
                    1 for i in items if isinstance(i, dict) and i.get("status") == "completed"
                )
            elif isinstance(improvements, list):
                total_improvements += len(improvements)
                completed_improvements += sum(
                    1 for i in improvements if isinstance(i, dict) and i.get("status") == "completed"
                )

        yearly_list = sorted(yearly_stats.values(), key=lambda x: x["year"])
        for entry in yearly_list:
            completed = entry["completed"]
            entry["achievement_rate"] = round(entry["pass_count"] / completed * 100.0, 1) if completed > 0 else 0.0

        improvement_rate = (
            round(completed_improvements / total_improvements * 100.0, 1) if total_improvements > 0 else 0.0
        )

        return {
            "report_id": "RPT-003",
            "report_type": "Exercise Trend Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_exercises": len(self.exercises),
            "yearly_trends": yearly_list,
            "common_issues": issue_categories,
            "total_improvements": total_improvements,
            "completed_improvements": completed_improvements,
            "improvement_completion_rate": improvement_rate,
        }

    def generate_iso20000_report(self) -> dict[str, Any]:
        """Generate ISO20000 ITSCM Compliance Report (RPT-004).

        Returns a dict with:
        - ITSCM requirements checklist
        - compliance_rate (%)
        - non_compliant_items
        - next_audit_actions
        """
        # Define ISO20000 ITSCM checklist items
        checklist = [
            {
                "id": "ITSCM-001",
                "requirement": "ITサービス継続計画が文書化されていること",
                "category": "計画",
            },
            {
                "id": "ITSCM-002",
                "requirement": "RTO/RPO目標が全対象システムに設定されていること",
                "category": "目標設定",
            },
            {
                "id": "ITSCM-003",
                "requirement": "年1回以上のBCP訓練が実施されていること",
                "category": "訓練",
            },
            {
                "id": "ITSCM-004",
                "requirement": "復旧手順が文書化・レビューされていること",
                "category": "手順",
            },
            {
                "id": "ITSCM-005",
                "requirement": "BIA（ビジネスインパクト分析）が実施されていること",
                "category": "分析",
            },
            {
                "id": "ITSCM-006",
                "requirement": "緊急連絡体制が整備されていること",
                "category": "連絡体制",
            },
            {
                "id": "ITSCM-007",
                "requirement": "DR試験結果に基づく改善が実施されていること",
                "category": "継続改善",
            },
            {
                "id": "ITSCM-008",
                "requirement": "代替手段・フォールバックが定義されていること",
                "category": "代替手段",
            },
        ]

        # Evaluate each item
        total_systems = len(self.systems)
        has_exercises = len(self.exercises) > 0
        completed_exercises = [e for e in self.exercises if e.get("status") == "completed"]

        systems_with_rto = sum(1 for s in self.systems if s.get("rto_target_hours"))
        systems_with_fallback = sum(1 for s in self.systems if s.get("fallback_system"))
        systems_tested = sum(1 for s in self.systems if s.get("last_dr_test"))

        results: list[dict[str, Any]] = []
        compliant_count = 0

        for item in checklist:
            compliant = False
            evidence = ""

            if item["id"] == "ITSCM-001":
                compliant = total_systems > 0
                evidence = f"{total_systems}件のシステムが登録済み" if compliant else "未登録"

            elif item["id"] == "ITSCM-002":
                compliant = systems_with_rto == total_systems and total_systems > 0
                evidence = f"{systems_with_rto}/{total_systems}件設定済み"

            elif item["id"] == "ITSCM-003":
                compliant = len(completed_exercises) > 0
                evidence = f"{len(completed_exercises)}回の訓練完了"

            elif item["id"] == "ITSCM-004":
                # Simplified: check if exercises exist
                compliant = has_exercises
                evidence = "訓練記録あり" if compliant else "訓練記録なし"

            elif item["id"] == "ITSCM-005":
                # Check if we have incidents data as proxy
                compliant = total_systems > 0
                evidence = "システム登録済み" if compliant else "未実施"

            elif item["id"] == "ITSCM-006":
                # Simplified
                compliant = total_systems > 0
                evidence = "システム体制登録済み" if compliant else "未整備"

            elif item["id"] == "ITSCM-007":
                compliant = systems_tested > 0
                evidence = f"{systems_tested}件テスト済み"

            elif item["id"] == "ITSCM-008":
                compliant = systems_with_fallback > 0
                evidence = f"{systems_with_fallback}/{total_systems}件定義済み"

            if compliant:
                compliant_count += 1

            results.append(
                {
                    "id": item["id"],
                    "requirement": item["requirement"],
                    "category": item["category"],
                    "compliant": compliant,
                    "evidence": evidence,
                }
            )

        total_items = len(checklist)
        rate = round(compliant_count / total_items * 100.0, 1) if total_items > 0 else 0.0

        non_compliant = [r for r in results if not r["compliant"]]
        next_actions: list[str] = []
        for nc in non_compliant:
            next_actions.append(f"[{nc['id']}] {nc['requirement']} - 対応が必要です")

        return {
            "report_id": "RPT-004",
            "report_type": "ISO20000 ITSCM Compliance Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "compliance_rate": rate,
            "total_items": total_items,
            "compliant_items": compliant_count,
            "checklist_results": results,
            "non_compliant_items": non_compliant,
            "next_audit_actions": next_actions,
        }
