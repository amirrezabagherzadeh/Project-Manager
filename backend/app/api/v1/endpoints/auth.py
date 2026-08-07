import hashlib
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_app_settings,
    get_auth_service,
    get_current_user,
    get_rate_limiter,
    get_session,
)
from app.api.error_handlers import render_domain_error
from app.core.auth_boundaries import (
    UntrustedOriginError,
    clear_refresh_cookie,
    set_refresh_cookie,
    validate_request_origin,
)
from app.core.config import Settings
from app.core.exceptions import DomainError, permission_denied, rate_limited, resource_not_found
from app.core.rate_limit import RateLimiter
from app.core.security import normalize_email
from app.models.identity import User
from app.schemas.auth import (
    ProfileUpdate,
    TokenResponse,
    UserPublic,
    UserRegistration,
    UserResponse,
)
from app.schemas.common import ErrorResponse
from app.services.auth import AuthService
from app.storage.local import LocalStorageService

router = APIRouter(prefix="/auth", tags=["authentication"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "احراز هویت ناموفق است."},
    403: {"model": ErrorResponse, "description": "مبدأ درخواست مجاز نیست."},
    409: {"model": ErrorResponse, "description": "داده با رکورد موجود تداخل دارد."},
    422: {"model": ErrorResponse, "description": "دادهٔ ورودی معتبر نیست."},
    429: {"model": ErrorResponse, "description": "محدودیت تعداد درخواست رد شده است."},
}


@router.post(
    "/register",
    summary="ثبت‌نام کاربر",
    description=(
        "حساب جدید را با ایمیل یکتای lowercase می‌سازد. این عملیات نشست ورود ایجاد نمی‌کند."
    ),
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "کاربر ایجاد شد.",
            "content": {
                "application/json": {
                    "example": {
                        "data": {
                            "id": "8b02464d-932d-4f30-8e8d-9b6b1ef4762b",
                            "email": "user@example.com",
                            "name": "کاربر نمونه",
                            "is_active": True,
                            "created_at": "2026-07-29T12:00:00Z",
                            "updated_at": "2026-07-29T12:00:00Z",
                        }
                    }
                }
            },
        },
        409: ERROR_RESPONSES[409],
        422: ERROR_RESPONSES[422],
        429: ERROR_RESPONSES[429],
    },
)
async def register(
    payload: UserRegistration,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> UserResponse:
    _enforce_rate_limit(
        limiter,
        key=f"register:{_client_address(request)}",
        limit=settings.register_rate_limit_requests,
        window_seconds=settings.register_rate_limit_window_seconds,
    )
    user = await service.register(
        name=payload.name,
        email=str(payload.email),
        password=payload.password.get_secret_value(),
    )
    return UserResponse(data=UserPublic.model_validate(user))


@router.post(
    "/token",
    summary="ورود و دریافت Access Token",
    description=(
        "OAuth2 Password Flow: ایمیل در فیلد username و رمز در password ارسال "
        "می‌شود؛ Access Token در پاسخ و Refresh Token در Cookie قرار می‌گیرد."
    ),
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "ورود موفق است.",
            "content": {
                "application/json": {"example": {"access_token": "eyJ...", "token_type": "bearer"}}
            },
        },
        401: ERROR_RESPONSES[401],
        422: ERROR_RESPONSES[422],
        429: ERROR_RESPONSES[429],
    },
)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> TokenResponse:
    normalized_email = normalize_email(form.username)
    email_key = hashlib.sha256(normalized_email.encode("utf-8")).hexdigest()
    _enforce_rate_limit(
        limiter,
        key=f"login:{_client_address(request)}:{email_key}",
        limit=settings.login_rate_limit_requests,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    result = await service.login(email=normalized_email, password=form.password)
    set_refresh_cookie(response, result.refresh_token, settings)
    return TokenResponse(access_token=result.access_token)


@router.post(
    "/refresh",
    summary="نوسازی نشست",
    description=(
        "Refresh Cookie معتبر را به‌صورت اتمیک می‌چرخاند و Access Token جدید "
        "برمی‌گرداند. ارسال Origin فقط برای مبدأهای مجاز پذیرفته می‌شود."
    ),
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "نشست چرخانده شد.",
            "content": {
                "application/json": {"example": {"access_token": "eyJ...", "token_type": "bearer"}}
            },
        },
        401: ERROR_RESPONSES[401],
        403: ERROR_RESPONSES[403],
    },
)
async def refresh(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> TokenResponse | JSONResponse:
    _validate_origin(request, settings)
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    try:
        if refresh_token is None:
            from app.core.exceptions import authentication_required

            raise authentication_required()
        result = await service.refresh(refresh_token)
    except DomainError as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            error_response = render_domain_error(request, exc)
            clear_refresh_cookie(error_response, settings)
            return error_response
        raise
    set_refresh_cookie(response, result.refresh_token, settings)
    return TokenResponse(access_token=result.access_token)


@router.post(
    "/logout",
    summary="خروج از نشست",
    description=(
        "Refresh Session شناخته‌شده را revoke و Cookie را پاک می‌کند؛ نبود نشست نیز پاسخ یکسان دارد."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={
        204: {"description": "Cookie پاک و نشست در صورت وجود revoke شد."},
        403: ERROR_RESPONSES[403],
    },
)
async def logout(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> None:
    _validate_origin(request, settings)
    await service.logout(request.cookies.get(settings.refresh_cookie_name))
    clear_refresh_cookie(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT


@router.get(
    "/me",
    summary="هویت کاربر جاری",
    description="اطلاعات عمومی کاربر متناظر با Bearer Access Token را برمی‌گرداند.",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "هویت معتبر است.",
            "content": {
                "application/json": {
                    "example": {
                        "data": {
                            "id": "8b02464d-932d-4f30-8e8d-9b6b1ef4762b",
                            "email": "user@example.com",
                            "name": "کاربر نمونه",
                            "is_active": True,
                            "created_at": "2026-07-29T12:00:00Z",
                            "updated_at": "2026-07-29T12:00:00Z",
                        }
                    }
                }
            },
        },
        401: ERROR_RESPONSES[401],
    },
)
async def me(
    user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse(data=UserPublic.model_validate(user))


@router.patch("/profile", response_model=UserResponse, summary="ویرایش پروفایل")
async def update_profile(
    payload: ProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    async with session.begin():
        if payload.name is not None:
            user.name = payload.name
        if payload.timezone is not None:
            user.timezone = payload.timezone
        await session.flush()
        return UserResponse(data=UserPublic.model_validate(user))


@router.post("/profile/avatar", response_model=UserResponse, summary="بارگذاری آواتار")
async def upload_avatar(
    file: Annotated[UploadFile, File(description="JPEG یا PNG تا 10MB")],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> UserResponse:
    data = await file.read()
    if file.content_type not in {"image/jpeg", "image/png"}:
        raise DomainError(
            status_code=415, code="unsupported_file_type", message="نوع آواتار مجاز نیست."
        )
    storage = LocalStorageService(settings.attachment_storage_path / "avatars")
    storage_name = storage.save(
        original_name=file.filename or "", content_type=file.content_type or "", data=data
    )
    old_name = user.avatar_storage_name
    try:
        async with session.begin():
            user.avatar_storage_name = storage_name
            user.avatar_content_type = file.content_type
            await session.flush()
            result = UserResponse(data=UserPublic.model_validate(user))
    except Exception:
        storage.delete(storage_name)
        raise
    if old_name is not None:
        storage.delete(old_name)
    return result


@router.get("/profile/avatar", summary="دریافت آواتار کاربر جاری")
async def read_avatar(
    user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> Response:
    if user.avatar_storage_name is None or user.avatar_content_type is None:
        raise resource_not_found()
    storage = LocalStorageService(settings.attachment_storage_path / "avatars")
    try:
        content = storage.read(user.avatar_storage_name)
    except FileNotFoundError as exc:
        raise resource_not_found() from exc
    return Response(content=content, media_type=user.avatar_content_type)


@router.delete("/profile/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> Response:
    old_name = user.avatar_storage_name
    async with session.begin():
        user.avatar_storage_name = None
        user.avatar_content_type = None
        await session.flush()
    if old_name is not None:
        LocalStorageService(settings.attachment_storage_path / "avatars").delete(old_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _client_address(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def _enforce_rate_limit(
    limiter: RateLimiter,
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    decision = limiter.check(
        key,
        limit=limit,
        window_seconds=window_seconds,
    )
    if not decision.allowed:
        raise rate_limited(decision.retry_after_seconds)


def _validate_origin(request: Request, settings: Settings) -> None:
    try:
        validate_request_origin(request.headers.get("Origin"), settings)
    except UntrustedOriginError as exc:
        raise permission_denied() from exc
