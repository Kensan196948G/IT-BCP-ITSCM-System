"""Create initial tables: it_systems_bcp, bcp_exercises, active_incidents.

Revision ID: 001
Revises: None
Create Date: 2026-03-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- it_systems_bcp --
    op.create_table(
        "it_systems_bcp",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("system_name", sa.String(100), unique=True, nullable=False),
        sa.Column("system_type", sa.String(30), nullable=False),
        sa.Column("criticality", sa.String(20), nullable=False),
        sa.Column("rto_target_hours", sa.Float, nullable=False),
        sa.Column("rpo_target_hours", sa.Float, nullable=False),
        sa.Column("mtpd_hours", sa.Float, nullable=True),
        sa.Column("fallback_system", sa.String(100), nullable=True),
        sa.Column("fallback_procedure", sa.Text, nullable=True),
        sa.Column("primary_owner", sa.String(100), nullable=True),
        sa.Column("vendor_name", sa.String(100), nullable=True),
        sa.Column("last_dr_test", sa.Date, nullable=True),
        sa.Column("last_test_rto", sa.Float, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # -- bcp_exercises --
    op.create_table(
        "bcp_exercises",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("exercise_id", sa.String(20), unique=True, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("exercise_type", sa.String(30), nullable=False),
        sa.Column("scenario_description", sa.Text, nullable=True),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_hours", sa.Float, nullable=True),
        sa.Column("facilitator", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), default="planned"),
        sa.Column("overall_result", sa.String(20), nullable=True),
        sa.Column("findings", JSON, nullable=True),
        sa.Column("improvements", JSON, nullable=True),
        sa.Column("lessons_learned", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # -- active_incidents --
    op.create_table(
        "active_incidents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", sa.String(20), unique=True, nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("scenario_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("declared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("incident_commander", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("situation_report", sa.Text, nullable=True),
        sa.Column("affected_systems", JSON, nullable=True),
        sa.Column("affected_users", sa.Integer, nullable=True),
        sa.Column("estimated_impact", sa.Text, nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_rto_hours", sa.Float, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("active_incidents")
    op.drop_table("bcp_exercises")
    op.drop_table("it_systems_bcp")
