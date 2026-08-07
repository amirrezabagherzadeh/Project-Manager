from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.core.exceptions import resource_not_found
from app.models.base import utc_now
from app.models.identity import User
from app.models.workspace import Notification
from app.schemas.notification import (
    NotificationCountResponse,
    NotificationListResponse,
    NotificationPublic,
)

router = APIRouter(tags=["notifications"])
CurrentUser = Annotated[User, Depends(get_current_user)]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    user: CurrentUser, session: Session, page: Annotated[int, Query(ge=1)] = 1
) -> NotificationListResponse:
    async with session.begin():
        unread = await session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        )
        items = list(
            await session.scalars(
                select(Notification)
                .where(Notification.user_id == user.id)
                .order_by(Notification.created_at.desc(), Notification.id.desc())
                .offset((page - 1) * 50)
                .limit(50)
            )
        )
        return NotificationListResponse(
            data=[NotificationPublic.model_validate(item) for item in items],
            unread_count=int(unread or 0),
        )


@router.get("/notifications/unread-count", response_model=NotificationCountResponse)
async def unread_count(user: CurrentUser, session: Session) -> NotificationCountResponse:
    async with session.begin():
        count = await session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        )
        return NotificationCountResponse(data=int(count or 0))


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(notification_id: UUID, user: CurrentUser, session: Session) -> Response:
    async with session.begin():
        item = await session.get(Notification, notification_id)
        if item is None or item.user_id != user.id:
            raise resource_not_found()
        item.read_at = item.read_at or utc_now()
        await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(user: CurrentUser, session: Session) -> Response:
    async with session.begin():
        await session.execute(
            update(Notification)
            .where(Notification.user_id == user.id, Notification.read_at.is_(None))
            .values(read_at=utc_now())
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
