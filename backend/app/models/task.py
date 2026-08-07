from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UTCDateTime, UUIDPrimaryKeyMixin


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


task_priority_type = Enum(TaskPriority, native_enum=False, length=20, name="task_priority")


class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_tasks_position_non_negative"),
        CheckConstraint("version >= 1", name="ck_tasks_version_positive"),
        Index("ix_tasks_project_column_position", "project_id", "column_id", "position"),
        Index("ix_tasks_project_archived", "project_id", "archived_at"),
        Index("ix_tasks_project_due", "project_id", "due_at"),
        Index("ix_tasks_parent_id", "parent_id"),
    )

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    column_id: Mapped[UUID] = mapped_column(
        ForeignKey("board_columns.id", ondelete="RESTRICT"), nullable=False
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    priority: Mapped[TaskPriority] = mapped_column(
        task_priority_type, nullable=False, default=TaskPriority.MEDIUM
    )
    position: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    version: Mapped[int] = mapped_column(Integer(), nullable=False, default=1)
    due_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    assignees: Mapped[list["TaskAssignee"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", passive_deletes=True
    )
    task_labels: Mapped[list["TaskLabel"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", passive_deletes=True
    )
    parent: Mapped["Task | None"] = relationship(back_populates="subtasks", remote_side="Task.id")
    subtasks: Mapped[list["Task"]] = relationship(back_populates="parent")


class TaskAssignee(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "task_assignees"
    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="uq_task_assignees_task_user"),
        Index("ix_task_assignees_user_id", "user_id"),
    )
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    task: Mapped[Task] = relationship(back_populates="assignees")


class Label(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "labels"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_labels_project_name"),
        Index("ix_labels_project_archived", "project_id", "archived_at"),
    )
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    task_labels: Mapped[list["TaskLabel"]] = relationship(
        back_populates="label", cascade="all, delete-orphan", passive_deletes=True
    )


class TaskLabel(Base):
    __tablename__ = "task_labels"
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    label_id: Mapped[UUID] = mapped_column(
        ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True
    )
    task: Mapped[Task] = relationship(back_populates="task_labels")
    label: Mapped[Label] = relationship(back_populates="task_labels")
