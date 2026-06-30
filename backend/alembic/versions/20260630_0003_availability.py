"""availability nodes checks backups alerts

Revision ID: 20260630_0003
Revises: 20260630_0002
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260630_0003"
down_revision: Union[str, None] = "20260630_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_availability_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("health_check_path", sa.String(255), nullable=False),
        sa.Column("health_check_url", sa.String(500)),
        sa.Column("high_availability_enabled", sa.Boolean(), nullable=False),
        sa.Column("auto_restart_enabled", sa.Boolean(), nullable=False),
        sa.Column("auto_rollback_enabled", sa.Boolean(), nullable=False),
        sa.Column("blue_green_enabled", sa.Boolean(), nullable=False),
        sa.Column("static_fallback_enabled", sa.Boolean(), nullable=False),
        sa.Column("cdn_fallback_enabled", sa.Boolean(), nullable=False),
        sa.Column("fallback_title", sa.String(255), nullable=False),
        sa.Column("fallback_message", sa.Text(), nullable=False),
        sa.Column("max_restart_attempts", sa.Integer(), nullable=False),
        sa.Column("restart_attempts", sa.Integer(), nullable=False),
        sa.Column("last_restart_at", sa.DateTime()),
        sa.Column("degraded_reason", sa.Text()),
        sa.Column("backup_enabled", sa.Boolean(), nullable=False),
        sa.Column("last_backup_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", name="uq_availability_project"),
    )
    op.create_table(
        "health_checks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("http_status", sa.Integer()),
        sa.Column("response_time_ms", sa.Integer()),
        sa.Column("error", sa.Text()),
        sa.Column("checked_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "server_nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(80), nullable=False),
        sa.Column("base_url", sa.String(500)),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("cpu_capacity", sa.String(80)),
        sa.Column("ram_capacity", sa.String(80)),
        sa.Column("last_seen_at", sa.DateTime()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_server_nodes_name", "server_nodes", ["name"], unique=True)
    op.create_table(
        "project_node_deployments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("node_id", sa.Integer(), sa.ForeignKey("server_nodes.id"), nullable=False),
        sa.Column("deploy_id", sa.Integer(), sa.ForeignKey("deploys.id")),
        sa.Column("version", sa.String(120)),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("healthy", sa.Boolean(), nullable=False),
        sa.Column("last_health_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "node_id", "deploy_id", name="uq_project_node_deploy"),
    )
    op.create_table(
        "backup_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id")),
        sa.Column("backup_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("path", sa.String(500)),
        sa.Column("size_bytes", sa.Integer()),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id")),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("acknowledged", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_alerts_event_type", "alerts", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_alerts_event_type", table_name="alerts")
    op.drop_table("alerts")
    op.drop_table("backup_records")
    op.drop_table("project_node_deployments")
    op.drop_index("ix_server_nodes_name", table_name="server_nodes")
    op.drop_table("server_nodes")
    op.drop_table("health_checks")
    op.drop_table("project_availability_settings")
