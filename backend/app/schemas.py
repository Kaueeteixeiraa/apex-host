from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    plan: str
    is_active: bool
    limits: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    github_url: str | None = Field(default=None, max_length=500)
    branch: str = Field(default="main", max_length=120)
    project_type: str = Field(default="manual", max_length=120)
    install_command: str | None = Field(default=None, max_length=500)
    build_command: str | None = Field(default=None, max_length=500)
    start_command: str | None = Field(default=None, max_length=500)
    github_repo_full_name: str | None = Field(default=None, max_length=255)
    cpu_limit: str | None = Field(default=None, max_length=40)
    memory_limit: str | None = Field(default=None, max_length=40)
    internal_port: int = 3000
    primary_domain: str | None = Field(default=None, max_length=255)

    @field_validator("internal_port")
    @classmethod
    def valid_port(cls, value: int) -> int:
        if value < 1 or value > 65535:
            raise ValueError("Port must be between 1 and 65535")
        return value


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    github_url: str | None = Field(default=None, max_length=500)
    branch: str | None = Field(default=None, max_length=120)
    project_type: str | None = Field(default=None, max_length=120)
    install_command: str | None = Field(default=None, max_length=500)
    build_command: str | None = Field(default=None, max_length=500)
    start_command: str | None = Field(default=None, max_length=500)
    github_repo_full_name: str | None = Field(default=None, max_length=255)
    github_webhook_enabled: bool | None = None
    cpu_limit: str | None = Field(default=None, max_length=40)
    memory_limit: str | None = Field(default=None, max_length=40)
    internal_port: int | None = None
    primary_domain: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=50)


class ProjectRead(BaseModel):
    id: int
    owner_id: int
    name: str
    slug: str
    github_url: str | None
    branch: str
    project_type: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    github_repo_full_name: str | None
    github_webhook_id: str | None
    github_webhook_enabled: bool
    cpu_limit: str | None
    memory_limit: str | None
    internal_port: int
    host_port: int | None
    primary_domain: str | None
    auto_subdomain: str
    status: str
    last_deploy_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnvVarCreate(BaseModel):
    key: str = Field(min_length=1, max_length=255, pattern=r"^[A-Z0-9_]+$")
    value: str = Field(min_length=0)
    is_secret: bool = True


class EnvVarUpdate(BaseModel):
    value: str | None = None
    is_secret: bool | None = None


class EnvVarRead(BaseModel):
    id: int
    project_id: int
    key: str
    is_secret: bool
    masked_value: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeployRequest(BaseModel):
    dry_run: bool | None = None


class DeployRead(BaseModel):
    id: int
    project_id: int
    status: str
    branch: str
    commit_sha: str | None
    commit_author: str | None
    commit_message: str | None
    deploy_type: str
    queue_job_id: str | None
    duration_seconds: int | None
    logs: str | None
    error: str | None
    dry_run: bool
    cancel_requested_at: datetime | None
    started_at: datetime
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DomainCreate(BaseModel):
    hostname: str = Field(min_length=3, max_length=255)
    is_primary: bool = False


class DomainUpdate(BaseModel):
    is_primary: bool | None = None
    ssl_enabled: bool | None = None
    ssl_status: str | None = Field(default=None, max_length=80)
    dns_status: str | None = Field(default=None, max_length=80)


class DomainRead(BaseModel):
    id: int
    project_id: int
    hostname: str
    is_primary: bool
    ssl_enabled: bool
    ssl_status: str
    ssl_expires_at: datetime | None
    dns_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogRead(BaseModel):
    id: int
    project_id: int
    deploy_id: int | None
    type: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServerMetric(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float


class DashboardStats(BaseModel):
    total_projects: int
    online_projects: int
    offline_projects: int
    building_projects: int
    error_projects: int
    active_domains: int
    recent_errors: int
    server: ServerMetric
    recent_deploys: list[DeployRead]
    recent_logs: list[LogRead]


class GitHubRepoRead(BaseModel):
    full_name: str
    clone_url: str
    default_branch: str
    private: bool


class GitHubConnectionRead(BaseModel):
    connected: bool
    login: str | None = None
    scope: str | None = None
    connected_at: datetime | None = None


class WebhookEventRead(BaseModel):
    id: int
    project_id: int | None
    github_delivery_id: str
    event_type: str
    branch: str | None
    commit_sha: str | None
    commit_author: str | None
    commit_message: str | None
    matched: bool
    action: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
