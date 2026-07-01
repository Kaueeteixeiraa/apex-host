"""project output directory

Revision ID: 20260701_0005
Revises: 20260630_0004
Create Date: 2026-07-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260701_0005"
down_revision: Union[str, None] = "20260630_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("output_directory", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "output_directory")
