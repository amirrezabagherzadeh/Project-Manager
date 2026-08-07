from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskPriority


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    column_id: UUID
    description: str | None = Field(default=None, max_length=10000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_at: datetime | None = None
    parent_id: UUID | None = None

    @field_validator("title")
    @classmethod
    def non_blank_title(cls, value: str) -> str:
        if not (value := value.strip()):
            raise ValueError("Task title must not be blank")
        return value


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=10000)
    priority: TaskPriority | None = None
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def non_blank_title(cls, value: str | None) -> str | None:
        if value is not None and not (value := value.strip()):
            raise ValueError("Task title must not be blank")
        return value


class TaskMove(BaseModel):
    target_column_id: UUID
    target_index: int = Field(ge=0)
    version: int = Field(ge=1)


class TaskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    column_id: UUID
    parent_id: UUID | None
    title: str
    description: str | None
    priority: TaskPriority
    position: int
    version: int
    due_at: datetime | None
    completed_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskResponse(BaseModel):
    data: TaskPublic


class TaskAssigneePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: UUID


class TaskLabelPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    label_id: UUID
    label: "LabelPublic"


class TaskDetailPublic(TaskPublic):
    assignees: list[TaskAssigneePublic]
    task_labels: list[TaskLabelPublic]
    subtasks: list[TaskPublic]


class TaskDetailResponse(BaseModel):
    data: TaskDetailPublic


class TaskListResponse(BaseModel):
    data: list[TaskPublic]
    page: int
    page_size: int
    total: int


class LabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=20)

    @field_validator("name")
    @classmethod
    def non_blank_name(cls, value: str) -> str:
        if not (value := value.strip()):
            raise ValueError("Label name must not be blank")
        return value


class LabelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=20)

    @field_validator("name")
    @classmethod
    def non_blank_name(cls, value: str | None) -> str | None:
        if value is not None and not (value := value.strip()):
            raise ValueError("Label name must not be blank")
        return value


class LabelPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    name: str
    color: str | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LabelResponse(BaseModel):
    data: LabelPublic


class LabelListResponse(BaseModel):
    data: list[LabelPublic]
    page: int
    page_size: int
    total: int


class TaskAssigneeCreate(BaseModel):
    user_id: UUID


class TaskLabelCreate(BaseModel):
    label_id: UUID
