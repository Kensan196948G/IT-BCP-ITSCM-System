"""Tests for BIA (Business Impact Analysis) endpoints and calculator."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from apps.bia_calculator import (
    calculate_recommended_rto,
    calculate_risk_score,
    get_bia_summary,
    get_risk_matrix,
)
from database import get_db
from main import app

FIXED_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")
FIXED_NOW = datetime(2026, 3, 27, 12, 0, 0, tzinfo=timezone.utc)


class MockBIA:
    """Mock BIAAssessment ORM instance."""

    def __init__(self, **overrides: object) -> None:
        defaults = {
            "id": FIXED_UUID,
            "assessment_id": "BIA-2026-001",
            "system_name": "Core Banking System",
            "assessment_date": date(2026, 3, 27),
            "assessor": "Risk Manager",
            "business_processes": ["決済処理", "口座管理"],
            "financial_impact_per_hour": 500.0,
            "financial_impact_per_day": 12000.0,
            "max_tolerable_downtime_hours": 24.0,
            "regulatory_risks": ["金融庁報告義務"],
            "reputation_impact": "high",
            "operational_impact": "critical",
            "recommended_rto_hours": 4.0,
            "recommended_rpo_hours": 1.0,
            "risk_score": 72,
            "mitigation_measures": ["DR環境整備"],
            "status": "draft",
            "notes": None,
            "created_at": FIXED_NOW,
            "updated_at": FIXED_NOW,
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            setattr(self, k, v)


def _sample_payload() -> dict:
    """Return a valid BIA assessment creation payload."""
    return {
        "assessment_id": "BIA-2026-001",
        "system_name": "Core Banking System",
        "assessment_date": "2026-03-27",
        "assessor": "Risk Manager",
        "business_processes": ["決済処理", "口座管理"],
        "financial_impact_per_hour": 500.0,
        "financial_impact_per_day": 12000.0,
        "max_tolerable_downtime_hours": 24.0,
        "regulatory_risks": ["金融庁報告義務"],
        "reputation_impact": "high",
        "operational_impact": "critical",
        "risk_score": 72,
        "status": "draft",
    }


def _fake_db():
    async def _gen():
        yield AsyncMock()

    return _gen


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = _fake_db()
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---- Calculator unit tests ----


class TestCalculateRiskScore:
    """Tests for calculate_risk_score function."""

    def test_all_none(self):
        score = calculate_risk_score()
        assert score == 1

    def test_high_financial_impact(self):
        score = calculate_risk_score(financial_impact_per_day=5000.0)
        assert 25 <= score <= 35

    def test_full_impact(self):
        score = calculate_risk_score(
            financial_impact_per_day=5000.0,
            regulatory_risks=["r1", "r2", "r3", "r4", "r5"],
            reputation_impact="critical",
            operational_impact="critical",
        )
        assert score == 100

    def test_medium_impact(self):
        score = calculate_risk_score(
            financial_impact_per_day=1000.0,
            regulatory_risks=["r1"],
            reputation_impact="medium",
            operational_impact="low",
        )
        assert 15 <= score <= 40


class TestCalculateRecommendedRto:
    """Tests for calculate_recommended_rto function."""

    def test_high_risk_with_mtpd(self):
        rto = calculate_recommended_rto(risk_score=80, mtpd_hours=24.0)
        assert rto == 2.4  # 24 * 0.10

    def test_mid_high_risk_with_mtpd(self):
        # risk_score 51-75 → fraction 0.25 (line 70)
        rto = calculate_recommended_rto(risk_score=60, mtpd_hours=24.0)
        assert rto == 6.0  # 24 * 0.25

    def test_mid_low_risk_with_mtpd(self):
        # risk_score 26-50 → fraction 0.50 (line 72)
        rto = calculate_recommended_rto(risk_score=40, mtpd_hours=24.0)
        assert rto == 12.0  # 24 * 0.50

    def test_low_risk_with_mtpd(self):
        rto = calculate_recommended_rto(risk_score=10, mtpd_hours=24.0)
        assert rto == 18.0  # 24 * 0.75

    def test_high_risk_no_mtpd(self):
        rto = calculate_recommended_rto(risk_score=80)
        assert rto == 2.0

    def test_mid_high_risk_no_mtpd(self):
        # risk_score 51-75 without MTPD → 4.0 (line 81)
        rto = calculate_recommended_rto(risk_score=60)
        assert rto == 4.0

    def test_mid_low_risk_no_mtpd(self):
        # risk_score 26-50 without MTPD → 8.0 (line 83)
        rto = calculate_recommended_rto(risk_score=40)
        assert rto == 8.0

    def test_low_risk_no_mtpd(self):
        rto = calculate_recommended_rto(risk_score=10)
        assert rto == 24.0


# ---- Summary and matrix tests ----


class TestBIASummary:
    """Tests for get_bia_summary function."""

    def test_empty(self):
        result = get_bia_summary([])
        assert result["total_assessments"] == 0
        assert result["average_risk_score"] is None

    def test_single(self):
        result = get_bia_summary([MockBIA()])
        assert result["total_assessments"] == 1
        assert result["average_risk_score"] == 72.0
        assert result["highest_risk_system"] == "Core Banking System"

    def test_multiple(self):
        assessments = [
            MockBIA(risk_score=80, system_name="System A"),
            MockBIA(risk_score=40, system_name="System B"),
        ]
        result = get_bia_summary(assessments)
        assert result["total_assessments"] == 2
        assert result["average_risk_score"] == 60.0
        assert result["highest_risk_system"] == "System A"


class TestRiskMatrix:
    """Tests for get_risk_matrix function."""

    def test_empty(self):
        result = get_risk_matrix([])
        assert result["entries"] == []
        assert len(result["matrix"]) == 5

    def test_single_entry(self):
        result = get_risk_matrix([MockBIA()])
        assert len(result["entries"]) == 1
        assert result["entries"][0]["system_name"] == "Core Banking System"
        # matrix should have count of 1 somewhere
        total = sum(sum(row) for row in result["matrix"])
        assert total == 1

    def test_skips_assessment_with_none_risk_score(self):
        # Assessment with risk_score=None should be skipped (line 173 `continue`)
        no_score = MockBIA(risk_score=None)
        valid = MockBIA(system_name="Valid System", risk_score=50)
        result = get_risk_matrix([no_score, valid])
        # Only the valid assessment should appear in entries
        assert len(result["entries"]) == 1
        assert result["entries"][0]["system_name"] == "Valid System"

    def test_risk_matrix_with_dict_assessments(self):
        # Pass dict-style assessments to cover _attr(obj, name) dict branch (line 201)
        dict_assessment = {
            "system_name": "Dict System",
            "risk_score": 65,
            "reputation_impact": "high",
            "operational_impact": "medium",
            "max_tolerable_downtime_hours": 8.0,
        }
        result = get_risk_matrix([dict_assessment])
        assert len(result["entries"]) == 1
        assert result["entries"][0]["system_name"] == "Dict System"


# ---- API endpoint tests ----


class TestBIAEndpoints:
    """Tests for BIA API endpoints."""

    @patch("apps.routers.bia.crud.create_bia_assessment", new_callable=AsyncMock)
    def test_create_bia(self, mock_create, client):
        mock_create.return_value = MockBIA()
        resp = client.post("/api/bia", json=_sample_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["assessment_id"] == "BIA-2026-001"
        assert data["system_name"] == "Core Banking System"

    @patch("apps.routers.bia.crud.get_all_bia_assessments", new_callable=AsyncMock)
    def test_list_bia(self, mock_list, client):
        mock_list.return_value = [MockBIA()]
        resp = client.get("/api/bia")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @patch("apps.routers.bia.crud.get_bia_assessment", new_callable=AsyncMock)
    def test_get_bia(self, mock_get, client):
        mock_get.return_value = MockBIA()
        resp = client.get(f"/api/bia/{FIXED_UUID}")
        assert resp.status_code == 200
        assert resp.json()["assessment_id"] == "BIA-2026-001"

    @patch("apps.routers.bia.crud.get_bia_assessment", new_callable=AsyncMock)
    def test_get_bia_not_found(self, mock_get, client):
        mock_get.return_value = None
        resp = client.get(f"/api/bia/{FIXED_UUID}")
        assert resp.status_code == 404

    @patch("apps.routers.bia.crud.update_bia_assessment", new_callable=AsyncMock)
    def test_update_bia(self, mock_update, client):
        mock_update.return_value = MockBIA(risk_score=85)
        resp = client.put(
            f"/api/bia/{FIXED_UUID}",
            json={"risk_score": 85},
        )
        assert resp.status_code == 200
        assert resp.json()["risk_score"] == 85

    @patch("apps.routers.bia.crud.delete_bia_assessment", new_callable=AsyncMock)
    def test_delete_bia(self, mock_delete, client):
        mock_delete.return_value = True
        resp = client.delete(f"/api/bia/{FIXED_UUID}")
        assert resp.status_code == 204

    @patch("apps.routers.bia.crud.get_all_bia_assessments", new_callable=AsyncMock)
    def test_summary(self, mock_list, client):
        mock_list.return_value = [MockBIA(), MockBIA(risk_score=50)]
        resp = client.get("/api/bia/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_assessments"] == 2
        assert data["average_risk_score"] == 61.0

    @patch("apps.routers.bia.crud.get_all_bia_assessments", new_callable=AsyncMock)
    def test_risk_matrix(self, mock_list, client):
        mock_list.return_value = [MockBIA()]
        resp = client.get("/api/bia/risk-matrix")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["matrix"]) == 5
        assert len(data["entries"]) == 1

    def test_create_bia_invalid_status(self, client):
        payload = _sample_payload()
        payload["status"] = "invalid"
        resp = client.post("/api/bia", json=payload)
        assert resp.status_code == 422

    def test_create_bia_blank_assessment_id(self, client):
        payload = _sample_payload()
        payload["assessment_id"] = "   "
        resp = client.post("/api/bia", json=payload)
        assert resp.status_code == 422
