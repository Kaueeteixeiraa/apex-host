"""initial setup fields

Revision ID: 20260701_0006
Revises: 20260701_0005
Create Date: 2026-07-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260701_0006"
down_revision: Union[str, None] = "20260701_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("platform_settings", sa.Column("company_name", sa.String(255), nullable=True))
    op.add_column("platform_settings", sa.Column("public_app_url", sa.String(500), nullable=True))
    op.add_column("platform_settings", sa.Column("contact_email", sa.String(255), nullable=True))
    op.add_column("platform_settings", sa.Column("installation_completed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("platform_settings", sa.Column("installation_completed_at", sa.DateTime(), nullable=True))
    op.alter_column("platform_settings", "installation_completed", server_default=None)


def downgrade() -> None:
    op.drop_column("platform_settings", "installation_completed_at")
    op.drop_column("platform_settings", "installation_completed")
    op.drop_column("platform_settings", "contact_email")
    op.drop_column("platform_settings", "public_app_url")
    op.drop_column("platform_settings", "company_name")
