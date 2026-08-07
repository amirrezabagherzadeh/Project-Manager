from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.deps import get_current_user, get_task_service
from app.models.identity import User
from app.schemas.task import (
    LabelCreate,
    LabelListResponse,
    LabelPublic,
    LabelResponse,
    LabelUpdate,
    TaskAssigneeCreate,
    TaskCreate,
    TaskDetailPublic,
    TaskDetailResponse,
    TaskLabelCreate,
    TaskListResponse,
    TaskMove,
    TaskPublic,
    TaskResponse,
    TaskUpdate,
)
from app.services.task import TaskService

router = APIRouter(tags=["tasks"])
CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[TaskService, Depends(get_task_service)]
ProjectId = Annotated[UUID, Path(description="شناسه پروژه")]


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ساخت وظیفه",
    description="یک وظیفه را در ستون فعال پروژه می‌سازد.",
)
async def create_task(
    project_id: ProjectId, payload: TaskCreate, user: CurrentUser, service: Service
) -> TaskResponse:
    task = await service.create(
        user,
        project_id,
        title=payload.title,
        column_id=payload.column_id,
        description=payload.description,
        priority=payload.priority,
        due_at=payload.due_at,
        parent_id=payload.parent_id,
    )
    return TaskResponse(data=TaskPublic.model_validate(task))


@router.post(
    "/tasks/{task_id}/subtasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ساخت زیروظیفه",
    description="یک زیروظیفه در همان پروژهٔ وظیفهٔ والد می‌سازد.",
)
async def create_subtask(
    task_id: UUID, payload: TaskCreate, user: CurrentUser, service: Service
) -> TaskResponse:
    parent = await service.get(user, task_id)
    task = await service.create(
        user,
        parent.project_id,
        title=payload.title,
        column_id=payload.column_id,
        description=payload.description,
        priority=payload.priority,
        due_at=payload.due_at,
        parent_id=parent.id,
    )
    return TaskResponse(data=TaskPublic.model_validate(task))


@router.get(
    "/projects/{project_id}/tasks",
    response_model=TaskListResponse,
    summary="فهرست وظایف",
    description="وظایف فعال قابل مشاهده پروژه را صفحه‌بندی‌شده برمی‌گرداند.",
)
async def list_tasks(
    project_id: ProjectId,
    user: CurrentUser,
    service: Service,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=240)] = None,
    column_id: UUID | None = None,
    priority: Annotated[str | None, Query(pattern="^(low|medium|high|urgent)$")] = None,
    completed: bool | None = None,
    overdue: bool | None = None,
    sort: Annotated[
        str,
        Query(pattern="^(created_at|updated_at|due_at|priority|title|position)$"),
    ] = "position",
    descending: bool = False,
    include_archived: bool = False,
) -> TaskListResponse:
    items, total = await service.list(
        user,
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
    return TaskListResponse(
        data=[TaskPublic.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskDetailResponse,
    summary="جزئیات وظیفه",
    description="یک وظیفه قابل دسترسی را برمی‌گرداند.",
)
async def get_task(task_id: UUID, user: CurrentUser, service: Service) -> TaskDetailResponse:
    return TaskDetailResponse(
        data=TaskDetailPublic.model_validate(await service.get_detail(user, task_id))
    )


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="ویرایش وظیفه",
    description="فیلدهای اصلی وظیفه را ویرایش می‌کند.",
)
async def update_task(
    task_id: UUID, payload: TaskUpdate, user: CurrentUser, service: Service
) -> TaskResponse:
    task = await service.update(
        user,
        task_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_at=payload.due_at,
    )
    return TaskResponse(data=TaskPublic.model_validate(task))


@router.post(
    "/tasks/{task_id}/move",
    response_model=TaskResponse,
    summary="جابه‌جایی وظیفه در Board",
    description="وظیفه را با version فعلی به ستون و موقعیت هدف به‌صورت اتمیک منتقل می‌کند.",
)
async def move_task(
    task_id: UUID, payload: TaskMove, user: CurrentUser, service: Service
) -> TaskResponse:
    task = await service.move(
        user,
        task_id,
        target_column_id=payload.target_column_id,
        target_index=payload.target_index,
        version=payload.version,
    )
    return TaskResponse(data=TaskPublic.model_validate(task))


@router.post(
    "/tasks/{task_id}/archive",
    response_model=TaskResponse,
    summary="آرشیو وظیفه",
    description="وظیفه را آرشیو می‌کند.",
)
async def archive_task(task_id: UUID, user: CurrentUser, service: Service) -> TaskResponse:
    return TaskResponse(
        data=TaskPublic.model_validate(await service.archive(user, task_id, archived=True))
    )


@router.post(
    "/tasks/{task_id}/restore",
    response_model=TaskResponse,
    summary="بازیابی وظیفه",
    description="وظیفه آرشیوشده را بازیابی می‌کند.",
)
async def restore_task(task_id: UUID, user: CurrentUser, service: Service) -> TaskResponse:
    return TaskResponse(
        data=TaskPublic.model_validate(await service.archive(user, task_id, archived=False))
    )


@router.post(
    "/projects/{project_id}/labels",
    response_model=LabelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ساخت برچسب",
    description="برچسب پروژه را می‌سازد.",
)
async def create_label(
    project_id: ProjectId, payload: LabelCreate, user: CurrentUser, service: Service
) -> LabelResponse:
    label = await service.create_label(user, project_id, name=payload.name, color=payload.color)
    return LabelResponse(data=LabelPublic.model_validate(label))


@router.get(
    "/projects/{project_id}/labels",
    response_model=LabelListResponse,
    summary="فهرست برچسب‌ها",  # noqa: RUF001
    description="برچسب‌های فعال پروژه را صفحه‌بندی‌شده برمی‌گرداند.",
)
async def list_labels(
    project_id: ProjectId,
    user: CurrentUser,
    service: Service,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> LabelListResponse:
    items, total = await service.list_labels(user, project_id, page=page, page_size=page_size)
    return LabelListResponse(
        data=[LabelPublic.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.patch(
    "/labels/{label_id}",
    response_model=LabelResponse,
    summary="ویرایش برچسب",
    description="نام یا رنگ برچسب را تغییر می‌دهد.",
)
async def update_label(
    label_id: UUID, payload: LabelUpdate, user: CurrentUser, service: Service
) -> LabelResponse:
    label = await service.update_label(user, label_id, name=payload.name, color=payload.color)
    return LabelResponse(data=LabelPublic.model_validate(label))


@router.delete(
    "/labels/{label_id}",
    response_model=LabelResponse,
    summary="آرشیو برچسب",
    description="برچسب را به‌صورت برگشت‌پذیر آرشیو می‌کند.",
)
async def archive_label(label_id: UUID, user: CurrentUser, service: Service) -> LabelResponse:
    return LabelResponse(
        data=LabelPublic.model_validate(await service.archive_label(user, label_id))
    )


@router.post(
    "/tasks/{task_id}/assignees",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="افزودن مسئول وظیفه",
    description="یک عضو همان پروژه را مسئول وظیفه می‌کند.",
)
async def add_assignee(
    task_id: UUID, payload: TaskAssigneeCreate, user: CurrentUser, service: Service
) -> Response:
    await service.add_assignee(user, task_id, payload.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/tasks/{task_id}/assignees/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف مسئول وظیفه",
    description="یک مسئول را از وظیفه حذف می‌کند.",
)
async def remove_assignee(
    task_id: UUID, user_id: UUID, user: CurrentUser, service: Service
) -> Response:
    await service.remove_assignee(user, task_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/tasks/{task_id}/labels",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="افزودن برچسب وظیفه",
    description="یک برچسب فعال همان پروژه را به وظیفه متصل می‌کند.",
)
async def add_task_label(
    task_id: UUID, payload: TaskLabelCreate, user: CurrentUser, service: Service
) -> Response:
    await service.add_label(user, task_id, payload.label_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/tasks/{task_id}/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف برچسب وظیفه",
    description="یک برچسب را از وظیفه جدا می‌کند.",
)
async def remove_task_label(
    task_id: UUID, label_id: UUID, user: CurrentUser, service: Service
) -> Response:
    await service.remove_label(user, task_id, label_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
