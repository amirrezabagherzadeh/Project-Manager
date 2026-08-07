from typing import Any, Literal

from pydantic import BaseModel


class HealthData(BaseModel):
    status: Literal["ok"]


class HealthResponse(BaseModel):
    data: HealthData


class ErrorData(BaseModel):
    code: str
    message: str
    details: Any = None
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorData
