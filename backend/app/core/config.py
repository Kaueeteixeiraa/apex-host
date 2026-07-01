from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Apex Host"
    environment: str = "development"
    api_prefix: str = "/api"

    secret_key: str = "change-me-before-production"
    jwt_secret: str | None = None
    encryption_key: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    database_url: str = "sqlite:///./apex_host.db"
    redis_url: str = "redis://localhost:6379/0"
    deploy_queue_name: str = "apex-host-deploys"
    use_redis_deploy_queue: bool = True
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    public_app_url: str = "http://localhost:5173"
    api_url: str = "http://localhost:8000/api"

    admin_email: str = "admin@apex.local"
    admin_password: str = "apex-admin"
    admin_name: str = "Apex Admin"

    base_domain: str = "apexhost.local"
    data_dir: Path = Path("./data")
    deploy_timeout_seconds: int = 900
    deploy_mode: str = "dry-run"
    dry_run: bool = True

    enable_docker_deploys: bool = False
    enable_build_commands: bool = False
    docker_network: str | None = None
    docker_apps_network: str = "apex-host-apps"
    docker_cpu_limit: str | None = None
    docker_memory_limit: str | None = None
    nginx_sites_dir: str | None = None
    nginx_test_command: str = "nginx -t"
    nginx_reload_command: str = "nginx -s reload"
    certbot_enabled: bool = False
    certbot_email: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    backup_path: str = "/data/backups"
    backup_retention_days: int = 14
    github_webhook_secret: str | None = None
    github_oauth_client_id: str | None = None
    github_oauth_client_secret: str | None = None
    github_oauth_redirect_url: str = "http://localhost:8000/api/github/oauth/callback"
    admin_signup_code: str | None = None
    public_registration_enabled: bool = True
    health_monitor_enabled: bool = True
    health_check_interval_seconds: int = 60
    default_health_check_timeout_seconds: int = 5
    auto_create_tables: bool = True
    allowed_command_prefixes: str = "npm,pnpm,yarn,node,python,pip,uvicorn,gunicorn"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @computed_field
    @property
    def allowed_commands(self) -> set[str]:
        return {item.strip() for item in self.allowed_command_prefixes.split(",") if item.strip()}

    @computed_field
    @property
    def effective_jwt_secret(self) -> str:
        return self.jwt_secret or self.secret_key

    @computed_field
    @property
    def effective_encryption_key(self) -> str:
        return self.encryption_key or self.secret_key

    def validate_for_production(self) -> None:
        if self.environment.lower() != "production":
            return
        weak_values = {
            "SECRET_KEY": self.secret_key,
            "JWT_SECRET": self.effective_jwt_secret,
            "ENCRYPTION_KEY": self.effective_encryption_key,
            "ADMIN_PASSWORD": self.admin_password,
        }
        unsafe = {
            key
            for key, value in weak_values.items()
            if value in {"change-me-before-production", "change-this-long-random-secret", "apex-admin", ""}
            or len(value) < 32
        }
        if unsafe:
            names = ", ".join(sorted(unsafe))
            raise RuntimeError(f"Unsafe production configuration. Set strong values for: {names}")
        if "*" in self.backend_cors_origins:
            raise RuntimeError("BACKEND_CORS_ORIGINS cannot contain '*' in production")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_for_production()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "repos").mkdir(parents=True, exist_ok=True)
    return settings
