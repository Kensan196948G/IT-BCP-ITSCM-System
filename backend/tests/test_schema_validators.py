"""Tests for Pydantic schema validators — error paths that require direct invocation.

These tests cover ValueError branches inside @field_validator methods that are
unreachable via normal model instantiation because Field-level constraints (e.g.
pattern=) reject invalid values before the Python validator function runs.
"""

import pytest
from pydantic import ValidationError

from apps.schemas import (
    ActiveIncidentCreate,
    BCPExerciseCreate,
    BCPScenarioCreate,
    EmergencyContactCreate,
    RecoveryProcedureCreate,
    VendorContactCreate,
)


def test_recovery_procedure_id_blank_raises() -> None:
    """RecoveryProcedureCreate raises ValidationError when procedure_id is blank."""
    with pytest.raises(ValidationError, match="procedure_id must not be blank"):
        RecoveryProcedureCreate(
            procedure_id="   ",
            system_name="Core Banking",
            scenario_type="dc_failure",
            title="Test Procedure",
            priority_order=1,
            procedure_steps=["Step 1"],
        )


def test_emergency_contact_name_blank_raises() -> None:
    """EmergencyContactCreate raises ValidationError when name is blank."""
    with pytest.raises(ValidationError, match="name must not be blank"):
        EmergencyContactCreate(
            name="   ",
            role="IT部門長",
            escalation_level=1,
            escalation_group="P1_FULL_BCP",
        )


def test_vendor_contact_vendor_name_blank_raises() -> None:
    """VendorContactCreate raises ValidationError when vendor_name is blank."""
    with pytest.raises(ValidationError, match="vendor_name must not be blank"):
        VendorContactCreate(
            vendor_name="   ",
            service_name="DB Support",
        )


def test_bcp_exercise_invalid_type_validator_raises() -> None:
    """BCPExerciseCreate.validate_exercise_type raises ValueError for invalid exercise type.

    This calls the classmethod directly to reach the else-branch in the validator,
    bypassing the Field-level pattern constraint that would otherwise reject the value first.
    """
    with pytest.raises(ValueError, match="exercise_type must be one of"):
        BCPExerciseCreate.validate_exercise_type("invalid_type")


def test_active_incident_invalid_severity_validator_raises() -> None:
    """ActiveIncidentCreate.validate_severity raises ValueError for invalid severity.

    This calls the classmethod directly to reach the else-branch in the validator,
    bypassing the Field-level pattern constraint that would otherwise reject the value first.
    """
    with pytest.raises(ValueError, match="severity must be one of"):
        ActiveIncidentCreate.validate_severity("p99")


def test_bcp_scenario_id_blank_raises() -> None:
    """BCPScenarioCreate raises ValidationError when scenario_id is blank."""
    with pytest.raises(ValidationError, match="scenario_id must not be blank"):
        BCPScenarioCreate(
            scenario_id="   ",
            title="Test Scenario",
            scenario_type="earthquake",
            description="A test scenario",
            initial_inject="Initial situation",
            injects=["Inject 1"],
        )
