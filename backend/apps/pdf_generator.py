"""PDF report generation utilities for BCP/ITSCM reports.

Uses reportlab to render report dicts produced by ReportGenerator into
downloadable PDF documents.
"""

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Shared styles
# ---------------------------------------------------------------------------

_STYLES = getSampleStyleSheet()

_TITLE_STYLE = ParagraphStyle(
    "ReportTitle",
    parent=_STYLES["Title"],
    fontSize=20,
    spaceAfter=6,
    textColor=colors.HexColor("#1a3a5c"),
)

_HEADING2_STYLE = ParagraphStyle(
    "ReportH2",
    parent=_STYLES["Heading2"],
    fontSize=13,
    spaceBefore=12,
    spaceAfter=4,
    textColor=colors.HexColor("#1a3a5c"),
)

_BODY_STYLE = ParagraphStyle(
    "ReportBody",
    parent=_STYLES["Normal"],
    fontSize=10,
    spaceAfter=4,
)

_TABLE_HEADER_STYLE = TableStyle(
    [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f8"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
)


def _make_doc(buf: io.BytesIO, title: str) -> SimpleDocTemplate:
    """Create a SimpleDocTemplate with standard margins."""
    return SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=title,
        author="IT-BCP-ITSCM System",
    )


def _header_block(title: str, report_id: str, generated_at: str) -> list:
    """Return common header flowables."""
    return [
        Paragraph(title, _TITLE_STYLE),
        Paragraph(f"Report ID: {report_id}", _BODY_STYLE),
        Paragraph(f"Generated: {generated_at}", _BODY_STYLE),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")),
        Spacer(1, 8),
    ]


# ---------------------------------------------------------------------------
# RPT-001: BCP Readiness Report
# ---------------------------------------------------------------------------


def generate_readiness_pdf(data: dict[str, Any]) -> bytes:
    """Generate RPT-001 BCP Readiness Report as PDF bytes."""
    buf = io.BytesIO()
    doc = _make_doc(buf, "BCP Readiness Report (RPT-001)")
    story: list = []

    story += _header_block(
        "BCP Readiness Report (RPT-001)",
        data.get("report_id", "-"),
        data.get("generated_at", "-"),
    )

    # Summary metrics
    story.append(Paragraph("Summary", _HEADING2_STYLE))
    summary_rows = [
        ["Metric", "Value"],
        ["Overall Score", f"{data.get('overall_score', 0):.1f} / 100"],
        ["Total Systems", str(data.get("total_systems", 0))],
        ["Tested Systems", str(data.get("tested_systems", 0))],
        ["RTO Met Systems", str(data.get("rto_met_systems", 0))],
    ]
    story.append(Table(summary_rows, colWidths=[100 * mm, 70 * mm], style=_TABLE_HEADER_STYLE))
    story.append(Spacer(1, 10))

    # System readiness table
    story.append(Paragraph("System Readiness Detail", _HEADING2_STYLE))
    sys_rows = [["System Name", "RTO Target (h)", "Last Test RTO (h)", "Tested", "RTO Met", "Score"]]
    for s in data.get("system_readiness", []):
        sys_rows.append(
            [
                s.get("system_name", "-"),
                str(s.get("rto_target_hours", "-")),
                str(s.get("last_test_rto_hours") or "-"),
                "Yes" if s.get("tested") else "No",
                "Yes" if s.get("rto_achieved") else "No",
                f"{s.get('readiness_score', 0):.1f}",
            ]
        )
    story.append(
        Table(
            sys_rows,
            colWidths=[55 * mm, 28 * mm, 32 * mm, 20 * mm, 22 * mm, 18 * mm],
            style=_TABLE_HEADER_STYLE,
        )
    )
    story.append(Spacer(1, 10))

    # Recommendations
    recs = data.get("recommendations", [])
    if recs:
        story.append(Paragraph("Recommendations", _HEADING2_STYLE))
        for rec in recs:
            story.append(Paragraph(f"• {rec}", _BODY_STYLE))

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# RPT-002: RTO Compliance Report
# ---------------------------------------------------------------------------


def generate_rto_compliance_pdf(data: dict[str, Any]) -> bytes:
    """Generate RPT-002 RTO/RPO Compliance Report as PDF bytes."""
    buf = io.BytesIO()
    doc = _make_doc(buf, "RTO Compliance Report (RPT-002)")
    story: list = []

    story += _header_block(
        "RTO/RPO Compliance Report (RPT-002)",
        data.get("report_id", "-"),
        data.get("generated_at", "-"),
    )

    # Summary
    story.append(Paragraph("Summary", _HEADING2_STYLE))
    summary_rows = [
        ["Metric", "Value"],
        ["Compliance Rate", f"{data.get('compliance_rate', 0):.1f}%"],
        ["Total Systems", str(data.get("total_systems", 0))],
        ["Compliant Systems", str(data.get("compliant_systems", 0))],
    ]
    story.append(Table(summary_rows, colWidths=[100 * mm, 70 * mm], style=_TABLE_HEADER_STYLE))
    story.append(Spacer(1, 10))

    # Per-system compliance
    story.append(Paragraph("System Compliance Detail", _HEADING2_STYLE))
    sys_rows = [["System Name", "RTO Target (h)", "Actual RTO (h)", "Deviation (h)", "Compliant", "Trend"]]
    for s in data.get("system_compliance", []):
        sys_rows.append(
            [
                s.get("system_name", "-"),
                str(s.get("rto_target_hours", "-")),
                str(s.get("rto_actual_hours") or "-"),
                str(s.get("deviation_hours") or "-"),
                "Yes" if s.get("compliant") else "No",
                str(s.get("trend", "-")),
            ]
        )
    story.append(
        Table(
            sys_rows,
            colWidths=[52 * mm, 28 * mm, 28 * mm, 28 * mm, 22 * mm, 17 * mm],
            style=_TABLE_HEADER_STYLE,
        )
    )

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# RPT-003: Exercise Trend Report
# ---------------------------------------------------------------------------


def generate_exercise_trends_pdf(data: dict[str, Any]) -> bytes:
    """Generate RPT-003 Exercise Trend Report as PDF bytes."""
    buf = io.BytesIO()
    doc = _make_doc(buf, "Exercise Trend Report (RPT-003)")
    story: list = []

    story += _header_block(
        "Exercise Trend Report (RPT-003)",
        data.get("report_id", "-"),
        data.get("generated_at", "-"),
    )

    # Summary
    story.append(Paragraph("Summary", _HEADING2_STYLE))
    summary_rows = [
        ["Metric", "Value"],
        ["Total Exercises", str(data.get("total_exercises", 0))],
        ["Total Improvements", str(data.get("total_improvements", 0))],
        ["Completed Improvements", str(data.get("completed_improvements", 0))],
    ]
    story.append(Table(summary_rows, colWidths=[100 * mm, 70 * mm], style=_TABLE_HEADER_STYLE))
    story.append(Spacer(1, 10))

    # Yearly trends
    story.append(Paragraph("Yearly Trends", _HEADING2_STYLE))
    trend_rows = [["Year", "Exercises", "Completed", "Pass Count", "Achievement Rate"]]
    for t in data.get("yearly_trends", []):
        trend_rows.append(
            [
                str(t.get("year", "-")),
                str(t.get("exercise_count", 0)),
                str(t.get("completed", 0)),
                str(t.get("pass_count", 0)),
                f"{t.get('achievement_rate', 0):.1f}%",
            ]
        )
    story.append(
        Table(
            trend_rows,
            colWidths=[25 * mm, 30 * mm, 30 * mm, 30 * mm, 40 * mm],
            style=_TABLE_HEADER_STYLE,
        )
    )

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# RPT-004: ISO20000 Compliance Report
# ---------------------------------------------------------------------------


def generate_iso20000_pdf(data: dict[str, Any]) -> bytes:
    """Generate RPT-004 ISO20000 ITSCM Compliance Report as PDF bytes."""
    buf = io.BytesIO()
    doc = _make_doc(buf, "ISO20000 ITSCM Compliance Report (RPT-004)")
    story: list = []

    story += _header_block(
        "ISO20000 ITSCM Compliance Report (RPT-004)",
        data.get("report_id", "-"),
        data.get("generated_at", "-"),
    )

    # Overall compliance score
    story.append(Paragraph("Compliance Overview", _HEADING2_STYLE))
    summary_rows = [
        ["Metric", "Value"],
        ["Overall Compliance Score", f"{data.get('overall_compliance_score', 0):.1f}%"],
        ["Assessment Date", data.get("generated_at", "-")],
    ]
    story.append(Table(summary_rows, colWidths=[100 * mm, 70 * mm], style=_TABLE_HEADER_STYLE))
    story.append(Spacer(1, 10))

    # Control areas
    control_areas = data.get("control_areas", {})
    if control_areas:
        story.append(Paragraph("Control Areas", _HEADING2_STYLE))
        ca_rows = [["Control Area", "Score", "Status"]]
        for area, detail in control_areas.items():
            if isinstance(detail, dict):
                ca_rows.append(
                    [
                        area,
                        f"{detail.get('score', 0):.1f}%",
                        detail.get("status", "-"),
                    ]
                )
        story.append(
            Table(
                ca_rows,
                colWidths=[100 * mm, 40 * mm, 35 * mm],
                style=_TABLE_HEADER_STYLE,
            )
        )
        story.append(Spacer(1, 10))

    # Findings
    findings = data.get("findings", [])
    if findings:
        story.append(Paragraph("Findings", _HEADING2_STYLE))
        for f in findings:
            story.append(Paragraph(f"• {f}", _BODY_STYLE))

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_REPORT_GENERATORS = {
    "readiness": generate_readiness_pdf,
    "rto-compliance": generate_rto_compliance_pdf,
    "exercise-trends": generate_exercise_trends_pdf,
    "iso20000": generate_iso20000_pdf,
}

_REPORT_FILENAMES = {
    "readiness": "bcp_readiness_report.pdf",
    "rto-compliance": "rto_compliance_report.pdf",
    "exercise-trends": "exercise_trend_report.pdf",
    "iso20000": "iso20000_compliance_report.pdf",
}


def generate_pdf(report_type: str, data: dict[str, Any]) -> tuple[bytes, str]:
    """Generate PDF for the given report_type.

    Returns (pdf_bytes, filename).
    Raises ValueError for unknown report types.
    """
    generator = _REPORT_GENERATORS.get(report_type)
    if generator is None:
        valid = ", ".join(_REPORT_GENERATORS.keys())
        raise ValueError(f"Unknown report type '{report_type}'. Valid types: {valid}")
    filename = _REPORT_FILENAMES[report_type]
    return generator(data), filename
