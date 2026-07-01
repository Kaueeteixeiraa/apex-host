"""phase 4 private admin platform

Revision ID: 20260630_0004
Revises: 20260630_0003
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260630_0004"
down_revision: Union[str, None] = "20260630_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform_name", sa.String(255), nullable=False),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("primary_color", sa.String(40), nullable=False),
        sa.Column("primary_domain", sa.String(255)),
        sa.Column("maintenance_mode", sa.Boolean(), nullable=False),
        sa.Column("allow_registration", sa.Boolean(), nullable=False),
        sa.Column("require_account_approval", sa.Boolean(), nullable=False),
        sa.Column("default_user_plan", sa.String(80), nullable=False),
        sa.Column("default_user_limits", sa.JSON(), nullable=False),
        sa.Column("smtp_config", sa.JSON(), nullable=False),
        sa.Column("alert_config", sa.JSON(), nullable=False),
        sa.Column("backup_config", sa.JSON(), nullable=False),
        sa.Column("cdn_config", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("ip_address", sa.String(80)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime()),
        sa.Column("revoked_at", sa.DateTime()),
    )
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_user_sessions_token_hash", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_table("platform_settings")
