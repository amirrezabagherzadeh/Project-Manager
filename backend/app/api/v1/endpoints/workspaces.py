from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.deps import get_current_user, get_workspace_service
from app.models.identity import User
from app.schemas.common import ErrorResponse
from app.schemas.workspace import (
    InvitationCreate,
    InvitationCreatedPublic,
    InvitationCreatedResponse,
    InvitationListResponse,
    InvitationPublic,
    InvitationResponse,
    MemberCreate,
    MemberListResponse,
    MemberPublic,
    MemberResponse,
    MemberRoleUpdate,
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspacePublic,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace import WorkspaceService

router = APIRouter(tags=["workspaces"])

ERRORS: dict[int, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "احراز هویت لازم است."},
    403: {"model": ErrorResponse, "description": "نقش کاربر مجاز نیست."},
    404: {"model": ErrorResponse, "description": "منبع در محدودهٔ کاربر پیدا نشد."},
    409: {"model": ErrorResponse, "description": "عملیات با وضعیت موجود تداخل دارد."},
    422: {"model": ErrorResponse, "description": "ورودی معتبر نیست."},
}

CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[WorkspaceService, Depends(get_workspace_service)]
WorkspaceId = Annotated[UUID, Path(description="شناسهٔ فضای کاری")]
Page = Annotated[int, Query(ge=1, description="شماره صفحه")]
PageSize = Annotated[int, Query(ge=1, le=100, description="اندازه صفحه، حداکثر 100")]


@router.post(
    "/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ساخت فضای کاری",
    description="فضای کاری، عضویت OWNER و Activity را در یک تراکنش می‌سازد.",
    responses={401: ERRORS[401], 422: ERRORS[422]},
)
async def create_workspace(
    payload: WorkspaceCreate,
    user: CurrentUser,
    service: Service,
) -> WorkspaceResponse:
    workspace = await service.create(
        user,
        name=payload.name,
        description=payload.description,
    )
    return WorkspaceResponse(data=WorkspacePublic.model_validate(workspace))


@router.get(
    "/workspaces",
    response_model=WorkspaceListResponse,
    summary="فهرست فضاهای کاری",
    description="فقط فضاهایی را برمی‌گرداند که کاربر جاری عضو آن‌هاست.",
    responses={401: ERRORS[401], 422: ERRORS[422]},
)
async def list_workspaces(
    user: CurrentUser,
    service: Service,
    page: Page = 1,
    page_size: PageSize = 20,
    include_archived: Annotated[bool, Query(description="شامل فضاهای کاری آرشیوشده")] = False,
) -> WorkspaceListResponse:
    items, total = await service.list_workspaces(
        user,
        include_archived=include_archived,
        page=page,
        page_size=page_size,
    )
    return WorkspaceListResponse(
        data=[WorkspacePublic.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="مشاهده فضای کاری",
    description="جزئیات یک فضای کاری عضو-محور را برمی‌گرداند.",
    responses={401: ERRORS[401], 404: ERRORS[404]},
)
async def read_workspace(
    workspace_id: WorkspaceId,
    user: CurrentUser,
    service: Service,
) -> WorkspaceResponse:
    workspace = await service.read(user, workspace_id)
    return WorkspaceResponse(data=WorkspacePublic.model_validate(workspace))


@router.patch(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponse,
    summary="ویرایش فضای کاری",
    description="OWNER یا ADMIN نام و توضیح را تغییر می‌دهد.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404], 422: ERRORS[422]},
)
async def update_workspace(
    workspace_id: WorkspaceId,
    payload: WorkspaceUpdate,
    user: CurrentUser,
    service: Service,
) -> WorkspaceResponse:
    workspace = await service.update(
        user,
        workspace_id,
        name=payload.name,
        description=payload.description,
    )
    return WorkspaceResponse(data=WorkspacePublic.model_validate(workspace))


@router.post(
    "/workspaces/{workspace_id}/archive",
    response_model=WorkspaceResponse,
    summary="آرشیو فضای کاری",
    description="OWNER یا ADMIN فضای کاری را آرشیو می‌کند.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]},
)
async def archive_workspace(
    workspace_id: WorkspaceId,
    user: CurrentUser,
    service: Service,
) -> WorkspaceResponse:
    return WorkspaceResponse(
        data=WorkspacePublic.model_validate(await service.archive(user, workspace_id))
    )


@router.post(
    "/workspaces/{workspace_id}/restore",
    response_model=WorkspaceResponse,
    summary="بازیابی فضای کاری",
    description="OWNER یا ADMIN فضای کاری آرشیوشده را بازیابی می‌کند.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]},
)
async def restore_workspace(
    workspace_id: WorkspaceId,
    user: CurrentUser,
    service: Service,
) -> WorkspaceResponse:
    return WorkspaceResponse(
        data=WorkspacePublic.model_validate(await service.restore(user, workspace_id))
    )


@router.delete(
    "/workspaces/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف دائمی فضای کاری",
    description="فقط OWNER می‌تواند فضای کاری را به‌صورت دائمی حذف کند.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]},
)
async def delete_workspace(
    workspace_id: WorkspaceId,
    user: CurrentUser,
    service: Service,
) -> Response:
    await service.delete(user, workspace_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/workspaces/{workspace_id}/members",
    response_model=MemberListResponse,
    summary="فهرست اعضا",
    description="اعضای فضای کاری را با pagination برمی‌گرداند.",
    responses={401: ERRORS[401], 404: ERRORS[404], 422: ERRORS[422]},
)
async def list_members(
    workspace_id: WorkspaceId,
    user: CurrentUser,
    service: Service,
    page: Page = 1,
    page_size: PageSize = 20,
) -> MemberListResponse:
    items, total = await service.list_members(
        user,
        workspace_id,
        page=page,
        page_size=page_size,
    )
    return MemberListResponse(
        data=[MemberPublic.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/workspaces/{workspace_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="افزودن عضو موجود",
    description="OWNER/ADMIN یک کاربر موجود را با نقش غیر OWNER اضافه می‌کند.",
    responses={
        401: ERRORS[401],
        403: ERRORS[403],
        404: ERRORS[404],
        409: ERRORS[409],
        422: ERRORS[422],
    },
)
async def add_member(
    workspace_id: WorkspaceId,
    payload: MemberCreate,
    user: CurrentUser,
    service: Service,
) -> MemberResponse:
    member = await service.add_member(
        user,
        workspace_id,
        email=str(payload.email),
        role=payload.role,
    )
    return MemberResponse(data=MemberPublic.model_validate(member))


@router.patch(
    "/workspaces/{workspace_id}/members/{member_id}",
    response_model=MemberResponse,
    summary="تغییر نقش یا انتقال مالکیت",
    description="نقش عضو را تغییر می‌دهد؛ تخصیص OWNER انتقال اتمیک مالکیت است.",
    responses={
        401: ERRORS[401],
        403: ERRORS[403],
        404: ERRORS[404],
        409: ERRORS[409],
        422: ERRORS[422],
    },
)
async def change_member_role(
    workspace_id: WorkspaceId,
    member_id: Annotated[UUID, Path(description="شناسهٔ عضویت")],
    payload: MemberRoleUpdate,
    user: CurrentUser,
    service: Service,
) -> MemberResponse:
    member = await service.change_member_role(
        user,
        workspace_id,
        member_id,
        role=payload.role,
    )
    return MemberResponse(data=MemberPublic.model_validate(member))


@router.delete(
    "/workspaces/{workspace_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف عضو",
    description="OWNER/ADMIN عضو غیرمالک را حذف می‌کند.",
    responses={
        401: ERRORS[401],
        403: ERRORS[403],
        404: ERRORS[404],
        409: ERRORS[409],
    },
)
async def remove_member(
    workspace_id: WorkspaceId,
    member_id: Annotated[UUID, Path(description="شناسهٔ عضویت")],
    user: CurrentUser,
    service: Service,
) -> Response:
    await service.remove_member(user, workspace_id, member_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/workspaces/{workspace_id}/invitations",
    response_model=InvitationListResponse,
    summary="فهرست دعوت‌ها",  # noqa: RUF001
    description="OWNER/ADMIN دعوت‌های فضای کاری را بدون token/hash می‌بیند.",
    responses={401: ERRORS[401], 403: ERRORS[403], 404: ERRORS[404]},
)
async def list_invitations(
    workspace_id: WorkspaceId,
    user: CurrentUser,
    service: Service,
    page: Page = 1,
    page_size: PageSize = 20,
) -> InvitationListResponse:
    items, total = await service.list_invitations(
        user,
        workspace_id,
        page=page,
        page_size=page_size,
    )
    return InvitationListResponse(
        data=[InvitationPublic.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/workspaces/{workspace_id}/invitations",
    response_model=InvitationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ساخت دعوت امن",
    description="توکن خام را فقط در همین پاسخ برمی‌گرداند و hash را ذخیره می‌کند.",
    responses={
        401: ERRORS[401],
        403: ERRORS[403],
        404: ERRORS[404],
        409: ERRORS[409],
        422: ERRORS[422],
    },
)
async def create_invitation(
    workspace_id: WorkspaceId,
    payload: InvitationCreate,
    user: CurrentUser,
    service: Service,
) -> InvitationCreatedResponse:
    result = await service.create_invitation(
        user,
        workspace_id,
        email=str(payload.email),
        role=payload.role,
    )
    public = InvitationPublic.model_validate(result.invitation)
    return InvitationCreatedResponse(
        data=InvitationCreatedPublic(**public.model_dump(), token=result.token)
    )


@router.post(
    "/workspaces/{workspace_id}/invitations/{invitation_id}/revoke",
    response_model=InvitationResponse,
    summary="لغو دعوت",
    description="OWNER/ADMIN دعوت pending را لغو می‌کند.",
    responses={
        401: ERRORS[401],
        403: ERRORS[403],
        404: ERRORS[404],
        409: ERRORS[409],
    },
)
async def revoke_invitation(
    workspace_id: WorkspaceId,
    invitation_id: Annotated[UUID, Path(description="شناسهٔ دعوت")],
    user: CurrentUser,
    service: Service,
) -> InvitationResponse:
    invitation = await service.revoke_invitation(user, workspace_id, invitation_id)
    return InvitationResponse(data=InvitationPublic.model_validate(invitation))


@router.post(
    "/invitations/{token}/accept",
    response_model=MemberResponse,
    summary="پذیرش دعوت",
    description="کاربر هم‌ایمیل دعوت معتبر را دقیقاً یک بار عضو می‌کند.",
    responses={401: ERRORS[401], 404: ERRORS[404], 409: ERRORS[409]},
)
async def accept_invitation(
    token: Annotated[str, Path(min_length=32, max_length=200, description="توکن پذیرش")],
    user: CurrentUser,
    service: Service,
) -> MemberResponse:
    member = await service.accept_invitation(user, token)
    return MemberResponse(data=MemberPublic.model_validate(member))
