from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import normalize_email
from app.models.identity import RefreshSession, User


class RefreshChainLimitError(RuntimeError):
    pass


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == normalize_email(email))
        return cast(User | None, await self._session.scalar(statement))

    async def add(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user


class RefreshSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_token_hash(self, token_hash: str) -> RefreshSession | None:
        statement = (
            select(RefreshSession)
            .where(RefreshSession.token_hash == token_hash)
            .options(selectinload(RefreshSession.user))
        )
        return cast(RefreshSession | None, await self._session.scalar(statement))

    async def get_by_id_for_user(
        self,
        session_id: UUID,
        user_id: UUID,
    ) -> RefreshSession | None:
        statement = select(RefreshSession).where(
            RefreshSession.id == session_id,
            RefreshSession.user_id == user_id,
        )
        return cast(RefreshSession | None, await self._session.scalar(statement))

    async def add(self, refresh_session: RefreshSession) -> RefreshSession:
        self._session.add(refresh_session)
        await self._session.flush()
        return refresh_session

    async def link_replacement(
        self,
        current: RefreshSession,
        replacement: RefreshSession,
    ) -> None:
        current.replaced_by_id = replacement.id
        await self._session.flush()

    async def get_replacement_chain(
        self,
        start: RefreshSession,
        *,
        max_depth: int = 32,
    ) -> list[RefreshSession]:
        chain = [start]
        current = start
        for _ in range(max_depth - 1):
            if current.replaced_by_id is None:
                return chain
            replacement = await self.get_by_id_for_user(
                current.replaced_by_id,
                current.user_id,
            )
            if replacement is None:
                return chain
            chain.append(replacement)
            current = replacement
        if current.replaced_by_id is not None:
            raise RefreshChainLimitError("Refresh replacement chain exceeds limit")
        return chain

    async def revoke_active_for_user(
        self,
        user_id: UUID,
        *,
        revoked_at: datetime,
    ) -> None:
        statement = (
            update(RefreshSession)
            .where(
                RefreshSession.user_id == user_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self._session.execute(statement)
        await self._session.flush()
