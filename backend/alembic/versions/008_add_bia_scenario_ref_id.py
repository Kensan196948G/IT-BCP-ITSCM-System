"""Add scenario_ref_id to bia_assessments table.

Revision ID: 008
Revises: 007
Create Date: 2026-04-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bia_assessments",
        sa.Column(
            "scenario_ref_id",
            UUID(as_uuid=True),
            sa.ForeignKey("bcp_scenarios.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("bia_assessments", "scenario_ref_id")
