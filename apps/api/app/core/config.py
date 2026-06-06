from functools import lru_cache

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VendorBridge"
    environment: str = "local"
    secret_key: str = "dev-secret-key"
    access_token_expire_minutes: int = 480
    database_url: str = "sqlite:///./vendorbridge.dev.db"
    redis_url: str | None = "redis://localhost:6379/0"
    backend_cors_origins: list[AnyHttpUrl | str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    company_state: str = "Gujarat"
    login_rate_limit_attempts: int = 8
    login_rate_limit_window_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str] | str:
        if isinstance(value, str) and value:
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
