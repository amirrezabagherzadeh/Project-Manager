from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.models.task import Label, Task, TaskAssignee, TaskLabel


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, task: Task) -> Task:
        self.session.add(task)
        await self.session.flush()
        return task

    async def get(self, task_id: UUID) -> Task | None:
        return await self.session.get(Task, task_id)

    async def get_detail(self, task_id: UUID) -> Task | None:
        return cast(
            Task | None,
            await self.session.scalar(
                select(Task)
                .where(Task.id == task_id)
                .options(
                    selectinload(Task.assignees),
                    selectinload(Task.task_labels).selectinload(TaskLabel.label),
                    selectinload(Task.subtasks),
                )
            ),
        )

    async def add_assignee(self, task_id: UUID, user_id: UUID) -> TaskAssignee:
        item = TaskAssignee(task_id=task_id, user_id=user_id)
        self.session.add(item)
        await self.session.flush()
        return item

    async def remove_assignee(self, task_id: UUID, user_id: UUID) -> bool:
        item = await self.session.scalar(
            select(TaskAssignee).where(
                TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id
            )
        )
        if item is None:
            return False
        await self.session.delete(item)
        await self.session.flush()
        return True

    async def add_label(self, task_id: UUID, label_id: UUID) -> TaskLabel:
        item = TaskLabel(task_id=task_id, label_id=label_id)
        self.session.add(item)
        await self.session.flush()
        return item

    async def remove_label(self, task_id: UUID, label_id: UUID) -> bool:
        item = await self.session.get(TaskLabel, (task_id, label_id))
        if item is None:
            return False
        await self.session.delete(item)
        await self.session.flush()
        return True

    async def next_position(self, project_id: UUID, column_id: UUID) -> int:
        value = await self.session.scalar(
            select(func.max(Task.position)).where(
                Task.project_id == project_id,
                Task.column_id == column_id,
                Task.archived_at.is_(None),
            )
        )
        return int(value) + 1 if value is not None else 0

    async def list_active_in_columns(self, project_id: UUID, column_ids: set[UUID]) -> list[Task]:
        rows = await self.session.scalars(
            select(Task)
            .where(
                Task.project_id == project_id,
                Task.column_id.in_(column_ids),
                Task.archived_at.is_(None),
            )
            .order_by(Task.column_id, Task.position, Task.id)
        )
        return list(rows)

    async def list(
        self,
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
        predicate: ColumnElement[bool] = Task.project_id == project_id
        if not include_archived:
            predicate = predicate & Task.archived_at.is_(None)
        if search:
            predicate = predicate & Task.title.ilike(f"%{search.strip()}%")
        if column_id:
            predicate = predicate & (Task.column_id == column_id)
        if priority:
            predicate = predicate & (Task.priority == priority)
        if completed is not None:
            predicate = predicate & (
                Task.completed_at.is_not(None) if completed else Task.completed_at.is_(None)
            )
        if overdue:
            predicate = predicate & Task.due_at.is_not(
                None
            ) & Task.due_at < func.now() & Task.completed_at.is_(None)
        sort_columns: dict[str, Any] = {
            "created_at": Task.created_at,
            "updated_at": Task.updated_at,
            "due_at": Task.due_at,
            "priority": Task.priority,
            "title": Task.title,
            "position": Task.position,
        }
        sort_column = sort_columns[sort]
        order = sort_column.desc() if descending else sort_column.asc()
        total = await self.session.scalar(select(func.count()).select_from(Task).where(predicate))
        rows = await self.session.scalars(
            select(Task)
            .where(predicate)
            .order_by(order, Task.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows), int(total or 0)


class LabelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, label: Label) -> Label:
        self.session.add(label)
        await self.session.flush()
        return label

    async def get(self, label_id: UUID) -> Label | None:
        return await self.session.get(Label, label_id)

    async def list(self, project_id: UUID, *, page: int, page_size: int) -> tuple[list[Label], int]:
        predicate = (Label.project_id == project_id) & Label.archived_at.is_(None)
        total = await self.session.scalar(select(func.count()).select_from(Label).where(predicate))
        rows = await self.session.scalars(
            select(Label)
            .where(predicate)
            .order_by(Label.name, Label.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows), int(total or 0)
