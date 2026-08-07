import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    insert,
    select,
)
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.core.database import Database
from app.main import create_app
from app.models.base import UTCDateTime


def test_database_sessions_are_request_scoped() -> None:
    async def scenario() -> None:
        database = Database("sqlite+aiosqlite:///:memory:")
        try:
            async with database.session() as first, database.session() as second:
                assert first is not second
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_sqlite_foreign_keys_are_enforced() -> None:
    async def scenario() -> None:
        database = Database("sqlite+aiosqlite:///:memory:")
        metadata = MetaData()
        Table("parents", metadata, Column("id", Integer, primary_key=True))
        children = Table(
            "children",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("parent_id", ForeignKey("parents.id"), nullable=False),
        )
        try:
            async with database.engine.begin() as connection:
                await connection.run_sync(metadata.create_all)

            with pytest.raises(IntegrityError):
                async with database.session() as session:
                    async with session.begin():
                        await session.execute(insert(children).values(id=1, parent_id=999))
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_utc_datetime_round_trips_as_aware_utc() -> None:
    async def scenario() -> None:
        database = Database("sqlite+aiosqlite:///:memory:")
        metadata = MetaData()
        moments = Table(
            "moments",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("occurred_at", UTCDateTime(), nullable=False),
        )
        expected = datetime(2026, 7, 29, 12, 30, tzinfo=UTC)
        try:
            async with database.engine.begin() as connection:
                await connection.run_sync(metadata.create_all)
            async with database.session() as session:
                async with session.begin():
                    await session.execute(insert(moments).values(id=1, occurred_at=expected))
                actual = await session.scalar(
                    select(moments.c.occurred_at).where(moments.c.id == 1)
                )
            assert actual == expected
            assert actual is not None
            assert actual.tzinfo is UTC
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_session_rolls_back_when_request_work_fails() -> None:
    async def fail_after_insert(database: Database, table: Table) -> NoReturn:
        async with database.session() as session, session.begin():
            await session.execute(insert(table).values(id=1))
            raise RuntimeError("simulated failure")

    async def scenario() -> None:
        database = Database("sqlite+aiosqlite:///:memory:")
        metadata = MetaData()
        records = Table("records", metadata, Column("id", Integer, primary_key=True))
        try:
            async with database.engine.begin() as connection:
                await connection.run_sync(metadata.create_all)
            with pytest.raises(RuntimeError, match="simulated failure"):
                await fail_after_insert(database, records)
            async with database.session() as session:
                assert (await session.scalars(select(records.c.id))).all() == []
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_application_startup_does_not_create_database_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "not-created-on-startup.db"
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{database_path.as_posix()}",
    )

    with TestClient(create_app(settings)) as client:
        assert client.get("/health").status_code == 200

    assert not database_path.exists()
