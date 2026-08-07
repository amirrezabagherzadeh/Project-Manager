import asyncio
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.core.database import Database
from app.models import (
    ActivityLog,
    Notification,
    Project,
    ProjectMember,
    ProjectRole,
    User,
    WorkspaceRole,
)
from app.services.project import ProjectService
from app.services.workspace import WorkspaceService
from tests.helpers import migrate_database


def test_project_creation_rolls_back_when_activity_write_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_url = migrate_database(tmp_path / "project-side-effect-rollback.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                owner = User(
                    email="owner@example.test",
                    name="Owner",
                    password_hash="private",
                )
                workspace_service = WorkspaceService(session)
                async with session.begin():
                    session.add(owner)
                workspace = await workspace_service.create(owner, name="Team", description=None)
                service = ProjectService(session)

                async def fail_activity(_item):
                    raise RuntimeError("simulated activity failure")

                monkeypatch.setattr(service._effects, "activity", fail_activity)
                with pytest.raises(RuntimeError, match="simulated activity failure"):
                    await service.create_project(owner, workspace.id, name="Team", key="TM")

                async with session.begin():
                    assert await session.scalar(select(func.count()).select_from(Project)) == 0
                    assert (
                        await session.scalar(select(func.count()).select_from(ProjectMember)) == 0
                    )
                    project_activity = await session.scalar(
                        select(func.count())
                        .select_from(ActivityLog)
                        .where(ActivityLog.action == "project.created")
                    )
                    assert project_activity == 0
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_project_member_notification_and_activity_are_durable_and_private(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_url = migrate_database(tmp_path / "project-side-effect-durable.db")

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
                other = User(
                    email="other@example.test",
                    name="Other",
                    password_hash="private",
                )
                workspace_service = WorkspaceService(session)
                async with session.begin():
                    session.add_all([owner, target, other])
                    await session.flush()
                    target_id = target.id
                    other_id = other.id
                workspace = await workspace_service.create(owner, name="Team", description=None)
                workspace_id = workspace.id
                await workspace_service.add_member(
                    owner,
                    workspace_id,
                    email="target@example.test",
                    role=WorkspaceRole.MEMBER,
                )
                await workspace_service.add_member(
                    owner,
                    workspace_id,
                    email="other@example.test",
                    role=WorkspaceRole.MEMBER,
                )
                service = ProjectService(session)
                project = await service.create_project(owner, workspace_id, name="Team", key="TM")
                project_id = project.id

                await service.add_project_member(
                    owner,
                    project_id,
                    user_id=target_id,
                    role=ProjectRole.MEMBER,
                )

                async with session.begin():
                    notifications = (
                        await session.scalars(
                            select(Notification).where(
                                Notification.user_id == target_id,
                                Notification.type == "project.member_added",
                            )
                        )
                    ).all()
                    activities = (
                        await session.scalars(
                            select(ActivityLog).where(
                                ActivityLog.workspace_id == workspace_id,
                                ActivityLog.entity_type == "project",
                            )
                        )
                    ).all()
                assert len(notifications) == 1
                assert notifications[0].type == "project.member_added"
                assert notifications[0].entity_type == "project"
                assert notifications[0].entity_id == project_id
                assert [item.action for item in activities] == [
                    "project.created",
                    "project.member_added",
                ]
                serialized = repr([item.details for item in activities]).lower()
                assert "password" not in serialized
                assert "token_hash" not in serialized
                assert "refresh_token" not in serialized

                async def fail_notification(_item):
                    raise RuntimeError("simulated notification failure")

                monkeypatch.setattr(service._effects, "notification", fail_notification)
                with pytest.raises(RuntimeError, match="simulated notification failure"):
                    await service.add_project_member(
                        owner,
                        project_id,
                        user_id=other_id,
                        role=ProjectRole.MEMBER,
                    )

                async with session.begin():
                    members = await session.scalar(
                        select(func.count())
                        .select_from(ProjectMember)
                        .where(ProjectMember.project_id == project_id)
                    )
                    project_notifications_after = await session.scalar(
                        select(func.count())
                        .select_from(Notification)
                        .where(Notification.type == "project.member_added")
                    )
                assert members == 2
                assert project_notifications_after == 1
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_project_column_reorder_records_activity_without_hashes(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "project-side-effect-reorder.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                owner = User(
                    email="owner@example.test",
                    name="Owner",
                    password_hash="private",
                )
                workspace_service = WorkspaceService(session)
                async with session.begin():
                    session.add(owner)
                workspace = await workspace_service.create(owner, name="Team", description=None)
                service = ProjectService(session)
                project = await service.create_project(owner, workspace.id, name="Team", key="TM")
                project_id = project.id

                columns, _total = await service.list_columns(
                    owner,
                    project_id,
                    page=1,
                    page_size=20,
                )
                column_ids = [column.id for column in columns]
                await service.reorder_columns(owner, project_id, column_ids[::-1])

                async with session.begin():
                    reorder_activity = await session.scalar(
                        select(ActivityLog).where(ActivityLog.action == "project.columns_reordered")
                    )
                assert reorder_activity is not None
                assert reorder_activity.entity_type == "project"
                serialized = repr(reorder_activity.details).lower()
                assert "password" not in serialized
                assert "token_hash" not in serialized
        finally:
            await database.dispose()

    asyncio.run(scenario())
