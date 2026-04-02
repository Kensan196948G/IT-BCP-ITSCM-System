"""API routes for dashboard and readiness overview."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.cache import TTL_DASHBOARD, get_cached, set_cached
from apps.models import ActiveIncident
from apps.report_generator import ReportGenerator
from apps.rto_tracker import RTOTracker
from apps.schemas import (
    DashboardResponse,
    ExerciseTrendReportResponse,
    ISO20000ReportResponse,
    RTOComplianceReportResponse,
    RTOStatusResponse,
    ReadinessReportResponse,
)
from database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

_CACHE_READINESS = "dashboard:readiness"
_CACHE_RTO_OVERVIEW = "dashboard:rto-overview"


@router.get("/readiness", response_model=DashboardResponse)
async def get_readiness(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get BCP readiness score and overall dashboard."""
    cached = await get_cached(_CACHE_READINESS)
    if cached is not None:
        return cached

    all_systems = await crud.get_all_systems(db)
    active_incidents = await crud.get_active_incidents(db)

    systems_data = [{"system_name": s.system_name, "rto_target_hours": s.rto_target_hours} for s in all_systems]

    incidents_data = [
        {
            "affected_systems": inc.affected_systems or [],
            "occurred_at": inc.occurred_at,
            "resolved_at": inc.resolved_at,
            "status": inc.status,
        }
        for inc in active_incidents
    ]

    dashboard = RTOTracker.get_dashboard(systems_data, incidents_data)
    await set_cached(_CACHE_READINESS, dashboard, TTL_DASHBOARD)
    return dashboard


@router.get("/rto-overview", response_model=list[RTOStatusResponse])
async def get_rto_overview(
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get RTO status overview for all systems."""
    cached = await get_cached(_CACHE_RTO_OVERVIEW)
    if cached is not None:
        return cached

    all_systems = await crud.get_all_systems(db)
    active_incidents = await crud.get_active_incidents(db)

    # Build affected system -> incident map
    system_incident_map: dict[str, ActiveIncident] = {}
    for incident in active_incidents:
        for sys_name in incident.affected_systems or []:
            system_incident_map[sys_name] = incident

    results: list[dict] = []
    for system in all_systems:
        matched_inc: ActiveIncident | None = system_incident_map.get(system.system_name)
        if matched_inc:
            tracker = RTOTracker(
                rto_target_hours=system.rto_target_hours,
                occurred_at=matched_inc.occurred_at,
                resolved_at=matched_inc.resolved_at,
                status=matched_inc.status,
            )
        else:
            tracker = RTOTracker(rto_target_hours=system.rto_target_hours)

        status_info = tracker.calculate_status()
        status_info["system_name"] = system.system_name
        results.append(status_info)

    await set_cached(_CACHE_RTO_OVERVIEW, results, TTL_DASHBOARD)
    return results


# ---------------------------------------------------------------------------
# Report endpoints (Phase 2)
# ---------------------------------------------------------------------------


async def _build_report_generator(db: AsyncSession) -> ReportGenerator:
    """Build a ReportGenerator with data from the database."""
    all_systems = await crud.get_all_systems(db)
    all_exercises = await crud.get_all_exercises(db)
    all_incidents = await crud.get_all_incidents(db)

    systems_data = [
        {
            "system_name": s.system_name,
            "system_type": getattr(s, "system_type", None),
            "criticality": getattr(s, "criticality", None),
            "rto_target_hours": s.rto_target_hours,
            "rpo_target_hours": getattr(s, "rpo_target_hours", 0),
            "fallback_system": getattr(s, "fallback_system", None),
            "last_dr_test": getattr(s, "last_dr_test", None),
            "last_test_rto": getattr(s, "last_test_rto", None),
        }
        for s in all_systems
    ]

    exercises_data = [
        {
            "exercise_id": getattr(e, "exercise_id", None),
            "title": getattr(e, "title", None),
            "exercise_type": getattr(e, "exercise_type", None),
            "scheduled_date": getattr(e, "scheduled_date", None),
            "status": getattr(e, "status", None),
            "overall_result": getattr(e, "overall_result", None),
            "findings": getattr(e, "findings", None),
            "improvements": getattr(e, "improvements", None),
        }
        for e in all_exercises
    ]

    incidents_data = [
        {
            "incident_id": getattr(i, "incident_id", None),
            "status": getattr(i, "status", None),
            "affected_systems": getattr(i, "affected_systems", None),
            "occurred_at": getattr(i, "occurred_at", None),
            "resolved_at": getattr(i, "resolved_at", None),
        }
        for i in all_incidents
    ]

    return ReportGenerator(
        systems=systems_data,
        exercises=exercises_data,
        incidents=incidents_data,
    )


@router.get("/reports/readiness", response_model=ReadinessReportResponse)
async def get_readiness_report(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate BCP Readiness Report (RPT-001)."""
    gen = await _build_report_generator(db)
    return gen.generate_readiness_report()


@router.get("/reports/rto-compliance", response_model=RTOComplianceReportResponse)
async def get_rto_compliance_report(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate RTO/RPO Compliance Report (RPT-002)."""
    gen = await _build_report_generator(db)
    return gen.generate_rto_compliance_report()


@router.get("/reports/exercise-trends", response_model=ExerciseTrendReportResponse)
async def get_exercise_trend_report(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate Exercise Trend Report (RPT-003)."""
    gen = await _build_report_generator(db)
    return gen.generate_exercise_trend_report()


@router.get("/reports/iso20000", response_model=ISO20000ReportResponse)
async def get_iso20000_report(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate ISO20000 ITSCM Compliance Report (RPT-004)."""
    gen = await _build_report_generator(db)
    return gen.generate_iso20000_report()
