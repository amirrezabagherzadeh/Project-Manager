import hashlib
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    invalid_operation,
    permission_denied,
    resource_conflict,
    resource_not_found,
)
from app.core.security import normalize_email
from app.models.base import utc_now
from app.models.identity import User
from app.models.workspace import (
    ActivityLog,
    Notification,
    Workspace,
    WorkspaceInvitation,
    WorkspaceMember,
    WorkspaceRole,
)
from app.repositories.workspace import (
    SideEffectRepository,
    WorkspaceInvitationRepository,
    WorkspaceMemberRepository,
    WorkspaceRepository,
    WorkspaceUserRepository,
)
from app.services.workspace_permissions import ADMIN_ROLES, require_role, resolve_membership


@dataclass(frozen=True)
class InvitationCreation:
    invitation: WorkspaceInvitation
    token: str


class WorkspaceService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._session = session
        self._clock = clock
        self._workspaces = WorkspaceRepository(session)
        self._members = WorkspaceMemberRepository(session)
        self._invitations = WorkspaceInvitationRepository(session)
        self._users = WorkspaceUserRepository(session)
        self._effects = SideEffectRepository(session)

    async def create(
        self,
        actor: User,
        *,
        name: str,
        description: str | None,
    ) -> Workspace:
        now = self._clock()
        workspace = Workspace(
            name=name.strip(),
            description=description.strip() if description else None,
            owner_id=actor.id,
        )
        async with self._session.begin():
            await self._workspaces.add(workspace)
            await self._members.add(
                WorkspaceMember(
                    workspace_id=workspace.id,
                    user_id=actor.id,
                    role=WorkspaceRole.OWNER,
                    joined_at=now,
                )
            )
            await self._activity(workspace, actor, "workspace.created")
        return workspace

    async def list_workspaces(
        self,
        actor: User,
        *,
        page: int,
        page_size: int,
        include_archived: bool = False,
    ) -> tuple[list[Workspace], int]:
        async with self._session.begin():
            return await self._workspaces.list_for_user(
                actor.id,
                include_archived=include_archived,
                offset=(page - 1) * page_size,
                limit=page_size,
            )

    async def read(self, actor: User, workspace_id: UUID) -> Workspace:
        async with self._session.begin():
            await self._membership(actor, workspace_id)
            workspace = await self._workspaces.get(workspace_id)
            if workspace is None:
                raise resource_not_found()
            return workspace

    async def update(
        self,
        actor: User,
        workspace_id: UUID,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Workspace:
        async with self._session.begin():
            member = await self._membership(actor, workspace_id)
            require_role(member, ADMIN_ROLES)
            workspace = await self._required_workspace(workspace_id)
            if name is not None:
                workspace.name = name.strip()
            if description is not None:
                workspace.description = description.strip() or None
            await self._activity(workspace, actor, "workspace.updated")
            await self._session.flush()
            return workspace

    async def archive(self, actor: User, workspace_id: UUID) -> Workspace:
        return await self._set_archived(actor, workspace_id, archived=True)

    async def restore(self, actor: User, workspace_id: UUID) -> Workspace:
        return await self._set_archived(actor, workspace_id, archived=False)

    async def _set_archived(
        self,
        actor: User,
        workspace_id: UUID,
        *,
        archived: bool,
    ) -> Workspace:
        async with self._session.begin():
            member = await self._membership(actor, workspace_id)
            require_role(member, ADMIN_ROLES)
            workspace = await self._required_workspace(workspace_id)
            workspace.archived_at = self._clock() if archived else None
            await self._activity(
                workspace,
                actor,
                "workspace.archived" if archived else "workspace.restored",
            )
            await self._session.flush()
            return workspace

    async def delete(self, actor: User, workspace_id: UUID) -> None:
        async with self._session.begin():
            member = await self._membership(actor, workspace_id)
            require_role(member, {WorkspaceRole.OWNER})
            workspace = await self._required_workspace(workspace_id)
            await self._workspaces.delete(workspace)

    async def list_members(
        self,
        actor: User,
        workspace_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[WorkspaceMember], int]:
        async with self._session.begin():
            await self._membership(actor, workspace_id)
            return await self._members.list(
                workspace_id,
                offset=(page - 1) * page_size,
                limit=page_size,
            )

    async def add_member(
        self,
        actor: User,
        workspace_id: UUID,
        *,
        email: str,
        role: WorkspaceRole,
    ) -> WorkspaceMember:
        self._require_non_owner_role(role)
        try:
            async with self._session.begin():
                actor_member = await self._membership(actor, workspace_id)
                require_role(actor_member, ADMIN_ROLES)
                workspace = await self._required_workspace(workspace_id)
                target = await self._users.get_by_email(email)
                if target is None:
                    raise resource_not_found()
                if await self._members.get(workspace_id, target.id) is not None:
                    raise resource_conflict("کاربر از قبل عضو این فضای کاری است.")
                member = WorkspaceMember(
                    workspace_id=workspace_id,
                    user_id=target.id,
                    role=role,
                    joined_at=self._clock(),
                )
                await self._members.add(member)
                await self._activity(
                    workspace,
                    actor,
                    "workspace.member_added",
                    details={"user_id": str(target.id), "role": role.value},
                )
                await self._notify_member(
                    actor=actor,
                    target=target,
                    workspace=workspace,
                    kind="workspace.member_added",
                    title="به فضای کاری افزوده شدید",
                    dedupe_key=f"workspace.member_added:{member.id}",
                )
                return member
        except IntegrityError as exc:
            raise resource_conflict("کاربر از قبل عضو این فضای کاری است.") from exc

    async def change_member_role(
        self,
        actor: User,
        workspace_id: UUID,
        member_id: UUID,
        *,
        role: WorkspaceRole,
    ) -> WorkspaceMember:
        async with self._session.begin():
            actor_member = await self._membership(actor, workspace_id)
            require_role(actor_member, ADMIN_ROLES)
            workspace = await self._required_workspace(workspace_id)
            target = await self._members.get_by_id(workspace_id, member_id)
            if target is None:
                raise resource_not_found()
            if role == WorkspaceRole.OWNER:
                if actor_member.role != WorkspaceRole.OWNER:
                    raise permission_denied()
                if target.role == WorkspaceRole.OWNER:
                    raise resource_conflict("این کاربر هم‌اکنون مالک است.")
                actor_member.role = WorkspaceRole.ADMIN
                target.role = WorkspaceRole.OWNER
                workspace.owner_id = target.user_id
                action = "workspace.ownership_transferred"
            else:
                if target.role == WorkspaceRole.OWNER:
                    raise invalid_operation("ابتدا مالکیت را به عضو دیگری منتقل کنید.")
                target.role = role
                action = "workspace.member_role_changed"
            await self._activity(
                workspace,
                actor,
                action,
                details={"user_id": str(target.user_id), "role": role.value},
            )
            await self._session.flush()
            return target

    async def remove_member(
        self,
        actor: User,
        workspace_id: UUID,
        member_id: UUID,
    ) -> None:
        async with self._session.begin():
            actor_member = await self._membership(actor, workspace_id)
            require_role(actor_member, ADMIN_ROLES)
            workspace = await self._required_workspace(workspace_id)
            target = await self._members.get_by_id(workspace_id, member_id)
            if target is None:
                raise resource_not_found()
            if target.role == WorkspaceRole.OWNER:
                raise invalid_operation("مالک فضای کاری را نمی‌توان حذف کرد.")
            target_user_id = target.user_id
            await self._members.delete(target)
            await self._activity(
                workspace,
                actor,
                "workspace.member_removed",
                details={"user_id": str(target_user_id)},
            )

    async def create_invitation(
        self,
        actor: User,
        workspace_id: UUID,
        *,
        email: str,
        role: WorkspaceRole,
    ) -> InvitationCreation:
        self._require_non_owner_role(role)
        normalized_email = normalize_email(email)
        token = secrets.token_urlsafe(48)
        now = self._clock()
        try:
            async with self._session.begin():
                actor_member = await self._membership(actor, workspace_id)
                require_role(actor_member, ADMIN_ROLES)
                workspace = await self._required_workspace(workspace_id)
                target = await self._users.get_by_email(normalized_email)
                if (
                    target is not None
                    and await self._members.get(workspace_id, target.id) is not None
                ):
                    raise resource_conflict("کاربر از قبل عضو این فضای کاری است.")
                current = await self._invitations.get_by_email(
                    workspace_id,
                    normalized_email,
                )
                if (
                    current is not None
                    and current.accepted_at is None
                    and current.revoked_at is None
                    and current.expires_at > now
                ):
                    raise resource_conflict("دعوت فعال برای این ایمیل وجود دارد.")
                if current is not None:
                    await self._session.delete(current)
                    await self._session.flush()
                invitation = WorkspaceInvitation(
                    workspace_id=workspace_id,
                    email=normalized_email,
                    role=role,
                    token_hash=self.hash_invitation_token(token),
                    invited_by_id=actor.id,
                    created_at=now,
                    expires_at=now + timedelta(days=7),
                )
                await self._invitations.add(invitation)
                await self._activity(
                    workspace,
                    actor,
                    "workspace.invitation_created",
                    details={"email": normalized_email, "role": role.value},
                )
                if target is not None:
                    await self._notify_member(
                        actor=actor,
                        target=target,
                        workspace=workspace,
                        kind="workspace.invitation_created",
                        title="برای عضویت در فضای کاری دعوت شدید",
                        dedupe_key=f"workspace.invitation_created:{invitation.id}",
                    )
                return InvitationCreation(invitation=invitation, token=token)
        except IntegrityError as exc:
            raise resource_conflict("دعوت فعال برای این ایمیل وجود دارد.") from exc

    async def list_invitations(
        self,
        actor: User,
        workspace_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[WorkspaceInvitation], int]:
        async with self._session.begin():
            member = await self._membership(actor, workspace_id)
            require_role(member, ADMIN_ROLES)
            return await self._invitations.list(
                workspace_id,
                offset=(page - 1) * page_size,
                limit=page_size,
            )

    async def revoke_invitation(
        self,
        actor: User,
        workspace_id: UUID,
        invitation_id: UUID,
    ) -> WorkspaceInvitation:
        async with self._session.begin():
            member = await self._membership(actor, workspace_id)
            require_role(member, ADMIN_ROLES)
            workspace = await self._required_workspace(workspace_id)
            invitation = await self._invitations.get_by_id(workspace_id, invitation_id)
            if invitation is None:
                raise resource_not_found()
            if invitation.accepted_at is not None:
                raise invalid_operation("دعوت پذیرفته‌شده قابل لغو نیست.")
            invitation.revoked_at = self._clock()
            await self._activity(
                workspace,
                actor,
                "workspace.invitation_revoked",
                details={"invitation_id": str(invitation.id)},
            )
            await self._session.flush()
            return invitation

    async def accept_invitation(
        self,
        actor: User,
        token: str,
    ) -> WorkspaceMember:
        now = self._clock()
        try:
            async with self._session.begin():
                invitation = await self._invitations.get_by_hash(self.hash_invitation_token(token))
                if invitation is None or invitation.email != normalize_email(actor.email):
                    raise resource_not_found()
                if invitation.revoked_at is not None or invitation.expires_at <= now:
                    raise resource_not_found()
                if invitation.accepted_at is not None:
                    raise resource_conflict("این دعوت قبلاً پذیرفته شده است.")
                if await self._members.get(invitation.workspace_id, actor.id) is not None:
                    raise resource_conflict("کاربر از قبل عضو این فضای کاری است.")
                workspace = await self._required_workspace(invitation.workspace_id)
                member = WorkspaceMember(
                    workspace_id=invitation.workspace_id,
                    user_id=actor.id,
                    role=invitation.role,
                    joined_at=now,
                )
                await self._members.add(member)
                invitation.accepted_at = now
                await self._activity(
                    workspace,
                    actor,
                    "workspace.invitation_accepted",
                    details={"user_id": str(actor.id), "role": invitation.role.value},
                )
                inviter = await self._users.get_by_id(invitation.invited_by_id)
                if inviter is not None:
                    await self._notify_member(
                        actor=actor,
                        target=inviter,
                        workspace=workspace,
                        kind="workspace.invitation_accepted",
                        title="دعوت فضای کاری پذیرفته شد",
                        dedupe_key=f"workspace.invitation_accepted:{invitation.id}",
                    )
                await self._session.flush()
                return member
        except IntegrityError as exc:
            raise resource_conflict("کاربر از قبل عضو این فضای کاری است.") from exc

    async def _membership(self, actor: User, workspace_id: UUID) -> WorkspaceMember:
        return await resolve_membership(
            self._members,
            workspace_id=workspace_id,
            user_id=actor.id,
        )

    async def _required_workspace(self, workspace_id: UUID) -> Workspace:
        workspace = await self._workspaces.get(workspace_id)
        if workspace is None:
            raise resource_not_found()
        return workspace

    async def _activity(
        self,
        workspace: Workspace,
        actor: User,
        action: str,
        *,
        details: dict[str, str] | None = None,
    ) -> None:
        await self._effects.activity(
            ActivityLog(
                workspace_id=workspace.id,
                actor_id=actor.id,
                entity_type="workspace",
                entity_id=workspace.id,
                action=action,
                details=details or {},
                created_at=self._clock(),
            )
        )

    async def _notify_member(
        self,
        *,
        actor: User,
        target: User,
        workspace: Workspace,
        kind: str,
        title: str,
        dedupe_key: str | None = None,
    ) -> None:
        if actor.id == target.id:
            return
        await self._effects.notification(
            Notification(
                user_id=target.id,
                type=kind,
                title=title,
                body=workspace.name,
                entity_type="workspace",
                entity_id=workspace.id,
                action_url=f"/app/workspaces/{workspace.id}",
                dedupe_key=dedupe_key or f"{kind}:{workspace.id}:{target.id}",
                created_at=self._clock(),
            )
        )

    @staticmethod
    def _require_non_owner_role(role: WorkspaceRole) -> None:
        if role == WorkspaceRole.OWNER:
            raise permission_denied()

    @staticmethod
    def hash_invitation_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
