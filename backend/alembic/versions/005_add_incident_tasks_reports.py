"""Add incident_tasks and situation_reports tables.

Revision ID: 005
Revises: 004
Create Date: 2026-03-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- incident_tasks --
    op.create_table(
        "incident_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", UUID(as_uuid=True), nullable=False),
        sa.Column("task_title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("assigned_to", sa.String(100), nullable=True),
        sa.Column("assigned_team", sa.String(100), nullable=True),
        sa.Column("priority", sa.String(20), server_default="medium"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("target_system", sa.String(100), nullable=True),
        sa.Column("due_hours", sa.Float, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
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

    # -- situation_reports --
    op.create_table(
        "situation_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", UUID(as_uuid=True), nullable=False),
        sa.Column("report_number", sa.Integer, nullable=False),
        sa.Column(
            "report_time",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("reporter", sa.String(100), nullable=True),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("systems_status", JSON, nullable=True),
        sa.Column("tasks_summary", JSON, nullable=True),
        sa.Column("next_actions", JSON, nullable=True),
        sa.Column("escalation_status", sa.String(50), nullable=True),
        sa.Column("audience", sa.String(50), server_default="internal"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("situation_reports")
    op.drop_table("incident_tasks")
