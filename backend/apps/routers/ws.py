"""WebSocket routes for real-time RTO dashboard updates."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from apps.auth import AuthService
from apps import crud
from apps.rto_tracker import RTOTracker
from apps.websocket_manager import manager
from database import async_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


async def _get_rto_snapshot() -> dict[str, Any]:
    """Build an RTO status snapshot from live database data."""
    now = datetime.now(timezone.utc)
    try:
        async with async_session() as db:
            all_systems = await crud.get_all_systems(db)
            active_incidents = await crud.get_active_incidents(db)

        # Map affected system name -> incident
        system_incident_map: dict[str, Any] = {}
        for inc in active_incidents:
            for sys_name in inc.affected_systems or []:
                system_incident_map[sys_name] = inc

        systems_data: list[dict[str, Any]] = []
        for system in all_systems:
            matched_inc = system_incident_map.get(system.system_name)
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
            systems_data.append(status_info)

    except Exception:
        logger.exception("Failed to query DB for RTO snapshot; returning empty snapshot")
        systems_data = []

    summary = {
        "total": len(systems_data),
        "on_track": sum(1 for s in systems_data if s.get("status") == "on_track"),
        "at_risk": sum(1 for s in systems_data if s.get("status") == "at_risk"),
        "overdue": sum(1 for s in systems_data if s.get("status") == "overdue"),
    }

    return {
        "type": "rto_snapshot",
        "timestamp": now.isoformat(),
        "systems": systems_data,
        "summary": summary,
    }


@router.websocket("/ws/rto-dashboard")
async def rto_dashboard_ws(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """WebSocket endpoint for real-time RTO dashboard updates.

    Requires a valid JWT token passed as ?token=<jwt>.
    Closes with code 1008 (Policy Violation) if authentication fails.

    - On connect: sends full RTO snapshot from live DB
    - Every 5 seconds: sends updated RTO status
    - Accepts client messages (e.g. ping)
    """
    # JWT authentication: token required
    if token is None:
        await websocket.close(code=1008, reason="Authentication required")
        return
    try:
        AuthService.verify_token(token)
    except Exception:
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    await manager.connect(websocket)
    try:
        # Send initial snapshot
        initial = await _get_rto_snapshot()
        await websocket.send_text(json.dumps(initial, default=str))

        # Background task: send updates every 5 seconds
        async def send_updates() -> None:
            while True:
                await asyncio.sleep(5)
                update = await _get_rto_snapshot()
                update["type"] = "rto_update"
                await websocket.send_text(json.dumps(update, default=str))

        update_task = asyncio.create_task(send_updates())

        try:
            while True:
                data = await websocket.receive_text()
                # Handle client messages
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_text(
                            json.dumps({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
                        )
                except json.JSONDecodeError:
                    pass
        finally:
            update_task.cancel()
            try:
                await update_task
            except asyncio.CancelledError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
