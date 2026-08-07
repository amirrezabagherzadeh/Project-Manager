from datetime import UTC, datetime

import pytest
from fastapi import Response
from pydantic import ValidationError

from app.core.auth_boundaries import (
    UntrustedOriginError,
    clear_refresh_cookie,
    generate_refresh_token,
    hash_refresh_token,
    set_refresh_cookie,
    validate_request_origin,
)
from app.core.config import Settings


def test_refresh_tokens_are_high_entropy_and_only_hashes_are_stable() -> None:
    first = generate_refresh_token()
    second = generate_refresh_token()

    assert first != second
    assert len(first) >= 64
    assert len(second) >= 64
    assert hash_refresh_token(first) == hash_refresh_token(first)
    assert hash_refresh_token(first) != hash_refresh_token(second)
    assert len(hash_refresh_token(first)) == 64
    assert first not in hash_refresh_token(first)


def test_refresh_cookie_set_and_delete_use_symmetric_security_attributes() -> None:
    settings = Settings(
        environment="test",
        refresh_cookie_secure=True,
        refresh_cookie_samesite="strict",
        refresh_cookie_domain="example.test",
    )
    issued = Response()
    set_refresh_cookie(
        issued,
        "opaque-value",
        settings,
        now=datetime(2026, 7, 29, 12, 0, tzinfo=UTC),
    )
    set_header = issued.headers["set-cookie"]

    assert "ppm_refresh=opaque-value" in set_header
    assert "HttpOnly" in set_header
    assert "Secure" in set_header
    assert "SameSite=strict" in set_header
    assert "Path=/api/v1/auth" in set_header
    assert "Domain=example.test" in set_header
    assert "Max-Age=604800" in set_header

    cleared = Response()
    clear_refresh_cookie(cleared, settings)
    clear_header = cleared.headers["set-cookie"]

    assert "ppm_refresh=" in clear_header
    assert "Max-Age=0" in clear_header
    assert "HttpOnly" in clear_header
    assert "Secure" in clear_header
    assert "SameSite=strict" in clear_header
    assert "Path=/api/v1/auth" in clear_header
    assert "Domain=example.test" in clear_header


@pytest.mark.parametrize("origin", [None, "http://localhost:3000", "HTTPS://EXAMPLE.TEST"])
def test_absent_or_allowed_origin_is_accepted(origin: str | None) -> None:
    settings = Settings(
        environment="test",
        trusted_origins=["http://localhost:3000", "https://example.test"],
    )

    validate_request_origin(origin, settings)


@pytest.mark.parametrize(
    "origin",
    [
        "https://attacker.test",
        "null",
        "javascript:alert(1)",
        "https://example.test/path",
        "https://user:password@example.test",
    ],
)
def test_untrusted_or_malformed_origin_is_rejected(origin: str) -> None:
    settings = Settings(
        environment="test",
        trusted_origins=["https://example.test"],
    )

    with pytest.raises(UntrustedOriginError):
        validate_request_origin(origin, settings)


def test_invalid_cookie_configuration_is_rejected() -> None:
    with pytest.raises(ValidationError, match="SameSite=None"):
        Settings(
            environment="test",
            refresh_cookie_samesite="none",
            refresh_cookie_secure=False,
        )
