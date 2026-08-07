from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.database import Database
from app.core.exceptions import authentication_required
from app.core.rate_limit import RateLimiter
from app.models.identity import User
from app.services.auth import AuthService
from app.services.collaboration import CollaborationService
from app.services.project import ProjectService
from app.services.reporting import ReportingService
from app.services.task import TaskService
from app.services.workspace import WorkspaceService
from app.storage.local import LocalStorageService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scheme_name="OAuth2Password",
    description="ورود با ایمیل در فیلد username و رمز عبور.",
    auto_error=False,
)


def get_database(request: Request) -> Database:
    database = request.app.state.database
    if not isinstance(database, Database):
        raise RuntimeError("Application database is not configured")
    return database


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    database = get_database(request)
    async with database.session() as session:
        yield session


def get_app_settings(request: Request) -> Settings:
    settings = request.app.state.settings
    if not isinstance(settings, Settings):
        raise RuntimeError("Application settings are not configured")
    return settings


def get_rate_limiter(request: Request) -> RateLimiter:
    return cast(RateLimiter, request.app.state.rate_limiter)


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AuthService:
    return AuthService(session, settings)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    if token is None:
        raise authentication_required()
    return await service.current_user(token)


def get_workspace_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceService:
    return WorkspaceService(session)


def get_project_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectService:
    return ProjectService(session)


def get_task_service(session: Annotated[AsyncSession, Depends(get_session)]) -> TaskService:
    return TaskService(session)


def get_reporting_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReportingService:
    return ReportingService(session)


def get_collaboration_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> CollaborationService:
    return CollaborationService(session, LocalStorageService(settings.attachment_storage_path))
