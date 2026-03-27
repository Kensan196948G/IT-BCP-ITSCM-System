"""API routes for dashboard and readiness overview."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps import crud
from apps.rto_tracker import RTOTracker
from apps.schemas import DashboardResponse, RTOStatusResponse
from database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/readiness", response_model=DashboardResponse)
async def get_readiness(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get BCP readiness score and overall dashboard."""
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
    return dashboard


@router.get("/rto-overview", response_model=list[RTOStatusResponse])
async def get_rto_overview(
    db: AsyncSession = Depends(get_db),
) -> list:
    """Get RTO status overview for all systems."""
    all_systems = await crud.get_all_systems(db)
    active_incidents = await crud.get_active_incidents(db)

    # Build affected system -> incident map
    system_incident_map: dict[str, object] = {}
    for inc in active_incidents:
        for sys_name in inc.affected_systems or []:
            system_incident_map[sys_name] = inc

    results: list[dict] = []
    for system in all_systems:
        inc = system_incident_map.get(system.system_name)
        if inc:
            tracker = RTOTracker(
                rto_target_hours=system.rto_target_hours,
                occurred_at=inc.occurred_at,  # type: ignore[union-attr]
                resolved_at=inc.resolved_at,  # type: ignore[union-attr]
                status=inc.status,  # type: ignore[union-attr]
            )
        else:
            tracker = RTOTracker(rto_target_hours=system.rto_target_hours)

        status_info = tracker.calculate_status()
        status_info["system_name"] = system.system_name
        results.append(status_info)

    return results
