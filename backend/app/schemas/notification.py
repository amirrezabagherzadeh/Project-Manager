from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    type: str
    title: str
    body: str | None
    entity_type: str | None
    entity_id: UUID | None
    action_url: str | None
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    data: list[NotificationPublic]
    unread_count: int


class NotificationCountResponse(BaseModel):
    data: int
