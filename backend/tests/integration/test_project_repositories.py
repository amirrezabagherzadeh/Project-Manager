import asyncio
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select

from app.core.database import Database
from app.models import (
    BoardColumn,
    Project,
    ProjectMember,
    ProjectRole,
    User,
    Workspace,
    WorkspaceMember,
    WorkspaceRole,
)
from app.repositories.project import (
    BoardColumnRepository,
    ProjectMemberRepository,
    ProjectRepository,
    ProjectUserRepository,
    WorkspaceLookupRepository,
)
from tests.helpers import migrate_database


def test_project_repositories_scope_paginate_filter_and_do_not_commit(
    tmp_path: Path,
) -> None:
    database_url = migrate_database(tmp_path / "project-repositories.db")
    now = datetime.now(UTC)

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
                owner = User(
                    email="owner@example.test",
                    name="Owner",
                    password_hash="private",
                )
                member_user = User(
                    email="member@example.test",
                    name="Member",
                    password_hash="private",
                )
                session.add_all([owner, member_user])
                await session.flush()

                workspace = Workspace(name="Team", owner_id=owner.id)
                session.add(workspace)
                await session.flush()
                session.add(
                    WorkspaceMember(
                        workspace_id=workspace.id,
                        user_id=owner.id,
                        role=WorkspaceRole.OWNER,
                        joined_at=now,
                    )
                )
                session.add(
                    WorkspaceMember(
                        workspace_id=workspace.id,
                        user_id=member_user.id,
                        role=WorkspaceRole.MEMBER,
                        joined_at=now,
                    )
                )
                await session.flush()

                projects = ProjectRepository(session)
                members = ProjectMemberRepository(session)
                columns = BoardColumnRepository(session)
                users = ProjectUserRepository(session)
                lookup = WorkspaceLookupRepository(session)

                active = await projects.add(
                    Project(workspace_id=workspace.id, name="Active", key="ACT")
                )
                archived = await projects.add(
                    Project(
                        workspace_id=workspace.id,
                        name="Archived",
                        key="ARC",
                        archived_at=now,
                    )
                )
                await members.add(
                    ProjectMember(
                        project_id=active.id,
                        user_id=member_user.id,
                        role=ProjectRole.MANAGER,
                        joined_at=now,
                    )
                )
                await columns.add(
                    BoardColumn(
                        project_id=active.id,
                        name="backlog",
                        position=0,
                        is_done=False,
                    )
                )
                await columns.add(
                    BoardColumn(
                        project_id=active.id,
                        name="done",
                        position=1,
                        is_done=True,
                    )
                )

                visible, total = await projects.list_for_workspace(
                    workspace.id,
                    include_archived=False,
                    offset=0,
                    limit=10,
                )
                assert [item.id for item in visible] == [active.id]
                assert total == 1

                with_archived, total_with = await projects.list_for_workspace(
                    workspace.id,
                    include_archived=True,
                    offset=0,
                    limit=10,
                )
                assert {item.id for item in with_archived} == {active.id, archived.id}
                assert total_with == 2

                assert (await projects.get_by_key(workspace.id, "ACT")).id == active.id
                assert (await projects.get_by_key(workspace.id, "MISSING")) is None

                loaded = await projects.get_with_columns(active.id)
                assert loaded is not None
                assert [column.name for column in loaded.columns] == ["backlog", "done"]

                member_rows, member_total = await members.list(active.id, offset=0, limit=10)
                assert member_total == 1
                assert member_rows[0].user_id == member_user.id
                assert (await members.get(active.id, owner.id)) is None
                assert (
                    await members.get_by_id(active.id, member_rows[0].id)
                ).user_id == member_user.id

                active_columns, column_total = await columns.list_active(
                    active.id,
                    offset=0,
                    limit=10,
                )
                assert column_total == 2
                assert [column.position for column in active_columns] == [0, 1]
                assert (await columns.next_position(active.id)) == 2
                assert (await columns.get_by_project(active.id, active_columns[0].id)).id == (
                    active_columns[0].id
                )
                assert (await columns.get_by_project(workspace.id, active_columns[0].id)) is None

                assert (await users.get_by_id(owner.id)).id == owner.id
                assert (
                    await lookup.get_membership(workspace.id, owner.id)
                ).role == WorkspaceRole.OWNER
                assert (await lookup.get_membership(workspace.id, archived.id)) is None
                assert commits == 0

                await session.rollback()
                count = await session.scalar(select(func.count()).select_from(Project))
                assert count == 0
        finally:
            await database.dispose()

    asyncio.run(scenario())
