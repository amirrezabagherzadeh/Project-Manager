from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from anyio import to_thread
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

PASSWORD_HASH = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$2dYb2dnqoFURkilU5uhaEw"
    "$9FjXYn108J/0wE7ZGDK9iHeO8V2CTcILQ4vbQQ8GhIk"
)


class AccessTokenExpiredError(ValueError):
    pass


class InvalidAccessTokenError(ValueError):
    pass


@dataclass(frozen=True)
class AccessTokenClaims:
    subject: UUID
    issued_at: datetime
    expires_at: datetime
    token_id: UUID


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def hash_password(password: str) -> str:
    return await to_thread.run_sync(PASSWORD_HASH.hash, password)


async def verify_password(password: str, password_hash: str) -> bool:
    try:
        return await to_thread.run_sync(PASSWORD_HASH.verify, password, password_hash)
    except UnknownHashError:
        return False


async def verify_password_or_dummy(
    password: str,
    password_hash: str | None,
) -> bool:
    if password_hash is None:
        await verify_password(password, DUMMY_PASSWORD_HASH)
        return False
    return await verify_password(password, password_hash)


def create_access_token(
    *,
    user_id: UUID,
    secret_key: str,
    algorithm: str,
    expires_minutes: int,
    now: datetime | None = None,
    token_id: UUID | None = None,
) -> str:
    issued_at = (now or datetime.now(UTC)).astimezone(UTC)
    expires_at = issued_at + timedelta(minutes=expires_minutes)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": issued_at,
            "exp": expires_at,
            "jti": str(token_id or uuid4()),
        },
        secret_key,
        algorithm=algorithm,
    )


def decode_access_token(
    token: str,
    *,
    secret_key: str,
    algorithm: str,
) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options={"require": ["sub", "iat", "exp", "jti"]},
        )
        return AccessTokenClaims(
            subject=UUID(payload["sub"]),
            issued_at=datetime.fromtimestamp(payload["iat"], tz=UTC),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
            token_id=UUID(payload["jti"]),
        )
    except ExpiredSignatureError as exc:
        raise AccessTokenExpiredError from exc
    except (InvalidTokenError, KeyError, TypeError, ValueError, OverflowError) as exc:
        raise InvalidAccessTokenError from exc
