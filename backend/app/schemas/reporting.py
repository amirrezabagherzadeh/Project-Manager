from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.task import TaskPublic


class ProjectMetrics(BaseModel):
    total: int
    completed: int
    overdue: int
    due_soon: int
    unassigned: int
    by_priority: dict[str, int]
    by_column: dict[str, int]
    by_assignee: dict[str, int]


class ProjectDashboardResponse(BaseModel):
    data: ProjectMetrics


class GlobalDashboard(BaseModel):
    projects: int
    tasks: int
    completed: int
    overdue: int


class GlobalDashboardResponse(BaseModel):
    data: GlobalDashboard


class ReportingTaskListResponse(BaseModel):
    data: list[TaskPublic]
    page: int
    page_size: int
    total: int


class ProjectActivityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    actor_id: UUID | None
    action: str
    created_at: datetime


class ProjectActivityResponse(BaseModel):
    data: list[ProjectActivityPublic]
