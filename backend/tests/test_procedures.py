"""Tests for Recovery Procedure CRUD API endpoints (mocked DB)."""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

SAMPLE_PROCEDURE = {
    "procedure_id": "RP-2026-001",
    "system_name": "Core Banking System",
    "scenario_type": "dc_failure",
    "title": "DC障害時の復旧手順",
    "version": "1.0",
    "priority_order": 1,
    "pre_requisites": "VPN接続が可能であること",
    "procedure_steps": [
        {"step": 1, "description": "状況確認", "duration_minutes": 10},
        {"step": 2, "description": "フェイルオーバー実行", "duration_minutes": 30},
    ],
    "estimated_time_hours": 2.0,
    "responsible_team": "Infrastructure Team",
    "status": "active",
}

MOCK_PROCEDURE_ID = uuid.uuid4()
FIXED_NOW = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)


class MockProcedure:
    """Mock SQLAlchemy model object for RecoveryProcedure."""

    def __init__(self, **kwargs: object) -> None:
        self.id = kwargs.get("id", MOCK_PROCEDURE_ID)
        self.procedure_id = kwargs.get("procedure_id", "RP-2026-001")
        self.system_name = kwargs.get("system_name", "Core Banking System")
        self.scenario_type = kwargs.get("scenario_type", "dc_failure")
        self.title = kwargs.get("title", "DC障害時の復旧手順")
        self.version = kwargs.get("version", "1.0")
        self.priority_order = kwargs.get("priority_order", 1)
        self.pre_requisites = kwargs.get("pre_requisites", None)
        self.procedure_steps = kwargs.get("procedure_steps", [{"step": 1, "description": "確認"}])
        self.estimated_time_hours = kwargs.get("estimated_time_hours", 2.0)
        self.responsible_team = kwargs.get("responsible_team", "Infrastructure Team")
        self.last_reviewed = kwargs.get("last_reviewed", None)
        self.review_cycle_months = kwargs.get("review_cycle_months", 12)
        self.status = kwargs.get("status", "active")
        self.created_at = kwargs.get("created_at", FIXED_NOW)
        self.updated_at = kwargs.get("updated_at", FIXED_NOW)


def _mock_db_override() -> Any:
    async def _fake_db() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    return _fake_db


@patch("apps.crud.get_all_procedures", new_callable=AsyncMock)
def test_list_procedures(mock_get_all: AsyncMock) -> None:
    """Test GET /api/procedures returns a list."""
    mock_get_all.return_value = [MockProcedure()]

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get("/api/procedures")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["procedure_id"] == "RP-2026-001"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.create_procedure", new_callable=AsyncMock)
def test_create_procedure(mock_create: AsyncMock) -> None:
    """Test POST /api/procedures creates a new procedure."""
    mock_create.return_value = MockProcedure(**SAMPLE_PROCEDURE)

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.post("/api/procedures", json=SAMPLE_PROCEDURE)
        assert response.status_code == 201
        data = response.json()
        assert data["procedure_id"] == "RP-2026-001"
        assert data["system_name"] == "Core Banking System"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.get_procedure", new_callable=AsyncMock)
def test_get_procedure(mock_get: AsyncMock) -> None:
    """Test GET /api/procedures/{id} returns a single procedure."""
    mock_get.return_value = MockProcedure()

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get(f"/api/procedures/{MOCK_PROCEDURE_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["procedure_id"] == "RP-2026-001"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.get_procedure", new_callable=AsyncMock)
def test_get_procedure_not_found(mock_get: AsyncMock) -> None:
    """Test GET /api/procedures/{id} returns 404 when not found."""
    mock_get.return_value = None

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get(f"/api/procedures/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.update_procedure", new_callable=AsyncMock)
def test_update_procedure(mock_update: AsyncMock) -> None:
    """Test PUT /api/procedures/{id} updates a procedure."""
    updated = MockProcedure(title="Updated Title")
    mock_update.return_value = updated

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.put(
            f"/api/procedures/{MOCK_PROCEDURE_ID}",
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.delete_procedure", new_callable=AsyncMock)
def test_delete_procedure(mock_delete: AsyncMock) -> None:
    """Test DELETE /api/procedures/{id} removes a procedure."""
    mock_delete.return_value = True

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.delete(f"/api/procedures/{MOCK_PROCEDURE_ID}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.update_procedure", new_callable=AsyncMock)
def test_update_procedure_not_found(mock_update: AsyncMock) -> None:
    """Test PUT /api/procedures/{id} returns 404 when procedure does not exist."""
    mock_update.return_value = None

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.put(
            f"/api/procedures/{uuid.uuid4()}",
            json={"title": "Ghost Procedure"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Procedure not found"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.delete_procedure", new_callable=AsyncMock)
def test_delete_procedure_not_found(mock_delete: AsyncMock) -> None:
    """Test DELETE /api/procedures/{id} returns 404 when not found."""
    mock_delete.return_value = False

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.delete(f"/api/procedures/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_create_procedure_validation() -> None:
    """Test POST /api/procedures rejects invalid data."""
    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.post("/api/procedures", json={"title": "Missing fields"})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
