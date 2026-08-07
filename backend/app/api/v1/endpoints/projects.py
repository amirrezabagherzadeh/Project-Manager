from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.deps import get_current_user, get_project_service
from app.models.identity import User
from app.schemas.common import ErrorResponse
from app.schemas.project import (
    ColumnCreate,
    ColumnListResponse,
    ColumnPublic,
    ColumnReorder,
    ColumnResponse,
    ColumnUpdate,
    ProjectCreate,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberListResponse,
    ProjectMemberPublic,
    ProjectMemberResponse,
    ProjectMemberRoleUpdate,
    ProjectPublic,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project import ProjectService

router = APIRouter(tags=["projects"])

ERRORS: dict[int, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "احراز هویت لازم است."},
    403: {"model": ErrorResponse, "description": "نقش کاربر مجاز نیست."},
    404: {"model": ErrorResponse, "description": "منبع در محدودهٔ کاربر پیدا نشد."},
    409: {"model": ErrorResponse, "description": "عملیات با وضعیت موجود تداخل دارد."},
    422: {"model": ErrorResponse, "description": "ورودی معتبر نیست."},
}

CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[ProjectService, Depends(get_project_service)]
ProjectId = Annotated[UUID, Path(description="شناسهٔ پروژه")]
WorkspaceId = Annotated[UUID, Path(description="شناسهٔ فضای کاری")]
Page = Annotated[int, Query(ge=1, description="شماره صفحه")]
PageSize = Annotated[int, Query(ge=1, le=100, description="اندازه صفحه، حداکثر 100")]


@router.post(
    "/workspaces/{workspace_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ساخت پروژه",
    description=(
        "پروژه، عضویت manager سازنده، پنج ستون پیش‌فرض و Activity را در یک تراکنش می‌سازد. "
        "کلید باید در فضای کاری یکتا باشد."
    ),
    responses={
        401: ERRORS[401],
        403: ERRORS[403],
        404: ERRORS[404],
        409: ERRORS[409],
        422: ERRORS[422],
    },
)
async def create_project(
    workspace_id: WorkspaceId,
    payload: ProjectCreate,
    user: CurrentUser,
    service: Service,
) -> ProjectResponse:
    project = await service.create_project(
        user,
        workspace_id,
        name=payload.name,
        key=payload.key,
        description=payload.description,
        is_private=payload.is_private,
        color=payload.color,
        start_date=payload.start_date,
        due_date=payload.due_date,
    )
    return ProjectResponse(data=ProjectPublic.model_validate(project))


@router.get(
    "/workspaces/{workspace_id}/projects",
    response_model=ProjectListResponse,
    summary="فهرست پروژه‌ها",  # noqa: RUF001
    description=(
        "پروژه‌های فضای کاری را که کاربر می‌تواند ببیند با pagination برمی‌گرداند؛ "
        "پروژه‌های آرشیوشده به‌صورت پیش‌فرض حذف می‌شوند."
    ),
    responses={401: ERRORS[401], 404: ERRORS[404], 422: ERRORS[422]},
)
async def list_projects(
    workspace_id: WorkspaceId,
    user: CurrentUser,
    service: Service,
    include_archived: bool = Query(default=False, description="شامل پروژه‌های آرشیوشده"),
    page: Page = 1,
    page_size: PageSize = 20,
) -> ProjectListResponse:
    items, total = await service.list_projects(
        user,
        workspace_id,
        page=page,
        page_size=page_size,
        include_archived=include_archived,
    )
    return ProjectListResponse(
        data=[ProjectPublic.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="مشاهده پروژه",
    description=(
        "جزئیات پروژه را با رعایت دسترسی پروژهٔ خصوصی برمی‌گرداند؛ "
        "کاربر غیرعضو در پروژهٔ خصوصی پاسخ 404 امن دریافت می‌کند."
    ),
    responses={401: ERRORS[401], 404: ERRORS[404]},
)
async def read_project(
    project_id: ProjectId,
    user: CurrentUser,
    service: Service,
) -> ProjectResponse:
    project = await service.read_project(user, project_id)
    return ProjectResponse(data=ProjectPublic.model_validate(project))


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="ویرایش پروژه",
    description="OWNER/ADMIN/PROJECT_MANAGER یا manager پروژه می‌تواند پروژه را ویرایش کند.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404], 422: ERRORS[422]},
)
async def update_project(
    project_id: ProjectId,
    payload: ProjectUpdate,
    user: CurrentUser,
    service: Service,
) -> ProjectResponse:
    project = await service.update_project(
        user,
        project_id,
        name=payload.name,
        description=payload.description,
        is_private=payload.is_private,
        color=payload.color,
        start_date=payload.start_date,
        due_date=payload.due_date,
    )
    return ProjectResponse(data=ProjectPublic.model_validate(project))


@router.post(
    "/projects/{project_id}/archive",
    response_model=ProjectResponse,
    summary="آرشیو پروژه",
    description="OWNER/ADMIN/PROJECT_MANAGER یا manager پروژه، پروژه را آرشیو می‌کند.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]},
)
async def archive_project(
    project_id: ProjectId,
    user: CurrentUser,
    service: Service,
) -> ProjectResponse:
    project = await service.archive_project(user, project_id)
    return ProjectResponse(data=ProjectPublic.model_validate(project))


@router.post(
    "/projects/{project_id}/restore",
    response_model=ProjectResponse,
    summary="بازیابی پروژه",
    description="OWNER/ADMIN/PROJECT_MANAGER یا manager پروژه، پروژهٔ آرشیوشده را بازیابی می‌کند.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]},
)
async def restore_project(
    project_id: ProjectId,
    user: CurrentUser,
    service: Service,
) -> ProjectResponse:
    project = await service.restore_project(user, project_id)
    return ProjectResponse(data=ProjectPublic.model_validate(project))


@router.get(
    "/projects/{project_id}/members",
    response_model=ProjectMemberListResponse,
    summary="فهرست اعضای پروژه",
    description="اعضای پروژه را با pagination برمی‌گرداند.",
    responses={401: ERRORS[401], 404: ERRORS[404], 422: ERRORS[422]},
)
async def list_project_members(
    project_id: ProjectId,
    user: CurrentUser,
    service: Service,
    page: Page = 1,
    page_size: PageSize = 20,
) -> ProjectMemberListResponse:
    items, total = await service.list_project_members(
        user,
        project_id,
        page=page,
        page_size=page_size,
    )
    return ProjectMemberListResponse(
        data=[ProjectMemberPublic.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/projects/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="افزودن عضو به پروژه",
    description=(
        "کاربر موجود در فضای کاری را با نقش manager/member به پروژه اضافه می‌کند؛ "
        "عضویت تکراری 409 برمی‌گرداند."
    ),
    responses={
        401: ERRORS[401],
        403: ERRORS[403],
        404: ERRORS[404],
        409: ERRORS[409],
        422: ERRORS[422],
    },
)
async def add_project_member(
    project_id: ProjectId,
    payload: ProjectMemberCreate,
    user: CurrentUser,
    service: Service,
) -> ProjectMemberResponse:
    member = await service.add_project_member(
        user,
        project_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    return ProjectMemberResponse(data=ProjectMemberPublic.model_validate(member))


@router.patch(
    "/projects/{project_id}/members/{member_id}",
    response_model=ProjectMemberResponse,
    summary="تغییر نقش عضو پروژه",
    description="نقش manager/member عضو پروژه را تغییر می‌دهد.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404], 422: ERRORS[422]},
)
async def change_project_member_role(
    project_id: ProjectId,
    member_id: Annotated[UUID, Path(description="شناسهٔ عضویت پروژه")],
    payload: ProjectMemberRoleUpdate,
    user: CurrentUser,
    service: Service,
) -> ProjectMemberResponse:
    member = await service.change_project_member_role(
        user,
        project_id,
        member_id,
        role=payload.role,
    )
    return ProjectMemberResponse(data=ProjectMemberPublic.model_validate(member))


@router.delete(
    "/projects/{project_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف عضو پروژه",
    description="عضو غیرمالک پروژه را حذف می‌کند.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]},
)
async def remove_project_member(
    project_id: ProjectId,
    member_id: Annotated[UUID, Path(description="شناسهٔ عضویت پروژه")],
    user: CurrentUser,
    service: Service,
) -> Response:
    await service.remove_project_member(user, project_id, member_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/projects/{project_id}/columns",
    response_model=ColumnListResponse,
    summary="فهرست ستون‌های فعال",
    description="ستون‌های فعال پروژه را به‌ترتیب position با pagination برمی‌گرداند.",
    responses={401: ERRORS[401], 404: ERRORS[404], 422: ERRORS[422]},
)
async def list_columns(
    project_id: ProjectId,
    user: CurrentUser,
    service: Service,
    page: Page = 1,
    page_size: PageSize = 20,
) -> ColumnListResponse:
    items, total = await service.list_columns(
        user,
        project_id,
        page=page,
        page_size=page_size,
    )
    return ColumnListResponse(
        data=[ColumnPublic.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/projects/{project_id}/columns",
    response_model=ColumnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ساخت ستون",
    description="ستون جدید را در پایان فهرست ستون‌های فعال پروژه می‌افزاید.",
    responses={
        401: ERRORS[401],
        403: ERRORS[403],
        404: ERRORS[404],
        409: ERRORS[409],
        422: ERRORS[422],
    },
)
async def create_column(
    project_id: ProjectId,
    payload: ColumnCreate,
    user: CurrentUser,
    service: Service,
) -> ColumnResponse:
    column = await service.create_column(
        user,
        project_id,
        name=payload.name,
        is_done=payload.is_done,
    )
    return ColumnResponse(data=ColumnPublic.model_validate(column))


@router.patch(
    "/projects/{project_id}/columns/{column_id}",
    response_model=ColumnResponse,
    summary="ویرایش ستون",
    description="نام و پرچم is_done ستون فعال را تغییر می‌دهد.",
    responses={
        401: ERRORS[401],
        403: ERRORS[403],
        404: ERRORS[404],
        409: ERRORS[409],
        422: ERRORS[422],
    },
)
async def update_column(
    project_id: ProjectId,
    column_id: Annotated[UUID, Path(description="شناسهٔ ستون")],
    payload: ColumnUpdate,
    user: CurrentUser,
    service: Service,
) -> ColumnResponse:
    column = await service.update_column(
        user,
        project_id,
        column_id,
        name=payload.name,
        is_done=payload.is_done,
    )
    return ColumnResponse(data=ColumnPublic.model_validate(column))


@router.post(
    "/projects/{project_id}/columns/{column_id}/archive",
    response_model=ColumnResponse,
    summary="آرشیو ستون",
    description="ستون فعال را آرشیو می‌کند و از فهرست فعال حذف می‌کند.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]},
)
async def archive_column(
    project_id: ProjectId,
    column_id: Annotated[UUID, Path(description="شناسهٔ ستون")],
    user: CurrentUser,
    service: Service,
) -> ColumnResponse:
    column = await service.archive_column(user, project_id, column_id)
    return ColumnResponse(data=ColumnPublic.model_validate(column))


@router.put(
    "/projects/{project_id}/columns/reorder",
    response_model=ColumnListResponse,
    summary="ترتیب ستون‌ها",  # noqa: RUF001
    description=(
        "فهرست کامل شناسهٔ ستون‌های فعال را می‌گیرد و موقعیت‌ها را اتمیک بازنویسی می‌کند؛ "  # noqa: RUF001
        "فهرست ناقص یا ناهم‌خوانا 409 برمی‌گرداند."
    ),
    responses={
        401: ERRORS[401],
        403: ERRORS[403],
        404: ERRORS[404],
        409: ERRORS[409],
        422: ERRORS[422],
    },
)
async def reorder_columns(
    project_id: ProjectId,
    payload: ColumnReorder,
    user: CurrentUser,
    service: Service,
) -> ColumnListResponse:
    columns = await service.reorder_columns(user, project_id, payload.column_ids)
    return ColumnListResponse(
        data=[ColumnPublic.model_validate(column) for column in columns],
        page=1,
        page_size=len(columns),
        total=len(columns),
    )
