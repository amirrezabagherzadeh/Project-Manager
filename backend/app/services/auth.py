from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_boundaries import generate_refresh_token, hash_refresh_token
from app.core.config import Settings
from app.core.exceptions import (
    authentication_required,
    invalid_credentials,
    resource_conflict,
    token_expired,
)
from app.core.security import (
    AccessTokenExpiredError,
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    normalize_email,
    verify_password_or_dummy,
)
from app.models.base import utc_now
from app.models.identity import RefreshSession, User
from app.repositories.identity import (
    RefreshChainLimitError,
    RefreshSessionRepository,
    UserRepository,
)


@dataclass(frozen=True)
class LoginResult:
    user: User
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._session = session
        self._settings = settings
        self._clock = clock
        self._users = UserRepository(session)
        self._refresh_sessions = RefreshSessionRepository(session)

    async def register(self, *, name: str, email: str, password: str) -> User:
        normalized_email = normalize_email(email)
        password_hash = await hash_password(password)
        user = User(
            name=name.strip(),
            email=normalized_email,
            password_hash=password_hash,
        )
        try:
            async with self._session.begin():
                if await self._users.get_by_email(normalized_email) is not None:
                    raise resource_conflict("کاربری با این ایمیل وجود دارد.")
                await self._users.add(user)
        except IntegrityError as exc:
            raise resource_conflict("کاربری با این ایمیل وجود دارد.") from exc
        return user

    async def login(self, *, email: str, password: str) -> LoginResult:
        normalized_email = normalize_email(email)
        async with self._session.begin():
            user = await self._users.get_by_email(normalized_email)

        password_hash = user.password_hash if user is not None else None
        password_is_valid = await verify_password_or_dummy(password, password_hash)
        if not password_is_valid or user is None or not user.is_active:
            raise invalid_credentials()

        refresh_token = generate_refresh_token()
        now = self._clock()
        refresh_session = RefreshSession(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            created_at=now,
            expires_at=now + timedelta(days=self._settings.refresh_token_expire_days),
        )
        async with self._session.begin():
            current_user = await self._users.get_by_id(user.id)
            if current_user is None or not current_user.is_active:
                raise invalid_credentials()
            await self._refresh_sessions.add(refresh_session)

        return LoginResult(
            user=user,
            access_token=self._access_token(user.id, now=now),
            refresh_token=refresh_token,
        )

    async def current_user(self, access_token: str) -> User:
        try:
            claims = decode_access_token(
                access_token,
                secret_key=self._settings.secret_key.get_secret_value(),
                algorithm=self._settings.jwt_algorithm,
            )
        except AccessTokenExpiredError as exc:
            raise token_expired() from exc
        except InvalidAccessTokenError as exc:
            raise authentication_required() from exc

        async with self._session.begin():
            user = await self._users.get_by_id(claims.subject)
        if user is None or not user.is_active:
            raise authentication_required()
        return user

    async def refresh(self, refresh_token: str) -> LoginResult:
        token_hash = hash_refresh_token(refresh_token)
        now = self._clock()
        replacement_token: str | None = None
        replacement_user: User | None = None
        replay_detected = False

        async with self._session.begin():
            current = await self._refresh_sessions.get_by_token_hash(token_hash)
            if current is None or current.expires_at <= now or not current.user.is_active:
                raise authentication_required()

            if current.revoked_at is not None:
                if current.replaced_by_id is not None:
                    replay_detected = True
                    current.replay_detected_at = now
                    try:
                        chain = await self._refresh_sessions.get_replacement_chain(current)
                    except RefreshChainLimitError:
                        await self._refresh_sessions.revoke_active_for_user(
                            current.user_id,
                            revoked_at=now,
                        )
                    else:
                        for item in chain[1:]:
                            if item.revoked_at is None:
                                item.revoked_at = now
                    await self._session.flush()
            else:
                replacement_token = generate_refresh_token()
                replacement = RefreshSession(
                    user_id=current.user_id,
                    token_hash=hash_refresh_token(replacement_token),
                    created_at=now,
                    expires_at=now + timedelta(days=self._settings.refresh_token_expire_days),
                )
                current.revoked_at = now
                await self._refresh_sessions.add(replacement)
                await self._refresh_sessions.link_replacement(current, replacement)
                replacement_user = current.user

        if replay_detected or replacement_token is None or replacement_user is None:
            raise authentication_required()
        return LoginResult(
            user=replacement_user,
            access_token=self._access_token(replacement_user.id, now=now),
            refresh_token=replacement_token,
        )

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        now = self._clock()
        async with self._session.begin():
            current = await self._refresh_sessions.get_by_token_hash(
                hash_refresh_token(refresh_token)
            )
            if current is not None and current.revoked_at is None:
                current.revoked_at = now
                await self._session.flush()

    def _access_token(self, user_id: UUID, *, now: datetime | None = None) -> str:
        return create_access_token(
            user_id=user_id,
            secret_key=self._settings.secret_key.get_secret_value(),
            algorithm=self._settings.jwt_algorithm,
            expires_minutes=self._settings.access_token_expire_minutes,
            now=now,
        )
