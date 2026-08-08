from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.models.task import Task
from app.repositories.reporting import _count_where


def test_conditional_count_compiles_for_postgresql() -> None:
    statement = select(_count_where(Task.completed_at.is_not(None)))

    sql = str(statement.compile(dialect=postgresql.dialect()))

    assert "sum(CASE WHEN" in sql
    assert "sum(tasks.completed_at IS NOT NULL)" not in sql
