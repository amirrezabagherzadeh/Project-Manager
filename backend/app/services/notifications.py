from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.task import Task, TaskAssignee
from app.models.workspace import Notification


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_due_notifications(self, *, now: datetime | None = None) -> int:
        moment = now or utc_now()
        async with self.session.begin():
            rows = await self.session.execute(
                select(TaskAssignee.user_id, Task.id, Task.title)
                .join(Task, Task.id == TaskAssignee.task_id)
                .where(
                    Task.archived_at.is_(None),
                    Task.completed_at.is_(None),
                    Task.due_at.is_not(None),
                    Task.due_at <= moment,
                )
            )
            created = 0
            for user_id, task_id, title in rows:
                item = Notification(
                    user_id=user_id,
                    type="task.due",
                    title="وظیفه سررسید شده است",
                    body=title,
                    entity_type="task",
                    entity_id=task_id,
                    action_url=f"/app/tasks/{task_id}",
                    dedupe_key=f"task.due:{task_id}:{user_id}",
                    created_at=moment,
                )
                try:
                    async with self.session.begin_nested():
                        self.session.add(item)
                        await self.session.flush()
                    created += 1
                except IntegrityError:
                    continue
            return created
