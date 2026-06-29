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
    plan: Mapped[str] = mapped_column(String(50), default="admin_unlimited", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    limits: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    projects: Mapped[list["Project"]] = relationship(back_populates="owner")


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
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    logs: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    dns_status: Mapped[str] = mapped_column(String(80), default="unchecked", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="domains")


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
