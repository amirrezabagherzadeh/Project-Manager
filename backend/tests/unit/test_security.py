import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import jwt
import pytest

from app.core.security import (
    DUMMY_PASSWORD_HASH,
    AccessTokenExpiredError,
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    normalize_email,
    verify_password,
    verify_password_or_dummy,
)

TEST_SECRET = "test-only-signing-secret-" + ("x" * 48)


def test_password_hash_is_one_way_and_verifiable() -> None:
    async def scenario() -> None:
        password = "correct horse battery staple"
        password_hash = await hash_password(password)

        assert password_hash != password
        assert password not in password_hash
        assert password_hash.startswith("$argon2")
        assert await verify_password(password, password_hash) is True
        assert await verify_password("wrong password", password_hash) is False

    asyncio.run(scenario())


def test_password_verification_rejects_unknown_hash_format() -> None:
    assert asyncio.run(verify_password("password", "not-a-password-hash")) is False


def test_unknown_user_password_verification_uses_dummy_hash_and_still_fails() -> None:
    async def scenario() -> None:
        assert DUMMY_PASSWORD_HASH.startswith("$argon2")
        assert await verify_password_or_dummy("irrelevant", None) is False

    asyncio.run(scenario())


def test_known_user_password_verification_uses_stored_hash() -> None:
    async def scenario() -> None:
        password_hash = await hash_password("known-user-password")

        assert await verify_password_or_dummy("known-user-password", password_hash) is True
        assert await verify_password_or_dummy("incorrect", password_hash) is False

    asyncio.run(scenario())


def test_email_normalization_is_lowercase_and_trimmed() -> None:
    assert normalize_email("  User.Name+Tag@EXAMPLE.COM ") == "user.name+tag@example.com"


def test_access_token_contains_required_claims_and_expected_lifetime() -> None:
    user_id = uuid4()
    issued_at = datetime.now(UTC).replace(microsecond=0)
    token = create_access_token(
        user_id=user_id,
        secret_key=TEST_SECRET,
        algorithm="HS256",
        expires_minutes=30,
        now=issued_at,
    )

    claims = decode_access_token(
        token,
        secret_key=TEST_SECRET,
        algorithm="HS256",
    )

    assert claims.subject == user_id
    assert claims.issued_at == issued_at
    assert (claims.expires_at - claims.issued_at).total_seconds() == 1800


def test_access_tokens_have_unique_token_ids() -> None:
    parameters = {
        "user_id": uuid4(),
        "secret_key": TEST_SECRET,
        "algorithm": "HS256",
        "expires_minutes": 30,
    }

    first = decode_access_token(
        create_access_token(**parameters),
        secret_key=TEST_SECRET,
        algorithm="HS256",
    )
    second = decode_access_token(
        create_access_token(**parameters),
        secret_key=TEST_SECRET,
        algorithm="HS256",
    )

    assert first.token_id != second.token_id


def test_expired_access_token_has_distinct_error() -> None:
    token = create_access_token(
        user_id=uuid4(),
        secret_key=TEST_SECRET,
        algorithm="HS256",
        expires_minutes=-1,
    )

    with pytest.raises(AccessTokenExpiredError):
        decode_access_token(
            token,
            secret_key=TEST_SECRET,
            algorithm="HS256",
        )


@pytest.mark.parametrize("invalid_kind", ["tampered", "wrong-algorithm", "missing-claim"])
def test_invalid_access_token_is_rejected(invalid_kind: str) -> None:
    secret_key = TEST_SECRET
    if invalid_kind == "wrong-algorithm":
        token = jwt.encode(
            {
                "sub": str(uuid4()),
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC).timestamp() + 1800,
                "jti": str(uuid4()),
            },
            secret_key,
            algorithm="HS384",
        )
    elif invalid_kind == "missing-claim":
        token = jwt.encode(
            {
                "sub": str(uuid4()),
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC).timestamp() + 1800,
            },
            secret_key,
            algorithm="HS256",
        )
    else:
        token = create_access_token(
            user_id=uuid4(),
            secret_key=secret_key,
            algorithm="HS256",
            expires_minutes=30,
        )
        header, payload, signature = token.split(".")
        signature = f"{'a' if signature[0] != 'a' else 'b'}{signature[1:]}"
        token = f"{header}.{payload}.{signature}"

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(
            token,
            secret_key=secret_key,
            algorithm="HS256",
        )
