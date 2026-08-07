from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models.project import Project
from app.models.task import Task, TaskAssignee
from app.models.workspace import ActivityLog, WorkspaceMember


class ReportingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _active(self, project_id: UUID) -> tuple[ColumnElement[bool], ColumnElement[bool]]:
        return Task.project_id == project_id, Task.archived_at.is_(None)

    async def metrics(
        self, project_id: UUID, *, now: datetime, due_soon: datetime
    ) -> dict[str, int | dict[str, int]]:
        active = self._active(project_id)
        row = (
            await self.session.execute(
                select(
                    func.count(Task.id),
                    func.sum(Task.completed_at.is_not(None)),
                    func.sum(
                        (Task.due_at.is_not(None))
                        & (Task.due_at < now)
                        & (Task.completed_at.is_(None))
                    ),
                    func.sum(
                        (Task.due_at.is_not(None))
                        & (Task.due_at >= now)
                        & (Task.due_at <= due_soon)
                        & (Task.completed_at.is_(None))
                    ),
                ).where(*active)
            )
        ).one()
        assigned = await self.session.scalar(
            select(func.count(func.distinct(TaskAssignee.task_id)))
            .select_from(TaskAssignee)
            .join(Task, Task.id == TaskAssignee.task_id)
            .where(*active)
        )
        total = int(row[0] or 0)
        priority_rows = await self.session.execute(
            select(Task.priority, func.count(Task.id)).where(*active).group_by(Task.priority)
        )
        column_rows = await self.session.execute(
            select(Task.column_id, func.count(Task.id)).where(*active).group_by(Task.column_id)
        )
        assignee_rows = await self.session.execute(
            select(TaskAssignee.user_id, func.count(TaskAssignee.task_id))
            .select_from(TaskAssignee)
            .join(Task, Task.id == TaskAssignee.task_id)
            .where(*active)
            .group_by(TaskAssignee.user_id)
        )
        return {
            "total": total,
            "completed": int(row[1] or 0),
            "overdue": int(row[2] or 0),
            "due_soon": int(row[3] or 0),
            "unassigned": total - int(assigned or 0),
            "by_priority": {str(key): int(value) for key, value in priority_rows},
            "by_column": {str(key): int(value) for key, value in column_rows},
            "by_assignee": {str(key): int(value) for key, value in assignee_rows},
        }

    async def range_tasks(
        self, project_id: UUID, *, start: datetime, end: datetime, page: int, page_size: int
    ) -> tuple[list[Task], int]:
        filters = (
            *self._active(project_id),
            Task.due_at.is_not(None),
            Task.due_at >= start,
            Task.due_at <= end,
        )
        total = await self.session.scalar(select(func.count()).select_from(Task).where(*filters))
        tasks = list(
            await self.session.scalars(
                select(Task)
                .where(*filters)
                .order_by(Task.due_at, Task.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return tasks, int(total or 0)

    async def activity(self, project_id: UUID, *, limit: int) -> list[ActivityLog]:
        return list(
            await self.session.scalars(
                select(ActivityLog)
                .where(ActivityLog.entity_type == "project", ActivityLog.entity_id == project_id)
                .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
                .limit(limit)
            )
        )

    async def global_metrics(self, user_id: UUID, *, now: datetime) -> dict[str, int]:
        visible_projects = (
            select(Project.id)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Project.workspace_id)
            .where(WorkspaceMember.user_id == user_id, Project.archived_at.is_(None))
        )
        task_filters = Task.project_id.in_(visible_projects), Task.archived_at.is_(None)
        row = (
            await self.session.execute(
                select(
                    func.count(Task.id),
                    func.sum(Task.completed_at.is_not(None)),
                    func.sum(
                        (Task.due_at.is_not(None))
                        & (Task.due_at < now)
                        & (Task.completed_at.is_(None))
                    ),
                ).where(*task_filters)
            )
        ).one()
        projects = await self.session.scalar(
            select(func.count()).select_from(visible_projects.subquery())
        )
        return {
            "projects": int(projects or 0),
            "tasks": int(row[0] or 0),
            "completed": int(row[1] or 0),
            "overdue": int(row[2] or 0),
        }
