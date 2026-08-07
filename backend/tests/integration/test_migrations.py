from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


def _alembic_config() -> Config:
    return Config("alembic.ini")


def test_identity_migration_upgrade_downgrade_and_reupgrade(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "migration-check.db"
    async_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("APP_DATABASE_URL", async_url)
    get_settings.cache_clear()
    config = _alembic_config()

    try:
        command.upgrade(config, "head")

        engine = create_engine(async_url.replace("+aiosqlite", ""))
        try:
            inspector = inspect(engine)
            assert {"users", "refresh_sessions"}.issubset(inspector.get_table_names())

            user_uniques = {
                constraint["name"] for constraint in inspector.get_unique_constraints("users")
            }
            refresh_uniques = {
                constraint["name"]
                for constraint in inspector.get_unique_constraints("refresh_sessions")
            }
            refresh_foreign_keys = {
                tuple(foreign_key["referred_columns"])
                for foreign_key in inspector.get_foreign_keys("refresh_sessions")
            }
            refresh_indexes = {index["name"] for index in inspector.get_indexes("refresh_sessions")}

            assert "uq_users_email" in user_uniques
            assert {
                "uq_refresh_sessions_token_hash",
                "uq_refresh_sessions_replaced_by_id",
            }.issubset(refresh_uniques)
            assert ("id",) in refresh_foreign_keys
            assert {
                "ix_refresh_sessions_user_id",
                "ix_refresh_sessions_expires_at",
                "ix_refresh_sessions_user_active",
            }.issubset(refresh_indexes)
        finally:
            engine.dispose()

        command.downgrade(config, "base")
        downgraded_engine = create_engine(async_url.replace("+aiosqlite", ""))
        try:
            assert "users" not in inspect(downgraded_engine).get_table_names()
            assert "refresh_sessions" not in inspect(downgraded_engine).get_table_names()
        finally:
            downgraded_engine.dispose()

        command.upgrade(config, "head")
        reupgraded_engine = create_engine(async_url.replace("+aiosqlite", ""))
        try:
            assert {"users", "refresh_sessions"}.issubset(
                inspect(reupgraded_engine).get_table_names()
            )
        finally:
            reupgraded_engine.dispose()
    finally:
        get_settings.cache_clear()
