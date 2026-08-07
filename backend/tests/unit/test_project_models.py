from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.models import (
    DEFAULT_COLUMN_NAMES,
    DONE_COLUMN_NAME,
    BoardColumn,
    Project,
    ProjectMember,
    ProjectRole,
)
from app.models.base import UTCDateTime


def _constraint_names(table_name: str, kind: type) -> set[str | None]:
    return {
        constraint.name
        for constraint in Project.metadata.tables[table_name].constraints
        if isinstance(constraint, kind)
    }


def _index_names(table_name: str) -> set[str | None]:
    return {
        index.name
        for index in Project.metadata.tables[table_name].indexes
        if isinstance(index, Index)
    }


def test_project_role_values_are_stable() -> None:
    assert {role.value for role in ProjectRole} == {"manager", "member"}


def test_default_column_names_are_fixed() -> None:
    assert DEFAULT_COLUMN_NAMES == ("backlog", "todo", "doing", "review", "done")
    assert DONE_COLUMN_NAME == "done"


def test_project_invariants_are_declared() -> None:
    table = Project.__table__
    assert table.c.workspace_id.nullable is False
    assert table.c.key.type.length == 20
    assert table.c.is_private.nullable is False
    assert isinstance(table.c.start_date.type, UTCDateTime)
    assert isinstance(table.c.due_date.type, UTCDateTime)
    assert isinstance(table.c.archived_at.type, UTCDateTime)
    assert "uq_projects_workspace_key" in _constraint_names("projects", UniqueConstraint)
    assert {
        "ix_projects_workspace_id",
        "ix_projects_archived_at",
    }.issubset(_index_names("projects"))
    assert Project.members.property.cascade.delete_orphan is True
    assert Project.columns.property.cascade.delete_orphan is True
    assert Project.columns.property.passive_deletes is True


def test_project_member_invariants_are_declared() -> None:
    table = ProjectMember.__table__
    assert table.c.project_id.nullable is False
    assert table.c.user_id.nullable is False
    assert "uq_project_members_project_user" in _constraint_names(
        "project_members", UniqueConstraint
    )
    assert {
        "ix_project_members_user_id",
        "ix_project_members_project_role",
    }.issubset(_index_names("project_members"))
    assert isinstance(table.c.joined_at.type, UTCDateTime)


def test_board_column_invariants_are_declared() -> None:
    table = BoardColumn.__table__
    assert table.c.position.nullable is False
    assert table.c.is_done.nullable is False
    assert "uq_board_columns_project_name" in _constraint_names("board_columns", UniqueConstraint)
    assert "ck_board_columns_position_non_negative" in _constraint_names(
        "board_columns", CheckConstraint
    )
    assert {
        "ix_board_columns_project_position",
        "ix_board_columns_archived_at",
    }.issubset(_index_names("board_columns"))
    assert isinstance(table.c.archived_at.type, UTCDateTime)
