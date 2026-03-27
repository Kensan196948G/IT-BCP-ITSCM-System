"""Add bia_assessments table.

Revision ID: 003
Revises: 002
Create Date: 2026-03-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bia_assessments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("assessment_id", sa.String(20), unique=True, nullable=False),
        sa.Column("system_name", sa.String(100), nullable=False),
        sa.Column("assessment_date", sa.Date, nullable=False),
        sa.Column("assessor", sa.String(100), nullable=True),
        sa.Column("business_processes", JSON, nullable=False),
        sa.Column("financial_impact_per_hour", sa.Float, nullable=True),
        sa.Column("financial_impact_per_day", sa.Float, nullable=True),
        sa.Column("max_tolerable_downtime_hours", sa.Float, nullable=True),
        sa.Column("regulatory_risks", JSON, nullable=True),
        sa.Column("reputation_impact", sa.String(20), nullable=True),
        sa.Column("operational_impact", sa.String(20), nullable=True),
        sa.Column("recommended_rto_hours", sa.Float, nullable=True),
        sa.Column("recommended_rpo_hours", sa.Float, nullable=True),
        sa.Column("risk_score", sa.Integer, nullable=True),
        sa.Column("mitigation_measures", JSON, nullable=True),
        sa.Column("status", sa.String(20), default="draft"),
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


def downgrade() -> None:
    op.drop_table("bia_assessments")
