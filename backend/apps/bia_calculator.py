"""BIA (Business Impact Analysis) calculation logic."""

from __future__ import annotations

from typing import Any

# Impact level numeric mapping
IMPACT_MAP: dict[str | None, int] = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
    None: 0,
}


def calculate_risk_score(
    financial_impact_per_day: float | None = None,
    regulatory_risks: list[str] | None = None,
    reputation_impact: str | None = None,
    operational_impact: str | None = None,
) -> int:
    """Calculate a composite risk score (1-100).

    Weighting:
      - Financial impact  : 30%
      - Regulatory risk   : 25%
      - Reputation impact : 25%
      - Operational impact: 20%
    """
    # Financial score (0-100): based on daily impact in 万円
    if financial_impact_per_day is not None and financial_impact_per_day > 0:
        # Scale: 0->0, 100万->25, 500万->50, 1000万->75, 5000万+->100
        fin = min(financial_impact_per_day / 5000.0, 1.0) * 100
    else:
        fin = 0.0

    # Regulatory score (0-100): based on number & existence of risks
    if regulatory_risks and len(regulatory_risks) > 0:
        reg = min(len(regulatory_risks) / 5.0, 1.0) * 100
    else:
        reg = 0.0

    # Reputation score (0-100)
    rep = IMPACT_MAP.get(reputation_impact, 0) * 25.0

    # Operational score (0-100)
    ops = IMPACT_MAP.get(operational_impact, 0) * 25.0

    raw = fin * 0.30 + reg * 0.25 + rep * 0.25 + ops * 0.20
    return max(1, min(100, round(raw)))


def calculate_recommended_rto(
    risk_score: int,
    mtpd_hours: float | None = None,
) -> float:
    """Derive a recommended RTO from risk score and MTPD.

    Higher risk => lower RTO (faster recovery needed).
    If MTPD is provided, RTO is a fraction of it.
    Otherwise, use a default scale.
    """
    if mtpd_hours is not None and mtpd_hours > 0:
        # fraction decreases as risk increases
        if risk_score >= 76:
            fraction = 0.10
        elif risk_score >= 51:
            fraction = 0.25
        elif risk_score >= 26:
            fraction = 0.50
        else:
            fraction = 0.75
        return round(mtpd_hours * fraction, 1)

    # Default scale without MTPD
    if risk_score >= 76:
        return 2.0
    elif risk_score >= 51:
        return 4.0
    elif risk_score >= 26:
        return 8.0
    else:
        return 24.0


def get_bia_summary(assessments: list[Any]) -> dict[str, Any]:
    """Aggregate BIA assessments into a summary.

    Parameters
    ----------
    assessments : list
        List of BIAAssessment ORM objects (or dicts with same keys).

    Returns
    -------
    dict matching BIASummaryResponse schema.
    """
    total = len(assessments)
    if total == 0:
        return {
            "total_assessments": 0,
            "average_risk_score": None,
            "max_risk_score": None,
            "highest_risk_system": None,
            "impact_distribution": {},
            "average_financial_impact_per_day": None,
            "status_distribution": {},
        }

    risk_scores: list[int] = []
    financial_impacts: list[float] = []
    impact_dist: dict[str, int] = {
        "none": 0,
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    }
    status_dist: dict[str, int] = {}
    max_score = 0
    highest_system: str | None = None

    for a in assessments:
        score = _attr(a, "risk_score")
        if score is not None:
            risk_scores.append(score)
            if score > max_score:
                max_score = score
                highest_system = _attr(a, "system_name")

        fi = _attr(a, "financial_impact_per_day")
        if fi is not None:
            financial_impacts.append(fi)

        rep = _attr(a, "reputation_impact") or "none"
        if rep in impact_dist:
            impact_dist[rep] += 1

        st = _attr(a, "status") or "draft"
        status_dist[st] = status_dist.get(st, 0) + 1

    avg_risk = round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else None
    avg_fin = round(sum(financial_impacts) / len(financial_impacts), 1) if financial_impacts else None

    return {
        "total_assessments": total,
        "average_risk_score": avg_risk,
        "max_risk_score": max_score if max_score > 0 else None,
        "highest_risk_system": highest_system,
        "impact_distribution": impact_dist,
        "average_financial_impact_per_day": avg_fin,
        "status_distribution": status_dist,
    }


def get_risk_matrix(assessments: list[Any]) -> dict[str, Any]:
    """Build a 5x5 risk matrix from assessments.

    X-axis: likelihood (derived from operational_impact 1-5)
    Y-axis: impact (derived from reputation_impact 1-5)

    Returns dict with ``entries`` and ``matrix`` keys.
    """
    entries: list[dict[str, Any]] = []
    # 5x5 matrix of counts  [impact][likelihood]
    matrix = [[0 for _ in range(5)] for _ in range(5)]

    for a in assessments:
        score = _attr(a, "risk_score")
        if score is None:
            continue

        rep = _attr(a, "reputation_impact")
        ops = _attr(a, "operational_impact")

        impact_level = IMPACT_MAP.get(rep, 0)
        likelihood_level = IMPACT_MAP.get(ops, 0)

        # Clamp to 1-5 for matrix (0 -> 1)
        il = max(1, min(5, impact_level + 1))
        ll = max(1, min(5, likelihood_level + 1))

        entries.append(
            {
                "impact_level": il,
                "likelihood_level": ll,
                "system_name": _attr(a, "system_name") or "",
                "risk_score": score,
            }
        )
        matrix[il - 1][ll - 1] += 1

    return {"entries": entries, "matrix": matrix}


def _attr(obj: Any, name: str) -> Any:
    """Get attribute from object or dict."""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)
