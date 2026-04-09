"""Unit tests for apps/pdf_generator.py.

Verifies that each PDF generator function returns valid PDF bytes
and handles edge cases (empty data, missing fields) gracefully.
"""

from typing import Any

import pytest

from apps.pdf_generator import (
    generate_exercise_trends_pdf,
    generate_iso20000_pdf,
    generate_pdf,
    generate_readiness_pdf,
    generate_rto_compliance_pdf,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PDF_MAGIC = b"%PDF"


def _is_valid_pdf(data: bytes) -> bool:
    """Return True if data starts with the PDF magic bytes."""
    return data[:4] == _PDF_MAGIC


# ---------------------------------------------------------------------------
# generate_readiness_pdf (RPT-001)
# ---------------------------------------------------------------------------


class TestGenerateReadinessPdf:
    def test_returns_bytes(self) -> None:
        result = generate_readiness_pdf({})
        assert isinstance(result, bytes)

    def test_valid_pdf_magic(self) -> None:
        result = generate_readiness_pdf({})
        assert _is_valid_pdf(result)

    def test_non_empty_output(self) -> None:
        result = generate_readiness_pdf({})
        assert len(result) > 100

    def test_with_full_data(self) -> None:
        data = {
            "report_id": "RPT-001-001",
            "generated_at": "2026-04-09T09:00:00Z",
            "overall_score": 85.5,
            "total_systems": 10,
            "tested_systems": 8,
            "rto_met_systems": 7,
            "system_readiness": [
                {
                    "system_name": "Core Banking",
                    "rto_target_hours": 4,
                    "last_test_rto_hours": 3.5,
                    "tested": True,
                    "rto_achieved": True,
                    "readiness_score": 90.0,
                },
                {
                    "system_name": "Email System",
                    "rto_target_hours": 8,
                    "last_test_rto_hours": None,
                    "tested": False,
                    "rto_achieved": False,
                    "readiness_score": 50.0,
                },
            ],
            "recommendations": [
                "Schedule test for Email System",
                "Review RTO targets for legacy systems",
            ],
        }
        result = generate_readiness_pdf(data)
        assert _is_valid_pdf(result)
        assert len(result) > 500

    def test_missing_fields_do_not_raise(self) -> None:
        # Partial data — defaults via dict.get() should prevent KeyError
        data = {"overall_score": 70.0, "total_systems": 5}
        result = generate_readiness_pdf(data)
        assert _is_valid_pdf(result)

    def test_empty_system_readiness_list(self) -> None:
        data: dict[str, Any] = {"system_readiness": [], "recommendations": []}
        result = generate_readiness_pdf(data)
        assert _is_valid_pdf(result)

    def test_with_recommendations(self) -> None:
        data = {"recommendations": ["Action A", "Action B", "Action C"]}
        result = generate_readiness_pdf(data)
        assert _is_valid_pdf(result)


# ---------------------------------------------------------------------------
# generate_rto_compliance_pdf (RPT-002)
# ---------------------------------------------------------------------------


class TestGenerateRtoCompliancePdf:
    def test_returns_bytes(self) -> None:
        result = generate_rto_compliance_pdf({})
        assert isinstance(result, bytes)

    def test_valid_pdf_magic(self) -> None:
        result = generate_rto_compliance_pdf({})
        assert _is_valid_pdf(result)

    def test_with_full_data(self) -> None:
        data = {
            "report_id": "RPT-002-001",
            "generated_at": "2026-04-09T09:00:00Z",
            "compliance_rate": 75.0,
            "total_systems": 4,
            "compliant_systems": 3,
            "system_compliance": [
                {
                    "system_name": "System A",
                    "rto_target_hours": 4,
                    "rto_actual_hours": 3.2,
                    "deviation_hours": -0.8,
                    "compliant": True,
                    "trend": "improving",
                },
                {
                    "system_name": "System B",
                    "rto_target_hours": 2,
                    "rto_actual_hours": 2.5,
                    "deviation_hours": 0.5,
                    "compliant": False,
                    "trend": "degrading",
                },
            ],
        }
        result = generate_rto_compliance_pdf(data)
        assert _is_valid_pdf(result)
        assert len(result) > 500

    def test_empty_system_compliance(self) -> None:
        data: dict[str, Any] = {"system_compliance": []}
        result = generate_rto_compliance_pdf(data)
        assert _is_valid_pdf(result)

    def test_none_actual_rto_handled(self) -> None:
        # rto_actual_hours may be None when untested
        data = {
            "system_compliance": [
                {
                    "system_name": "Untested System",
                    "rto_target_hours": 4,
                    "rto_actual_hours": None,
                    "deviation_hours": None,
                    "compliant": False,
                    "trend": "unknown",
                }
            ]
        }
        result = generate_rto_compliance_pdf(data)
        assert _is_valid_pdf(result)


# ---------------------------------------------------------------------------
# generate_exercise_trends_pdf (RPT-003)
# ---------------------------------------------------------------------------


class TestGenerateExerciseTrendsPdf:
    def test_returns_bytes(self) -> None:
        result = generate_exercise_trends_pdf({})
        assert isinstance(result, bytes)

    def test_valid_pdf_magic(self) -> None:
        result = generate_exercise_trends_pdf({})
        assert _is_valid_pdf(result)

    def test_with_full_data(self) -> None:
        data = {
            "report_id": "RPT-003-001",
            "generated_at": "2026-04-09T09:00:00Z",
            "total_exercises": 12,
            "total_improvements": 25,
            "completed_improvements": 20,
            "yearly_trends": [
                {
                    "year": 2024,
                    "exercise_count": 5,
                    "completed": 5,
                    "pass_count": 4,
                    "achievement_rate": 80.0,
                },
                {
                    "year": 2025,
                    "exercise_count": 7,
                    "completed": 6,
                    "pass_count": 6,
                    "achievement_rate": 85.7,
                },
            ],
        }
        result = generate_exercise_trends_pdf(data)
        assert _is_valid_pdf(result)
        assert len(result) > 500

    def test_empty_yearly_trends(self) -> None:
        data: dict[str, Any] = {"yearly_trends": []}
        result = generate_exercise_trends_pdf(data)
        assert _is_valid_pdf(result)


# ---------------------------------------------------------------------------
# generate_iso20000_pdf (RPT-004)
# ---------------------------------------------------------------------------


class TestGenerateIso20000Pdf:
    def test_returns_bytes(self) -> None:
        result = generate_iso20000_pdf({})
        assert isinstance(result, bytes)

    def test_valid_pdf_magic(self) -> None:
        result = generate_iso20000_pdf({})
        assert _is_valid_pdf(result)

    def test_with_full_data(self) -> None:
        data = {
            "report_id": "RPT-004-001",
            "generated_at": "2026-04-09T09:00:00Z",
            "overall_compliance_score": 88.0,
            "control_areas": {
                "BCP Documentation": {"score": 90.0, "status": "compliant"},
                "RTO Management": {"score": 85.0, "status": "compliant"},
                "Exercise Program": {"score": 80.0, "status": "minor_gap"},
            },
            "findings": [
                "Update BCP documentation annually",
                "Increase exercise frequency for Tier-1 systems",
            ],
        }
        result = generate_iso20000_pdf(data)
        assert _is_valid_pdf(result)
        assert len(result) > 500

    def test_empty_control_areas(self) -> None:
        data: dict[str, Any] = {"control_areas": {}, "findings": []}
        result = generate_iso20000_pdf(data)
        assert _is_valid_pdf(result)

    def test_non_dict_control_area_value_skipped(self) -> None:
        # Control area values that are not dicts should be skipped without error
        data = {
            "control_areas": {
                "Area A": {"score": 80.0, "status": "ok"},
                "Area B": "not-a-dict",  # edge case
            }
        }
        result = generate_iso20000_pdf(data)
        assert _is_valid_pdf(result)

    def test_with_findings(self) -> None:
        data = {"findings": ["Finding 1", "Finding 2", "Finding 3"]}
        result = generate_iso20000_pdf(data)
        assert _is_valid_pdf(result)


# ---------------------------------------------------------------------------
# generate_pdf dispatcher
# ---------------------------------------------------------------------------


class TestGeneratePdfDispatcher:
    @pytest.mark.parametrize(
        "report_type, expected_filename",
        [
            ("readiness", "bcp_readiness_report.pdf"),
            ("rto-compliance", "rto_compliance_report.pdf"),
            ("exercise-trends", "exercise_trend_report.pdf"),
            ("iso20000", "iso20000_compliance_report.pdf"),
        ],
    )
    def test_valid_report_types(self, report_type: str, expected_filename: str) -> None:
        pdf_bytes, filename = generate_pdf(report_type, {})
        assert _is_valid_pdf(pdf_bytes)
        assert filename == expected_filename

    def test_unknown_report_type_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown report type"):
            generate_pdf("nonexistent-type", {})

    def test_error_message_includes_valid_types(self) -> None:
        try:
            generate_pdf("bad-type", {})
        except ValueError as exc:
            assert "readiness" in str(exc)
            assert "rto-compliance" in str(exc)

    def test_returns_tuple(self) -> None:
        result = generate_pdf("readiness", {})
        assert isinstance(result, tuple)
        assert len(result) == 2
