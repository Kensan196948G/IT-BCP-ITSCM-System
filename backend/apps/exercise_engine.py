"""Tabletop exercise engine for BCP drills."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.models import BCPExercise, ExerciseRTORecord


class ExerciseEngine:
    """Orchestrates BCP tabletop exercises."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def start_exercise(self, exercise_id: uuid.UUID) -> BCPExercise:
        """Start an exercise by setting status to in_progress."""
        exercise = await crud.get_exercise(self.db, exercise_id)
        if exercise is None:
            raise ValueError("Exercise not found")
        if exercise.status not in ("planned",):
            raise ValueError(f"Cannot start exercise with status '{exercise.status}'")
        exercise.status = "in_progress"
        exercise.actual_date = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(exercise)
        return exercise

    async def inject_scenario(self, exercise_id: uuid.UUID, inject_index: int) -> dict[str, Any]:
        """Inject a scenario step into a running exercise.

        Returns the inject data dict from the scenario's injects list.
        """
        exercise = await crud.get_exercise(self.db, exercise_id)
        if exercise is None:
            raise ValueError("Exercise not found")
        if exercise.status != "in_progress":
            raise ValueError("Exercise is not in progress")

        # Try to load scenario from exercise's scenario_ref_id
        scenario = None
        if hasattr(exercise, "scenario_ref_id") and exercise.scenario_ref_id:
            scenario = await crud.get_scenario(self.db, exercise.scenario_ref_id)

        if scenario is None:
            raise ValueError("No scenario linked to this exercise")

        injects = scenario.injects or []
        if inject_index < 0 or inject_index >= len(injects):
            raise ValueError(f"inject_index {inject_index} out of range " f"(0-{len(injects) - 1})")

        inject_data = injects[inject_index]
        return {
            "inject_index": inject_index,
            "total_injects": len(injects),
            "inject": inject_data,
            "exercise_id": str(exercise.id),
        }

    async def record_rto(
        self,
        exercise_id: uuid.UUID,
        system_name: str,
        rto_target_hours: float,
        rto_actual_hours: float | None = None,
        recorded_by: str | None = None,
        notes: str | None = None,
    ) -> ExerciseRTORecord:
        """Record an RTO measurement for a system in an exercise."""
        exercise = await crud.get_exercise(self.db, exercise_id)
        if exercise is None:
            raise ValueError("Exercise not found")

        achieved = None
        if rto_actual_hours is not None:
            achieved = rto_actual_hours <= rto_target_hours

        record = await crud.create_rto_record(
            self.db,
            {
                "exercise_id": exercise_id,
                "system_name": system_name,
                "rto_target_hours": rto_target_hours,
                "rto_actual_hours": rto_actual_hours,
                "achieved": achieved,
                "recorded_by": recorded_by,
                "notes": notes,
            },
        )
        return record

    async def complete_exercise(self, exercise_id: uuid.UUID) -> BCPExercise:
        """Complete an exercise and compute overall result."""
        exercise = await crud.get_exercise(self.db, exercise_id)
        if exercise is None:
            raise ValueError("Exercise not found")
        if exercise.status not in ("in_progress",):
            raise ValueError(f"Cannot complete exercise with status '{exercise.status}'")

        rto_records = await crud.get_rto_records_by_exercise(self.db, exercise_id)

        # Determine overall result based on RTO achievement
        if rto_records:
            achieved_count = sum(1 for r in rto_records if r.achieved is True)
            total = len(rto_records)
            rate = achieved_count / total if total > 0 else 0.0

            if rate >= 1.0:
                overall_result = "pass"
            elif rate >= 0.5:
                overall_result = "partial_pass"
            else:
                overall_result = "fail"
        else:
            overall_result = "pass"

        exercise.status = "completed"
        exercise.overall_result = overall_result
        await self.db.flush()
        await self.db.refresh(exercise)
        return exercise

    async def generate_report(self, exercise_id: uuid.UUID) -> dict[str, Any]:
        """Generate a comprehensive exercise report."""
        exercise = await crud.get_exercise(self.db, exercise_id)
        if exercise is None:
            raise ValueError("Exercise not found")

        rto_records = await crud.get_rto_records_by_exercise(self.db, exercise_id)

        total_systems = len(rto_records)
        achieved = sum(1 for r in rto_records if r.achieved is True)
        failed = sum(1 for r in rto_records if r.achieved is False)
        achievement_rate = (achieved / total_systems * 100.0) if total_systems > 0 else None

        # Generate findings
        findings: list[str] = []
        recommendations: list[str] = []

        for record in rto_records:
            if record.achieved is False and record.rto_actual_hours is not None:
                overshoot = record.rto_actual_hours - record.rto_target_hours
                findings.append(
                    f"{record.system_name}: RTO exceeded by "
                    f"{overshoot:.1f}h "
                    f"(target={record.rto_target_hours}h, "
                    f"actual={record.rto_actual_hours}h)"
                )
                recommendations.append(f"Review and improve recovery procedure for " f"{record.system_name}")

        if total_systems == 0:
            findings.append("No RTO records were captured during this exercise")
            recommendations.append("Ensure RTO measurements are recorded " "during future exercises")

        if achievement_rate is not None and achievement_rate < 80.0:
            recommendations.append(
                "Overall RTO achievement rate is below 80%. " "Consider additional DR training and procedure reviews."
            )

        return {
            "exercise": exercise,
            "rto_records": rto_records,
            "rto_achievement_rate": achievement_rate,
            "total_systems_tested": total_systems,
            "systems_achieved": achieved,
            "systems_failed": failed,
            "findings": findings,
            "recommendations": recommendations,
        }
