import pytest
from pydantic import ValidationError

from app.core.config import DEVELOPMENT_SECRET_KEY, Settings


def test_auth_and_database_defaults_are_safe_for_local_development() -> None:
    settings = Settings(environment="test")

    assert settings.database_url == "sqlite+aiosqlite:///./storage/app.db"
    assert settings.jwt_algorithm == "HS256"
    assert settings.access_token_expire_minutes == 30
    assert settings.refresh_token_expire_days == 7
    assert settings.refresh_cookie_path == "/api/v1/auth"
    assert settings.refresh_cookie_samesite == "lax"
    assert settings.refresh_cookie_secure is False
    assert settings.register_rate_limit_requests != settings.login_rate_limit_requests


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({}, "APP_SECRET_KEY"),
        ({"secret_key": "short"}, "APP_SECRET_KEY"),
        (
            {"secret_key": "x" * 32, "refresh_cookie_secure": False},
            "Secure",
        ),
    ],
)
def test_production_rejects_insecure_auth_settings(
    overrides: dict[str, object],
    message: str,
) -> None:
    values: dict[str, object] = {
        "environment": "production",
        "secret_key": DEVELOPMENT_SECRET_KEY,
        "refresh_cookie_secure": True,
        **overrides,
    }

    with pytest.raises(ValidationError, match=message):
        Settings(**values)


def test_production_accepts_explicit_secret_and_secure_cookie() -> None:
    settings = Settings(
        environment="production",
        secret_key="production-only-secret-value-that-is-long-enough",
        refresh_cookie_secure=True,
    )

    assert settings.expose_docs is False
    assert settings.refresh_cookie_secure is True


def test_samesite_none_requires_secure_cookie() -> None:
    with pytest.raises(ValidationError, match="SameSite=None"):
        Settings(
            environment="test",
            refresh_cookie_samesite="none",
            refresh_cookie_secure=False,
        )


def test_origins_are_explicit_and_normalized() -> None:
    settings = Settings(
        environment="test",
        cors_origins=["http://localhost:3000/"],
        trusted_origins=["https://example.test/"],
    )

    assert settings.cors_origins == ["http://localhost:3000"]
    assert settings.trusted_origins == ["https://example.test"]

    with pytest.raises(ValidationError, match="explicit origins"):
        Settings(environment="test", trusted_origins=["*"])
