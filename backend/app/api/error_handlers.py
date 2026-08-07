from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.exceptions import DomainError
from app.core.request_id import get_request_id


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": get_request_id(request),
            }
        },
    )


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, DomainError):
        return await unhandled_exception_handler(request, exc)
    return render_domain_error(request, exc)


def render_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    return _error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HTTPException):
        return await unhandled_exception_handler(request, exc)
    message = exc.detail if isinstance(exc.detail, str) else "درخواست قابل انجام نیست."
    return _error_response(
        request,
        status_code=exc.status_code,
        code="resource_not_found" if exc.status_code == 404 else "invalid_operation",
        message=message,
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return await unhandled_exception_handler(request, exc)
    safe_details = [
        {
            "location": list(error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return _error_response(
        request,
        status_code=422,
        code="validation_error",
        message="داده‌های ورودی معتبر نیست.",
        details=safe_details,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request.app.state.logger.exception(
        "Unhandled application error",
        extra={"request_id": get_request_id(request)},
    )
    return _error_response(
        request,
        status_code=500,
        code="internal_error",
        message="خطایی رخ داد. دوباره تلاش کنید.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
