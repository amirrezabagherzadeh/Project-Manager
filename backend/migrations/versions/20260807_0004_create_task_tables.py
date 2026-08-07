"""Create task core tables.

Revision ID: 20260807_0004
Revises: 20260729_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260807_0004"
down_revision: str | None = "20260729_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

priority = sa.Enum(
    "low", "medium", "high", "urgent", name="task_priority", native_enum=False, length=20
)


def upgrade() -> None:
    op.create_table(
        "labels",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("color", sa.String(20)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "name", name="uq_labels_project_name"),
    )
    op.create_index("ix_labels_project_archived", "labels", ["project_id", "archived_at"])
    op.create_table(
        "tasks",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("column_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid()),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("priority", priority, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_tasks_position_non_negative"),
        sa.CheckConstraint("version >= 1", name="ck_tasks_version_positive"),
        sa.ForeignKeyConstraint(["column_id"], ["board_columns.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tasks_project_column_position", "tasks", ["project_id", "column_id", "position"]
    )
    op.create_index("ix_tasks_project_archived", "tasks", ["project_id", "archived_at"])
    op.create_index("ix_tasks_project_due", "tasks", ["project_id", "due_at"])
    op.create_index("ix_tasks_parent_id", "tasks", ["parent_id"])
    op.create_table(
        "task_assignees",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "user_id", name="uq_task_assignees_task_user"),
    )
    op.create_index("ix_task_assignees_user_id", "task_assignees", ["user_id"])
    op.create_table(
        "task_labels",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("label_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["label_id"], ["labels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("task_id", "label_id"),
    )


def downgrade() -> None:
    op.drop_table("task_labels")
    op.drop_index("ix_task_assignees_user_id", table_name="task_assignees")
    op.drop_table("task_assignees")
    for name in (
        "ix_tasks_parent_id",
        "ix_tasks_project_due",
        "ix_tasks_project_archived",
        "ix_tasks_project_column_position",
    ):
        op.drop_index(name, table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_labels_project_archived", table_name="labels")
    op.drop_table("labels")
