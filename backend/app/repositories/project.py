from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.identity import User
from app.models.project import BoardColumn, Project, ProjectMember
from app.models.workspace import ActivityLog, Notification, WorkspaceMember


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, project: Project) -> Project:
        self._session.add(project)
        await self._session.flush()
        return project

    async def get(self, project_id: UUID) -> Project | None:
        return await self._session.get(Project, project_id)

    async def get_with_columns(self, project_id: UUID) -> Project | None:
        statement = (
            select(Project).where(Project.id == project_id).options(selectinload(Project.columns))
        )
        return cast(Project | None, await self._session.scalar(statement))

    async def get_with_members(self, project_id: UUID) -> Project | None:
        statement = (
            select(Project).where(Project.id == project_id).options(selectinload(Project.members))
        )
        return cast(Project | None, await self._session.scalar(statement))

    async def get_by_key(
        self,
        workspace_id: UUID,
        key: str,
    ) -> Project | None:
        statement = select(Project).where(
            Project.workspace_id == workspace_id,
            Project.key == key,
        )
        return cast(Project | None, await self._session.scalar(statement))

    async def list_for_workspace(
        self,
        workspace_id: UUID,
        *,
        include_archived: bool,
        offset: int,
        limit: int,
    ) -> tuple[list[Project], int]:
        predicate = Project.workspace_id == workspace_id
        if not include_archived:
            predicate = predicate & Project.archived_at.is_(None)
        total = await self._session.scalar(
            select(func.count()).select_from(Project).where(predicate)
        )
        statement = (
            select(Project)
            .where(predicate)
            .order_by(Project.created_at.desc(), Project.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all()), int(total or 0)


class ProjectMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, member: ProjectMember) -> ProjectMember:
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member, ["user"])
        return member

    async def get(self, project_id: UUID, user_id: UUID) -> ProjectMember | None:
        statement = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        return cast(ProjectMember | None, await self._session.scalar(statement))

    async def get_by_id(
        self,
        project_id: UUID,
        member_id: UUID,
    ) -> ProjectMember | None:
        statement = (
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.id == member_id,
            )
            .options(selectinload(ProjectMember.user))
        )
        return cast(ProjectMember | None, await self._session.scalar(statement))

    async def list(
        self,
        project_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[ProjectMember], int]:
        predicate = ProjectMember.project_id == project_id
        total = await self._session.scalar(
            select(func.count()).select_from(ProjectMember).where(predicate)
        )
        statement = (
            select(ProjectMember)
            .where(predicate)
            .options(selectinload(ProjectMember.user))
            .order_by(ProjectMember.joined_at, ProjectMember.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all()), int(total or 0)

    async def delete(self, member: ProjectMember) -> None:
        await self._session.delete(member)
        await self._session.flush()


class BoardColumnRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, column: BoardColumn) -> BoardColumn:
        self._session.add(column)
        await self._session.flush()
        return column

    async def get(self, column_id: UUID) -> BoardColumn | None:
        return await self._session.get(BoardColumn, column_id)

    async def get_by_project(
        self,
        project_id: UUID,
        column_id: UUID,
    ) -> BoardColumn | None:
        statement = select(BoardColumn).where(
            BoardColumn.project_id == project_id,
            BoardColumn.id == column_id,
        )
        return cast(BoardColumn | None, await self._session.scalar(statement))

    async def list_active(
        self,
        project_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[BoardColumn], int]:
        predicate = (BoardColumn.project_id == project_id) & BoardColumn.archived_at.is_(None)
        total = await self._session.scalar(
            select(func.count()).select_from(BoardColumn).where(predicate)
        )
        statement = (
            select(BoardColumn)
            .where(predicate)
            .order_by(BoardColumn.position, BoardColumn.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all()), int(total or 0)

    async def list_all_active(self, project_id: UUID) -> list[BoardColumn]:
        statement = (
            select(BoardColumn)
            .where(
                BoardColumn.project_id == project_id,
                BoardColumn.archived_at.is_(None),
            )
            .order_by(BoardColumn.position, BoardColumn.id)
        )
        return list((await self._session.scalars(statement)).all())

    async def next_position(self, project_id: UUID) -> int:
        statement = select(func.max(BoardColumn.position)).where(
            BoardColumn.project_id == project_id,
            BoardColumn.archived_at.is_(None),
        )
        value = await self._session.scalar(statement)
        return int(value) + 1 if value is not None else 0


class ProjectUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._session.get(User, user_id)


class ProjectSideEffectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def activity(self, item: ActivityLog) -> ActivityLog:
        self._session.add(item)
        await self._session.flush()
        return item

    async def notification(self, item: Notification) -> Notification:
        self._session.add(item)
        await self._session.flush()
        return item


class WorkspaceLookupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_membership(
        self,
        workspace_id: UUID,
        user_id: UUID,
    ) -> WorkspaceMember | None:
        statement = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        return cast(WorkspaceMember | None, await self._session.scalar(statement))
