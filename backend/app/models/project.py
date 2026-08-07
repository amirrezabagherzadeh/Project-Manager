from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
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
from app.models.identity import User


class ProjectRole(StrEnum):
    MANAGER = "manager"
    MEMBER = "member"


project_role_type = Enum(
    ProjectRole,
    native_enum=False,
    length=20,
    name="project_role",
    validate_strings=True,
)

DEFAULT_COLUMN_NAMES: tuple[str, ...] = ("backlog", "todo", "doing", "review", "done")
DONE_COLUMN_NAME: str = "done"


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("workspace_id", "key", name="uq_projects_workspace_key"),
        Index("ix_projects_workspace_id", "workspace_id"),
        Index("ix_projects_archived_at", "archived_at"),
    )

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    key: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    start_date: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    members: Mapped[list["ProjectMember"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    columns: Mapped[list["BoardColumn"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="BoardColumn.position",
    )


class ProjectMember(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "user_id",
            name="uq_project_members_project_user",
        ),
        Index("ix_project_members_user_id", "user_id"),
        Index("ix_project_members_project_role", "project_id", "role"),
    )

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[ProjectRole] = mapped_column(project_role_type, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship()


class BoardColumn(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "board_columns"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "name",
            name="uq_board_columns_project_name",
        ),
        Index("ix_board_columns_project_position", "project_id", "position"),
        Index("ix_board_columns_archived_at", "archived_at"),
        CheckConstraint("position >= 0", name="ck_board_columns_position_non_negative"),
    )

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    position: Mapped[int] = mapped_column(Integer(), nullable=False)
    is_done: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    project: Mapped[Project] = relationship(back_populates="columns")
