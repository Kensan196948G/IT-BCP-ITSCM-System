"""Add bcp_scenarios and exercise_rto_records tables.

Revision ID: 004
Revises: 003
Create Date: 2026-03-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- bcp_scenarios --
    op.create_table(
        "bcp_scenarios",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("scenario_id", sa.String(20), unique=True, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("scenario_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("initial_inject", sa.Text, nullable=False),
        sa.Column("injects", JSON, nullable=False),
        sa.Column("affected_systems", JSON, nullable=True),
        sa.Column("expected_duration_hours", sa.Float, nullable=True),
        sa.Column("difficulty", sa.String(20), server_default="medium"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
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

    # -- exercise_rto_records --
    op.create_table(
        "exercise_rto_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "exercise_id",
            UUID(as_uuid=True),
            sa.ForeignKey("bcp_exercises.id"),
            nullable=False,
        ),
        sa.Column("system_name", sa.String(100), nullable=False),
        sa.Column("rto_target_hours", sa.Float, nullable=False),
        sa.Column("rto_actual_hours", sa.Float, nullable=True),
        sa.Column("achieved", sa.Boolean, nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("recorded_by", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )

    # -- Add scenario_ref_id FK to bcp_exercises --
    op.add_column(
        "bcp_exercises",
        sa.Column(
            "scenario_ref_id",
            UUID(as_uuid=True),
            sa.ForeignKey("bcp_scenarios.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("bcp_exercises", "scenario_ref_id")
    op.drop_table("exercise_rto_records")
    op.drop_table("bcp_scenarios")
