from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.workspace import WorkspaceRole


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, examples=["تیم محصول"])
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("name")
    @classmethod
    def reject_blank_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Workspace name must not be blank")
        return value


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("name")
    @classmethod
    def reject_blank_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Workspace name must not be blank")
        return value


class WorkspacePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WorkspaceResponse(BaseModel):
    data: WorkspacePublic


class WorkspaceListResponse(BaseModel):
    data: list[WorkspacePublic]
    page: int
    page_size: int
    total: int


class MemberCreate(BaseModel):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.MEMBER


class MemberRoleUpdate(BaseModel):
    role: WorkspaceRole


class MemberIdentityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    name: str
    avatar_content_type: str | None


class MemberPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    joined_at: datetime
    user: MemberIdentityPublic


class MemberResponse(BaseModel):
    data: MemberPublic


class MemberListResponse(BaseModel):
    data: list[MemberPublic]
    page: int
    page_size: int
    total: int


class InvitationCreate(BaseModel):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.MEMBER


class InvitationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    email: EmailStr
    role: WorkspaceRole
    invited_by_id: UUID
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None


class InvitationCreatedPublic(InvitationPublic):
    token: str = Field(description="توکن یک‌بارنمایش پذیرش دعوت")


class InvitationResponse(BaseModel):
    data: InvitationPublic


class InvitationCreatedResponse(BaseModel):
    data: InvitationCreatedPublic


class InvitationListResponse(BaseModel):
    data: list[InvitationPublic]
    page: int
    page_size: int
    total: int
