"""RTO (Recovery Time Objective) tracking and status calculation."""

from datetime import datetime, timezone

STATUS_COLORS: dict[str, str] = {
    "on_track": "#22c55e",
    "at_risk": "#eab308",
    "overdue": "#dc2626",
    "recovered": "#2563eb",
    "not_started": "#94a3b8",
}


class RTOTracker:
    """Calculates RTO status for IT systems during incidents."""

    def __init__(
        self,
        rto_target_hours: float,
        occurred_at: datetime | None = None,
        resolved_at: datetime | None = None,
        status: str = "active",
    ) -> None:
        self.rto_target_hours = rto_target_hours
        self.occurred_at = occurred_at
        self.resolved_at = resolved_at
        self.status = status

    def calculate_status(self, now: datetime | None = None) -> dict:
        """Calculate the current RTO status.

        Returns a dict with: status, color, elapsed_hours, remaining_hours, rto_target, overdue_hours
        """
        if now is None:
            now = datetime.now(timezone.utc)

        rto_target = self.rto_target_hours

        # Not started: no incident time recorded
        if self.occurred_at is None:
            return {
                "status": "not_started",
                "color": STATUS_COLORS["not_started"],
                "elapsed_hours": None,
                "remaining_hours": None,
                "rto_target": rto_target,
                "overdue_hours": None,
            }

        # Recovered: incident resolved
        if self.resolved_at is not None or self.status in ("resolved", "closed"):
            end_time = self.resolved_at if self.resolved_at else now
            elapsed = (end_time - self.occurred_at).total_seconds() / 3600.0
            overdue = max(0.0, elapsed - rto_target) if elapsed > rto_target else None
            return {
                "status": "recovered",
                "color": STATUS_COLORS["recovered"],
                "elapsed_hours": round(elapsed, 2),
                "remaining_hours": None,
                "rto_target": rto_target,
                "overdue_hours": round(overdue, 2) if overdue else None,
            }

        # Active incident
        elapsed = (now - self.occurred_at).total_seconds() / 3600.0
        remaining = rto_target - elapsed

        if elapsed > rto_target:
            # Overdue
            overdue = elapsed - rto_target
            return {
                "status": "overdue",
                "color": STATUS_COLORS["overdue"],
                "elapsed_hours": round(elapsed, 2),
                "remaining_hours": 0.0,
                "rto_target": rto_target,
                "overdue_hours": round(overdue, 2),
            }
        elif remaining <= rto_target * 0.2:
            # At risk: less than 20% of RTO remaining
            return {
                "status": "at_risk",
                "color": STATUS_COLORS["at_risk"],
                "elapsed_hours": round(elapsed, 2),
                "remaining_hours": round(remaining, 2),
                "rto_target": rto_target,
                "overdue_hours": None,
            }
        else:
            # On track
            return {
                "status": "on_track",
                "color": STATUS_COLORS["on_track"],
                "elapsed_hours": round(elapsed, 2),
                "remaining_hours": round(remaining, 2),
                "rto_target": rto_target,
                "overdue_hours": None,
            }

    @staticmethod
    def get_dashboard(systems: list[dict], incidents: list[dict], now: datetime | None = None) -> dict:
        """Build a dashboard overview of all system RTO statuses.

        Args:
            systems: List of system dicts with at least 'system_name' and 'rto_target_hours'.
            incidents: List of active incident dicts with 'affected_systems', 'occurred_at',
                       'resolved_at', 'status'.
            now: Optional current time for calculation.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        rto_statuses: list[dict] = []
        on_track = 0
        at_risk = 0
        overdue = 0

        # Build a mapping: system_name -> incident info
        system_incident_map: dict[str, dict] = {}
        for incident_dict in incidents:
            affected = incident_dict.get("affected_systems") or []
            for sys_name in affected:
                system_incident_map[sys_name] = incident_dict

        for system in systems:
            sys_name = system["system_name"]
            rto_target = system["rto_target_hours"]

            matched_inc: dict | None = system_incident_map.get(sys_name)
            if matched_inc:
                tracker = RTOTracker(
                    rto_target_hours=rto_target,
                    occurred_at=matched_inc.get("occurred_at"),
                    resolved_at=matched_inc.get("resolved_at"),
                    status=matched_inc.get("status", "active"),
                )
            else:
                tracker = RTOTracker(rto_target_hours=rto_target)

            status_info = tracker.calculate_status(now)
            status_info["system_name"] = sys_name

            rto_statuses.append(status_info)

            if status_info["status"] == "on_track":
                on_track += 1
            elif status_info["status"] == "at_risk":
                at_risk += 1
            elif status_info["status"] == "overdue":
                overdue += 1

        total = len(systems)
        active_count = len(incidents)

        # Readiness score: percentage of systems not overdue
        readiness_score = ((total - overdue) / total * 100.0) if total > 0 else 100.0

        return {
            "total_systems": total,
            "active_incidents": active_count,
            "rto_statuses": rto_statuses,
            "readiness_score": round(readiness_score, 1),
            "systems_on_track": on_track,
            "systems_at_risk": at_risk,
            "systems_overdue": overdue,
        }
