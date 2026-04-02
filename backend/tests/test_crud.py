"""Unit tests for apps/crud.py — all 11 entity CRUD functions.

Strategy:
- Use AsyncMock to simulate AsyncSession (no real DB required).
- Mock db.execute() to return a MagicMock whose scalar_one_or_none() / scalars().all()
  return the expected ORM object or None.
- Test both success path and "not found" path for get/update/delete.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

import apps.crud as crud
from apps.models import (
    ActiveIncident,
    BCPExercise,
    BCPScenario,
    BIAAssessment,
    EmergencyContact,
    ExerciseRTORecord,
    ITSystemBCP,
    IncidentTask,
    RecoveryProcedure,
    SituationReport,
    VendorContact,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_UUID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


def _mock_db_execute_scalar(return_val):
    """Return an AsyncMock db whose execute().scalar_one_or_none() returns return_val."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = return_val
    db = AsyncMock()
    db.execute.return_value = result
    return db


def _mock_db_execute_scalars(items: list):
    """Return an AsyncMock db whose execute().scalars().all() returns items."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = items
    result = MagicMock()
    result.scalars.return_value = scalars_mock
    db = AsyncMock()
    db.execute.return_value = result
    return db


# ---------------------------------------------------------------------------
# ITSystemBCP CRUD
# ---------------------------------------------------------------------------


class TestITSystemBCPCRUD:
    @pytest.mark.asyncio
    async def test_create_system(self):
        db = AsyncMock()
        await crud.create_system(
            db,
            {
                "system_name": "SysA",
                "system_type": "onprem",
                "criticality": "tier1",
                "rto_target_hours": 4.0,
                "rpo_target_hours": 1.0,
                "mtpd_hours": 24.0,
                "primary_owner": "IT Ops",
            },
        )
        assert db.add.called
        assert db.flush.called

    @pytest.mark.asyncio
    async def test_get_system_found(self):
        obj = ITSystemBCP()
        db = _mock_db_execute_scalar(obj)
        result = await crud.get_system(db, SAMPLE_UUID)
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_system_not_found(self):
        db = _mock_db_execute_scalar(None)
        result = await crud.get_system(db, SAMPLE_UUID)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_systems(self):
        items = [ITSystemBCP(), ITSystemBCP()]
        db = _mock_db_execute_scalars(items)
        result = await crud.get_all_systems(db)
        assert result == items

    @pytest.mark.asyncio
    async def test_update_system_found(self):
        obj = ITSystemBCP(system_name="Old")
        db = _mock_db_execute_scalar(obj)
        result = await crud.update_system(db, SAMPLE_UUID, {"system_name": "New"})
        assert result is obj
        assert obj.system_name == "New"

    @pytest.mark.asyncio
    async def test_update_system_not_found(self):
        db = _mock_db_execute_scalar(None)
        result = await crud.update_system(db, SAMPLE_UUID, {"system_name": "New"})
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_system_found(self):
        obj = ITSystemBCP()
        db = _mock_db_execute_scalar(obj)
        result = await crud.delete_system(db, SAMPLE_UUID)
        assert result is True
        db.delete.assert_called_once_with(obj)

    @pytest.mark.asyncio
    async def test_delete_system_not_found(self):
        db = _mock_db_execute_scalar(None)
        result = await crud.delete_system(db, SAMPLE_UUID)
        assert result is False


# ---------------------------------------------------------------------------
# RecoveryProcedure CRUD
# ---------------------------------------------------------------------------


class TestRecoveryProcedureCRUD:
    @pytest.mark.asyncio
    async def test_create_procedure(self):
        db = AsyncMock()
        await crud.create_procedure(
            db,
            {
                "procedure_id": "PROC-001",
                "system_name": "Core DB",
                "scenario_type": "dc_failure",
                "title": "Restart DB",
                "priority_order": 1,
                "procedure_steps": [{"step": 1, "action": "Do X"}],
            },
        )
        assert db.add.called

    @pytest.mark.asyncio
    async def test_get_procedure_found(self):
        obj = RecoveryProcedure()
        db = _mock_db_execute_scalar(obj)
        assert await crud.get_procedure(db, SAMPLE_UUID) is obj

    @pytest.mark.asyncio
    async def test_get_procedure_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.get_procedure(db, SAMPLE_UUID) is None

    @pytest.mark.asyncio
    async def test_get_all_procedures(self):
        items = [RecoveryProcedure()]
        db = _mock_db_execute_scalars(items)
        assert await crud.get_all_procedures(db) == items

    @pytest.mark.asyncio
    async def test_update_procedure_found(self):
        obj = RecoveryProcedure()
        obj.action_description = "Old"
        db = _mock_db_execute_scalar(obj)
        result = await crud.update_procedure(db, SAMPLE_UUID, {"action_description": "New"})
        assert result is obj
        assert obj.action_description == "New"

    @pytest.mark.asyncio
    async def test_update_procedure_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.update_procedure(db, SAMPLE_UUID, {}) is None

    @pytest.mark.asyncio
    async def test_delete_procedure_found(self):
        obj = RecoveryProcedure()
        db = _mock_db_execute_scalar(obj)
        assert await crud.delete_procedure(db, SAMPLE_UUID) is True

    @pytest.mark.asyncio
    async def test_delete_procedure_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.delete_procedure(db, SAMPLE_UUID) is False


# ---------------------------------------------------------------------------
# EmergencyContact CRUD
# ---------------------------------------------------------------------------


class TestEmergencyContactCRUD:
    @pytest.mark.asyncio
    async def test_create_emergency_contact(self):
        db = AsyncMock()
        await crud.create_emergency_contact(
            db,
            {
                "name": "Alice",
                "role": "Manager",
                "escalation_level": 1,
                "escalation_group": "L1",
            },
        )
        assert db.add.called

    @pytest.mark.asyncio
    async def test_get_emergency_contact_found(self):
        obj = EmergencyContact()
        db = _mock_db_execute_scalar(obj)
        assert await crud.get_emergency_contact(db, SAMPLE_UUID) is obj

    @pytest.mark.asyncio
    async def test_get_emergency_contact_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.get_emergency_contact(db, SAMPLE_UUID) is None

    @pytest.mark.asyncio
    async def test_get_all_emergency_contacts(self):
        items = [EmergencyContact(), EmergencyContact()]
        db = _mock_db_execute_scalars(items)
        assert await crud.get_all_emergency_contacts(db) == items

    @pytest.mark.asyncio
    async def test_update_emergency_contact_found(self):
        obj = EmergencyContact()
        obj.name = "Old"
        db = _mock_db_execute_scalar(obj)
        result = await crud.update_emergency_contact(db, SAMPLE_UUID, {"name": "New"})
        assert result is obj
        assert obj.name == "New"

    @pytest.mark.asyncio
    async def test_update_emergency_contact_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.update_emergency_contact(db, SAMPLE_UUID, {}) is None

    @pytest.mark.asyncio
    async def test_delete_emergency_contact_found(self):
        obj = EmergencyContact()
        db = _mock_db_execute_scalar(obj)
        assert await crud.delete_emergency_contact(db, SAMPLE_UUID) is True

    @pytest.mark.asyncio
    async def test_delete_emergency_contact_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.delete_emergency_contact(db, SAMPLE_UUID) is False

    @pytest.mark.asyncio
    async def test_get_emergency_contacts_by_escalation_group(self):
        items = [EmergencyContact()]
        db = _mock_db_execute_scalars(items)
        result = await crud.get_emergency_contacts_by_escalation_group(db, "L1")
        assert result == items


# ---------------------------------------------------------------------------
# VendorContact CRUD
# ---------------------------------------------------------------------------


class TestVendorContactCRUD:
    @pytest.mark.asyncio
    async def test_create_vendor_contact(self):
        db = AsyncMock()
        await crud.create_vendor_contact(
            db,
            {
                "vendor_name": "ACME",
                "service_name": "Cloud Hosting",
            },
        )
        assert db.add.called

    @pytest.mark.asyncio
    async def test_get_vendor_contact_found(self):
        obj = VendorContact()
        db = _mock_db_execute_scalar(obj)
        assert await crud.get_vendor_contact(db, SAMPLE_UUID) is obj

    @pytest.mark.asyncio
    async def test_get_vendor_contact_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.get_vendor_contact(db, SAMPLE_UUID) is None

    @pytest.mark.asyncio
    async def test_get_all_vendor_contacts(self):
        items = [VendorContact()]
        db = _mock_db_execute_scalars(items)
        assert await crud.get_all_vendor_contacts(db) == items

    @pytest.mark.asyncio
    async def test_update_vendor_contact_found(self):
        obj = VendorContact()
        obj.contact_name = "Old"
        db = _mock_db_execute_scalar(obj)
        result = await crud.update_vendor_contact(db, SAMPLE_UUID, {"contact_name": "New"})
        assert result is obj
        assert obj.contact_name == "New"

    @pytest.mark.asyncio
    async def test_update_vendor_contact_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.update_vendor_contact(db, SAMPLE_UUID, {}) is None

    @pytest.mark.asyncio
    async def test_delete_vendor_contact_found(self):
        obj = VendorContact()
        db = _mock_db_execute_scalar(obj)
        assert await crud.delete_vendor_contact(db, SAMPLE_UUID) is True

    @pytest.mark.asyncio
    async def test_delete_vendor_contact_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.delete_vendor_contact(db, SAMPLE_UUID) is False


# ---------------------------------------------------------------------------
# BCPExercise CRUD
# ---------------------------------------------------------------------------


class TestBCPExerciseCRUD:
    @pytest.mark.asyncio
    async def test_create_exercise(self):
        db = AsyncMock()
        await crud.create_exercise(
            db,
            {
                "exercise_id": "EX-001",
                "title": "Drill",
                "exercise_type": "tabletop",
                "scheduled_date": "2026-01-01",
                "status": "planned",
            },
        )
        assert db.add.called

    @pytest.mark.asyncio
    async def test_get_exercise_found(self):
        obj = BCPExercise()
        db = _mock_db_execute_scalar(obj)
        assert await crud.get_exercise(db, SAMPLE_UUID) is obj

    @pytest.mark.asyncio
    async def test_get_exercise_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.get_exercise(db, SAMPLE_UUID) is None

    @pytest.mark.asyncio
    async def test_get_all_exercises(self):
        items = [BCPExercise(), BCPExercise()]
        db = _mock_db_execute_scalars(items)
        assert await crud.get_all_exercises(db) == items

    @pytest.mark.asyncio
    async def test_update_exercise_found(self):
        obj = BCPExercise()
        obj.title = "Old"
        db = _mock_db_execute_scalar(obj)
        result = await crud.update_exercise(db, SAMPLE_UUID, {"title": "New"})
        assert result is obj
        assert obj.title == "New"

    @pytest.mark.asyncio
    async def test_update_exercise_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.update_exercise(db, SAMPLE_UUID, {}) is None


# ---------------------------------------------------------------------------
# ActiveIncident CRUD
# ---------------------------------------------------------------------------


class TestActiveIncidentCRUD:
    @pytest.mark.asyncio
    async def test_create_incident(self):
        db = AsyncMock()
        await crud.create_incident(
            db,
            {
                "incident_id": "INC-001",
                "title": "Outage",
                "scenario_type": "dc_failure",
                "severity": "p1",
                "occurred_at": "2026-01-01T00:00:00Z",
                "detected_at": "2026-01-01T00:01:00Z",
                "status": "active",
                "affected_systems": ["SysA"],
                "affected_users": 100,
            },
        )
        assert db.add.called

    @pytest.mark.asyncio
    async def test_get_incident_found(self):
        obj = ActiveIncident()
        db = _mock_db_execute_scalar(obj)
        assert await crud.get_incident(db, SAMPLE_UUID) is obj

    @pytest.mark.asyncio
    async def test_get_incident_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.get_incident(db, SAMPLE_UUID) is None

    @pytest.mark.asyncio
    async def test_get_all_incidents(self):
        items = [ActiveIncident()]
        db = _mock_db_execute_scalars(items)
        assert await crud.get_all_incidents(db) == items

    @pytest.mark.asyncio
    async def test_update_incident_found(self):
        obj = ActiveIncident()
        obj.status = "active"
        db = _mock_db_execute_scalar(obj)
        result = await crud.update_incident(db, SAMPLE_UUID, {"status": "resolved"})
        assert result is obj
        assert obj.status == "resolved"

    @pytest.mark.asyncio
    async def test_update_incident_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.update_incident(db, SAMPLE_UUID, {}) is None

    @pytest.mark.asyncio
    async def test_get_active_incidents(self):
        items = [ActiveIncident(), ActiveIncident()]
        db = _mock_db_execute_scalars(items)
        result = await crud.get_active_incidents(db)
        assert result == items


# ---------------------------------------------------------------------------
# BIAAssessment CRUD
# ---------------------------------------------------------------------------


class TestBIAAssessmentCRUD:
    @pytest.mark.asyncio
    async def test_create_bia_assessment(self):
        db = AsyncMock()
        await crud.create_bia_assessment(
            db,
            {
                "assessment_id": "BIA-001",
                "system_name": "Core DB",
                "assessment_date": "2026-01-01",
                "business_processes": ["Payments"],
            },
        )
        assert db.add.called

    @pytest.mark.asyncio
    async def test_get_bia_assessment_found(self):
        obj = BIAAssessment()
        db = _mock_db_execute_scalar(obj)
        assert await crud.get_bia_assessment(db, SAMPLE_UUID) is obj

    @pytest.mark.asyncio
    async def test_get_bia_assessment_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.get_bia_assessment(db, SAMPLE_UUID) is None

    @pytest.mark.asyncio
    async def test_get_all_bia_assessments(self):
        items = [BIAAssessment()]
        db = _mock_db_execute_scalars(items)
        assert await crud.get_all_bia_assessments(db) == items

    @pytest.mark.asyncio
    async def test_update_bia_assessment_found(self):
        obj = BIAAssessment()
        obj.business_impact = "Medium"
        db = _mock_db_execute_scalar(obj)
        result = await crud.update_bia_assessment(db, SAMPLE_UUID, {"business_impact": "High"})
        assert result is obj
        assert obj.business_impact == "High"

    @pytest.mark.asyncio
    async def test_update_bia_assessment_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.update_bia_assessment(db, SAMPLE_UUID, {}) is None

    @pytest.mark.asyncio
    async def test_delete_bia_assessment_found(self):
        obj = BIAAssessment()
        db = _mock_db_execute_scalar(obj)
        assert await crud.delete_bia_assessment(db, SAMPLE_UUID) is True

    @pytest.mark.asyncio
    async def test_delete_bia_assessment_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.delete_bia_assessment(db, SAMPLE_UUID) is False


# ---------------------------------------------------------------------------
# BCPScenario CRUD
# ---------------------------------------------------------------------------


class TestBCPScenarioCRUD:
    @pytest.mark.asyncio
    async def test_create_scenario(self):
        db = AsyncMock()
        await crud.create_scenario(
            db,
            {
                "scenario_id": "SCN-001",
                "title": "DC Failure",
                "scenario_type": "dc_failure",
                "description": "Primary DC fails",
                "initial_inject": "DC power lost",
                "injects": [{"time": 0, "event": "Alert"}],
            },
        )
        assert db.add.called

    @pytest.mark.asyncio
    async def test_get_scenario_found(self):
        obj = BCPScenario()
        db = _mock_db_execute_scalar(obj)
        assert await crud.get_scenario(db, SAMPLE_UUID) is obj

    @pytest.mark.asyncio
    async def test_get_scenario_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.get_scenario(db, SAMPLE_UUID) is None

    @pytest.mark.asyncio
    async def test_get_all_scenarios(self):
        items = [BCPScenario(), BCPScenario()]
        db = _mock_db_execute_scalars(items)
        assert await crud.get_all_scenarios(db) == items

    @pytest.mark.asyncio
    async def test_update_scenario_found(self):
        obj = BCPScenario()
        obj.scenario_name = "Old"
        db = _mock_db_execute_scalar(obj)
        result = await crud.update_scenario(db, SAMPLE_UUID, {"scenario_name": "New"})
        assert result is obj
        assert obj.scenario_name == "New"

    @pytest.mark.asyncio
    async def test_update_scenario_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.update_scenario(db, SAMPLE_UUID, {}) is None

    @pytest.mark.asyncio
    async def test_delete_scenario_found(self):
        obj = BCPScenario()
        db = _mock_db_execute_scalar(obj)
        assert await crud.delete_scenario(db, SAMPLE_UUID) is True

    @pytest.mark.asyncio
    async def test_delete_scenario_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.delete_scenario(db, SAMPLE_UUID) is False


# ---------------------------------------------------------------------------
# ExerciseRTORecord CRUD
# ---------------------------------------------------------------------------


class TestExerciseRTORecordCRUD:
    @pytest.mark.asyncio
    async def test_create_rto_record(self):
        db = AsyncMock()
        await crud.create_rto_record(
            db,
            {
                "exercise_id": SAMPLE_UUID,
                "system_name": "Core DB",
                "rto_target_hours": 4.0,
            },
        )
        assert db.add.called

    @pytest.mark.asyncio
    async def test_get_rto_records_by_exercise(self):
        items = [ExerciseRTORecord(), ExerciseRTORecord()]
        db = _mock_db_execute_scalars(items)
        result = await crud.get_rto_records_by_exercise(db, SAMPLE_UUID)
        assert result == items

    @pytest.mark.asyncio
    async def test_get_rto_records_empty(self):
        db = _mock_db_execute_scalars([])
        result = await crud.get_rto_records_by_exercise(db, SAMPLE_UUID)
        assert result == []


# ---------------------------------------------------------------------------
# IncidentTask CRUD
# ---------------------------------------------------------------------------


class TestIncidentTaskCRUD:
    @pytest.mark.asyncio
    async def test_create_incident_task(self):
        db = AsyncMock()
        await crud.create_incident_task(
            db,
            {
                "incident_id": SAMPLE_UUID,
                "task_title": "Restart DB",
                "priority": "critical",
                "assigned_team": "DBA",
            },
        )
        assert db.add.called

    @pytest.mark.asyncio
    async def test_get_incident_task_found(self):
        obj = IncidentTask()
        db = _mock_db_execute_scalar(obj)
        assert await crud.get_incident_task(db, SAMPLE_UUID) is obj

    @pytest.mark.asyncio
    async def test_get_incident_task_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.get_incident_task(db, SAMPLE_UUID) is None

    @pytest.mark.asyncio
    async def test_get_incident_tasks_by_incident(self):
        items = [IncidentTask(), IncidentTask()]
        db = _mock_db_execute_scalars(items)
        result = await crud.get_incident_tasks_by_incident(db, SAMPLE_UUID)
        assert result == items

    @pytest.mark.asyncio
    async def test_update_incident_task_found(self):
        obj = IncidentTask()
        obj.status = "pending"
        db = _mock_db_execute_scalar(obj)
        result = await crud.update_incident_task(db, SAMPLE_UUID, {"status": "completed"})
        assert result is obj
        assert obj.status == "completed"

    @pytest.mark.asyncio
    async def test_update_incident_task_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.update_incident_task(db, SAMPLE_UUID, {}) is None

    @pytest.mark.asyncio
    async def test_delete_incident_task_found(self):
        obj = IncidentTask()
        db = _mock_db_execute_scalar(obj)
        assert await crud.delete_incident_task(db, SAMPLE_UUID) is True

    @pytest.mark.asyncio
    async def test_delete_incident_task_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.delete_incident_task(db, SAMPLE_UUID) is False


# ---------------------------------------------------------------------------
# SituationReport CRUD
# ---------------------------------------------------------------------------


class TestSituationReportCRUD:
    @pytest.mark.asyncio
    async def test_create_situation_report(self):
        db = AsyncMock()
        await crud.create_situation_report(
            db,
            {
                "incident_id": SAMPLE_UUID,
                "report_number": 1,
                "summary": "Initial report",
                "audience": "internal",
            },
        )
        assert db.add.called

    @pytest.mark.asyncio
    async def test_get_situation_report_found(self):
        obj = SituationReport()
        db = _mock_db_execute_scalar(obj)
        assert await crud.get_situation_report(db, SAMPLE_UUID) is obj

    @pytest.mark.asyncio
    async def test_get_situation_report_not_found(self):
        db = _mock_db_execute_scalar(None)
        assert await crud.get_situation_report(db, SAMPLE_UUID) is None

    @pytest.mark.asyncio
    async def test_get_situation_reports_by_incident(self):
        items = [SituationReport()]
        db = _mock_db_execute_scalars(items)
        result = await crud.get_situation_reports_by_incident(db, SAMPLE_UUID)
        assert result == items

    @pytest.mark.asyncio
    async def test_get_situation_reports_empty(self):
        db = _mock_db_execute_scalars([])
        result = await crud.get_situation_reports_by_incident(db, SAMPLE_UUID)
        assert result == []
