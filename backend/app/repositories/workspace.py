from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import normalize_email
from app.models.identity import User
from app.models.workspace import (
    ActivityLog,
    Notification,
    Workspace,
    WorkspaceInvitation,
    WorkspaceMember,
)


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, workspace: Workspace) -> Workspace:
        self._session.add(workspace)
        await self._session.flush()
        return workspace

    async def get(self, workspace_id: UUID) -> Workspace | None:
        return await self._session.get(Workspace, workspace_id)

    async def get_with_members(self, workspace_id: UUID) -> Workspace | None:
        statement = (
            select(Workspace)
            .where(Workspace.id == workspace_id)
            .options(selectinload(Workspace.members))
        )
        return cast(Workspace | None, await self._session.scalar(statement))

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        offset: int,
        limit: int,
        include_archived: bool = False,
    ) -> tuple[list[Workspace], int]:
        predicate = WorkspaceMember.user_id == user_id
        if not include_archived:
            predicate = predicate & Workspace.archived_at.is_(None)
        scope = select(Workspace.id).join(WorkspaceMember).where(predicate)
        total = await self._session.scalar(select(func.count()).select_from(scope.subquery()))
        statement = (
            select(Workspace)
            .join(WorkspaceMember)
            .where(predicate)
            .order_by(Workspace.created_at.desc(), Workspace.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all()), int(total or 0)

    async def delete(self, workspace: Workspace) -> None:
        await self._session.delete(workspace)
        await self._session.flush()


class WorkspaceMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, member: WorkspaceMember) -> WorkspaceMember:
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member, ["user"])
        return member

    async def get(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        statement = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        return cast(WorkspaceMember | None, await self._session.scalar(statement))

    async def get_by_id(
        self,
        workspace_id: UUID,
        member_id: UUID,
    ) -> WorkspaceMember | None:
        statement = (
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.id == member_id,
            )
            .options(selectinload(WorkspaceMember.user))
        )
        return cast(WorkspaceMember | None, await self._session.scalar(statement))

    async def list(
        self,
        workspace_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[WorkspaceMember], int]:
        predicate = WorkspaceMember.workspace_id == workspace_id
        total = await self._session.scalar(
            select(func.count()).select_from(WorkspaceMember).where(predicate)
        )
        statement = (
            select(WorkspaceMember)
            .where(predicate)
            .options(selectinload(WorkspaceMember.user))
            .order_by(WorkspaceMember.joined_at, WorkspaceMember.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all()), int(total or 0)

    async def delete(self, member: WorkspaceMember) -> None:
        await self._session.delete(member)
        await self._session.flush()


class WorkspaceInvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, invitation: WorkspaceInvitation) -> WorkspaceInvitation:
        self._session.add(invitation)
        await self._session.flush()
        return invitation

    async def get_by_id(
        self,
        workspace_id: UUID,
        invitation_id: UUID,
    ) -> WorkspaceInvitation | None:
        statement = select(WorkspaceInvitation).where(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.id == invitation_id,
        )
        return cast(WorkspaceInvitation | None, await self._session.scalar(statement))

    async def get_by_hash(self, token_hash: str) -> WorkspaceInvitation | None:
        statement = select(WorkspaceInvitation).where(WorkspaceInvitation.token_hash == token_hash)
        return cast(WorkspaceInvitation | None, await self._session.scalar(statement))

    async def get_by_email(
        self,
        workspace_id: UUID,
        email: str,
    ) -> WorkspaceInvitation | None:
        statement = select(WorkspaceInvitation).where(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.email == normalize_email(email),
        )
        return cast(WorkspaceInvitation | None, await self._session.scalar(statement))

    async def list(
        self,
        workspace_id: UUID,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[WorkspaceInvitation], int]:
        predicate = WorkspaceInvitation.workspace_id == workspace_id
        total = await self._session.scalar(
            select(func.count()).select_from(WorkspaceInvitation).where(predicate)
        )
        statement = (
            select(WorkspaceInvitation)
            .where(predicate)
            .order_by(WorkspaceInvitation.created_at.desc(), WorkspaceInvitation.id)
            .offset(offset)
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all()), int(total or 0)

    async def remove_expired_for_email(
        self,
        workspace_id: UUID,
        email: str,
        *,
        now: datetime,
    ) -> None:
        statement = delete(WorkspaceInvitation).where(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.email == normalize_email(email),
            WorkspaceInvitation.expires_at <= now,
            WorkspaceInvitation.accepted_at.is_(None),
        )
        await self._session.execute(statement)
        await self._session.flush()


class SideEffectRepository:
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


class WorkspaceUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == normalize_email(email))
        return cast(User | None, await self._session.scalar(statement))

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._session.get(User, user_id)
