import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

from fastapi import Response

from app.core.config import Settings


class UntrustedOriginError(ValueError):
    pass


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_request_origin(origin: str | None, settings: Settings) -> None:
    if origin is None:
        return
    normalized = _normalize_origin(origin)
    if normalized is None or normalized not in settings.trusted_origins:
        raise UntrustedOriginError


def set_refresh_cookie(
    response: Response,
    token: str,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> None:
    max_age = settings.refresh_token_expire_days * 24 * 60 * 60
    expires = (now or datetime.now(UTC)).astimezone(UTC) + timedelta(seconds=max_age)
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=max_age,
        expires=expires,
        path=settings.refresh_cookie_path,
        domain=settings.refresh_cookie_domain,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite=settings.refresh_cookie_samesite,
    )


def clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
        domain=settings.refresh_cookie_domain,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite=settings.refresh_cookie_samesite,
    )


def _normalize_origin(origin: str) -> str | None:
    try:
        parsed = urlsplit(origin)
    except ValueError:
        return None
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        return None
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"
