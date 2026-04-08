"""API routes for operational runbooks."""

from typing import Any

from fastapi import APIRouter, HTTPException

from apps.runbook import Runbook

router = APIRouter(prefix="/api/runbook", tags=["runbook"])


@router.get("/deployment-checklist")
async def get_deployment_checklist() -> dict[str, Any]:
    """Get pre-deployment verification checklist."""
    return Runbook.get_deployment_checklist()


@router.get("/rollback-procedure")
async def get_rollback_procedure() -> dict[str, Any]:
    """Get rollback procedure steps."""
    return Runbook.get_rollback_procedure()


@router.get("/dr-failover")
async def get_dr_failover() -> dict[str, Any]:
    """Get DR failover procedure steps."""
    return Runbook.get_dr_failover_steps()


@router.get("/incident-playbook/{scenario_type}")
async def get_incident_playbook(scenario_type: str) -> dict[str, Any]:
    """Get incident response playbook for a specific scenario.

    Supported scenarios: earthquake, ransomware, dc_failure.
    """
    result = Runbook.get_incident_response_playbook(scenario_type)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result)
    return result
