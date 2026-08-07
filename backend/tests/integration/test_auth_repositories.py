import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.core.database import Database
from app.models.identity import RefreshSession, User
from app.repositories.identity import (
    RefreshChainLimitError,
    RefreshSessionRepository,
    UserRepository,
)
from tests.helpers import migrate_database


def _user(email: str = "user@example.test") -> User:
    return User(
        email=email,
        name="Test User",
        password_hash="$argon2id$private",
    )


def _refresh_session(user_id, token_hash: str) -> RefreshSession:
    now = datetime.now(UTC)
    return RefreshSession(
        user_id=user_id,
        token_hash=token_hash,
        created_at=now,
        expires_at=now + timedelta(days=7),
    )


def test_identity_repositories_query_and_walk_user_scoped_chain(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "repositories.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session, session.begin():
                users = UserRepository(session)
                refresh_sessions = RefreshSessionRepository(session)
                user = await users.add(_user())
                first = await refresh_sessions.add(_refresh_session(user.id, "a" * 64))
                second = await refresh_sessions.add(_refresh_session(user.id, "b" * 64))
                third = await refresh_sessions.add(_refresh_session(user.id, "c" * 64))
                await refresh_sessions.link_replacement(first, second)
                await refresh_sessions.link_replacement(second, third)

            async with database.session() as session:
                users = UserRepository(session)
                refresh_sessions = RefreshSessionRepository(session)
                found_user = await users.get_by_email("  USER@EXAMPLE.TEST ")
                found_first = await refresh_sessions.get_by_token_hash("a" * 64)
                assert found_user is not None
                assert found_first is not None
                assert found_first.user.email == "user@example.test"
                chain = await refresh_sessions.get_replacement_chain(found_first)
                assert [item.token_hash for item in chain] == [
                    "a" * 64,
                    "b" * 64,
                    "c" * 64,
                ]
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_repository_flush_does_not_commit_failed_transaction(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "rollback.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            with pytest.raises(RuntimeError, match="simulated failure"):
                async with database.session() as session:
                    async with session.begin():
                        await UserRepository(session).add(_user())
                        raise RuntimeError("simulated failure")

            async with database.session() as session:
                assert await UserRepository(session).get_by_email("user@example.test") is None
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_refresh_chain_traversal_is_bounded(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "bounded-chain.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                async with session.begin():
                    user = await UserRepository(session).add(_user())
                    repository = RefreshSessionRepository(session)
                    first = await repository.add(_refresh_session(user.id, "d" * 64))
                    second = await repository.add(_refresh_session(user.id, "e" * 64))
                    third = await repository.add(_refresh_session(user.id, "f" * 64))
                    await repository.link_replacement(first, second)
                    await repository.link_replacement(second, third)

                with pytest.raises(RefreshChainLimitError):
                    await repository.get_replacement_chain(first, max_depth=2)
        finally:
            await database.dispose()

    asyncio.run(scenario())
