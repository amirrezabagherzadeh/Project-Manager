import asyncio
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.core.database import Database
from app.models import ActivityLog, Notification, User, Workspace, WorkspaceMember, WorkspaceRole
from app.services.workspace import WorkspaceService
from tests.helpers import migrate_database


def test_workspace_creation_rolls_back_when_activity_write_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_url = migrate_database(tmp_path / "workspace-activity-rollback.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                owner = User(
                    email="owner@example.test",
                    name="Owner",
                    password_hash="private",
                )
                async with session.begin():
                    session.add(owner)
                service = WorkspaceService(session)

                async def fail_activity(_item):
                    raise RuntimeError("simulated activity failure")

                monkeypatch.setattr(service._effects, "activity", fail_activity)
                with pytest.raises(RuntimeError, match="simulated activity failure"):
                    await service.create(owner, name="Team", description=None)

                async with session.begin():
                    assert await session.scalar(select(func.count()).select_from(Workspace)) == 0
                    assert (
                        await session.scalar(select(func.count()).select_from(WorkspaceMember)) == 0
                    )
                    assert await session.scalar(select(func.count()).select_from(ActivityLog)) == 0
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_member_mutation_and_activity_roll_back_when_notification_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_url = migrate_database(tmp_path / "workspace-notification-rollback.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                owner = User(
                    email="owner@example.test",
                    name="Owner",
                    password_hash="private",
                )
                target = User(
                    email="target@example.test",
                    name="Target",
                    password_hash="private",
                )
                async with session.begin():
                    session.add_all([owner, target])
                service = WorkspaceService(session)
                workspace = await service.create(owner, name="Team", description=None)
                workspace_id = workspace.id
                target_email = target.email

                async def fail_notification(_item):
                    raise RuntimeError("simulated notification failure")

                monkeypatch.setattr(service._effects, "notification", fail_notification)
                with pytest.raises(RuntimeError, match="simulated notification failure"):
                    await service.add_member(
                        owner,
                        workspace_id,
                        email=target_email,
                        role=WorkspaceRole.MEMBER,
                    )

                async with session.begin():
                    members = await session.scalar(
                        select(func.count())
                        .select_from(WorkspaceMember)
                        .where(WorkspaceMember.workspace_id == workspace_id)
                    )
                    activities = (
                        await session.scalars(
                            select(ActivityLog).where(ActivityLog.workspace_id == workspace_id)
                        )
                    ).all()
                    notifications = await session.scalar(
                        select(func.count()).select_from(Notification)
                    )
                assert members == 1
                assert [item.action for item in activities] == ["workspace.created"]
                assert notifications == 0
                serialized = repr([item.details for item in activities]).lower()
                assert "password" not in serialized
                assert "token_hash" not in serialized
        finally:
            await database.dispose()

    asyncio.run(scenario())
