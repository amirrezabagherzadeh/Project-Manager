from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.project import ProjectRole


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, examples=["تیم محصول"])
    key: str = Field(min_length=1, max_length=20, examples=["PM"])
    description: str | None = Field(default=None, max_length=5000)
    is_private: bool = Field(default=False)
    color: str | None = Field(default=None, max_length=20)
    start_date: datetime | None = Field(default=None)
    due_date: datetime | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def reject_blank_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Project name must not be blank")
        return value

    @field_validator("key")
    @classmethod
    def normalize_key(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("Project key must not be blank")
        return value


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    is_private: bool | None = Field(default=None)
    color: str | None = Field(default=None, max_length=20)
    start_date: datetime | None = Field(default=None)
    due_date: datetime | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def reject_blank_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Project name must not be blank")
        return value


class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    key: str
    description: str | None
    is_private: bool
    color: str | None
    start_date: datetime | None
    due_date: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProjectResponse(BaseModel):
    data: ProjectPublic


class ProjectListResponse(BaseModel):
    data: list[ProjectPublic]
    page: int
    page_size: int
    total: int


class ProjectMemberCreate(BaseModel):
    user_id: UUID = Field(description="شناسهٔ کاربر موجود در فضای کاری")
    role: ProjectRole = ProjectRole.MEMBER


class ProjectMemberRoleUpdate(BaseModel):
    role: ProjectRole


class ProjectMemberIdentityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    avatar_content_type: str | None


class ProjectMemberPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    user_id: UUID
    role: ProjectRole
    joined_at: datetime
    user: ProjectMemberIdentityPublic


class ProjectMemberResponse(BaseModel):
    data: ProjectMemberPublic


class ProjectMemberListResponse(BaseModel):
    data: list[ProjectMemberPublic]
    page: int
    page_size: int
    total: int


class ColumnCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80, examples=["در حال انجام"])
    is_done: bool = Field(default=False)

    @field_validator("name")
    @classmethod
    def reject_blank_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Column name must not be blank")
        return value


class ColumnUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    is_done: bool | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def reject_blank_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Column name must not be blank")
        return value


class ColumnReorder(BaseModel):
    column_ids: list[UUID] = Field(
        min_length=1,
        description="فهرست مرتب کامل شناسهٔ ستون‌های فعال پروژه",
    )


class ColumnPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    position: int
    is_done: bool
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ColumnResponse(BaseModel):
    data: ColumnPublic


class ColumnListResponse(BaseModel):
    data: list[ColumnPublic]
    page: int
    page_size: int
    total: int
