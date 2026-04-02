"""Tests for WebSocket RTO dashboard endpoint and ConnectionManager."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import WebSocket
from fastapi.testclient import TestClient

from apps.auth import AuthService
from apps.websocket_manager import ConnectionManager
from main import app

_VALID_TOKEN = AuthService.create_access_token("test-user", "viewer")
_WS_URL = f"/ws/rto-dashboard?token={_VALID_TOKEN}"


@pytest.fixture()
def ws_client():
    """Provide a TestClient for WebSocket testing."""
    yield TestClient(app)


class TestWebSocketRTODashboard:
    """Tests for the /ws/rto-dashboard WebSocket endpoint."""

    def test_websocket_connect_and_receive_snapshot(self, ws_client):
        """Test that connecting receives an initial RTO snapshot."""
        with ws_client.websocket_connect(_WS_URL) as ws:
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["type"] == "rto_snapshot"
            assert "systems" in msg
            assert "summary" in msg
            assert "timestamp" in msg

    def test_websocket_snapshot_has_systems(self, ws_client):
        """Test that the snapshot contains system data."""
        with ws_client.websocket_connect(_WS_URL) as ws:
            data = ws.receive_text()
            msg = json.loads(data)
            assert len(msg["systems"]) > 0
            system = msg["systems"][0]
            assert "system_name" in system
            assert "rto_target_hours" in system
            assert "status" in system

    def test_websocket_snapshot_summary(self, ws_client):
        """Test that the snapshot summary has correct structure."""
        with ws_client.websocket_connect(_WS_URL) as ws:
            data = ws.receive_text()
            msg = json.loads(data)
            summary = msg["summary"]
            assert "total" in summary
            assert "on_track" in summary
            assert "at_risk" in summary
            assert "overdue" in summary
            assert summary["total"] == len(msg["systems"])

    def test_websocket_ping_pong(self, ws_client):
        """Test that sending a ping receives a pong."""
        with ws_client.websocket_connect(_WS_URL) as ws:
            # Consume initial snapshot
            ws.receive_text()
            # Send ping
            ws.send_text(json.dumps({"type": "ping"}))
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["type"] == "pong"
            assert "timestamp" in msg

    def test_websocket_handles_invalid_json(self, ws_client):
        """Test that invalid JSON does not crash the connection."""
        with ws_client.websocket_connect(_WS_URL) as ws:
            # Consume initial snapshot
            ws.receive_text()
            # Send invalid JSON
            ws.send_text("not-json")
            # Send valid ping to confirm connection is still alive
            ws.send_text(json.dumps({"type": "ping"}))
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["type"] == "pong"

    def test_websocket_receives_background_update(self, ws_client):
        """Background task sends rto_update messages (covers lines 91-93)."""
        with patch("asyncio.sleep", new_callable=AsyncMock, return_value=None):
            with ws_client.websocket_connect(_WS_URL) as ws:
                # Initial snapshot (line 85)
                snapshot = json.loads(ws.receive_text())
                assert snapshot["type"] == "rto_snapshot"
                # Background update sent after mocked sleep returns immediately
                update = json.loads(ws.receive_text())
                assert update["type"] == "rto_update"
                assert "systems" in update
                assert "summary" in update

    @pytest.mark.asyncio
    async def test_websocket_generic_exception_disconnects(self):
        """Generic exceptions (not WebSocketDisconnect) call manager.disconnect (lines 118-119)."""
        from apps.routers.ws import rto_dashboard_ws
        from apps.websocket_manager import manager

        ws = AsyncMock(spec=WebSocket)
        # receive_text raises a non-WebSocketDisconnect exception immediately
        ws.receive_text.side_effect = RuntimeError("network reset")

        with patch.object(manager, "connect", new_callable=AsyncMock):
            with patch.object(manager, "disconnect") as mock_disconnect:
                await rto_dashboard_ws(ws, token=_VALID_TOKEN)

        mock_disconnect.assert_called_once_with(ws)

    def test_websocket_rejects_without_token(self, ws_client):
        """Connecting without a token closes with 1008."""
        with pytest.raises(Exception):
            with ws_client.websocket_connect("/ws/rto-dashboard"):
                pass

    def test_websocket_rejects_invalid_token(self, ws_client):
        """Connecting with an invalid token closes with 1008."""
        with pytest.raises(Exception):
            with ws_client.websocket_connect("/ws/rto-dashboard?token=invalid.token.here"):
                pass


# ---------------------------------------------------------------------------
# ConnectionManager unit tests
# ---------------------------------------------------------------------------


class TestConnectionManager:
    """Unit tests for ConnectionManager.broadcast() and send_rto_update()."""

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(self):
        """broadcast() sends JSON message to every active connection."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.active_connections = [ws1, ws2]

        await manager.broadcast({"event": "test"})

        expected = json.dumps({"event": "test"}, default=str)
        ws1.send_text.assert_awaited_once_with(expected)
        ws2.send_text.assert_awaited_once_with(expected)

    @pytest.mark.asyncio
    async def test_broadcast_removes_failed_connections(self):
        """broadcast() cleans up connections that raise on send_text."""
        manager = ConnectionManager()
        healthy = AsyncMock()
        broken = AsyncMock()
        broken.send_text.side_effect = Exception("disconnected")
        manager.active_connections = [healthy, broken]

        await manager.broadcast({"event": "test"})

        # broken connection removed, healthy remains
        assert broken not in manager.active_connections
        assert healthy in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_empty_connections(self):
        """broadcast() works with no active connections (no error)."""
        manager = ConnectionManager()
        manager.active_connections = []
        # Should complete without raising
        await manager.broadcast({"event": "empty"})

    @pytest.mark.asyncio
    async def test_send_rto_update_broadcasts_correct_payload(self):
        """send_rto_update() wraps data in rto_update payload and broadcasts."""
        manager = ConnectionManager()
        ws = AsyncMock()
        manager.active_connections = [ws]

        await manager.send_rto_update("incident-123", {"rto_hours": 4})

        ws.send_text.assert_awaited_once()
        sent_msg = json.loads(ws.send_text.call_args[0][0])
        assert sent_msg["type"] == "rto_update"
        assert sent_msg["incident_id"] == "incident-123"
        assert sent_msg["data"] == {"rto_hours": 4}
