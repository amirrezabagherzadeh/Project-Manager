from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.identity import User
from app.models.task import Task
from app.models.workspace import ActivityLog
from app.repositories.reporting import ReportingRepository
from app.services.task import TaskService


class ReportingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.reporting = ReportingRepository(session)
        self.tasks = TaskService(session)

    async def dashboard(self, actor: User, project_id: UUID) -> dict[str, int | dict[str, int]]:
        async with self.session.begin():
            await self.tasks._access(actor, project_id)
            now = utc_now()
            return await self.reporting.metrics(
                project_id, now=now, due_soon=now + timedelta(days=7)
            )

    async def range_tasks(
        self,
        actor: User,
        project_id: UUID,
        *,
        start: datetime,
        end: datetime,
        page: int,
        page_size: int,
    ) -> tuple[list[Task], int]:
        async with self.session.begin():
            await self.tasks._access(actor, project_id)
            return await self.reporting.range_tasks(
                project_id, start=start, end=end, page=page, page_size=page_size
            )

    async def activity(self, actor: User, project_id: UUID) -> list[ActivityLog]:
        async with self.session.begin():
            await self.tasks._access(actor, project_id)
            return await self.reporting.activity(project_id, limit=100)

    async def global_dashboard(self, actor: User) -> dict[str, int]:
        async with self.session.begin():
            return await self.reporting.global_metrics(actor.id, now=utc_now())
