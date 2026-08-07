from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from fastapi.responses import Response as FileResponse

from app.api.deps import get_collaboration_service, get_current_user
from app.models.identity import User
from app.schemas.collaboration import (
    ActivityListResponse,
    ActivityPublic,
    AttachmentListResponse,
    AttachmentPublic,
    AttachmentResponse,
    ChecklistCreate,
    ChecklistDetailPublic,
    ChecklistItemCreate,
    ChecklistItemPublic,
    ChecklistItemReorder,
    ChecklistItemResponse,
    ChecklistItemUpdate,
    ChecklistListResponse,
    ChecklistPublic,
    ChecklistResponse,
    ChecklistUpdate,
    CommentCreate,
    CommentListResponse,
    CommentPublic,
    CommentResponse,
)
from app.services.collaboration import CollaborationService

router = APIRouter(tags=["collaboration"])
CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[CollaborationService, Depends(get_collaboration_service)]
AttachmentFile = Annotated[UploadFile, File(description="PDF، JPEG، PNG یا متن تا 10MB")]


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ثبت نظر",
    description="برای وظیفه قابل دسترسی یک نظر متنی ثبت می‌کند.",
)
async def create_comment(
    task_id: UUID, payload: CommentCreate, user: CurrentUser, service: Service
) -> CommentResponse:
    return CommentResponse(
        data=CommentPublic.model_validate(
            await service.create_comment(user, task_id, body=payload.body)
        )
    )


@router.post(
    "/tasks/{task_id}/checklists",
    response_model=ChecklistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ساخت چک‌لیست",
    description="چک‌لیست مرتب برای وظیفه می‌سازد.",
)
async def create_checklist(
    task_id: UUID, payload: ChecklistCreate, user: CurrentUser, service: Service
) -> ChecklistResponse:
    return ChecklistResponse(
        data=ChecklistPublic.model_validate(
            await service.create_checklist(user, task_id, title=payload.title)
        )
    )


@router.get("/tasks/{task_id}/checklists", response_model=ChecklistListResponse)
async def list_checklists(
    task_id: UUID, user: CurrentUser, service: Service
) -> ChecklistListResponse:
    rows = await service.list_checklists(user, task_id)
    return ChecklistListResponse(
        data=[
            ChecklistDetailPublic(
                **ChecklistPublic.model_validate(checklist).model_dump(),
                items=[ChecklistItemPublic.model_validate(item) for item in items],
                completed_items=sum(item.completed for item in items),
                total_items=len(items),
            )
            for checklist, items in rows
        ]
    )


@router.patch("/checklists/{checklist_id}", response_model=ChecklistResponse)
async def update_checklist(
    checklist_id: UUID, payload: ChecklistUpdate, user: CurrentUser, service: Service
) -> ChecklistResponse:
    return ChecklistResponse(
        data=ChecklistPublic.model_validate(
            await service.update_checklist(user, checklist_id, title=payload.title)
        )
    )


@router.delete("/checklists/{checklist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist(checklist_id: UUID, user: CurrentUser, service: Service) -> Response:
    await service.delete_checklist(user, checklist_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/checklists/{checklist_id}/items",
    response_model=ChecklistItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="افزودن آیتم چک‌لیست",
)
async def create_checklist_item(
    checklist_id: UUID, payload: ChecklistItemCreate, user: CurrentUser, service: Service
) -> ChecklistItemResponse:
    return ChecklistItemResponse(
        data=ChecklistItemPublic.model_validate(
            await service.create_checklist_item(
                user, checklist_id, title=payload.title, completed=payload.completed
            )
        )
    )


@router.patch(
    "/checklist-items/{item_id}",
    response_model=ChecklistItemResponse,
    summary="ویرایش آیتم چک‌لیست",
)
async def update_checklist_item(
    item_id: UUID, payload: ChecklistItemUpdate, user: CurrentUser, service: Service
) -> ChecklistItemResponse:
    return ChecklistItemResponse(
        data=ChecklistItemPublic.model_validate(
            await service.update_checklist_item(
                user, item_id, title=payload.title, completed=payload.completed
            )
        )
    )


@router.put("/checklists/{checklist_id}/items/reorder", response_model=list[ChecklistItemPublic])
async def reorder_checklist_items(
    checklist_id: UUID, payload: ChecklistItemReorder, user: CurrentUser, service: Service
) -> list[ChecklistItemPublic]:
    return [
        ChecklistItemPublic.model_validate(item)
        for item in await service.reorder_checklist_items(
            user, checklist_id, item_ids=payload.item_ids
        )
    ]


@router.delete("/checklist-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist_item(item_id: UUID, user: CurrentUser, service: Service) -> Response:
    await service.delete_checklist_item(user, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/tasks/{task_id}/comments",
    response_model=CommentListResponse,
    summary="فهرست نظرها",
    description="نظرهای وظیفه را با pagination برمی‌گرداند.",
)
async def list_comments(
    task_id: UUID,
    user: CurrentUser,
    service: Service,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CommentListResponse:
    items, total = await service.list_comments(user, task_id, page=page, page_size=page_size)
    return CommentListResponse(
        data=[CommentPublic.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    summary="ویرایش نظر",
    description="نظر خود یا نظر با مجوز مدیریتی را ویرایش می‌کند.",
)
async def update_comment(
    comment_id: UUID, payload: CommentCreate, user: CurrentUser, service: Service
) -> CommentResponse:
    return CommentResponse(
        data=CommentPublic.model_validate(
            await service.update_comment(user, comment_id, body=payload.body)
        )
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف نظر",
    description="نظر خود یا نظر با مجوز مدیریتی را حذف می‌کند.",
)
async def delete_comment(comment_id: UUID, user: CurrentUser, service: Service) -> Response:
    await service.delete_comment(user, comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/tasks/{task_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="بارگذاری پیوست",
)
async def upload_attachment(
    task_id: UUID,
    user: CurrentUser,
    service: Service,
    file: AttachmentFile,
) -> AttachmentResponse:
    data = await file.read()
    attachment = await service.upload_attachment(
        user,
        task_id,
        original_name=file.filename or "",
        content_type=file.content_type or "",
        data=data,
    )
    return AttachmentResponse(data=AttachmentPublic.model_validate(attachment))


@router.get(
    "/tasks/{task_id}/attachments",
    response_model=AttachmentListResponse,
    summary="فهرست پیوست‌ها",  # noqa: RUF001
)
async def list_attachments(
    task_id: UUID, user: CurrentUser, service: Service
) -> AttachmentListResponse:
    return AttachmentListResponse(
        data=[
            AttachmentPublic.model_validate(item)
            for item in await service.list_attachments(user, task_id)
        ]
    )


@router.get("/attachments/{attachment_id}/download", summary="دریافت پیوست")
async def download_attachment(
    attachment_id: UUID, user: CurrentUser, service: Service
) -> FileResponse:
    attachment, data = await service.download_attachment(user, attachment_id)
    return FileResponse(
        content=data,
        media_type=attachment.content_type,
        headers={"Content-Disposition": f'attachment; filename="{attachment.original_name}"'},
    )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(attachment_id: UUID, user: CurrentUser, service: Service) -> Response:
    await service.delete_attachment(user, attachment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/tasks/{task_id}/activity", response_model=ActivityListResponse, summary="تاریخچه وظیفه"
)
async def list_task_activity(
    task_id: UUID, user: CurrentUser, service: Service
) -> ActivityListResponse:
    return ActivityListResponse(
        data=[
            ActivityPublic.model_validate(item)
            for item in await service.list_activity(user, task_id)
        ]
    )
