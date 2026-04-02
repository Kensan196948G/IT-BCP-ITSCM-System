#!/usr/bin/env python3
"""Seed data script for IT-BCP-ITSCM-System.

Usage:
    python3 scripts/seed_data.py             # dry-run (prints data, no DB required)
    python3 scripts/seed_data.py --execute   # insert into database
"""

import argparse
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

SYSTEMS: list[dict[str, Any]] = [
    {
        "id": uuid.uuid4(),
        "system_name": "Active Directory",
        "system_type": "onprem",
        "criticality": "tier1",
        "rto_target_hours": 2.0,
        "rpo_target_hours": 0.5,
        "mtpd_hours": 8.0,
        "fallback_system": None,
        "fallback_procedure": "Restore from backup DC",
        "primary_owner": "Infrastructure Team",
        "vendor_name": "Microsoft",
        "is_active": True,
    },
    {
        "id": uuid.uuid4(),
        "system_name": "Entra ID",
        "system_type": "cloud",
        "criticality": "tier1",
        "rto_target_hours": 1.0,
        "rpo_target_hours": 0.25,
        "mtpd_hours": 4.0,
        "fallback_system": "Active Directory",
        "fallback_procedure": "Failover to on-premises AD for authentication",
        "primary_owner": "Identity Team",
        "vendor_name": "Microsoft",
        "is_active": True,
    },
    {
        "id": uuid.uuid4(),
        "system_name": "Exchange Online",
        "system_type": "cloud",
        "criticality": "tier2",
        "rto_target_hours": 4.0,
        "rpo_target_hours": 1.0,
        "mtpd_hours": 24.0,
        "fallback_system": None,
        "fallback_procedure": "Use alternative communication (Teams/Phone)",
        "primary_owner": "Messaging Team",
        "vendor_name": "Microsoft",
        "is_active": True,
    },
    {
        "id": uuid.uuid4(),
        "system_name": "File Server",
        "system_type": "onprem",
        "criticality": "tier2",
        "rto_target_hours": 4.0,
        "rpo_target_hours": 1.0,
        "mtpd_hours": 24.0,
        "fallback_system": "SharePoint Online",
        "fallback_procedure": "Redirect users to SharePoint Online",
        "primary_owner": "Infrastructure Team",
        "vendor_name": None,
        "is_active": True,
    },
    {
        "id": uuid.uuid4(),
        "system_name": "DeskNet's Neo",
        "system_type": "onprem",
        "criticality": "tier2",
        "rto_target_hours": 8.0,
        "rpo_target_hours": 2.0,
        "mtpd_hours": 48.0,
        "fallback_system": None,
        "fallback_procedure": "Use email and shared drives as temporary workflow",
        "primary_owner": "Application Team",
        "vendor_name": "Neo Japan",
        "is_active": True,
    },
    {
        "id": uuid.uuid4(),
        "system_name": "AppSuite",
        "system_type": "hybrid",
        "criticality": "tier2",
        "rto_target_hours": 8.0,
        "rpo_target_hours": 2.0,
        "mtpd_hours": 48.0,
        "fallback_system": None,
        "fallback_procedure": "Manual process with paper forms",
        "primary_owner": "Application Team",
        "vendor_name": "AppSuite Inc.",
        "is_active": True,
    },
    {
        "id": uuid.uuid4(),
        "system_name": "ITSM-System",
        "system_type": "cloud",
        "criticality": "tier3",
        "rto_target_hours": 12.0,
        "rpo_target_hours": 4.0,
        "mtpd_hours": 72.0,
        "fallback_system": None,
        "fallback_procedure": "Use email-based ticket tracking",
        "primary_owner": "Service Management Team",
        "vendor_name": None,
        "is_active": True,
    },
    {
        "id": uuid.uuid4(),
        "system_name": "SIEM Platform",
        "system_type": "hybrid",
        "criticality": "tier1",
        "rto_target_hours": 2.0,
        "rpo_target_hours": 0.5,
        "mtpd_hours": 8.0,
        "fallback_system": None,
        "fallback_procedure": "Enable local log collection and manual review",
        "primary_owner": "Security Operations Team",
        "vendor_name": None,
        "is_active": True,
    },
]

EXERCISES: list[dict[str, Any]] = [
    {
        "id": uuid.uuid4(),
        "exercise_id": "EX-2026-001",
        "title": "Annual BCP Tabletop Exercise - DC Failure Scenario",
        "exercise_type": "tabletop",
        "scenario_description": (
            "Simulated data center power failure affecting all on-premises systems. "
            "Teams must execute failover procedures and restore services within RTO."
        ),
        "scheduled_date": datetime(2026, 6, 15, 9, 0, 0, tzinfo=timezone.utc),
        "actual_date": None,
        "duration_hours": 4.0,
        "facilitator": "IT-BCP Manager",
        "status": "planned",
        "overall_result": None,
        "findings": None,
        "improvements": None,
        "lessons_learned": None,
    },
    {
        "id": uuid.uuid4(),
        "exercise_id": "EX-2026-002",
        "title": "Ransomware Response Functional Exercise",
        "exercise_type": "functional",
        "scenario_description": (
            "Simulated ransomware attack affecting Active Directory and file servers. "
            "Teams must isolate, contain, and recover affected systems."
        ),
        "scheduled_date": datetime(2026, 9, 20, 9, 0, 0, tzinfo=timezone.utc),
        "actual_date": None,
        "duration_hours": 8.0,
        "facilitator": "Security Operations Lead",
        "status": "planned",
        "overall_result": None,
        "findings": None,
        "improvements": None,
        "lessons_learned": None,
    },
]


def print_seed_data() -> None:
    """Print seed data summary (dry-run mode)."""
    print("=" * 60)
    print("IT-BCP-ITSCM-System Seed Data (dry-run)")
    print("=" * 60)

    print(f"\n--- IT Systems ({len(SYSTEMS)} records) ---")
    for s in SYSTEMS:
        print(
            f"  {s['system_name']:25s} | type={s['system_type']:6s} "
            f"| crit={s['criticality']:5s} "
            f"| RTO={s['rto_target_hours']}h RPO={s['rpo_target_hours']}h"
        )

    print(f"\n--- BCP Exercises ({len(EXERCISES)} records) ---")
    for e in EXERCISES:
        print(f"  {e['exercise_id']:15s} | {e['title'][:50]:50s} " f"| type={e['exercise_type']}")

    print("\n" + "=" * 60)
    print("Dry-run complete. Use --execute to insert into database.")
    print("=" * 60)


def execute_seed() -> None:
    """Insert seed data into the database using sync SQLAlchemy."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
    except ImportError:
        print("ERROR: sqlalchemy is not installed.")
        sys.exit(1)

    from config import settings

    # Convert async URL to sync
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)

    engine = create_engine(url)

    # Import models so metadata is populated
    from apps.models import ActiveIncident, BCPExercise, ITSystemBCP  # noqa: F401

    with Session(engine) as session:
        # Insert systems
        for data in SYSTEMS:
            system_obj = ITSystemBCP(**data)
            session.merge(system_obj)
        print(f"Inserted/updated {len(SYSTEMS)} IT systems.")

        # Insert exercises
        for data in EXERCISES:
            exercise_obj = BCPExercise(**data)
            session.merge(exercise_obj)
        print(f"Inserted/updated {len(EXERCISES)} BCP exercises.")

        session.commit()
        print("Seed data committed successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed data for IT-BCP-ITSCM-System")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually insert data into the database (default is dry-run)",
    )
    args = parser.parse_args()

    if args.execute:
        execute_seed()
    else:
        print_seed_data()


if __name__ == "__main__":
    main()
