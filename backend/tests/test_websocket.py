"""Tests for WebSocket RTO dashboard endpoint."""

import json

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture()
def ws_client():
    """Provide a TestClient for WebSocket testing."""
    yield TestClient(app)


class TestWebSocketRTODashboard:
    """Tests for the /ws/rto-dashboard WebSocket endpoint."""

    def test_websocket_connect_and_receive_snapshot(self, ws_client):
        """Test that connecting receives an initial RTO snapshot."""
        with ws_client.websocket_connect("/ws/rto-dashboard") as ws:
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["type"] == "rto_snapshot"
            assert "systems" in msg
            assert "summary" in msg
            assert "timestamp" in msg

    def test_websocket_snapshot_has_systems(self, ws_client):
        """Test that the snapshot contains system data."""
        with ws_client.websocket_connect("/ws/rto-dashboard") as ws:
            data = ws.receive_text()
            msg = json.loads(data)
            assert len(msg["systems"]) > 0
            system = msg["systems"][0]
            assert "system_name" in system
            assert "rto_target_hours" in system
            assert "status" in system

    def test_websocket_snapshot_summary(self, ws_client):
        """Test that the snapshot summary has correct structure."""
        with ws_client.websocket_connect("/ws/rto-dashboard") as ws:
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
        with ws_client.websocket_connect("/ws/rto-dashboard") as ws:
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
        with ws_client.websocket_connect("/ws/rto-dashboard") as ws:
            # Consume initial snapshot
            ws.receive_text()
            # Send invalid JSON
            ws.send_text("not-json")
            # Send valid ping to confirm connection is still alive
            ws.send_text(json.dumps({"type": "ping"}))
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["type"] == "pong"
