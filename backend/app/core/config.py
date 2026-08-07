from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, PositiveInt, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_SECRET_KEY = "development-only-insecure-key-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "Persian Project Manager API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    docs_enabled: bool = True
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    trusted_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    database_url: str = Field(
        default="sqlite+aiosqlite:///./storage/app.db",
        validation_alias=AliasChoices("APP_DATABASE_URL", "DATABASE_URL", "POSTGRES_URL"),
    )
    attachment_storage_path: Path = Path("./storage/uploads")

    secret_key: SecretStr = SecretStr(DEVELOPMENT_SECRET_KEY)
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: PositiveInt = 30
    refresh_token_expire_days: PositiveInt = 7

    refresh_cookie_name: str = "ppm_refresh"
    refresh_cookie_path: str = "/api/v1/auth"
    refresh_cookie_domain: str | None = None
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    register_rate_limit_requests: PositiveInt = 5
    register_rate_limit_window_seconds: PositiveInt = 3600
    login_rate_limit_requests: PositiveInt = 10
    login_rate_limit_window_seconds: PositiveInt = 60

    @field_validator("cors_origins", "trusted_origins")
    @classmethod
    def validate_origins(cls, value: list[str]) -> list[str]:
        if "*" in value:
            raise ValueError("Credentialed CORS requires explicit origins")
        normalized = [origin.strip().rstrip("/") for origin in value]
        if not normalized or any(not origin for origin in normalized):
            raise ValueError("At least one explicit origin is required")
        return normalized

    @field_validator("database_url", "refresh_cookie_name")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value must not be blank")
        return value

    @field_validator("database_url", mode="after")
    @classmethod
    def use_async_postgres_driver(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        return value

    @field_validator("refresh_cookie_path")
    @classmethod
    def validate_cookie_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("Refresh cookie path must start with '/'")
        return value

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        secret_value = self.secret_key.get_secret_value()
        if self.environment == "production":
            if secret_value == DEVELOPMENT_SECRET_KEY or len(secret_value) < 32:
                raise ValueError(
                    "APP_SECRET_KEY must be a unique value of at least 32 characters in production"
                )
            if not self.refresh_cookie_secure:
                raise ValueError("Production refresh cookies must be Secure")
        if self.refresh_cookie_samesite == "none" and not self.refresh_cookie_secure:
            raise ValueError("SameSite=None refresh cookies must be Secure")
        return self

    @property
    def expose_docs(self) -> bool:
        return self.docs_enabled and self.environment != "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
