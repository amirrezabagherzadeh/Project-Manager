from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


def test_workspace_migration_upgrade_downgrade_and_reupgrade(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "workspace-migration.db"
    async_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("APP_DATABASE_URL", async_url)
    get_settings.cache_clear()
    config = Config("alembic.ini")

    try:
        command.upgrade(config, "head")
        engine = create_engine(async_url.replace("+aiosqlite", ""))
        try:
            inspector = inspect(engine)
            expected = {
                "workspaces",
                "workspace_members",
                "workspace_invitations",
                "activity_logs",
                "notifications",
            }
            assert expected.issubset(inspector.get_table_names())
            member_uniques = {
                item["name"] for item in inspector.get_unique_constraints("workspace_members")
            }
            invitation_uniques = {
                item["name"] for item in inspector.get_unique_constraints("workspace_invitations")
            }
            assert "uq_workspace_members_workspace_user" in member_uniques
            assert {
                "uq_workspace_invitations_workspace_email",
                "uq_workspace_invitations_token_hash",
            }.issubset(invitation_uniques)
            assert {
                "ix_activity_logs_workspace_created",
                "ix_activity_logs_entity",
            }.issubset({item["name"] for item in inspector.get_indexes("activity_logs")})
            invitation_fks = {
                (item["referred_table"], item["options"].get("ondelete"))
                for item in inspector.get_foreign_keys("workspace_invitations")
            }
            assert ("workspaces", "CASCADE") in invitation_fks
            assert ("users", "CASCADE") in invitation_fks
        finally:
            engine.dispose()

        command.downgrade(config, "20260729_0001")
        downgraded_engine = create_engine(async_url.replace("+aiosqlite", ""))
        try:
            inspector = inspect(downgraded_engine)
            assert "users" in inspector.get_table_names()
            assert "workspaces" not in inspector.get_table_names()
        finally:
            downgraded_engine.dispose()

        command.upgrade(config, "head")
        reupgraded_engine = create_engine(async_url.replace("+aiosqlite", ""))
        try:
            assert "workspaces" in inspect(reupgraded_engine).get_table_names()
        finally:
            reupgraded_engine.dispose()
    finally:
        get_settings.cache_clear()
