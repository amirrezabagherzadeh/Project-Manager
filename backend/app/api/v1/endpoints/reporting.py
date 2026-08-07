from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_reporting_service
from app.models.identity import User
from app.schemas.reporting import (
    GlobalDashboard,
    GlobalDashboardResponse,
    ProjectActivityPublic,
    ProjectActivityResponse,
    ProjectDashboardResponse,
    ProjectMetrics,
    ReportingTaskListResponse,
)
from app.schemas.task import TaskPublic
from app.services.reporting import ReportingService

router = APIRouter(tags=["reporting"])
CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[ReportingService, Depends(get_reporting_service)]


@router.get("/dashboard", response_model=GlobalDashboardResponse)
async def global_dashboard(user: CurrentUser, service: Service) -> GlobalDashboardResponse:
    return GlobalDashboardResponse(data=GlobalDashboard(**await service.global_dashboard(user)))


@router.get("/projects/{project_id}/dashboard", response_model=ProjectDashboardResponse)
async def project_dashboard(
    project_id: UUID, user: CurrentUser, service: Service
) -> ProjectDashboardResponse:
    return ProjectDashboardResponse(
        data=ProjectMetrics(**await service.dashboard(user, project_id))
    )


@router.get("/projects/{project_id}/timeline", response_model=ReportingTaskListResponse)
@router.get("/projects/{project_id}/calendar", response_model=ReportingTaskListResponse)
async def project_range_tasks(
    project_id: UUID,
    start: datetime,
    end: datetime,
    user: CurrentUser,
    service: Service,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ReportingTaskListResponse:
    tasks, total = await service.range_tasks(
        user, project_id, start=start, end=end, page=page, page_size=page_size
    )
    return ReportingTaskListResponse(
        data=[TaskPublic.model_validate(task) for task in tasks],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/projects/{project_id}/activity", response_model=ProjectActivityResponse)
async def project_activity(
    project_id: UUID, user: CurrentUser, service: Service
) -> ProjectActivityResponse:
    return ProjectActivityResponse(
        data=[
            ProjectActivityPublic.model_validate(item)
            for item in await service.activity(user, project_id)
        ]
    )
