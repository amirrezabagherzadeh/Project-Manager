import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import Database
from app.core.security import hash_password
from app.models.base import utc_now
from app.models.identity import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole

DEMO_EMAIL = "demo@example.com"
LEGACY_DEMO_EMAIL = "demo@local.test"
DEMO_WORKSPACE = "Demo Workspace"


async def seed() -> None:
    settings = get_settings()
    if settings.environment == "production":
        raise RuntimeError("Demo seed is disabled in production")
    database = Database(settings.database_url)
    try:
        async with database.session() as session, session.begin():
            user = await session.scalar(
                select(User).where(User.email.in_((DEMO_EMAIL, LEGACY_DEMO_EMAIL)))
            )
            if user is None:
                user = User(
                    email=DEMO_EMAIL,
                    name="Demo User",
                    password_hash=await hash_password("demo-password-change-me"),
                    is_active=True,
                )
                session.add(user)
                await session.flush()
            elif user.email == LEGACY_DEMO_EMAIL:
                user.email = DEMO_EMAIL
                await session.flush()
            workspace = await session.scalar(
                select(Workspace).where(
                    Workspace.owner_id == user.id, Workspace.name == DEMO_WORKSPACE
                )
            )
            if workspace is None:
                workspace = Workspace(
                    name=DEMO_WORKSPACE, description="Local demo data", owner_id=user.id
                )
                session.add(workspace)
                await session.flush()
                session.add(
                    WorkspaceMember(
                        workspace_id=workspace.id,
                        user_id=user.id,
                        role=WorkspaceRole.OWNER,
                        joined_at=utc_now(),
                    )
                )
    finally:
        await database.dispose()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
