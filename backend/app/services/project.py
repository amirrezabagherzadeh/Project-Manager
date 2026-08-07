from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    invalid_operation,
    resource_conflict,
    resource_not_found,
)
from app.models.base import utc_now
from app.models.identity import User
from app.models.project import (
    DEFAULT_COLUMN_NAMES,
    BoardColumn,
    Project,
    ProjectMember,
    ProjectRole,
)
from app.models.workspace import ActivityLog, Notification, Workspace, WorkspaceMember
from app.repositories.project import (
    BoardColumnRepository,
    ProjectMemberRepository,
    ProjectRepository,
    ProjectSideEffectRepository,
    ProjectUserRepository,
    WorkspaceLookupRepository,
)
from app.services.project_permissions import (
    PROJECT_MUTATION_ROLES,
    require_project_access,
    require_project_mutation_role,
    require_role,
)


class ProjectService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._session = session
        self._clock = clock
        self._projects = ProjectRepository(session)
        self._members = ProjectMemberRepository(session)
        self._columns = BoardColumnRepository(session)
        self._users = ProjectUserRepository(session)
        self._lookup = WorkspaceLookupRepository(session)
        self._effects = ProjectSideEffectRepository(session)

    # ------------------------------------------------------------------ projects

    async def create_project(
        self,
        actor: User,
        workspace_id: UUID,
        *,
        name: str,
        key: str,
        description: str | None = None,
        is_private: bool = False,
        color: str | None = None,
        start_date: datetime | None = None,
        due_date: datetime | None = None,
    ) -> Project:
        now = self._clock()
        try:
            async with self._session.begin():
                actor_member = await self._membership(actor, workspace_id)
                require_role(actor_member, PROJECT_MUTATION_ROLES)
                await self._required_workspace(workspace_id)
                if await self._projects.get_by_key(workspace_id, key) is not None:
                    raise resource_conflict("پروژه‌ای با این کلید در این فضای کاری وجود دارد.")
                project = Project(
                    workspace_id=workspace_id,
                    name=name.strip(),
                    key=key,
                    description=description.strip() if description else None,
                    is_private=is_private,
                    color=color.strip() if color else None,
                    start_date=start_date,
                    due_date=due_date,
                )
                await self._projects.add(project)
                await self._members.add(
                    ProjectMember(
                        project_id=project.id,
                        user_id=actor.id,
                        role=ProjectRole.MANAGER,
                        joined_at=now,
                    )
                )
                for position, column_name in enumerate(DEFAULT_COLUMN_NAMES):
                    await self._columns.add(
                        BoardColumn(
                            project_id=project.id,
                            name=column_name,
                            position=position,
                            is_done=column_name == "done",
                        )
                    )
                await self._activity(
                    project,
                    actor,
                    "project.created",
                    details={"workspace_id": str(workspace_id), "key": key},
                )
                return project
        except IntegrityError as exc:
            raise resource_conflict("پروژه‌ای با این کلید در این فضای کاری وجود دارد.") from exc

    async def list_projects(
        self,
        actor: User,
        workspace_id: UUID,
        *,
        page: int,
        page_size: int,
        include_archived: bool = False,
    ) -> tuple[list[Project], int]:
        async with self._session.begin():
            await self._membership(actor, workspace_id)
            return await self._projects.list_for_workspace(
                workspace_id,
                include_archived=include_archived,
                offset=(page - 1) * page_size,
                limit=page_size,
            )

    async def read_project(self, actor: User, project_id: UUID) -> Project:
        async with self._session.begin():
            project, workspace_member, _project_member = await self._resolved_project(
                actor,
                project_id,
            )
            await require_project_access(
                self._members,
                project=project,
                workspace_member=workspace_member,
                user_id=actor.id,
            )
            return project

    async def update_project(
        self,
        actor: User,
        project_id: UUID,
        *,
        name: str | None = None,
        description: str | None = None,
        is_private: bool | None = None,
        color: str | None = None,
        start_date: datetime | None = None,
        due_date: datetime | None = None,
    ) -> Project:
        async with self._session.begin():
            project, workspace_member, project_member = await self._resolved_project(
                actor,
                project_id,
            )
            project_member = await require_project_access(
                self._members,
                project=project,
                workspace_member=workspace_member,
                user_id=actor.id,
            )
            require_project_mutation_role(workspace_member, project_member)
            if name is not None:
                project.name = name.strip()
            if description is not None:
                project.description = description.strip() or None
            if is_private is not None:
                project.is_private = is_private
            if color is not None:
                project.color = color.strip() or None
            if start_date is not None:
                project.start_date = start_date
            if due_date is not None:
                project.due_date = due_date
            await self._activity(project, actor, "project.updated")
            await self._session.flush()
            return project

    async def archive_project(self, actor: User, project_id: UUID) -> Project:
        return await self._set_archived(actor, project_id, archived=True)

    async def restore_project(self, actor: User, project_id: UUID) -> Project:
        return await self._set_archived(actor, project_id, archived=False)

    async def _set_archived(
        self,
        actor: User,
        project_id: UUID,
        *,
        archived: bool,
    ) -> Project:
        async with self._session.begin():
            project, workspace_member, project_member = await self._resolved_project(
                actor,
                project_id,
            )
            project_member = await require_project_access(
                self._members,
                project=project,
                workspace_member=workspace_member,
                user_id=actor.id,
            )
            require_project_mutation_role(workspace_member, project_member)
            project.archived_at = self._clock() if archived else None
            await self._activity(
                project,
                actor,
                "project.archived" if archived else "project.restored",
            )
            await self._session.flush()
            return project

    # ------------------------------------------------------------------- members

    async def list_project_members(
        self,
        actor: User,
        project_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[ProjectMember], int]:
        async with self._session.begin():
            project, workspace_member, _project_member = await self._resolved_project(
                actor,
                project_id,
            )
            await require_project_access(
                self._members,
                project=project,
                workspace_member=workspace_member,
                user_id=actor.id,
            )
            return await self._members.list(
                project_id,
                offset=(page - 1) * page_size,
                limit=page_size,
            )

    async def add_project_member(
        self,
        actor: User,
        project_id: UUID,
        *,
        user_id: UUID,
        role: ProjectRole,
    ) -> ProjectMember:
        try:
            async with self._session.begin():
                project, workspace_member, project_member = await self._resolved_project(
                    actor,
                    project_id,
                )
                project_member = await require_project_access(
                    self._members,
                    project=project,
                    workspace_member=workspace_member,
                    user_id=actor.id,
                )
                require_project_mutation_role(workspace_member, project_member)
                workspace_membership = await self._lookup.get_membership(
                    project.workspace_id,
                    user_id,
                )
                if workspace_membership is None:
                    raise resource_not_found()
                if await self._members.get(project_id, user_id) is not None:
                    raise resource_conflict("این کاربر از قبل عضو این پروژه است.")
                target = await self._users.get_by_id(user_id)
                if target is None:
                    raise resource_not_found()
                member = ProjectMember(
                    project_id=project_id,
                    user_id=user_id,
                    role=role,
                    joined_at=self._clock(),
                )
                await self._members.add(member)
                await self._activity(
                    project,
                    actor,
                    "project.member_added",
                    details={"user_id": str(user_id), "role": role.value},
                )
                await self._notify_member(
                    actor=actor,
                    target=target,
                    project=project,
                    kind="project.member_added",
                    title="به پروژه افزوده شدید",
                    dedupe_key=f"project.member_added:{member.id}",
                )
                return member
        except IntegrityError as exc:
            raise resource_conflict("این کاربر از قبل عضو این پروژه است.") from exc

    async def change_project_member_role(
        self,
        actor: User,
        project_id: UUID,
        member_id: UUID,
        *,
        role: ProjectRole,
    ) -> ProjectMember:
        async with self._session.begin():
            project, workspace_member, project_member = await self._resolved_project(
                actor,
                project_id,
            )
            project_member = await require_project_access(
                self._members,
                project=project,
                workspace_member=workspace_member,
                user_id=actor.id,
            )
            require_project_mutation_role(workspace_member, project_member)
            target = await self._members.get_by_id(project_id, member_id)
            if target is None:
                raise resource_not_found()
            target.role = role
            await self._activity(
                project,
                actor,
                "project.member_role_changed",
                details={"user_id": str(target.user_id), "role": role.value},
            )
            await self._session.flush()
            return target

    async def remove_project_member(
        self,
        actor: User,
        project_id: UUID,
        member_id: UUID,
    ) -> None:
        async with self._session.begin():
            project, workspace_member, project_member = await self._resolved_project(
                actor,
                project_id,
            )
            project_member = await require_project_access(
                self._members,
                project=project,
                workspace_member=workspace_member,
                user_id=actor.id,
            )
            require_project_mutation_role(workspace_member, project_member)
            target = await self._members.get_by_id(project_id, member_id)
            if target is None:
                raise resource_not_found()
            workspace = await self._required_workspace(project.workspace_id)
            if target.user_id == workspace.owner_id:
                raise invalid_operation("مالک فضای کاری را نمی‌توان از پروژه حذف کرد.")
            target_user_id = target.user_id
            await self._members.delete(target)
            await self._activity(
                project,
                actor,
                "project.member_removed",
                details={"user_id": str(target_user_id)},
            )

    # ------------------------------------------------------------------- columns

    async def list_columns(
        self,
        actor: User,
        project_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[BoardColumn], int]:
        async with self._session.begin():
            project, workspace_member, _project_member = await self._resolved_project(
                actor,
                project_id,
            )
            await require_project_access(
                self._members,
                project=project,
                workspace_member=workspace_member,
                user_id=actor.id,
            )
            return await self._columns.list_active(
                project_id,
                offset=(page - 1) * page_size,
                limit=page_size,
            )

    async def create_column(
        self,
        actor: User,
        project_id: UUID,
        *,
        name: str,
        is_done: bool = False,
    ) -> BoardColumn:
        try:
            async with self._session.begin():
                project, workspace_member, project_member = await self._resolved_project(
                    actor,
                    project_id,
                )
                project_member = await require_project_access(
                    self._members,
                    project=project,
                    workspace_member=workspace_member,
                    user_id=actor.id,
                )
                require_project_mutation_role(workspace_member, project_member)
                if project.archived_at is not None:
                    raise invalid_operation("پروژهٔ آرشیوشده را نمی‌توان تغییر داد.")
                column = BoardColumn(
                    project_id=project_id,
                    name=name.strip(),
                    position=await self._columns.next_position(project_id),
                    is_done=is_done,
                )
                await self._columns.add(column)
                await self._activity(
                    project,
                    actor,
                    "project.column_created",
                    details={"column_id": str(column.id), "name": column.name},
                )
                return column
        except IntegrityError as exc:
            raise resource_conflict("ستونی با این نام در این پروژه وجود دارد.") from exc

    async def update_column(
        self,
        actor: User,
        project_id: UUID,
        column_id: UUID,
        *,
        name: str | None = None,
        is_done: bool | None = None,
    ) -> BoardColumn:
        try:
            async with self._session.begin():
                project, workspace_member, project_member = await self._resolved_project(
                    actor,
                    project_id,
                )
                project_member = await require_project_access(
                    self._members,
                    project=project,
                    workspace_member=workspace_member,
                    user_id=actor.id,
                )
                require_project_mutation_role(workspace_member, project_member)
                column = await self._required_column(project_id, column_id)
                if column.archived_at is not None:
                    raise invalid_operation("ستون آرشیوشده را نمی‌توان تغییر داد.")
                if name is not None:
                    column.name = name.strip()
                if is_done is not None:
                    column.is_done = is_done
                await self._activity(
                    project,
                    actor,
                    "project.column_updated",
                    details={"column_id": str(column.id), "name": column.name},
                )
                await self._session.flush()
                return column
        except IntegrityError as exc:
            raise resource_conflict("ستونی با این نام در این پروژه وجود دارد.") from exc

    async def archive_column(
        self,
        actor: User,
        project_id: UUID,
        column_id: UUID,
    ) -> BoardColumn:
        async with self._session.begin():
            project, workspace_member, project_member = await self._resolved_project(
                actor,
                project_id,
            )
            project_member = await require_project_access(
                self._members,
                project=project,
                workspace_member=workspace_member,
                user_id=actor.id,
            )
            require_project_mutation_role(workspace_member, project_member)
            column = await self._required_column(project_id, column_id)
            if column.archived_at is None:
                column.archived_at = self._clock()
            await self._activity(
                project,
                actor,
                "project.column_archived",
                details={"column_id": str(column.id), "name": column.name},
            )
            await self._session.flush()
            return column

    async def reorder_columns(
        self,
        actor: User,
        project_id: UUID,
        column_ids: list[UUID],
    ) -> list[BoardColumn]:
        async with self._session.begin():
            project, workspace_member, project_member = await self._resolved_project(
                actor,
                project_id,
            )
            project_member = await require_project_access(
                self._members,
                project=project,
                workspace_member=workspace_member,
                user_id=actor.id,
            )
            require_project_mutation_role(workspace_member, project_member)
            active = await self._columns.list_all_active(project_id)
            active_by_id = {column.id: column for column in active}
            if set(column_ids) != set(active_by_id):
                raise invalid_operation("فهرست ستون‌ها باید دقیقاً همهٔ ستون‌های فعال پروژه باشد.")  # noqa: RUF001
            for position, column_id in enumerate(column_ids):
                active_by_id[column_id].position = position
            await self._activity(
                project,
                actor,
                "project.columns_reordered",
                details={"column_ids": [str(item) for item in column_ids]},
            )
            await self._session.flush()
            return [active_by_id[column_id] for column_id in column_ids]

    # ------------------------------------------------------------------- helpers

    async def _membership(self, actor: User, workspace_id: UUID) -> WorkspaceMember:
        member = await self._lookup.get_membership(workspace_id, actor.id)
        if member is None:
            raise resource_not_found()
        return member

    async def _required_workspace(self, workspace_id: UUID) -> Workspace:
        workspace = await self._session.get(Workspace, workspace_id)
        if workspace is None:
            raise resource_not_found()
        return workspace

    async def _resolved_project(
        self,
        actor: User,
        project_id: UUID,
    ) -> tuple[Project, WorkspaceMember, ProjectMember | None]:
        project = await self._projects.get(project_id)
        if project is None:
            raise resource_not_found()
        workspace_member = await self._lookup.get_membership(project.workspace_id, actor.id)
        if workspace_member is None:
            raise resource_not_found()
        project_member = await self._members.get(project_id, actor.id)
        return project, workspace_member, project_member

    async def _required_column(
        self,
        project_id: UUID,
        column_id: UUID,
    ) -> BoardColumn:
        column = await self._columns.get_by_project(project_id, column_id)
        if column is None:
            raise resource_not_found()
        return column

    async def _activity(
        self,
        project: Project,
        actor: User,
        action: str,
        *,
        details: dict[str, object] | None = None,
    ) -> None:
        await self._effects.activity(
            ActivityLog(
                workspace_id=project.workspace_id,
                actor_id=actor.id,
                entity_type="project",
                entity_id=project.id,
                action=action,
                details=details or {},
                created_at=self._clock(),
            )
        )

    async def _notify_member(
        self,
        *,
        actor: User,
        target: User,
        project: Project,
        kind: str,
        title: str,
        dedupe_key: str | None = None,
    ) -> None:
        if actor.id == target.id:
            return
        await self._effects.notification(
            Notification(
                user_id=target.id,
                type=kind,
                title=title,
                body=project.name,
                entity_type="project",
                entity_id=project.id,
                action_url=f"/app/projects/{project.id}",
                dedupe_key=dedupe_key or f"{kind}:{project.id}:{target.id}",
                created_at=self._clock(),
            )
        )
