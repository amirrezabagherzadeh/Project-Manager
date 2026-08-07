import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.core.database import Database
from app.core.exceptions import DomainError
from app.models import (
    ActivityLog,
    Notification,
    User,
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
)
from app.services.workspace import WorkspaceService
from tests.helpers import migrate_database


async def _users(session) -> tuple[User, User, User]:
    owner = User(email="owner@example.test", name="Owner", password_hash="private")
    admin = User(email="admin@example.test", name="Admin", password_hash="private")
    member = User(email="member@example.test", name="Member", password_hash="private")
    async with session.begin():
        session.add_all([owner, admin, member])
    return owner, admin, member


def _actor(user_id, email: str) -> User:
    return User(id=user_id, email=email, name="Actor", password_hash="private")


def test_workspace_lifecycle_is_atomic_scoped_and_role_enforced(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "workspace-service.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                owner, _admin, outsider = await _users(session)
                service = WorkspaceService(session)
                workspace = await service.create(
                    owner,
                    name="  تیم محصول  ",
                    description="  برنامه‌ریزی  ",
                )
                workspace_id = workspace.id
                owner_id = owner.id
                assert workspace.name == "تیم محصول"

                async with session.begin():
                    owners = await session.scalar(
                        select(func.count())
                        .select_from(WorkspaceMember)
                        .where(
                            WorkspaceMember.workspace_id == workspace.id,
                            WorkspaceMember.role == WorkspaceRole.OWNER,
                        )
                    )
                    activities = await session.scalar(select(func.count()).select_from(ActivityLog))
                assert owners == 1
                assert activities == 1

                visible, total = await service.list_workspaces(owner, page=1, page_size=20)
                assert total == 1 and visible[0].id == workspace.id
                assert (await service.read(owner, workspace.id)).id == workspace.id

                with pytest.raises(DomainError) as hidden:
                    await service.read(outsider, workspace.id)
                assert hidden.value.status_code == 404
                owner = _actor(owner_id, "owner@example.test")

                workspace = await service.archive(owner, workspace_id)
                assert workspace.archived_at is not None
                workspace = await service.restore(owner, workspace_id)
                assert workspace.archived_at is None

                await service.delete(owner, workspace_id)
                async with session.begin():
                    assert await session.get(Workspace, workspace_id) is None
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_member_management_and_ownership_transfer_preserve_invariants(
    tmp_path: Path,
) -> None:
    database_url = migrate_database(tmp_path / "workspace-members.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                owner, admin, member_user = await _users(session)
                service = WorkspaceService(session)
                workspace = await service.create(owner, name="Team", description=None)
                workspace_id = workspace.id
                owner_id = owner.id
                admin_id = admin.id
                member_user_id = member_user.id
                await service.add_member(
                    owner,
                    workspace.id,
                    email=admin.email,
                    role=WorkspaceRole.ADMIN,
                )
                member_membership = await service.add_member(
                    admin,
                    workspace.id,
                    email=member_user.email,
                    role=WorkspaceRole.MEMBER,
                )
                member_membership_id = member_membership.id

                with pytest.raises(DomainError) as duplicate:
                    await service.add_member(
                        owner,
                        workspace_id,
                        email=member_user.email,
                        role=WorkspaceRole.MEMBER,
                    )
                assert duplicate.value.status_code == 409
                owner = _actor(owner_id, "owner@example.test")
                member_user = _actor(member_user_id, "member@example.test")

                with pytest.raises(DomainError) as forbidden:
                    await service.add_member(
                        member_user,
                        workspace_id,
                        email="missing@example.test",
                        role=WorkspaceRole.MEMBER,
                    )
                assert forbidden.value.status_code == 403
                owner = _actor(owner_id, "owner@example.test")
                admin = _actor(admin_id, "admin@example.test")

                with pytest.raises(DomainError) as admin_owner:
                    await service.change_member_role(
                        admin,
                        workspace_id,
                        member_membership_id,
                        role=WorkspaceRole.OWNER,
                    )
                assert admin_owner.value.status_code == 403
                owner = _actor(owner_id, "owner@example.test")

                transferred = await service.change_member_role(
                    owner,
                    workspace_id,
                    member_membership_id,
                    role=WorkspaceRole.OWNER,
                )
                assert transferred.role == WorkspaceRole.OWNER
                async with session.begin():
                    stored_workspace = await session.get(Workspace, workspace_id)
                assert stored_workspace is not None
                assert stored_workspace.owner_id == member_user_id

                old_owner_membership = next(
                    item
                    for item in (
                        await service.list_members(
                            member_user,
                            workspace_id,
                            page=1,
                            page_size=20,
                        )
                    )[0]
                    if item.user_id == owner_id
                )
                assert old_owner_membership.role == WorkspaceRole.ADMIN
                with pytest.raises(DomainError) as remove_owner:
                    await service.remove_member(
                        owner,
                        workspace_id,
                        transferred.id,
                    )
                assert remove_owner.value.code == "invalid_operation"

                async with session.begin():
                    notifications = await session.scalar(
                        select(func.count()).select_from(Notification)
                    )
                assert notifications == 2
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_invitation_token_is_hashed_and_acceptance_is_single_use(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "workspace-invitation.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                owner, _admin, invited = await _users(session)
                service = WorkspaceService(session)
                workspace = await service.create(owner, name="Team", description=None)
                invited_id = invited.id
                created = await service.create_invitation(
                    owner,
                    workspace.id,
                    email=" MEMBER@EXAMPLE.TEST ",
                    role=WorkspaceRole.PROJECT_MANAGER,
                )
                assert created.invitation.token_hash != created.token
                assert created.invitation.token_hash == service.hash_invitation_token(created.token)
                assert created.invitation.email == "member@example.test"

                with pytest.raises(DomainError) as mismatch:
                    await service.accept_invitation(owner, created.token)
                assert mismatch.value.status_code == 404
                invited = _actor(invited_id, "member@example.test")

                membership = await service.accept_invitation(invited, created.token)
                assert membership.role == WorkspaceRole.PROJECT_MANAGER
                with pytest.raises(DomainError) as reused:
                    await service.accept_invitation(invited, created.token)
                assert reused.value.status_code == 409
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_expired_and_revoked_invitations_are_rejected(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "workspace-invalid-invitation.db")
    now = datetime.now(UTC).replace(microsecond=0)

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                owner, admin, invited = await _users(session)
                service = WorkspaceService(session, clock=lambda: now)
                workspace = await service.create(owner, name="Team", description=None)
                workspace_id = workspace.id
                owner_id = owner.id
                admin_id = admin.id
                invited_id = invited.id
                await service.add_member(
                    owner,
                    workspace.id,
                    email=admin.email,
                    role=WorkspaceRole.ADMIN,
                )
                expired = await service.create_invitation(
                    admin,
                    workspace.id,
                    email=invited.email,
                    role=WorkspaceRole.MEMBER,
                )
                service = WorkspaceService(session, clock=lambda: now + timedelta(days=8))
                with pytest.raises(DomainError) as expired_error:
                    await service.accept_invitation(invited, expired.token)
                assert expired_error.value.status_code == 404
                owner = _actor(owner_id, "owner@example.test")
                admin = _actor(admin_id, "admin@example.test")
                invited = _actor(invited_id, "member@example.test")

                replacement = await service.create_invitation(
                    admin,
                    workspace_id,
                    email=invited.email,
                    role=WorkspaceRole.MEMBER,
                )
                await service.revoke_invitation(
                    owner,
                    workspace_id,
                    replacement.invitation.id,
                )
                with pytest.raises(DomainError) as revoked:
                    await service.accept_invitation(invited, replacement.token)
                assert revoked.value.status_code == 404
        finally:
            await database.dispose()

    asyncio.run(scenario())
