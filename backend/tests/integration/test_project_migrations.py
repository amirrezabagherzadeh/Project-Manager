from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


def test_project_migration_upgrade_downgrade_and_reupgrade(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "project-migration.db"
    async_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("APP_DATABASE_URL", async_url)
    get_settings.cache_clear()
    config = Config("alembic.ini")

    try:
        command.upgrade(config, "head")
        engine = create_engine(async_url.replace("+aiosqlite", ""))
        try:
            inspector = inspect(engine)
            expected = {"projects", "project_members", "board_columns"}
            assert expected.issubset(inspector.get_table_names())

            project_uniques = {
                item["name"] for item in inspector.get_unique_constraints("projects")
            }
            assert "uq_projects_workspace_key" in project_uniques

            member_uniques = {
                item["name"] for item in inspector.get_unique_constraints("project_members")
            }
            assert "uq_project_members_project_user" in member_uniques

            column_uniques = {
                item["name"] for item in inspector.get_unique_constraints("board_columns")
            }
            assert "uq_board_columns_project_name" in column_uniques

            column_indexes = {item["name"] for item in inspector.get_indexes("board_columns")}
            assert {
                "ix_board_columns_project_position",
                "ix_board_columns_archived_at",
            }.issubset(column_indexes)

            project_fks = {
                (item["referred_table"], item["options"].get("ondelete"))
                for item in inspector.get_foreign_keys("projects")
            }
            assert ("workspaces", "CASCADE") in project_fks
        finally:
            engine.dispose()

        command.downgrade(config, "20260729_0002")
        downgraded_engine = create_engine(async_url.replace("+aiosqlite", ""))
        try:
            inspector = inspect(downgraded_engine)
            assert "workspaces" in inspector.get_table_names()
            assert "projects" not in inspector.get_table_names()
            assert "project_members" not in inspector.get_table_names()
            assert "board_columns" not in inspector.get_table_names()
        finally:
            downgraded_engine.dispose()

        command.upgrade(config, "head")
        reupgraded_engine = create_engine(async_url.replace("+aiosqlite", ""))
        try:
            assert "projects" in inspect(reupgraded_engine).get_table_names()
        finally:
            reupgraded_engine.dispose()
    finally:
        get_settings.cache_clear()
