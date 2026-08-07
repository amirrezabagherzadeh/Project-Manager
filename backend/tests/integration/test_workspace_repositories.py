import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select

from app.core.database import Database
from app.models import User, Workspace, WorkspaceInvitation, WorkspaceMember, WorkspaceRole
from app.repositories.workspace import (
    WorkspaceInvitationRepository,
    WorkspaceMemberRepository,
    WorkspaceRepository,
    WorkspaceUserRepository,
)
from tests.helpers import migrate_database


def test_workspace_repositories_scope_paginate_normalize_and_do_not_commit(
    tmp_path: Path,
) -> None:
    database_url = migrate_database(tmp_path / "workspace-repositories.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                commits = 0
                original_commit = session.commit

                async def tracked_commit() -> None:
                    nonlocal commits
                    commits += 1
                    await original_commit()

                session.commit = tracked_commit  # type: ignore[method-assign]
                now = datetime.now(UTC)
                owner = User(
                    email="owner@example.test",
                    name="Owner",
                    password_hash="private",
                )
                outsider = User(
                    email="outsider@example.test",
                    name="Outsider",
                    password_hash="private",
                )
                session.add_all([owner, outsider])
                await session.flush()

                workspaces = WorkspaceRepository(session)
                members = WorkspaceMemberRepository(session)
                invitations = WorkspaceInvitationRepository(session)
                users = WorkspaceUserRepository(session)

                first = await workspaces.add(Workspace(name="First", owner_id=owner.id))
                second = await workspaces.add(Workspace(name="Second", owner_id=outsider.id))
                await members.add(
                    WorkspaceMember(
                        workspace_id=first.id,
                        user_id=owner.id,
                        role=WorkspaceRole.OWNER,
                        joined_at=now,
                    )
                )
                await members.add(
                    WorkspaceMember(
                        workspace_id=second.id,
                        user_id=outsider.id,
                        role=WorkspaceRole.OWNER,
                        joined_at=now,
                    )
                )
                invitation = await invitations.add(
                    WorkspaceInvitation(
                        workspace_id=first.id,
                        email="invite@example.test",
                        role=WorkspaceRole.MEMBER,
                        token_hash="a" * 64,
                        invited_by_id=owner.id,
                        created_at=now,
                        expires_at=now + timedelta(days=7),
                    )
                )

                visible, total = await workspaces.list_for_user(
                    owner.id,
                    offset=0,
                    limit=1,
                )
                assert [item.id for item in visible] == [first.id]
                assert total == 1
                assert (await members.get(first.id, outsider.id)) is None
                assert (await invitations.get_by_id(second.id, invitation.id)) is None
                assert (
                    await invitations.get_by_email(first.id, " INVITE@EXAMPLE.TEST ")
                ).id == invitation.id
                assert (await users.get_by_email(" OWNER@EXAMPLE.TEST ")).id == owner.id
                assert commits == 0

                await session.rollback()
                count = await session.scalar(select(func.count()).select_from(Workspace))
                assert count == 0
        finally:
            await database.dispose()

    asyncio.run(scenario())
