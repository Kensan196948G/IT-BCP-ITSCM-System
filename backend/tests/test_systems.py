"""Tests for IT System BCP CRUD API endpoints (mocked DB)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

SAMPLE_SYSTEM = {
    "system_name": "Core Banking System",
    "system_type": "onprem",
    "criticality": "tier1",
    "rto_target_hours": 4.0,
    "rpo_target_hours": 1.0,
    "mtpd_hours": 24.0,
    "primary_owner": "IT Operations",
    "is_active": True,
}

MOCK_SYSTEM_ID = uuid.uuid4()


class MockSystem:
    """Mock SQLAlchemy model object for ITSystemBCP."""

    def __init__(self, **kwargs: object) -> None:
        self.id = kwargs.get("id", MOCK_SYSTEM_ID)
        self.system_name = kwargs.get("system_name", "Core Banking System")
        self.system_type = kwargs.get("system_type", "onprem")
        self.criticality = kwargs.get("criticality", "tier1")
        self.rto_target_hours = kwargs.get("rto_target_hours", 4.0)
        self.rpo_target_hours = kwargs.get("rpo_target_hours", 1.0)
        self.mtpd_hours = kwargs.get("mtpd_hours", 24.0)
        self.fallback_system = kwargs.get("fallback_system", None)
        self.fallback_procedure = kwargs.get("fallback_procedure", None)
        self.primary_owner = kwargs.get("primary_owner", "IT Operations")
        self.vendor_name = kwargs.get("vendor_name", None)
        self.last_dr_test = kwargs.get("last_dr_test", None)
        self.last_test_rto = kwargs.get("last_test_rto", None)
        self.is_active = kwargs.get("is_active", True)
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))


def _mock_db_override():  # type: ignore[no-untyped-def]
    """Override get_db with a no-op async generator."""

    async def _fake_db():  # type: ignore[no-untyped-def]
        yield AsyncMock()

    return _fake_db


@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_list_systems(mock_get_all: AsyncMock) -> None:
    """Test GET /api/systems returns a list."""
    mock_get_all.return_value = [MockSystem()]

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get("/api/systems")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["system_name"] == "Core Banking System"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.create_system", new_callable=AsyncMock)
def test_create_system(mock_create: AsyncMock) -> None:
    """Test POST /api/systems creates a new system."""
    mock_create.return_value = MockSystem(**SAMPLE_SYSTEM)

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.post("/api/systems", json=SAMPLE_SYSTEM)
        assert response.status_code == 201
        data = response.json()
        assert data["system_name"] == "Core Banking System"
        assert data["criticality"] == "tier1"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.get_system", new_callable=AsyncMock)
def test_get_system(mock_get: AsyncMock) -> None:
    """Test GET /api/systems/{id} returns a single system."""
    mock_get.return_value = MockSystem()

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get(f"/api/systems/{MOCK_SYSTEM_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["system_name"] == "Core Banking System"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.get_system", new_callable=AsyncMock)
def test_get_system_not_found(mock_get: AsyncMock) -> None:
    """Test GET /api/systems/{id} returns 404 when not found."""
    mock_get.return_value = None

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get(f"/api/systems/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.update_system", new_callable=AsyncMock)
def test_update_system(mock_update: AsyncMock) -> None:
    """Test PUT /api/systems/{id} updates a system."""
    updated = MockSystem(system_name="Updated System")
    mock_update.return_value = updated

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.put(
            f"/api/systems/{MOCK_SYSTEM_ID}",
            json={"system_name": "Updated System"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["system_name"] == "Updated System"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.delete_system", new_callable=AsyncMock)
def test_delete_system(mock_delete: AsyncMock) -> None:
    """Test DELETE /api/systems/{id} removes a system."""
    mock_delete.return_value = True

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.delete(f"/api/systems/{MOCK_SYSTEM_ID}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.delete_system", new_callable=AsyncMock)
def test_delete_system_not_found(mock_delete: AsyncMock) -> None:
    """Test DELETE /api/systems/{id} returns 404 when not found."""
    mock_delete.return_value = False

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.delete(f"/api/systems/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
