from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Apex Host"
    environment: str = "development"
    api_prefix: str = "/api"

    secret_key: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    database_url: str = "sqlite:///./apex_host.db"
    redis_url: str = "redis://localhost:6379/0"
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    admin_email: str = "admin@apex.local"
    admin_password: str = "apex-admin"
    admin_name: str = "Apex Admin"

    base_domain: str = "apexhost.local"
    data_dir: Path = Path("./data")
    deploy_timeout_seconds: int = 900

    enable_docker_deploys: bool = False
    enable_build_commands: bool = False
    docker_network: str | None = None
    nginx_sites_dir: str | None = None
    certbot_enabled: bool = False
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


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "repos").mkdir(parents=True, exist_ok=True)
    return settings
