"""WebSocket routes for real-time RTO dashboard updates."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from apps.auth import AuthService
from apps.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Mock RTO data for real-time updates
MOCK_RTO_SYSTEMS = [
    {
        "system_name": "Core Banking System",
        "rto_target_hours": 4.0,
        "status": "on_track",
        "elapsed_hours": 1.5,
        "remaining_hours": 2.5,
    },
    {
        "system_name": "Email System",
        "rto_target_hours": 2.0,
        "status": "at_risk",
        "elapsed_hours": 1.7,
        "remaining_hours": 0.3,
    },
    {
        "system_name": "CRM System",
        "rto_target_hours": 8.0,
        "status": "on_track",
        "elapsed_hours": 3.0,
        "remaining_hours": 5.0,
    },
    {
        "system_name": "File Server",
        "rto_target_hours": 2.0,
        "status": "overdue",
        "elapsed_hours": 2.5,
        "remaining_hours": 0.0,
        "overdue_hours": 0.5,
    },
    {
        "system_name": "HR System",
        "rto_target_hours": 24.0,
        "status": "not_started",
        "elapsed_hours": 0.0,
        "remaining_hours": 24.0,
    },
]


def _get_mock_rto_snapshot() -> dict[str, Any]:
    """Generate a mock RTO status snapshot with slight variations."""
    now = datetime.now(timezone.utc)
    return {
        "type": "rto_snapshot",
        "timestamp": now.isoformat(),
        "systems": MOCK_RTO_SYSTEMS,
        "summary": {
            "total": len(MOCK_RTO_SYSTEMS),
            "on_track": sum(1 for s in MOCK_RTO_SYSTEMS if s["status"] == "on_track"),
            "at_risk": sum(1 for s in MOCK_RTO_SYSTEMS if s["status"] == "at_risk"),
            "overdue": sum(1 for s in MOCK_RTO_SYSTEMS if s["status"] == "overdue"),
        },
    }


@router.websocket("/ws/rto-dashboard")
async def rto_dashboard_ws(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """WebSocket endpoint for real-time RTO dashboard updates.

    Requires a valid JWT token passed as ?token=<jwt>.
    Closes with code 1008 (Policy Violation) if authentication fails.

    - On connect: sends full RTO snapshot
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
        initial = _get_mock_rto_snapshot()
        await websocket.send_text(json.dumps(initial, default=str))

        # Background task: send updates every 5 seconds
        async def send_updates() -> None:
            while True:
                await asyncio.sleep(5)
                update = _get_mock_rto_snapshot()
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
