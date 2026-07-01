from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    limits: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    projects: Mapped[list["Project"]] = relationship(back_populates="owner")
    github_accounts: Mapped[list["GitHubAccount"]] = relationship(cascade="all, delete-orphan", back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")
    project_memberships: Mapped[list["ProjectMember"]] = relationship(cascade="all, delete-orphan", back_populates="user")
    sessions: Mapped[list["UserSession"]] = relationship(cascade="all, delete-orphan", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    github_url: Mapped[str | None] = mapped_column(String(500))
    branch: Mapped[str] = mapped_column(String(120), default="main", nullable=False)
    project_type: Mapped[str] = mapped_column(String(120), default="manual", nullable=False)
    install_command: Mapped[str | None] = mapped_column(String(500))
    build_command: Mapped[str | None] = mapped_column(String(500))
    start_command: Mapped[str | None] = mapped_column(String(500))
    github_repo_full_name: Mapped[str | None] = mapped_column(String(255), index=True)
    github_webhook_id: Mapped[str | None] = mapped_column(String(120))
    github_webhook_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cpu_limit: Mapped[str | None] = mapped_column(String(40))
    memory_limit: Mapped[str | None] = mapped_column(String(40))
    internal_port: Mapped[int] = mapped_column(Integer, default=3000, nullable=False)
    host_port: Mapped[int | None] = mapped_column(Integer)
    primary_domain: Mapped[str | None] = mapped_column(String(255))
    auto_subdomain: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="offline", nullable=False)
    last_deploy_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner: Mapped[User] = relationship(back_populates="projects")
    env_vars: Mapped[list["EnvironmentVariable"]] = relationship(
        cascade="all, delete-orphan",
        back_populates="project",
    )
    deploys: Mapped[list["Deploy"]] = relationship(
        cascade="all, delete-orphan",
        back_populates="project",
        order_by="Deploy.started_at.desc()",
    )
    domains: Mapped[list["Domain"]] = relationship(
        cascade="all, delete-orphan",
        back_populates="project",
    )
    logs: Mapped[list["LogEntry"]] = relationship(
        cascade="all, delete-orphan",
        back_populates="project",
        order_by="LogEntry.created_at.desc()",
    )
    webhook_events: Mapped[list["WebhookEvent"]] = relationship(
        cascade="all, delete-orphan",
        back_populates="project",
        order_by="WebhookEvent.created_at.desc()",
    )
    members: Mapped[list["ProjectMember"]] = relationship(cascade="all, delete-orphan", back_populates="project")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="project")


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    can_view: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_deploy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="project_memberships")


class EnvironmentVariable(Base):
    __tablename__ = "environment_variables"
    __table_args__ = (UniqueConstraint("project_id", "key", name="uq_env_project_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project: Mapped[Project] = relationship(back_populates="env_vars")


class Deploy(Base):
    __tablename__ = "deploys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)
    branch: Mapped[str] = mapped_column(String(120), nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(String(80))
    commit_author: Mapped[str | None] = mapped_column(String(255))
    commit_message: Mapped[str | None] = mapped_column(Text)
    deploy_type: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    queue_job_id: Mapped[str | None] = mapped_column(String(255), index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    logs: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    project: Mapped[Project] = relationship(back_populates="deploys")
    log_entries: Mapped[list["LogEntry"]] = relationship(cascade="all, delete-orphan", back_populates="deploy")


class Domain(Base):
    __tablename__ = "domains"
    __table_args__ = (UniqueConstraint("project_id", "hostname", name="uq_domain_project_hostname"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ssl_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ssl_status: Mapped[str] = mapped_column(String(80), default="not_requested", nullable=False)
    ssl_expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    dns_status: Mapped[str] = mapped_column(String(80), default="unchecked", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="domains")


class GitHubAccount(Base):
    __tablename__ = "github_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    github_user_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    login: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str | None] = mapped_column(String(500))
    connected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="github_accounts")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    github_delivery_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    branch: Mapped[str | None] = mapped_column(String(120))
    commit_sha: Mapped[str | None] = mapped_column(String(80))
    commit_author: Mapped[str | None] = mapped_column(String(255))
    commit_message: Mapped[str | None] = mapped_column(Text)
    matched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    action: Mapped[str] = mapped_column(String(80), default="ignored", nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project: Mapped[Project | None] = relationship(back_populates="webhook_events")


class LogEntry(Base):
    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    deploy_id: Mapped[int | None] = mapped_column(ForeignKey("deploys.id"))
    type: Mapped[str] = mapped_column(String(80), default="app", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="logs")
    deploy: Mapped[Deploy | None] = relationship(back_populates="log_entries")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    action: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(120))
    target_id: Mapped[str | None] = mapped_column(String(120))
    ip_address: Mapped[str | None] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped[User | None] = relationship(back_populates="audit_logs")
    project: Mapped[Project | None] = relationship(back_populates="audit_logs")


class ProjectAvailabilitySetting(Base):
    __tablename__ = "project_availability_settings"
    __table_args__ = (UniqueConstraint("project_id", name="uq_availability_project"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    health_check_path: Mapped[str] = mapped_column(String(255), default="/", nullable=False)
    health_check_url: Mapped[str | None] = mapped_column(String(500))
    high_availability_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_restart_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_rollback_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    blue_green_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    static_fallback_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cdn_fallback_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fallback_title: Mapped[str] = mapped_column(String(255), default="Site temporariamente instavel", nullable=False)
    fallback_message: Mapped[str] = mapped_column(
        Text,
        default="Estamos restaurando este projeto automaticamente pelo Apex Host.",
        nullable=False,
    )
    max_restart_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    restart_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_restart_at: Mapped[datetime | None] = mapped_column(DateTime)
    degraded_reason: Mapped[str | None] = mapped_column(Text)
    backup_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_backup_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class HealthCheck(Base):
    __tablename__ = "health_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class ServerNode(Base):
    __tablename__ = "server_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(80), default="primary", nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default="online", nullable=False)
    cpu_capacity: Mapped[str | None] = mapped_column(String(80))
    ram_capacity: Mapped[str | None] = mapped_column(String(80))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class ProjectNodeDeployment(Base):
    __tablename__ = "project_node_deployments"
    __table_args__ = (UniqueConstraint("project_id", "node_id", "deploy_id", name="uq_project_node_deploy"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    node_id: Mapped[int] = mapped_column(ForeignKey("server_nodes.id"), nullable=False)
    deploy_id: Mapped[int | None] = mapped_column(ForeignKey("deploys.id"))
    version: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(50), default="prepared", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    healthy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_health_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class BackupRecord(Base):
    __tablename__ = "backup_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    backup_type: Mapped[str] = mapped_column(String(80), default="manual", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)
    path: Mapped[str | None] = mapped_column(String(500))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    severity: Mapped[str] = mapped_column(String(50), default="warning", nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped[User] = relationship(back_populates="sessions")


class PlatformSetting(Base):
    __tablename__ = "platform_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    platform_name: Mapped[str] = mapped_column(String(255), default="Apex Host", nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    primary_color: Mapped[str] = mapped_column(String(40), default="#18b6ff", nullable=False)
    primary_domain: Mapped[str | None] = mapped_column(String(255))
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_registration: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_account_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_user_plan: Mapped[str] = mapped_column(String(80), default="viewer", nullable=False)
    default_user_limits: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    smtp_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    alert_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    backup_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    cdn_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
