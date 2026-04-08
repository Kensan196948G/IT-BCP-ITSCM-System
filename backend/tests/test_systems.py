"""Tests for IT System BCP CRUD API endpoints (mocked DB)."""

import uuid
from collections.abc import AsyncGenerator, Callable
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


def _mock_db_override() -> Callable[[], AsyncGenerator[AsyncMock, None]]:
    """Override get_db with a no-op async generator."""

    async def _fake_db() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    return _fake_db


@patch("apps.routers.systems.get_cached", new_callable=AsyncMock, return_value=None)
@patch("apps.routers.systems.set_cached", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_list_systems(mock_get_all: AsyncMock, _sc: AsyncMock, _gc: AsyncMock) -> None:
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


@patch("apps.routers.systems.get_cached", new_callable=AsyncMock)
@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_list_systems_cache_hit(mock_get_all: AsyncMock, mock_gc: AsyncMock) -> None:
    """Test GET /api/systems returns cached result without calling DB."""
    mock_gc.return_value = [MockSystem(system_name="Cached System")]

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get("/api/systems")
        assert response.status_code == 200
        assert response.json()[0]["system_name"] == "Cached System"
        mock_get_all.assert_not_called()
    finally:
        app.dependency_overrides.clear()


@patch("apps.routers.systems.invalidate_pattern", new_callable=AsyncMock)
@patch("apps.crud.create_system", new_callable=AsyncMock)
def test_create_system(mock_create: AsyncMock, mock_inv: AsyncMock) -> None:
    """Test POST /api/systems creates a new system and invalidates cache."""
    mock_create.return_value = MockSystem(**SAMPLE_SYSTEM)

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.post("/api/systems", json=SAMPLE_SYSTEM)
        assert response.status_code == 201
        data = response.json()
        assert data["system_name"] == "Core Banking System"
        assert data["criticality"] == "tier1"
        mock_inv.assert_awaited_once()
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


@patch("apps.routers.systems.invalidate_pattern", new_callable=AsyncMock)
@patch("apps.crud.update_system", new_callable=AsyncMock)
def test_update_system(mock_update: AsyncMock, mock_inv: AsyncMock) -> None:
    """Test PUT /api/systems/{id} updates a system and invalidates cache."""
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
        mock_inv.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


@patch("apps.routers.systems.invalidate_pattern", new_callable=AsyncMock)
@patch("apps.crud.delete_system", new_callable=AsyncMock)
def test_delete_system(mock_delete: AsyncMock, mock_inv: AsyncMock) -> None:
    """Test DELETE /api/systems/{id} removes a system and invalidates cache."""
    mock_delete.return_value = True

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.delete(f"/api/systems/{MOCK_SYSTEM_ID}")
        assert response.status_code == 204
        mock_inv.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.update_system", new_callable=AsyncMock)
def test_update_system_not_found(mock_update: AsyncMock) -> None:
    """Test PUT /api/systems/{id} returns 404 when system does not exist."""
    mock_update.return_value = None

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.put(
            f"/api/systems/{uuid.uuid4()}",
            json={"system_name": "Ghost System"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "System not found"
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


@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_export_systems_csv(mock_get_all: AsyncMock) -> None:
    """Test GET /api/systems/export/csv returns CSV content."""
    mock_get_all.return_value = [MockSystem()]

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get("/api/systems/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        assert "systems.csv" in response.headers["content-disposition"]
        lines = response.text.strip().splitlines()
        assert len(lines) == 2  # header + 1 data row
        assert "system_name" in lines[0]
        assert "Core Banking System" in lines[1]
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.get_all_systems", new_callable=AsyncMock)
def test_export_systems_csv_empty(mock_get_all: AsyncMock) -> None:
    """Test GET /api/systems/export/csv returns header-only CSV when no records."""
    mock_get_all.return_value = []

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get("/api/systems/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        lines = response.text.strip().splitlines()
        assert len(lines) == 1  # header only
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/systems/import/csv
# ---------------------------------------------------------------------------

_SYSTEMS_CSV_HEADER = "system_name,system_type,criticality,rto_target_hours,rpo_target_hours\n"
_SYSTEMS_CSV_ROW = "Core Banking System,onprem,tier1,4.0,1.0\n"


@patch("apps.routers.systems.invalidate_pattern", new_callable=AsyncMock)
@patch("apps.crud.create_system", new_callable=AsyncMock)
def test_import_systems_csv_success(mock_create: AsyncMock, mock_inv: AsyncMock) -> None:
    """POST /api/systems/import/csv imports valid rows and returns summary."""
    mock_create.return_value = MockSystem()

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        csv_content = _SYSTEMS_CSV_HEADER + _SYSTEMS_CSV_ROW
        response = client.post(
            "/api/systems/import/csv",
            files={"file": ("systems.csv", csv_content.encode(), "text/csv")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["total_rows"] == 1
        assert data["imported"] == 1
        assert data["skipped"] == 0
        assert data["errors"] == []
        mock_inv.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()


@patch("apps.routers.systems.invalidate_pattern", new_callable=AsyncMock)
@patch("apps.crud.create_system", new_callable=AsyncMock)
def test_import_systems_csv_partial_error(mock_create: AsyncMock, mock_inv: AsyncMock) -> None:
    """POST /api/systems/import/csv skips invalid rows and reports errors."""
    mock_create.return_value = MockSystem()

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        # Row 2 valid, Row 3 has invalid system_type
        csv_content = (
            "system_name,system_type,criticality,rto_target_hours,rpo_target_hours\n"
            "Core Banking System,onprem,tier1,4.0,1.0\n"
            "Bad System,invalid_type,tier1,4.0,1.0\n"
        )
        response = client.post(
            "/api/systems/import/csv",
            files={"file": ("systems.csv", csv_content.encode(), "text/csv")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["total_rows"] == 2
        assert data["imported"] == 1
        assert data["skipped"] == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["row"] == 3
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.create_system", new_callable=AsyncMock)
def test_import_systems_csv_empty_file(mock_create: AsyncMock) -> None:
    """POST /api/systems/import/csv handles an empty CSV (header only)."""
    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        csv_content = _SYSTEMS_CSV_HEADER  # header only, no data rows
        response = client.post(
            "/api/systems/import/csv",
            files={"file": ("systems.csv", csv_content.encode(), "text/csv")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["total_rows"] == 0
        assert data["imported"] == 0
        mock_create.assert_not_called()
    finally:
        app.dependency_overrides.clear()


@patch("apps.routers.systems.invalidate_pattern", new_callable=AsyncMock)
@patch("apps.crud.create_system", new_callable=AsyncMock)
def test_import_systems_csv_multiple_rows(mock_create: AsyncMock, mock_inv: AsyncMock) -> None:
    """POST /api/systems/import/csv imports multiple valid rows."""
    mock_create.return_value = MockSystem()

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        csv_content = (
            "system_name,system_type,criticality,rto_target_hours,rpo_target_hours\n"
            "System A,onprem,tier1,4.0,1.0\n"
            "System B,cloud,tier2,8.0,2.0\n"
            "System C,hybrid,tier3,24.0,4.0\n"
        )
        response = client.post(
            "/api/systems/import/csv",
            files={"file": ("systems.csv", csv_content.encode(), "text/csv")},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["total_rows"] == 3
        assert data["imported"] == 3
        assert data["skipped"] == 0
    finally:
        app.dependency_overrides.clear()
