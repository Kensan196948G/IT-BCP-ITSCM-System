"""Tests for BCP Exercise API endpoints (mocked DB)."""

import uuid
from unittest.mock import AsyncMock, patch

from tests.conftest import FIXED_UUID, MockExercise, sample_exercise_payload


# ---------------------------------------------------------------------------
# GET /api/exercises  (list)
# ---------------------------------------------------------------------------


@patch("apps.crud.get_all_exercises", new_callable=AsyncMock)
def test_list_exercises(mock_get_all: AsyncMock, client) -> None:
    """GET /api/exercises should return a list of exercises."""
    mock_get_all.return_value = [MockExercise()]
    response = client.get("/api/exercises")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["exercise_id"] == "EX-2026-001"


@patch("apps.crud.get_all_exercises", new_callable=AsyncMock)
def test_list_exercises_empty(mock_get_all: AsyncMock, client) -> None:
    """GET /api/exercises should return empty list when no records exist."""
    mock_get_all.return_value = []
    response = client.get("/api/exercises")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# POST /api/exercises  (create)
# ---------------------------------------------------------------------------


@patch("apps.crud.create_exercise", new_callable=AsyncMock)
def test_create_exercise(mock_create: AsyncMock, client) -> None:
    """POST /api/exercises should create and return the exercise."""
    mock_create.return_value = MockExercise()
    payload = sample_exercise_payload()
    response = client.post("/api/exercises", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Annual DR drill"
    assert data["exercise_type"] == "tabletop"


def test_create_exercise_invalid_type(client) -> None:
    """POST /api/exercises should reject invalid exercise_type."""
    payload = sample_exercise_payload()
    payload["exercise_type"] = "invalid_type"
    response = client.post("/api/exercises", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/exercises/{id}  (detail)
# ---------------------------------------------------------------------------


@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_get_exercise(mock_get: AsyncMock, client) -> None:
    """GET /api/exercises/{id} should return the exercise."""
    mock_get.return_value = MockExercise()
    response = client.get(f"/api/exercises/{FIXED_UUID}")
    assert response.status_code == 200
    assert response.json()["exercise_id"] == "EX-2026-001"


@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_get_exercise_not_found(mock_get: AsyncMock, client) -> None:
    """GET /api/exercises/{id} should return 404 when not found."""
    mock_get.return_value = None
    response = client.get(f"/api/exercises/{uuid.uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/exercises/{id}  (update)
# ---------------------------------------------------------------------------


@patch("apps.crud.update_exercise", new_callable=AsyncMock)
def test_update_exercise(mock_update: AsyncMock, client) -> None:
    """PUT /api/exercises/{id} should update and return the exercise."""
    mock_update.return_value = MockExercise(title="Updated drill", status="completed", overall_result="pass")
    response = client.put(
        f"/api/exercises/{FIXED_UUID}",
        json={"title": "Updated drill", "status": "completed", "overall_result": "pass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated drill"
    assert data["status"] == "completed"


@patch("apps.crud.update_exercise", new_callable=AsyncMock)
def test_update_exercise_not_found(mock_update: AsyncMock, client) -> None:
    """PUT /api/exercises/{id} should return 404 when not found."""
    mock_update.return_value = None
    response = client.put(f"/api/exercises/{uuid.uuid4()}", json={"title": "No match"})
    assert response.status_code == 404
