from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import resource_conflict, resource_not_found, version_conflict
from app.models.base import utc_now
from app.models.identity import User
from app.models.project import BoardColumn, Project, ProjectMember
from app.models.task import Label, Task, TaskPriority
from app.models.workspace import Notification
from app.repositories.project import (
    ProjectMemberRepository,
    ProjectRepository,
    WorkspaceLookupRepository,
)
from app.repositories.task import LabelRepository, TaskRepository
from app.services.project_permissions import require_project_access, require_project_mutation_role


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tasks = TaskRepository(session)
        self.labels = LabelRepository(session)
        self.projects = ProjectRepository(session)
        self.members = ProjectMemberRepository(session)
        self.workspaces = WorkspaceLookupRepository(session)

    async def create(
        self,
        actor: User,
        project_id: UUID,
        *,
        title: str,
        column_id: UUID,
        description: str | None,
        priority: TaskPriority,
        due_at: datetime | None,
        parent_id: UUID | None,
    ) -> Task:
        async with self.session.begin():
            project, _ = await self._mutate(actor, project_id)
            column = await self._column(project.id, column_id)
            if parent_id is not None:
                parent = await self.tasks.get(parent_id)
                if parent is None or parent.project_id != project.id:
                    raise resource_not_found()
            task = Task(
                project_id=project.id,
                column_id=column.id,
                parent_id=parent_id,
                title=title,
                description=description,
                priority=priority,
                due_at=due_at,
                position=await self.tasks.next_position(project.id, column.id),
                completed_at=utc_now() if column.is_done else None,
            )
            return await self.tasks.add(task)

    async def get(self, actor: User, task_id: UUID) -> Task:
        async with self.session.begin():
            task = await self.tasks.get(task_id)
            if task is None:
                raise resource_not_found()
            await self._access(actor, task.project_id)
            return task

    async def get_detail(self, actor: User, task_id: UUID) -> Task:
        async with self.session.begin():
            task = await self.tasks.get_detail(task_id)
            if task is None:
                raise resource_not_found()
            await self._access(actor, task.project_id)
            return task

    async def list(
        self,
        actor: User,
        project_id: UUID,
        *,
        page: int,
        page_size: int,
        search: str | None,
        column_id: UUID | None,
        priority: str | None,
        completed: bool | None,
        overdue: bool | None,
        sort: str,
        descending: bool,
        include_archived: bool = False,
    ) -> tuple[list[Task], int]:
        async with self.session.begin():
            await self._access(actor, project_id)
            return await self.tasks.list(
                project_id,
                page=page,
                page_size=page_size,
                search=search,
                column_id=column_id,
                priority=priority,
                completed=completed,
                overdue=overdue,
                sort=sort,
                descending=descending,
                include_archived=include_archived,
            )

    async def update(
        self,
        actor: User,
        task_id: UUID,
        *,
        title: str | None,
        description: str | None,
        priority: TaskPriority | None,
        due_at: datetime | None,
    ) -> Task:
        async with self.session.begin():
            task = await self.tasks.get(task_id)
            if task is None:
                raise resource_not_found()
            await self._mutate(actor, task.project_id)
            if title is not None:
                task.title = title
            if description is not None:
                task.description = description
            if priority is not None:
                task.priority = priority
            if due_at is not None:
                task.due_at = due_at
            await self.session.flush()
            return task

    async def archive(self, actor: User, task_id: UUID, *, archived: bool) -> Task:
        async with self.session.begin():
            task = await self.tasks.get(task_id)
            if task is None:
                raise resource_not_found()
            await self._mutate(actor, task.project_id)
            task.archived_at = utc_now() if archived else None
            await self.session.flush()
            return task

    async def move(
        self,
        actor: User,
        task_id: UUID,
        *,
        target_column_id: UUID,
        target_index: int,
        version: int,
    ) -> Task:
        async with self.session.begin():
            task = await self._required_task(task_id)
            await self._mutate(actor, task.project_id)
            if task.archived_at is not None:
                raise resource_not_found()
            if task.version != version:
                raise version_conflict()
            target = await self._column(task.project_id, target_column_id)
            source_column_id = task.column_id
            tasks = await self.tasks.list_active_in_columns(
                task.project_id, {source_column_id, target.id}
            )
            grouped: dict[UUID, list[Task]] = {source_column_id: [], target.id: []}
            for item in tasks:
                if item.id != task.id:
                    grouped[item.column_id].append(item)
            destination = grouped[target.id]
            insert_index = min(target_index, len(destination))
            destination.insert(insert_index, task)
            for column_id, items in grouped.items():
                for position, item in enumerate(items):
                    item.column_id = column_id
                    item.position = position
            task.completed_at = utc_now() if target.is_done else None
            task.version += 1
            await self.session.flush()
            return task

    async def create_label(
        self, actor: User, project_id: UUID, *, name: str, color: str | None
    ) -> Label:
        async with self.session.begin():
            project, _ = await self._mutate(actor, project_id)
            label = Label(project_id=project.id, name=name, color=color)
            try:
                return await self.labels.add(label)
            except Exception as exc:
                raise resource_conflict() from exc

    async def list_labels(
        self, actor: User, project_id: UUID, *, page: int, page_size: int
    ) -> tuple[Sequence[Label], int]:
        async with self.session.begin():
            await self._access(actor, project_id)
            return await self.labels.list(project_id, page=page, page_size=page_size)

    async def update_label(
        self, actor: User, label_id: UUID, *, name: str | None, color: str | None
    ) -> Label:
        async with self.session.begin():
            label = await self._required_label(label_id)
            await self._mutate(actor, label.project_id)
            if name is not None:
                label.name = name
            if color is not None:
                label.color = color
            try:
                await self.session.flush()
            except IntegrityError as exc:
                raise resource_conflict("برچسبی با این نام وجود دارد.") from exc
            return label

    async def archive_label(self, actor: User, label_id: UUID) -> Label:
        async with self.session.begin():
            label = await self._required_label(label_id)
            await self._mutate(actor, label.project_id)
            label.archived_at = utc_now()
            await self.session.flush()
            return label

    async def add_assignee(self, actor: User, task_id: UUID, user_id: UUID) -> None:
        async with self.session.begin():
            task = await self._required_task(task_id)
            await self._mutate(actor, task.project_id)
            if await self.members.get(task.project_id, user_id) is None:
                raise resource_not_found()
            try:
                await self.tasks.add_assignee(task.id, user_id)
            except IntegrityError as exc:
                raise resource_conflict("این کاربر پیش‌تر مسئول وظیفه است.") from exc
            if user_id != actor.id:
                self.session.add(
                    Notification(
                        user_id=user_id,
                        type="task.assigned",
                        title="وظیفه‌ای به شما واگذار شد",
                        body=task.title,
                        entity_type="task",
                        entity_id=task.id,
                        action_url=f"/app/tasks/{task.id}",
                        dedupe_key=f"task.assigned:{task.id}:{user_id}",
                        created_at=utc_now(),
                    )
                )
                await self.session.flush()

    async def remove_assignee(self, actor: User, task_id: UUID, user_id: UUID) -> None:
        async with self.session.begin():
            task = await self._required_task(task_id)
            await self._mutate(actor, task.project_id)
            if not await self.tasks.remove_assignee(task.id, user_id):
                raise resource_not_found()

    async def add_label(self, actor: User, task_id: UUID, label_id: UUID) -> None:
        async with self.session.begin():
            task = await self._required_task(task_id)
            await self._mutate(actor, task.project_id)
            label = await self.labels.get(label_id)
            if (
                label is None
                or label.project_id != task.project_id
                or label.archived_at is not None
            ):
                raise resource_not_found()
            try:
                await self.tasks.add_label(task.id, label.id)
            except IntegrityError as exc:
                raise resource_conflict("این برچسب پیش‌تر به وظیفه متصل است.") from exc

    async def remove_label(self, actor: User, task_id: UUID, label_id: UUID) -> None:
        async with self.session.begin():
            task = await self._required_task(task_id)
            await self._mutate(actor, task.project_id)
            if not await self.tasks.remove_label(task.id, label_id):
                raise resource_not_found()

    async def _access(self, actor: User, project_id: UUID) -> tuple[Project, ProjectMember | None]:
        project = await self.projects.get(project_id)
        if project is None:
            raise resource_not_found()
        workspace_member = await self.workspaces.get_membership(project.workspace_id, actor.id)
        if workspace_member is None:
            raise resource_not_found()
        project_member = await require_project_access(
            self.members, project=project, workspace_member=workspace_member, user_id=actor.id
        )
        return project, project_member

    async def _mutate(self, actor: User, project_id: UUID) -> tuple[Project, ProjectMember | None]:
        project, project_member = await self._access(actor, project_id)
        workspace_member = await self.workspaces.get_membership(project.workspace_id, actor.id)
        if workspace_member is None:
            raise resource_not_found()
        require_project_mutation_role(workspace_member, project_member)
        return project, project_member

    async def _column(self, project_id: UUID, column_id: UUID) -> BoardColumn:
        column = await self.session.get(BoardColumn, column_id)
        if column is None or column.project_id != project_id or column.archived_at is not None:
            raise resource_not_found()
        return column

    async def _required_task(self, task_id: UUID) -> Task:
        task = await self.tasks.get(task_id)
        if task is None:
            raise resource_not_found()
        return task

    async def _required_label(self, label_id: UUID) -> Label:
        label = await self.labels.get(label_id)
        if label is None:
            raise resource_not_found()
        return label
