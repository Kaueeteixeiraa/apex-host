"""phase2 initial schema

Revision ID: 20260629_0001
Revises:
Create Date: 2026-06-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260629_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("plan", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("limits", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("github_url", sa.String(500)),
        sa.Column("branch", sa.String(120), nullable=False),
        sa.Column("project_type", sa.String(120), nullable=False),
        sa.Column("install_command", sa.String(500)),
        sa.Column("build_command", sa.String(500)),
        sa.Column("start_command", sa.String(500)),
        sa.Column("github_repo_full_name", sa.String(255)),
        sa.Column("github_webhook_id", sa.String(120)),
        sa.Column("github_webhook_enabled", sa.Boolean(), nullable=False),
        sa.Column("cpu_limit", sa.String(40)),
        sa.Column("memory_limit", sa.String(40)),
        sa.Column("internal_port", sa.Integer(), nullable=False),
        sa.Column("host_port", sa.Integer()),
        sa.Column("primary_domain", sa.String(255)),
        sa.Column("auto_subdomain", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("last_deploy_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_slug", "projects", ["slug"], unique=True)
    op.create_index("ix_projects_github_repo_full_name", "projects", ["github_repo_full_name"])
    op.create_table("environment_variables", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False), sa.Column("key", sa.String(255), nullable=False), sa.Column("value_encrypted", sa.Text(), nullable=False), sa.Column("is_secret", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("project_id", "key", name="uq_env_project_key"))
    op.create_table("deploys", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False), sa.Column("status", sa.String(50), nullable=False), sa.Column("branch", sa.String(120), nullable=False), sa.Column("commit_sha", sa.String(80)), sa.Column("commit_author", sa.String(255)), sa.Column("commit_message", sa.Text()), sa.Column("deploy_type", sa.String(40), nullable=False), sa.Column("queue_job_id", sa.String(255)), sa.Column("duration_seconds", sa.Integer()), sa.Column("logs", sa.Text()), sa.Column("error", sa.Text()), sa.Column("dry_run", sa.Boolean(), nullable=False), sa.Column("cancel_requested_at", sa.DateTime()), sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("finished_at", sa.DateTime()))
    op.create_index("ix_deploys_queue_job_id", "deploys", ["queue_job_id"])
    op.create_table("domains", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False), sa.Column("hostname", sa.String(255), nullable=False), sa.Column("is_primary", sa.Boolean(), nullable=False), sa.Column("ssl_enabled", sa.Boolean(), nullable=False), sa.Column("ssl_status", sa.String(80), nullable=False), sa.Column("ssl_expires_at", sa.DateTime()), sa.Column("dns_status", sa.String(80), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("project_id", "hostname", name="uq_domain_project_hostname"))
    op.create_table("log_entries", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False), sa.Column("deploy_id", sa.Integer(), sa.ForeignKey("deploys.id")), sa.Column("type", sa.String(80), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_table("github_accounts", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("github_user_id", sa.String(120), nullable=False), sa.Column("login", sa.String(255), nullable=False), sa.Column("access_token_encrypted", sa.Text(), nullable=False), sa.Column("scope", sa.String(500)), sa.Column("connected_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_github_accounts_github_user_id", "github_accounts", ["github_user_id"])
    op.create_table("webhook_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id")), sa.Column("github_delivery_id", sa.String(255), nullable=False), sa.Column("event_type", sa.String(120), nullable=False), sa.Column("branch", sa.String(120)), sa.Column("commit_sha", sa.String(80)), sa.Column("commit_author", sa.String(255)), sa.Column("commit_message", sa.Text()), sa.Column("matched", sa.Boolean(), nullable=False), sa.Column("action", sa.String(80), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_webhook_events_github_delivery_id", "webhook_events", ["github_delivery_id"])


def downgrade() -> None:
    for table in ["webhook_events", "github_accounts", "log_entries", "domains", "deploys", "environment_variables", "projects", "users"]:
        op.drop_table(table)
