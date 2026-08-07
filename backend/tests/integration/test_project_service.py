import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.core.database import Database
from app.core.exceptions import DomainError
from app.models import (
    ActivityLog,
    BoardColumn,
    Notification,
    Project,
    ProjectMember,
    ProjectRole,
    User,
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
)
from app.services.project import ProjectService
from tests.helpers import migrate_database

EMAILS = {
    "owner": "owner@example.test",
    "admin": "admin@example.test",
    "pm": "pm@example.test",
    "member": "member@example.test",
}


@dataclass(frozen=True)
class Seed:
    workspace_id: UUID
    owner_id: UUID
    admin_id: UUID
    pm_id: UUID
    member_id: UUID


def _actor(seed: Seed, who: str) -> User:
    return User(
        id=getattr(seed, f"{who}_id"),
        email=EMAILS[who],
        name=who.title(),
        password_hash="private",
    )


async def _seed_workspace(
    session,
    *,
    with_member: bool = False,
    with_pm: bool = False,
    with_admin: bool = False,
) -> Seed:
    owner = User(email="owner@example.test", name="Owner", password_hash="private")
    admin = User(email="admin@example.test", name="Admin", password_hash="private")
    pm = User(email="pm@example.test", name="Manager", password_hash="private")
    member = User(email="member@example.test", name="Member", password_hash="private")
    async with session.begin():
        session.add_all([owner, admin, pm, member])
        await session.flush()
        workspace = Workspace(name="Team", owner_id=owner.id)
        session.add(workspace)
        await session.flush()
        now = datetime.now(UTC)
        memberships = [
            (owner.id, WorkspaceRole.OWNER),
            (admin.id, WorkspaceRole.ADMIN) if with_admin else None,
            (pm.id, WorkspaceRole.PROJECT_MANAGER) if with_pm else None,
            (member.id, WorkspaceRole.MEMBER) if with_member else None,
        ]
        for entry in memberships:
            if entry is None:
                continue
            user_id, role = entry
            session.add(
                WorkspaceMember(
                    workspace_id=workspace.id,
                    user_id=user_id,
                    role=role,
                    joined_at=now,
                )
            )
        return Seed(
            owner_id=owner.id,
            admin_id=admin.id,
            pm_id=pm.id,
            member_id=member.id,
            workspace_id=workspace.id,
        )


def _outsider() -> User:
    return User(id=uuid4(), email="outside@example.test", name="Outside", password_hash="private")


def test_project_creation_is_atomic_with_creator_manager_and_default_columns(
    tmp_path: Path,
) -> None:
    database_url = migrate_database(tmp_path / "project-service-create.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                seed = await _seed_workspace(session, with_member=True)
                service = ProjectService(session)
                project = await service.create_project(
                    _actor(seed, "owner"),
                    seed.workspace_id,
                    name="  تیم محصول  ",
                    key="PM",
                )
                project_id = project.id
                assert project.name == "تیم محصول"
                assert project.key == "PM"

                async with session.begin():
                    creator_membership = await session.scalar(
                        select(ProjectMember).where(
                            ProjectMember.project_id == project_id,
                            ProjectMember.user_id == seed.owner_id,
                        )
                    )
                    columns = (
                        await session.scalars(
                            select(BoardColumn)
                            .where(BoardColumn.project_id == project_id)
                            .order_by(BoardColumn.position)
                        )
                    ).all()
                    activities = await session.scalar(select(func.count()).select_from(ActivityLog))
                assert creator_membership is not None
                assert creator_membership.role == ProjectRole.MANAGER
                assert [column.name for column in columns] == [
                    "backlog",
                    "todo",
                    "doing",
                    "review",
                    "done",
                ]
                assert [column.position for column in columns] == [0, 1, 2, 3, 4]
                assert [column.is_done for column in columns] == [False, False, False, False, True]
                assert activities == 1

                with pytest.raises(DomainError) as duplicate:
                    await service.create_project(
                        _actor(seed, "owner"),
                        seed.workspace_id,
                        name="Duplicate",
                        key="PM",
                    )
                assert duplicate.value.status_code == 409
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_project_lifecycle_is_permission_scoped(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "project-service-lifecycle.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                seed = await _seed_workspace(
                    session,
                    with_member=True,
                    with_pm=True,
                    with_admin=True,
                )
                service = ProjectService(session)
                project = await service.create_project(
                    _actor(seed, "owner"),
                    seed.workspace_id,
                    name="Product",
                    key="PD",
                )
                project_id = project.id

                with pytest.raises(DomainError) as forbidden_create:
                    await service.create_project(
                        _actor(seed, "member"),
                        seed.workspace_id,
                        name="Forbidden",
                        key="FB",
                    )
                assert forbidden_create.value.status_code == 403

                owner_read = await service.read_project(_actor(seed, "owner"), project_id)
                assert owner_read.id == project_id
                member_read = await service.read_project(_actor(seed, "member"), project_id)
                assert member_read.id == project_id

                with pytest.raises(DomainError) as hidden:
                    await service.read_project(_outsider(), project_id)
                assert hidden.value.status_code == 404

                with pytest.raises(DomainError) as forbidden_update:
                    await service.update_project(_actor(seed, "member"), project_id, name="Nope")
                assert forbidden_update.value.status_code == 403

                updated = await service.update_project(
                    _actor(seed, "pm"),
                    project_id,
                    name="Product 2",
                )
                assert updated.name == "Product 2"

                archived = await service.archive_project(_actor(seed, "pm"), project_id)
                assert archived.archived_at is not None

                visible, total = await service.list_projects(
                    _actor(seed, "member"),
                    seed.workspace_id,
                    page=1,
                    page_size=20,
                )
                assert total == 0 and visible == []
                with_archived, total_with = await service.list_projects(
                    _actor(seed, "member"),
                    seed.workspace_id,
                    page=1,
                    page_size=20,
                    include_archived=True,
                )
                assert total_with == 1 and with_archived[0].id == project_id

                restored = await service.restore_project(_actor(seed, "owner"), project_id)
                assert restored.archived_at is None
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_private_project_access_is_enumeration_safe(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "project-service-private.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                seed = await _seed_workspace(session, with_member=True)
                service = ProjectService(session)
                project = await service.create_project(
                    _actor(seed, "owner"),
                    seed.workspace_id,
                    name="Private",
                    key="PVT",
                    is_private=True,
                )
                project_id = project.id

                with pytest.raises(DomainError) as hidden:
                    await service.read_project(_actor(seed, "member"), project_id)
                assert hidden.value.status_code == 404

                with pytest.raises(DomainError) as hidden_update:
                    await service.update_project(_actor(seed, "member"), project_id, name="Nope")
                assert hidden_update.value.status_code == 404

                added = await service.add_project_member(
                    _actor(seed, "owner"),
                    project_id,
                    user_id=seed.member_id,
                    role=ProjectRole.MEMBER,
                )
                assert added.role == ProjectRole.MEMBER

                member_read = await service.read_project(_actor(seed, "member"), project_id)
                assert member_read.id == project_id
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_project_member_management_enforces_workspace_membership_and_roles(
    tmp_path: Path,
) -> None:
    database_url = migrate_database(tmp_path / "project-service-members.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                seed = await _seed_workspace(session, with_member=True, with_pm=True)
                service = ProjectService(session)
                project = await service.create_project(
                    _actor(seed, "owner"),
                    seed.workspace_id,
                    name="Team",
                    key="TM",
                )
                project_id = project.id

                with pytest.raises(DomainError) as not_in_workspace:
                    await service.add_project_member(
                        _actor(seed, "owner"),
                        project_id,
                        user_id=uuid4(),
                        role=ProjectRole.MEMBER,
                    )
                assert not_in_workspace.value.status_code == 404

                added = await service.add_project_member(
                    _actor(seed, "owner"),
                    project_id,
                    user_id=seed.member_id,
                    role=ProjectRole.MEMBER,
                )
                added_id = added.id
                assert added.user_id == seed.member_id

                with pytest.raises(DomainError) as duplicate:
                    await service.add_project_member(
                        _actor(seed, "owner"),
                        project_id,
                        user_id=seed.member_id,
                        role=ProjectRole.MEMBER,
                    )
                assert duplicate.value.status_code == 409

                with pytest.raises(DomainError) as forbidden_member:
                    await service.add_project_member(
                        _actor(seed, "member"),
                        project_id,
                        user_id=seed.pm_id,
                        role=ProjectRole.MEMBER,
                    )
                assert forbidden_member.value.status_code == 403

                changed = await service.change_project_member_role(
                    _actor(seed, "owner"),
                    project_id,
                    added_id,
                    role=ProjectRole.MANAGER,
                )
                assert changed.role == ProjectRole.MANAGER

                rows, total = await service.list_project_members(
                    _actor(seed, "owner"),
                    project_id,
                    page=1,
                    page_size=20,
                )
                assert total == 2
                assert {item.role for item in rows} == {ProjectRole.MANAGER}

                await service.remove_project_member(_actor(seed, "owner"), project_id, added_id)
                rows_after, total_after = await service.list_project_members(
                    _actor(seed, "owner"),
                    project_id,
                    page=1,
                    page_size=20,
                )
                assert total_after == 1
                assert rows_after[0].user_id == seed.owner_id

                async with session.begin():
                    notifications = await session.scalar(
                        select(func.count()).select_from(Notification)
                    )
                    member_activity = await session.scalar(
                        select(func.count())
                        .select_from(ActivityLog)
                        .where(ActivityLog.action == "project.member_added")
                    )
                assert notifications == 1
                assert member_activity == 1
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_column_crud_reorder_and_archive_exclusion(tmp_path: Path) -> None:
    database_url = migrate_database(tmp_path / "project-service-columns.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                seed = await _seed_workspace(session, with_member=True)
                service = ProjectService(session)
                project = await service.create_project(
                    _actor(seed, "owner"),
                    seed.workspace_id,
                    name="Team",
                    key="TM",
                )
                project_id = project.id

                added = await service.create_column(
                    _actor(seed, "owner"),
                    project_id,
                    name="In Progress",
                )
                added_id = added.id
                assert added.position == 5

                all_columns, total = await service.list_columns(
                    _actor(seed, "owner"),
                    project_id,
                    page=1,
                    page_size=20,
                )
                assert total == 6
                assert all_columns[-1].id == added_id
                column_ids = [column.id for column in all_columns]

                with pytest.raises(DomainError) as invalid_reorder:
                    await service.reorder_columns(
                        _actor(seed, "owner"),
                        project_id,
                        column_ids[:-1],
                    )
                assert invalid_reorder.value.status_code == 409

                order = column_ids[1:] + column_ids[:1]
                reordered = await service.reorder_columns(_actor(seed, "owner"), project_id, order)
                assert [column.position for column in reordered] == [0, 1, 2, 3, 4, 5]

                renamed = await service.update_column(
                    _actor(seed, "owner"),
                    project_id,
                    added_id,
                    name="Doing",
                    is_done=False,
                )
                assert renamed.name == "Doing"

                archived = await service.archive_column(_actor(seed, "owner"), project_id, added_id)
                assert archived.archived_at is not None

                active, active_total = await service.list_columns(
                    _actor(seed, "owner"),
                    project_id,
                    page=1,
                    page_size=20,
                )
                assert active_total == 5
                assert added_id not in [column.id for column in active]

                with pytest.raises(DomainError) as forbidden_column:
                    await service.create_column(_actor(seed, "member"), project_id, name="Blocked")
                assert forbidden_column.value.status_code == 403
        finally:
            await database.dispose()

    asyncio.run(scenario())


def test_compound_project_mutations_roll_back_on_side_effect_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_url = migrate_database(tmp_path / "project-service-rollback.db")

    async def scenario() -> None:
        database = Database(database_url)
        try:
            async with database.session() as session:
                seed = await _seed_workspace(session, with_member=True)
                service = ProjectService(session)

                async def fail_activity(_item):
                    raise RuntimeError("simulated activity failure")

                monkeypatch.setattr(service._effects, "activity", fail_activity)
                with pytest.raises(RuntimeError, match="simulated activity failure"):
                    await service.create_project(
                        _actor(seed, "owner"),
                        seed.workspace_id,
                        name="Team",
                        key="TM",
                    )

                async with session.begin():
                    assert await session.scalar(select(func.count()).select_from(Project)) == 0
                    assert (
                        await session.scalar(select(func.count()).select_from(ProjectMember)) == 0
                    )
                    assert await session.scalar(select(func.count()).select_from(BoardColumn)) == 0
                    assert await session.scalar(select(func.count()).select_from(ActivityLog)) == 0

                monkeypatch.undo()
                project = await service.create_project(
                    _actor(seed, "owner"),
                    seed.workspace_id,
                    name="Team",
                    key="TM",
                )
                project_id = project.id

                async def fail_notification(_item):
                    raise RuntimeError("simulated notification failure")

                monkeypatch.setattr(service._effects, "notification", fail_notification)
                with pytest.raises(RuntimeError, match="simulated notification failure"):
                    await service.add_project_member(
                        _actor(seed, "owner"),
                        project_id,
                        user_id=seed.member_id,
                        role=ProjectRole.MEMBER,
                    )

                async with session.begin():
                    member_count = await session.scalar(
                        select(func.count())
                        .select_from(ProjectMember)
                        .where(ProjectMember.project_id == project_id)
                    )
                    activities = (
                        await session.scalars(
                            select(ActivityLog).where(ActivityLog.workspace_id == seed.workspace_id)
                        )
                    ).all()
                    notifications = await session.scalar(
                        select(func.count()).select_from(Notification)
                    )
                assert member_count == 1
                assert [item.action for item in activities] == ["project.created"]
                assert notifications == 0
                serialized = repr([item.details for item in activities]).lower()
                assert "password" not in serialized
                assert "token_hash" not in serialized
        finally:
            await database.dispose()

    asyncio.run(scenario())
