"""Shared test fixtures and helpers for IT-BCP-ITSCM-System tests."""

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from apps.auth import ROLE_PERMISSIONS, AuthService
from database import get_db
from main import app

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

_MOCK_ADMIN: dict[str, Any] = {
    "user_id": "test-admin",
    "role": "admin",
    "permissions": ROLE_PERMISSIONS["admin"],
}


async def _mock_admin_user() -> dict[str, Any]:
    """Return a mock admin user — used to bypass JWT auth in tests."""
    return _MOCK_ADMIN


# ---------------------------------------------------------------------------
# Fake DB dependency
# ---------------------------------------------------------------------------


def _fake_db_generator():
    """Return an async generator yielding a mock session."""

    async def _gen():
        yield AsyncMock()

    return _gen


@pytest.fixture(autouse=True)
def _auto_auth():
    """Automatically inject mock admin auth for every test.

    Tests that specifically verify 401 behaviour must use the
    ``unauthenticated_client`` fixture, which explicitly removes this override.
    """
    app.dependency_overrides[AuthService.get_current_user] = _mock_admin_user
    yield
    app.dependency_overrides.pop(AuthService.get_current_user, None)


@pytest.fixture()
def client():
    """Provide a TestClient with the DB dependency and auth overridden."""
    from main import _rate_limiter

    app.dependency_overrides[get_db] = _fake_db_generator()
    app.dependency_overrides[AuthService.get_current_user] = _mock_admin_user
    _rate_limiter._history.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()
    _rate_limiter._history.clear()


@pytest.fixture()
def unauthenticated_client():
    """Provide a TestClient with DB overridden but NO auth override.

    Use this for tests that specifically verify 401 / authentication behaviour.
    The autouse ``_auto_auth`` fixture is intentionally cancelled here.
    """
    from main import _rate_limiter

    app.dependency_overrides[get_db] = _fake_db_generator()
    app.dependency_overrides.pop(AuthService.get_current_user, None)
    _rate_limiter._history.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()
    _rate_limiter._history.clear()


# ---------------------------------------------------------------------------
# Sample data helpers
# ---------------------------------------------------------------------------

FIXED_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")
FIXED_NOW = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)


class MockExercise:
    """Mock object mimicking a BCPExercise ORM instance."""

    def __init__(self, **overrides: object) -> None:
        defaults = {
            "id": FIXED_UUID,
            "exercise_id": "EX-2026-001",
            "title": "Annual DR drill",
            "exercise_type": "tabletop",
            "scenario_description": "DC failure scenario",
            "scheduled_date": FIXED_NOW,
            "actual_date": None,
            "duration_hours": 2.0,
            "facilitator": "IT Manager",
            "status": "planned",
            "overall_result": None,
            "findings": None,
            "improvements": None,
            "lessons_learned": None,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(self, k, v)


class MockIncident:
    """Mock object mimicking an ActiveIncident ORM instance."""

    def __init__(self, **overrides: object) -> None:
        defaults = {
            "id": FIXED_UUID,
            "incident_id": "BCP-2026-001",
            "title": "DC power failure",
            "scenario_type": "dc_failure",
            "severity": "p1",
            "occurred_at": FIXED_NOW,
            "detected_at": FIXED_NOW,
            "declared_at": None,
            "incident_commander": "Incident Lead",
            "status": "active",
            "situation_report": None,
            "affected_systems": ["Core Banking System"],
            "affected_users": 500,
            "estimated_impact": "High",
            "resolved_at": None,
            "actual_rto_hours": None,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(self, k, v)


class MockSystem:
    """Mock object mimicking an ITSystemBCP ORM instance."""

    def __init__(self, **overrides: object) -> None:
        defaults = {
            "id": FIXED_UUID,
            "system_name": "Core Banking System",
            "system_type": "onprem",
            "criticality": "tier1",
            "rto_target_hours": 4.0,
            "rpo_target_hours": 1.0,
            "mtpd_hours": 24.0,
            "fallback_system": None,
            "fallback_procedure": None,
            "primary_owner": "IT Operations",
            "vendor_name": None,
            "last_dr_test": None,
            "last_test_rto": None,
            "is_active": True,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(self, k, v)


def sample_exercise_payload() -> dict:
    """Return a valid payload for creating a BCPExercise."""
    return {
        "exercise_id": "EX-2026-001",
        "title": "Annual DR drill",
        "exercise_type": "tabletop",
        "scenario_description": "DC failure scenario",
        "scheduled_date": "2026-03-27T12:00:00Z",
        "status": "planned",
    }


def sample_incident_payload() -> dict:
    """Return a valid payload for creating an ActiveIncident."""
    return {
        "incident_id": "BCP-2026-001",
        "title": "DC power failure",
        "scenario_type": "dc_failure",
        "severity": "p1",
        "occurred_at": "2026-03-27T12:00:00Z",
        "detected_at": "2026-03-27T12:05:00Z",
        "status": "active",
        "affected_systems": ["Core Banking System"],
        "affected_users": 500,
    }
