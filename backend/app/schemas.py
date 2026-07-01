from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.validators import validate_branch, validate_command, validate_domain, validate_slug


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)
    account_type: str = Field(default="viewer", pattern=r"^(admin|dev|viewer)$")
    admin_signup_code: str | None = Field(default=None, max_length=120)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        if info.data.get("password") and value != info.data["password"]:
            raise ValueError("Passwords do not match")
        return value

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if not any(char.islower() for char in value):
            raise ValueError("Password must include a lowercase letter")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include an uppercase letter")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include a number")
        return value


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    access_profile: str
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

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str | None) -> str | None:
        return validate_slug(value) if value else value

    @field_validator("branch")
    @classmethod
    def valid_branch(cls, value: str) -> str:
        return validate_branch(value)

    @field_validator("install_command", "build_command", "start_command")
    @classmethod
    def valid_command(cls, value: str | None) -> str | None:
        return validate_command(value)

    @field_validator("primary_domain")
    @classmethod
    def valid_primary_domain(cls, value: str | None) -> str | None:
        return validate_domain(value) if value else value


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

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str | None) -> str | None:
        return validate_slug(value) if value else value

    @field_validator("branch")
    @classmethod
    def valid_branch(cls, value: str | None) -> str | None:
        return validate_branch(value) if value else value

    @field_validator("install_command", "build_command", "start_command")
    @classmethod
    def valid_command(cls, value: str | None) -> str | None:
        return validate_command(value)

    @field_validator("primary_domain")
    @classmethod
    def valid_primary_domain(cls, value: str | None) -> str | None:
        return validate_domain(value) if value else value


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


class EnvVarRevealRead(BaseModel):
    id: int
    key: str
    value: str
    expires_in_seconds: int = 30


class DeployRequest(BaseModel):
    dry_run: bool | None = None


class RollbackRequest(BaseModel):
    dry_run: bool | None = None
    target_deploy_id: int | None = None


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

    @field_validator("hostname")
    @classmethod
    def valid_hostname(cls, value: str) -> str:
        return validate_domain(value)


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
    recent_projects: list[ProjectRead]


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


class AuditLogRead(BaseModel):
    id: int
    user_id: int | None
    project_id: int | None
    action: str
    target_type: str | None
    target_id: str | None
    ip_address: str | None
    details: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvailabilitySettingsRead(BaseModel):
    id: int
    project_id: int
    health_check_path: str
    health_check_url: str | None
    high_availability_enabled: bool
    auto_restart_enabled: bool
    auto_rollback_enabled: bool
    blue_green_enabled: bool
    static_fallback_enabled: bool
    cdn_fallback_enabled: bool
    fallback_title: str
    fallback_message: str
    max_restart_attempts: int
    restart_attempts: int
    last_restart_at: datetime | None
    degraded_reason: str | None
    backup_enabled: bool
    last_backup_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvailabilitySettingsUpdate(BaseModel):
    health_check_path: str | None = Field(default=None, max_length=255)
    health_check_url: str | None = Field(default=None, max_length=500)
    high_availability_enabled: bool | None = None
    auto_restart_enabled: bool | None = None
    auto_rollback_enabled: bool | None = None
    blue_green_enabled: bool | None = None
    static_fallback_enabled: bool | None = None
    cdn_fallback_enabled: bool | None = None
    fallback_title: str | None = Field(default=None, max_length=255)
    fallback_message: str | None = None
    max_restart_attempts: int | None = Field(default=None, ge=0, le=10)
    backup_enabled: bool | None = None


class HealthCheckRead(BaseModel):
    id: int
    project_id: int
    status: str
    http_status: int | None
    response_time_ms: int | None
    error: str | None
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServerNodeRead(BaseModel):
    id: int
    name: str
    role: str
    base_url: str | None
    status: str
    cpu_capacity: str | None
    ram_capacity: str | None
    last_seen_at: datetime | None
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ServerNodeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    role: str = Field(default="secondary", pattern=r"^(primary|secondary|edge)$")
    base_url: str | None = Field(default=None, max_length=500)
    status: str = Field(default="online", pattern=r"^(online|offline|degraded)$")
    cpu_capacity: str | None = Field(default=None, max_length=80)
    ram_capacity: str | None = Field(default=None, max_length=80)


class AlertRead(BaseModel):
    id: int
    project_id: int | None
    severity: str
    event_type: str
    message: str
    acknowledged: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BackupRecordRead(BaseModel):
    id: int
    project_id: int | None
    backup_type: str
    status: str
    path: str | None
    size_bytes: int | None
    error: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvailabilitySummaryRead(BaseModel):
    settings: AvailabilitySettingsRead
    last_check: HealthCheckRead | None
    uptime_24h: float
    uptime_7d: float
    average_response_ms: float | None
    recent_checks: list[HealthCheckRead]
    recent_alerts: list[AlertRead]
    nodes: list[ServerNodeRead]
    backups: list[BackupRecordRead]
    stable_deploy: DeployRead | None
    ha_warning: str | None


class ConfirmAction(BaseModel):
    confirmation: str = Field(min_length=2, max_length=255)


class AdminUserUpdate(BaseModel):
    role: str | None = Field(default=None, pattern=r"^(admin|dev|viewer)$")
    access_profile: str | None = Field(default=None, max_length=80)
    is_active: bool | None = None
    limits: dict[str, Any] | None = None


class AdminOverviewRead(BaseModel):
    stats: dict[str, Any]
    users: list[UserRead]
    projects: list[ProjectRead]
    deploys: list[DeployRead]
    alerts: list[AlertRead]
    audit_logs: list[AuditLogRead]
    nodes: list[ServerNodeRead]
    recent_errors: list[LogRead]


class PlanRead(BaseModel):
    id: str
    name: str
    description: str
    audience: str
    price_label: str
    limits: dict[str, Any]
    features: list[str]
    highlighted: bool = False


class ProjectTemplateRead(BaseModel):
    id: str
    name: str
    description: str
    stack: str
    install_command: str | None
    build_command: str | None
    start_command: str | None
    output_directory: str | None
    internal_port: int
    project_type: str
    icon: str
    preview: str
    tags: list[str]


class FrameworkDetectionRequest(BaseModel):
    files: list[str] = Field(default_factory=list)
    package_json: dict[str, Any] | None = None


class FrameworkDetectionRead(BaseModel):
    framework: str
    project_type: str
    build_command: str | None
    start_command: str | None
    install_command: str | None
    output_directory: str | None
    default_port: int
    runtime: str
    confidence: float
    reasons: list[str]


class LogAnalysisRequest(BaseModel):
    deploy_id: int | None = None
    limit: int = Field(default=200, ge=1, le=1000)


class LogAnalysisRead(BaseModel):
    summary: str
    possible_cause: str
    suggested_fix: str
    severity: str
    important_lines: list[str]
    signals: list[str]
    provider: str = "apex-local-heuristics"


class PlatformSettingsRead(BaseModel):
    id: int
    platform_name: str
    logo_url: str | None
    primary_color: str
    primary_domain: str | None
    maintenance_mode: bool
    allow_registration: bool
    require_account_approval: bool
    default_user_profile: str
    default_user_limits: dict[str, Any]
    smtp_config: dict[str, Any]
    alert_config: dict[str, Any]
    backup_config: dict[str, Any]
    cdn_config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlatformSettingsUpdate(BaseModel):
    platform_name: str | None = Field(default=None, min_length=2, max_length=255)
    logo_url: str | None = Field(default=None, max_length=500)
    primary_color: str | None = Field(default=None, max_length=40)
    primary_domain: str | None = Field(default=None, max_length=255)
    maintenance_mode: bool | None = None
    allow_registration: bool | None = None
    require_account_approval: bool | None = None
    default_user_profile: str | None = Field(default=None, max_length=80)
    default_user_limits: dict[str, Any] | None = None
    smtp_config: dict[str, Any] | None = None
    alert_config: dict[str, Any] | None = None
    backup_config: dict[str, Any] | None = None
    cdn_config: dict[str, Any] | None = None


class UserSessionRead(BaseModel):
    id: int
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    last_seen_at: datetime | None
    revoked_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TwoFactorSetupRead(BaseModel):
    enabled: bool
    status: str
    manual_secret: str
    message: str


class PublicComponentStatus(BaseModel):
    name: str
    status: str
    detail: str


class PublicStatusRead(BaseModel):
    overall_status: str
    uptime_24h: float
    uptime_7d: float
    components: list[PublicComponentStatus]
    incidents: list[AlertRead]
    recent_checks: list[HealthCheckRead]
    platform: dict[str, Any]
