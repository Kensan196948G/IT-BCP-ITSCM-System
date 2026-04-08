"""Tests for the exercise engine and related API endpoints."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from tests.conftest import FIXED_UUID, FIXED_NOW, MockExercise

# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

SCENARIO_UUID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


class MockScenario:
    """Mock BCPScenario ORM instance."""

    def __init__(self, **overrides: object) -> None:
        defaults = {
            "id": SCENARIO_UUID,
            "scenario_id": "SCN-001",
            "title": "DC Failure Scenario",
            "scenario_type": "dc_failure",
            "description": "Data center failure drill",
            "initial_inject": "Power lost at primary DC",
            "injects": [
                {
                    "offset_minutes": 0,
                    "title": "Power failure",
                    "description": "Main power lost",
                    "expected_actions": ["Activate backup"],
                },
                {
                    "offset_minutes": 30,
                    "title": "Generator failure",
                    "description": "Backup generator fails",
                    "expected_actions": ["Escalate to vendor"],
                },
            ],
            "affected_systems": ["Core Banking", "Email"],
            "expected_duration_hours": 4.0,
            "difficulty": "hard",
            "is_active": True,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(self, k, v)


class MockRTORecord:
    """Mock ExerciseRTORecord ORM instance."""

    def __init__(self, **overrides: object) -> None:
        defaults = {
            "id": uuid.uuid4(),
            "exercise_id": FIXED_UUID,
            "system_name": "Core Banking",
            "rto_target_hours": 4.0,
            "rto_actual_hours": 3.5,
            "achieved": True,
            "recorded_at": FIXED_NOW,
            "recorded_by": "Test User",
            "notes": None,
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(self, k, v)


def sample_scenario_payload() -> dict[str, Any]:
    """Return a valid payload for creating a BCPScenario."""
    return {
        "scenario_id": "SCN-001",
        "title": "DC Failure Scenario",
        "scenario_type": "dc_failure",
        "description": "Data center failure drill",
        "initial_inject": "Power lost at primary DC",
        "injects": [
            {
                "offset_minutes": 0,
                "title": "Power failure",
                "description": "Main power lost",
                "expected_actions": ["Activate backup"],
            }
        ],
        "difficulty": "hard",
    }


# ---------------------------------------------------------------------------
# Scenario CRUD tests
# ---------------------------------------------------------------------------


@patch("apps.crud.get_all_scenarios", new_callable=AsyncMock)
def test_list_scenarios(mock_get_all: AsyncMock, client: TestClient) -> None:
    """GET /api/scenarios should return a list of scenarios."""
    mock_get_all.return_value = [MockScenario()]
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["scenario_id"] == "SCN-001"


@patch("apps.crud.get_all_scenarios", new_callable=AsyncMock)
def test_list_scenarios_empty(mock_get_all: AsyncMock, client: TestClient) -> None:
    """GET /api/scenarios should return empty list when none exist."""
    mock_get_all.return_value = []
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    assert response.json() == []


@patch("apps.crud.create_scenario", new_callable=AsyncMock)
def test_create_scenario(mock_create: AsyncMock, client: TestClient) -> None:
    """POST /api/scenarios should create and return a scenario."""
    mock_create.return_value = MockScenario()
    payload = sample_scenario_payload()
    response = client.post("/api/scenarios", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "DC Failure Scenario"
    assert data["difficulty"] == "hard"


def test_create_scenario_invalid_type(client: TestClient) -> None:
    """POST /api/scenarios should reject invalid scenario_type."""
    payload = sample_scenario_payload()
    payload["scenario_type"] = "zombie_apocalypse"
    response = client.post("/api/scenarios", json=payload)
    assert response.status_code == 422


@patch("apps.crud.get_scenario", new_callable=AsyncMock)
def test_get_scenario(mock_get: AsyncMock, client: TestClient) -> None:
    """GET /api/scenarios/{id} should return the scenario."""
    mock_get.return_value = MockScenario()
    response = client.get(f"/api/scenarios/{SCENARIO_UUID}")
    assert response.status_code == 200
    assert response.json()["scenario_id"] == "SCN-001"


@patch("apps.crud.get_scenario", new_callable=AsyncMock)
def test_get_scenario_not_found(mock_get: AsyncMock, client: TestClient) -> None:
    """GET /api/scenarios/{id} should return 404 when not found."""
    mock_get.return_value = None
    response = client.get(f"/api/scenarios/{uuid.uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Exercise start / complete tests
# ---------------------------------------------------------------------------


@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_start_exercise(mock_get: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/start should set status to in_progress."""
    exercise = MockExercise(status="planned")
    mock_get.return_value = exercise
    response = client.post(f"/api/exercises/{FIXED_UUID}/start")
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_start_exercise_already_in_progress(mock_get: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/start should reject non-planned exercises."""
    mock_get.return_value = MockExercise(status="in_progress")
    response = client.post(f"/api/exercises/{FIXED_UUID}/start")
    assert response.status_code == 400


@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_start_exercise_not_found(mock_get: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/start should return 400 when exercise not found."""
    mock_get.return_value = None
    response = client.post(f"/api/exercises/{uuid.uuid4()}/start")
    assert response.status_code == 400
    assert "Exercise not found" in response.json()["detail"]


@patch("apps.crud.get_rto_records_by_exercise", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_complete_exercise_pass(mock_get: AsyncMock, mock_rto: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/complete should set pass when all achieved."""
    exercise = MockExercise(status="in_progress")
    mock_get.return_value = exercise
    mock_rto.return_value = [
        MockRTORecord(achieved=True),
        MockRTORecord(achieved=True),
    ]
    response = client.post(f"/api/exercises/{FIXED_UUID}/complete")
    assert response.status_code == 200
    assert response.json()["overall_result"] == "pass"
    assert response.json()["status"] == "completed"


@patch("apps.crud.get_rto_records_by_exercise", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_complete_exercise_partial(mock_get: AsyncMock, mock_rto: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/complete should set partial_pass."""
    exercise = MockExercise(status="in_progress")
    mock_get.return_value = exercise
    mock_rto.return_value = [
        MockRTORecord(achieved=True),
        MockRTORecord(achieved=False),
    ]
    response = client.post(f"/api/exercises/{FIXED_UUID}/complete")
    assert response.status_code == 200
    assert response.json()["overall_result"] == "partial_pass"


@patch("apps.crud.get_rto_records_by_exercise", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_complete_exercise_fail(mock_get: AsyncMock, mock_rto: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/complete should set fail."""
    exercise = MockExercise(status="in_progress")
    mock_get.return_value = exercise
    mock_rto.return_value = [
        MockRTORecord(achieved=False),
        MockRTORecord(achieved=False),
    ]
    response = client.post(f"/api/exercises/{FIXED_UUID}/complete")
    assert response.status_code == 200
    assert response.json()["overall_result"] == "fail"


# ---------------------------------------------------------------------------
# RTO record tests
# ---------------------------------------------------------------------------


@patch("apps.crud.create_rto_record", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_record_rto(mock_get: AsyncMock, mock_create: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/rto-record should create RTO record."""
    mock_get.return_value = MockExercise(status="in_progress")
    mock_create.return_value = MockRTORecord()
    payload = {
        "system_name": "Core Banking",
        "rto_target_hours": 4.0,
        "rto_actual_hours": 3.5,
    }
    response = client.post(f"/api/exercises/{FIXED_UUID}/rto-record", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["system_name"] == "Core Banking"
    assert data["achieved"] is True


@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_record_rto_exercise_not_found(mock_get: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/rto-record should return 400 for missing exercise."""
    mock_get.return_value = None
    payload = {
        "system_name": "Core Banking",
        "rto_target_hours": 4.0,
    }
    response = client.post(f"/api/exercises/{uuid.uuid4()}/rto-record", json=payload)
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Report generation tests
# ---------------------------------------------------------------------------


@patch("apps.crud.get_rto_records_by_exercise", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_generate_report_with_records(mock_get: AsyncMock, mock_rto: AsyncMock, client: TestClient) -> None:
    """GET /api/exercises/{id}/report should return report with RTO data."""
    mock_get.return_value = MockExercise(status="completed")
    mock_rto.return_value = [
        MockRTORecord(
            system_name="Core Banking",
            rto_target_hours=4.0,
            rto_actual_hours=3.5,
            achieved=True,
        ),
        MockRTORecord(
            system_name="Email",
            rto_target_hours=2.0,
            rto_actual_hours=3.0,
            achieved=False,
        ),
    ]
    response = client.get(f"/api/exercises/{FIXED_UUID}/report")
    assert response.status_code == 200
    data = response.json()
    assert data["total_systems_tested"] == 2
    assert data["systems_achieved"] == 1
    assert data["systems_failed"] == 1
    assert data["rto_achievement_rate"] == 50.0
    assert len(data["findings"]) > 0
    assert len(data["recommendations"]) > 0


@patch("apps.crud.get_rto_records_by_exercise", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_generate_report_no_records(mock_get: AsyncMock, mock_rto: AsyncMock, client: TestClient) -> None:
    """GET /api/exercises/{id}/report should handle no RTO records."""
    mock_get.return_value = MockExercise(status="completed")
    mock_rto.return_value = []
    response = client.get(f"/api/exercises/{FIXED_UUID}/report")
    assert response.status_code == 200
    data = response.json()
    assert data["total_systems_tested"] == 0
    assert data["rto_achievement_rate"] is None
    assert len(data["findings"]) > 0


@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_generate_report_not_found(mock_get: AsyncMock, client: TestClient) -> None:
    """GET /api/exercises/{id}/report should return 400 for missing exercise."""
    mock_get.return_value = None
    response = client.get(f"/api/exercises/{uuid.uuid4()}/report")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# inject_scenario tests — cover engine lines 36-55
# ---------------------------------------------------------------------------


@patch("apps.crud.get_scenario", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_inject_scenario_success(mock_get: AsyncMock, mock_scenario: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/inject should return inject data."""
    exercise = MockExercise(status="in_progress", scenario_ref_id=SCENARIO_UUID)
    mock_get.return_value = exercise
    mock_scenario.return_value = MockScenario()
    response = client.post(
        f"/api/exercises/{FIXED_UUID}/inject",
        json={"inject_index": 0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inject_index"] == 0
    assert "inject" in data
    assert data["total_injects"] == 2


@patch("apps.crud.get_scenario", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_inject_scenario_out_of_range(mock_get: AsyncMock, mock_scenario: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/inject should return 400 for out-of-range index."""
    exercise = MockExercise(status="in_progress", scenario_ref_id=SCENARIO_UUID)
    mock_get.return_value = exercise
    mock_scenario.return_value = MockScenario()
    response = client.post(
        f"/api/exercises/{FIXED_UUID}/inject",
        json={"inject_index": 99},
    )
    assert response.status_code == 400
    assert "out of range" in response.json()["detail"]


@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_inject_scenario_not_in_progress(mock_get: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/inject should return 400 when exercise not in_progress."""
    mock_get.return_value = MockExercise(status="planned")
    response = client.post(
        f"/api/exercises/{FIXED_UUID}/inject",
        json={"inject_index": 0},
    )
    assert response.status_code == 400
    assert "not in progress" in response.json()["detail"]


@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_inject_scenario_exercise_not_found(mock_get: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/inject should return 400 when exercise not found."""
    mock_get.return_value = None
    response = client.post(
        f"/api/exercises/{uuid.uuid4()}/inject",
        json={"inject_index": 0},
    )
    assert response.status_code == 400
    assert "Exercise not found" in response.json()["detail"]


@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_inject_scenario_no_scenario_linked(mock_get: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/inject should return 400 when no scenario linked."""
    exercise = MockExercise(status="in_progress", scenario_ref_id=None)
    mock_get.return_value = exercise
    response = client.post(
        f"/api/exercises/{FIXED_UUID}/inject",
        json={"inject_index": 0},
    )
    assert response.status_code == 400
    assert "No scenario linked" in response.json()["detail"]


@patch("apps.crud.get_rto_records_by_exercise", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_complete_exercise_not_found(mock_get: AsyncMock, mock_rto: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/complete should return 400 when exercise not found."""
    mock_get.return_value = None
    response = client.post(f"/api/exercises/{uuid.uuid4()}/complete")
    assert response.status_code == 400
    assert "Exercise not found" in response.json()["detail"]


@patch("apps.crud.get_rto_records_by_exercise", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_complete_exercise_wrong_status(mock_get: AsyncMock, mock_rto: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/complete should return 400 for non-in_progress status."""
    mock_get.return_value = MockExercise(status="planned")
    response = client.post(f"/api/exercises/{FIXED_UUID}/complete")
    assert response.status_code == 400
    assert "Cannot complete" in response.json()["detail"]


@patch("apps.crud.get_rto_records_by_exercise", new_callable=AsyncMock)
@patch("apps.crud.get_exercise", new_callable=AsyncMock)
def test_complete_exercise_no_rto_records(mock_get: AsyncMock, mock_rto: AsyncMock, client: TestClient) -> None:
    """POST /api/exercises/{id}/complete with no RTO records defaults to pass."""
    exercise = MockExercise(status="in_progress")
    mock_get.return_value = exercise
    mock_rto.return_value = []
    response = client.post(f"/api/exercises/{FIXED_UUID}/complete")
    assert response.status_code == 200
    assert response.json()["overall_result"] == "pass"
