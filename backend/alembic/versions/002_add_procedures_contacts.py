"""Add recovery_procedures, emergency_contacts, vendor_contacts tables.

Revision ID: 002
Revises: 001
Create Date: 2026-03-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- recovery_procedures --
    op.create_table(
        "recovery_procedures",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("procedure_id", sa.String(20), unique=True, nullable=False),
        sa.Column("system_name", sa.String(100), nullable=False),
        sa.Column("scenario_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("version", sa.String(20), default="1.0"),
        sa.Column("priority_order", sa.Integer, nullable=False),
        sa.Column("pre_requisites", sa.Text, nullable=True),
        sa.Column("procedure_steps", JSON, nullable=False),
        sa.Column("estimated_time_hours", sa.Float, nullable=True),
        sa.Column("responsible_team", sa.String(100), nullable=True),
        sa.Column("last_reviewed", sa.Date, nullable=True),
        sa.Column("review_cycle_months", sa.Integer, default=12),
        sa.Column("status", sa.String(20), default="active"),
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

    # -- emergency_contacts --
    op.create_table(
        "emergency_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("phone_primary", sa.String(20), nullable=True),
        sa.Column("phone_secondary", sa.String(20), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("teams_id", sa.String(200), nullable=True),
        sa.Column("escalation_level", sa.Integer, nullable=False),
        sa.Column("escalation_group", sa.String(50), nullable=False),
        sa.Column("notification_channels", JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
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

    # -- vendor_contacts --
    op.create_table(
        "vendor_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("vendor_name", sa.String(200), nullable=False),
        sa.Column("service_name", sa.String(200), nullable=False),
        sa.Column("contract_id", sa.String(100), nullable=True),
        sa.Column("support_level", sa.String(50), nullable=True),
        sa.Column("phone_primary", sa.String(20), nullable=True),
        sa.Column("phone_emergency", sa.String(20), nullable=True),
        sa.Column("email_support", sa.String(200), nullable=True),
        sa.Column("sla_response_hours", sa.Float, nullable=True),
        sa.Column("sla_resolution_hours", sa.Float, nullable=True),
        sa.Column("contract_expiry", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
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


def downgrade() -> None:
    op.drop_table("vendor_contacts")
    op.drop_table("emergency_contacts")
    op.drop_table("recovery_procedures")
