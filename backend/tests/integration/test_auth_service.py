import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.auth_boundaries import hash_refresh_token
from app.core.config import Settings
from app.core.database import Database
from app.core.exceptions import DomainError
from app.core.security import decode_access_token, verify_password
from app.models.identity import RefreshSession, User
from app.services.auth import AuthService
from tests.helpers import migrate_database

TEST_SECRET = "test-only-auth-service-secret-" + ("x" * 40)


def _settings(database_url: str) -> Settings:
    return Settings(
        environment="test",
        database_url=database_url,
        secret_key=TEST_SECRET,
    )


def test_register_normalizes_email_hashes_password_and_rejects_duplicate(
    tmp_path: Path,
) -> None:
    database_url = migrate_database(tmp_path / "register.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                service = AuthService(session, _settings(database_url))
                user = await service.register(
                    name="  Test User  ",
                    email="  USER@Example.Test ",
                    password="a-secure-password",
                )

                assert user.email == "user@example.test"
                assert user.name == "Test User"
                assert user.password_hash != "a-secure-password"
                assert await verify_password(
                    "a-secure-password",
                    user.password_hash,
                )

                with pytest.raises(DomainError) as duplicate:
                    await service.register(
                        name="Other User",
                        email="USER@example.test",
                        password="another-secure-password",
                    )
                assert duplicate.value.status_code == 409
                assert duplicate.value.code == "resource_conflict"

                async with session.begin():
                    count = await session.scalar(select(func.count()).select_from(User))
                assert count == 1
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_login_returns_access_token_and_stores_only_refresh_hash(
    tmp_path: Path,
) -> None:
    database_url = migrate_database(tmp_path / "login.db")
    now = datetime.now(UTC).replace(microsecond=0)

    async def scenario() -> None:
        database = Database(database_url)
        settings = _settings(database_url)
        try:
            async with database.session() as session:
                service = AuthService(session, settings, clock=lambda: now)
                user = await service.register(
                    name="Test User",
                    email="user@example.test",
                    password="a-secure-password",
                )
                result = await service.login(
                    email="USER@EXAMPLE.TEST",
                    password="a-secure-password",
                )

                claims = decode_access_token(
                    result.access_token,
                    secret_key=TEST_SECRET,
                    algorithm="HS256",
                )
                assert claims.subject == user.id
                assert result.refresh_token not in result.access_token

                async with session.begin():
                    stored = await session.scalar(select(RefreshSession))
                assert stored is not None
                assert stored.token_hash == hash_refresh_token(result.refresh_token)
                assert stored.token_hash != result.refresh_token
                assert stored.expires_at > stored.created_at
        finally:
            await database.dispose()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("missing@example.test", "a-secure-password"),
        ("user@example.test", "wrong-password"),
    ],
)
def test_login_uses_same_generic_error_for_unknown_or_wrong_credentials(
    tmp_path: Path,
    email: str,
    password: str,
) -> None:
    database_url = migrate_database(tmp_path / f"login-failure-{email.split('@')[0]}.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                service = AuthService(session, _settings(database_url))
                await service.register(
                    name="Test User",
                    email="user@example.test",
                    password="a-secure-password",
                )

                with pytest.raises(DomainError) as error:
                    await service.login(email=email, password=password)

                assert error.value.status_code == 401
                assert error.value.code == "invalid_credentials"
                assert error.value.message == "ایمیل یا رمز عبور صحیح نیست."
                async with session.begin():
                    count = await session.scalar(select(func.count()).select_from(RefreshSession))
                assert count == 0
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_current_user_accepts_valid_token_and_rejects_unknown_subject(
    tmp_path: Path,
) -> None:
    database_url = migrate_database(tmp_path / "current-user.db")

    async def scenario() -> None:
        database = Database(database_url)
        settings = _settings(database_url)
        try:
            async with database.session() as session:
                service = AuthService(session, settings)
                user = await service.register(
                    name="Test User",
                    email="user@example.test",
                    password="a-secure-password",
                )
                login = await service.login(
                    email=user.email,
                    password="a-secure-password",
                )
                assert (await service.current_user(login.access_token)).id == user.id

                with pytest.raises(DomainError) as error:
                    await service.current_user(service._access_token(uuid4()))
                assert error.value.code == "authentication_required"
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_refresh_rotates_and_replay_revokes_replacement_chain(
    tmp_path: Path,
) -> None:
    database_url = migrate_database(tmp_path / "refresh-replay.db")

    async def scenario() -> None:
        database = Database(database_url)
        settings = _settings(database_url)
        try:
            async with database.session() as session:
                service = AuthService(session, settings)
                await service.register(
                    name="Test User",
                    email="user@example.test",
                    password="a-secure-password",
                )
                login = await service.login(
                    email="user@example.test",
                    password="a-secure-password",
                )
                refreshed = await service.refresh(login.refresh_token)
                assert refreshed.refresh_token != login.refresh_token

                with pytest.raises(DomainError) as replay:
                    await service.refresh(login.refresh_token)
                assert replay.value.code == "authentication_required"

                with pytest.raises(DomainError) as revoked_replacement:
                    await service.refresh(refreshed.refresh_token)
                assert revoked_replacement.value.code == "authentication_required"

                async with session.begin():
                    sessions = (
                        await session.scalars(
                            select(RefreshSession).order_by(RefreshSession.created_at)
                        )
                    ).all()
                assert len(sessions) == 2
                assert sessions[0].replay_detected_at is not None
                assert all(item.revoked_at is not None for item in sessions)
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_refresh_rejects_expired_and_unknown_tokens(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "refresh-invalid.db")
    issued_at = datetime.now(UTC) - timedelta(days=8)

    async def scenario() -> None:
        database = Database(database_url)
        settings = _settings(database_url)
        try:
            async with database.session() as session:
                old_service = AuthService(session, settings, clock=lambda: issued_at)
                await old_service.register(
                    name="Test User",
                    email="user@example.test",
                    password="a-secure-password",
                )
                login = await old_service.login(
                    email="user@example.test",
                    password="a-secure-password",
                )
                current_service = AuthService(session, settings)

                for refresh_token in (login.refresh_token, "unknown-refresh-token"):
                    with pytest.raises(DomainError) as error:
                        await current_service.refresh(refresh_token)
                    assert error.value.code == "authentication_required"
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_refresh_rolls_back_when_replacement_link_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_url = migrate_database(tmp_path / "refresh-rollback.db")

    async def scenario() -> None:
        database = Database(database_url)
        settings = _settings(database_url)
        try:
            async with database.session() as session:
                service = AuthService(session, settings)
                await service.register(
                    name="Test User",
                    email="user@example.test",
                    password="a-secure-password",
                )
                login = await service.login(
                    email="user@example.test",
                    password="a-secure-password",
                )

                async def fail_link(*_args, **_kwargs) -> None:
                    raise RuntimeError("simulated link failure")

                monkeypatch.setattr(
                    service._refresh_sessions,
                    "link_replacement",
                    fail_link,
                )
                with pytest.raises(RuntimeError, match="simulated link failure"):
                    await service.refresh(login.refresh_token)

                async with session.begin():
                    sessions = (await session.scalars(select(RefreshSession))).all()
                assert len(sessions) == 1
                assert sessions[0].revoked_at is None
                assert sessions[0].replaced_by_id is None
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_logout_is_enumeration_safe_and_idempotent(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "logout.db")

    async def scenario() -> None:
        database = Database(database_url)
        settings = _settings(database_url)
        try:
            async with database.session() as session:
                service = AuthService(session, settings)
                await service.register(
                    name="Test User",
                    email="user@example.test",
                    password="a-secure-password",
                )
                login = await service.login(
                    email="user@example.test",
                    password="a-secure-password",
                )

                await service.logout(login.refresh_token)
                await service.logout(login.refresh_token)
                await service.logout("unknown-refresh-token")
                await service.logout(None)

                with pytest.raises(DomainError):
                    await service.refresh(login.refresh_token)
        finally:
            await database.dispose()

    asyncio.run(scenario())
