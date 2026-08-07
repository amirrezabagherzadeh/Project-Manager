from pathlib import Path

from alembic import command
from alembic.config import Config


def migrate_database(database_path: Path, revision: str = "head") -> str:
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    config = Config("alembic.ini")
    config.attributes["database_url"] = database_url
    command.upgrade(config, revision)
    return database_url
