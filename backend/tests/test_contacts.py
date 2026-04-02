"""Tests for Emergency Contact and Vendor Contact API endpoints (mocked DB)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

FIXED_NOW = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)
MOCK_CONTACT_ID = uuid.uuid4()
MOCK_VENDOR_ID = uuid.uuid4()

SAMPLE_EMERGENCY_CONTACT = {
    "name": "田中太郎",
    "role": "IT部門長",
    "department": "IT部門",
    "phone_primary": "03-1234-5678",
    "email": "tanaka@example.com",
    "escalation_level": 1,
    "escalation_group": "P1_FULL_BCP",
    "notification_channels": ["teams", "phone"],
    "is_active": True,
}

SAMPLE_VENDOR_CONTACT = {
    "vendor_name": "Oracle Japan",
    "service_name": "Oracle Database Support",
    "contract_id": "ORA-2026-001",
    "support_level": "premier",
    "phone_primary": "0120-000-000",
    "email_support": "support@oracle.example.com",
    "sla_response_hours": 1.0,
    "sla_resolution_hours": 4.0,
    "is_active": True,
}


class MockEmergencyContact:
    """Mock SQLAlchemy model object for EmergencyContact."""

    def __init__(self, **kwargs: object) -> None:
        self.id = kwargs.get("id", MOCK_CONTACT_ID)
        self.name = kwargs.get("name", "田中太郎")
        self.role = kwargs.get("role", "IT部門長")
        self.department = kwargs.get("department", "IT部門")
        self.phone_primary = kwargs.get("phone_primary", "03-1234-5678")
        self.phone_secondary = kwargs.get("phone_secondary", None)
        self.email = kwargs.get("email", "tanaka@example.com")
        self.teams_id = kwargs.get("teams_id", None)
        self.escalation_level = kwargs.get("escalation_level", 1)
        self.escalation_group = kwargs.get("escalation_group", "P1_FULL_BCP")
        self.notification_channels = kwargs.get("notification_channels", ["teams", "phone"])
        self.is_active = kwargs.get("is_active", True)
        self.notes = kwargs.get("notes", None)
        self.created_at = kwargs.get("created_at", FIXED_NOW)
        self.updated_at = kwargs.get("updated_at", FIXED_NOW)


class MockVendorContact:
    """Mock SQLAlchemy model object for VendorContact."""

    def __init__(self, **kwargs: object) -> None:
        self.id = kwargs.get("id", MOCK_VENDOR_ID)
        self.vendor_name = kwargs.get("vendor_name", "Oracle Japan")
        self.service_name = kwargs.get("service_name", "Oracle Database Support")
        self.contract_id = kwargs.get("contract_id", "ORA-2026-001")
        self.support_level = kwargs.get("support_level", "premier")
        self.phone_primary = kwargs.get("phone_primary", "0120-000-000")
        self.phone_emergency = kwargs.get("phone_emergency", None)
        self.email_support = kwargs.get("email_support", "support@oracle.example.com")
        self.sla_response_hours = kwargs.get("sla_response_hours", 1.0)
        self.sla_resolution_hours = kwargs.get("sla_resolution_hours", 4.0)
        self.contract_expiry = kwargs.get("contract_expiry", None)
        self.notes = kwargs.get("notes", None)
        self.is_active = kwargs.get("is_active", True)
        self.created_at = kwargs.get("created_at", FIXED_NOW)
        self.updated_at = kwargs.get("updated_at", FIXED_NOW)


def _mock_db_override():  # type: ignore[no-untyped-def]
    async def _fake_db():  # type: ignore[no-untyped-def]
        yield AsyncMock()

    return _fake_db


# ---- Emergency Contact Tests ----


@patch("apps.crud.get_all_emergency_contacts", new_callable=AsyncMock)
def test_list_emergency_contacts(mock_get_all: AsyncMock) -> None:
    """Test GET /api/contacts/emergency returns a list."""
    mock_get_all.return_value = [MockEmergencyContact()]

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get("/api/contacts/emergency")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "田中太郎"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.create_emergency_contact", new_callable=AsyncMock)
def test_create_emergency_contact(mock_create: AsyncMock) -> None:
    """Test POST /api/contacts/emergency creates a new contact."""
    mock_create.return_value = MockEmergencyContact(**SAMPLE_EMERGENCY_CONTACT)

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.post("/api/contacts/emergency", json=SAMPLE_EMERGENCY_CONTACT)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "田中太郎"
        assert data["escalation_group"] == "P1_FULL_BCP"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.get_emergency_contact", new_callable=AsyncMock)
def test_get_emergency_contact(mock_get: AsyncMock) -> None:
    """Test GET /api/contacts/emergency/{id} returns a single contact."""
    mock_get.return_value = MockEmergencyContact()

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get(f"/api/contacts/emergency/{MOCK_CONTACT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "田中太郎"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.get_emergency_contact", new_callable=AsyncMock)
def test_get_emergency_contact_not_found(mock_get: AsyncMock) -> None:
    """Test GET /api/contacts/emergency/{id} returns 404 when not found."""
    mock_get.return_value = None

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get(f"/api/contacts/emergency/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.get_emergency_contacts_by_escalation_group", new_callable=AsyncMock)
def test_get_emergency_contacts_by_escalation(mock_get: AsyncMock) -> None:
    """Test GET /api/contacts/emergency/escalation/{group} returns filtered contacts."""
    mock_get.return_value = [MockEmergencyContact()]

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get("/api/contacts/emergency/escalation/P1_FULL_BCP")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
    finally:
        app.dependency_overrides.clear()


# ---- Vendor Contact Tests ----


@patch("apps.crud.get_all_vendor_contacts", new_callable=AsyncMock)
def test_list_vendor_contacts(mock_get_all: AsyncMock) -> None:
    """Test GET /api/contacts/vendors returns a list."""
    mock_get_all.return_value = [MockVendorContact()]

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get("/api/contacts/vendors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["vendor_name"] == "Oracle Japan"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.create_vendor_contact", new_callable=AsyncMock)
def test_create_vendor_contact(mock_create: AsyncMock) -> None:
    """Test POST /api/contacts/vendors creates a new vendor contact."""
    mock_create.return_value = MockVendorContact(**SAMPLE_VENDOR_CONTACT)

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.post("/api/contacts/vendors", json=SAMPLE_VENDOR_CONTACT)
        assert response.status_code == 201
        data = response.json()
        assert data["vendor_name"] == "Oracle Japan"
        assert data["support_level"] == "premier"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.get_vendor_contact", new_callable=AsyncMock)
def test_get_vendor_contact(mock_get: AsyncMock) -> None:
    """Test GET /api/contacts/vendors/{id} returns a single vendor contact."""
    mock_get.return_value = MockVendorContact()

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get(f"/api/contacts/vendors/{MOCK_VENDOR_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["vendor_name"] == "Oracle Japan"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.get_vendor_contact", new_callable=AsyncMock)
def test_get_vendor_contact_not_found(mock_get: AsyncMock) -> None:
    """Test GET /api/contacts/vendors/{id} returns 404 when not found."""
    mock_get.return_value = None

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.get(f"/api/contacts/vendors/{uuid.uuid4()}")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.delete_vendor_contact", new_callable=AsyncMock)
def test_delete_vendor_contact(mock_delete: AsyncMock) -> None:
    """Test DELETE /api/contacts/vendors/{id} removes a vendor contact."""
    mock_delete.return_value = True

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.delete(f"/api/contacts/vendors/{MOCK_VENDOR_ID}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()


# ---- Error path tests for update/delete 404s ----


@patch("apps.crud.update_emergency_contact", new_callable=AsyncMock)
def test_update_emergency_contact_not_found(mock_update: AsyncMock) -> None:
    """Test PUT /api/contacts/emergency/{id} returns 404 when record does not exist."""
    mock_update.return_value = None

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.put(
            f"/api/contacts/emergency/{uuid.uuid4()}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Emergency contact not found"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.delete_emergency_contact", new_callable=AsyncMock)
def test_delete_emergency_contact_not_found(mock_delete: AsyncMock) -> None:
    """Test DELETE /api/contacts/emergency/{id} returns 404 when record does not exist."""
    mock_delete.return_value = False

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.delete(f"/api/contacts/emergency/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Emergency contact not found"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.update_vendor_contact", new_callable=AsyncMock)
def test_update_vendor_contact_not_found(mock_update: AsyncMock) -> None:
    """Test PUT /api/contacts/vendors/{id} returns 404 when record does not exist."""
    mock_update.return_value = None

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.put(
            f"/api/contacts/vendors/{uuid.uuid4()}",
            json={"company_name": "Updated Corp"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Vendor contact not found"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.delete_vendor_contact", new_callable=AsyncMock)
def test_delete_vendor_contact_not_found(mock_delete: AsyncMock) -> None:
    """Test DELETE /api/contacts/vendors/{id} returns 404 when record does not exist."""
    mock_delete.return_value = False

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.delete(f"/api/contacts/vendors/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Vendor contact not found"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.update_emergency_contact", new_callable=AsyncMock)
def test_update_emergency_contact_success(mock_update: AsyncMock) -> None:
    """Test PUT /api/contacts/emergency/{id} returns updated object on success."""
    contact_id = MOCK_CONTACT_ID
    mock_update.return_value = MockEmergencyContact(name="Updated Name")

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.put(
            f"/api/contacts/emergency/{contact_id}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
    finally:
        app.dependency_overrides.clear()


@patch("apps.crud.update_vendor_contact", new_callable=AsyncMock)
def test_update_vendor_contact_success(mock_update: AsyncMock) -> None:
    """Test PUT /api/contacts/vendors/{id} returns updated object on success."""
    vendor_id = MOCK_VENDOR_ID
    mock_update.return_value = MockVendorContact(vendor_name="Updated Corp")

    from database import get_db

    app.dependency_overrides[get_db] = _mock_db_override()
    try:
        response = client.put(
            f"/api/contacts/vendors/{vendor_id}",
            json={"vendor_name": "Updated Corp"},
        )
        assert response.status_code == 200
        assert response.json()["vendor_name"] == "Updated Corp"
    finally:
        app.dependency_overrides.clear()
