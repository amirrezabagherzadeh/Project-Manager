from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)

    @field_validator("body")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not (value := value.strip()):
            raise ValueError("Comment must not be blank")
        return value


class CommentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    author_id: UUID
    body: str
    created_at: datetime
    updated_at: datetime


class CommentResponse(BaseModel):
    data: CommentPublic


class CommentListResponse(BaseModel):
    data: list[CommentPublic]
    page: int
    page_size: int
    total: int


class ChecklistCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class ChecklistUpdate(ChecklistCreate):
    pass


class ChecklistItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    completed: bool = False


class ChecklistItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    completed: bool | None = None


class ChecklistItemReorder(BaseModel):
    item_ids: list[UUID] = Field(min_length=1)


class ChecklistPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    title: str
    position: int


class ChecklistItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    checklist_id: UUID
    title: str
    completed: bool
    position: int


class ChecklistResponse(BaseModel):
    data: ChecklistPublic


class ChecklistDetailPublic(ChecklistPublic):
    items: list[ChecklistItemPublic]
    completed_items: int
    total_items: int


class ChecklistListResponse(BaseModel):
    data: list[ChecklistDetailPublic]


class ChecklistItemResponse(BaseModel):
    data: ChecklistItemPublic


class AttachmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    uploaded_by_id: UUID
    original_name: str
    content_type: str
    size_bytes: int
    created_at: datetime


class AttachmentResponse(BaseModel):
    data: AttachmentPublic


class AttachmentListResponse(BaseModel):
    data: list[AttachmentPublic]


class ActivityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    actor_id: UUID | None
    action: str
    created_at: datetime


class ActivityListResponse(BaseModel):
    data: list[ActivityPublic]
