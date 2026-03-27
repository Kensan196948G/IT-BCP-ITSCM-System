"""Tests for the runbook API endpoints."""

import pytest

from apps.runbook import Runbook


class TestRunbookClass:
    """Unit tests for the Runbook class."""

    def test_deployment_checklist_has_12_items(self):
        result = Runbook.get_deployment_checklist()
        assert result["total_items"] == 12
        assert len(result["items"]) == 12

    def test_rollback_procedure_has_8_steps(self):
        result = Runbook.get_rollback_procedure()
        assert result["total_steps"] == 8
        assert len(result["steps"]) == 8

    def test_dr_failover_has_10_steps(self):
        result = Runbook.get_dr_failover_steps()
        assert result["total_steps"] == 10
        assert len(result["steps"]) == 10

    def test_earthquake_playbook_has_7_steps(self):
        result = Runbook.get_incident_response_playbook("earthquake")
        assert result["total_steps"] == 7
        assert len(result["steps"]) == 7

    def test_ransomware_playbook_has_8_steps(self):
        result = Runbook.get_incident_response_playbook("ransomware")
        assert result["total_steps"] == 8
        assert len(result["steps"]) == 8

    def test_dc_failure_playbook_has_6_steps(self):
        result = Runbook.get_incident_response_playbook("dc_failure")
        assert result["total_steps"] == 6
        assert len(result["steps"]) == 6

    def test_unknown_scenario_returns_error(self):
        result = Runbook.get_incident_response_playbook("unknown")
        assert "error" in result
        assert "available_scenarios" in result


class TestRunbookEndpoints:
    """Integration tests for runbook API endpoints."""

    def test_get_deployment_checklist(self, client):
        resp = client.get("/api/runbook/deployment-checklist")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_items"] == 12
        assert len(data["items"]) == 12
        # Verify each item has required fields
        for item in data["items"]:
            assert "id" in item
            assert "category" in item
            assert "item" in item
            assert "required" in item

    def test_get_rollback_procedure(self, client):
        resp = client.get("/api/runbook/rollback-procedure")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_steps"] == 8
        assert len(data["steps"]) == 8
        for step in data["steps"]:
            assert "step" in step
            assert "action" in step
            assert "responsible" in step

    def test_get_dr_failover(self, client):
        resp = client.get("/api/runbook/dr-failover")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_steps"] == 10
        assert len(data["steps"]) == 10

    def test_get_incident_playbook_earthquake(self, client):
        resp = client.get("/api/runbook/incident-playbook/earthquake")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_type"] == "earthquake"
        assert data["total_steps"] == 7

    def test_get_incident_playbook_ransomware(self, client):
        resp = client.get("/api/runbook/incident-playbook/ransomware")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_type"] == "ransomware"
        assert data["total_steps"] == 8

    def test_get_incident_playbook_dc_failure(self, client):
        resp = client.get("/api/runbook/incident-playbook/dc_failure")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_type"] == "dc_failure"
        assert data["total_steps"] == 6

    def test_get_incident_playbook_unknown_returns_404(self, client):
        resp = client.get("/api/runbook/incident-playbook/unknown_scenario")
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data

    def test_deployment_checklist_categories(self, client):
        resp = client.get("/api/runbook/deployment-checklist")
        data = resp.json()
        categories = {item["category"] for item in data["items"]}
        expected = {"テスト", "品質", "セキュリティ", "データベース", "インフラ", "承認"}
        assert categories == expected

    @pytest.mark.parametrize(
        "scenario,expected_steps",
        [
            ("earthquake", 7),
            ("ransomware", 8),
            ("dc_failure", 6),
        ],
    )
    def test_playbook_step_counts_parametrized(self, client, scenario, expected_steps):
        resp = client.get(f"/api/runbook/incident-playbook/{scenario}")
        assert resp.status_code == 200
        assert resp.json()["total_steps"] == expected_steps
