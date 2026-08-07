from collections.abc import Collection
from uuid import UUID

from app.core.exceptions import permission_denied, resource_not_found
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.repositories.workspace import WorkspaceMemberRepository

ADMIN_ROLES = frozenset({WorkspaceRole.OWNER, WorkspaceRole.ADMIN})
ALL_ROLES = frozenset(WorkspaceRole)


def require_role(
    member: WorkspaceMember,
    allowed_roles: Collection[WorkspaceRole],
) -> None:
    if member.role not in allowed_roles:
        raise permission_denied()


async def resolve_membership(
    repository: WorkspaceMemberRepository,
    *,
    workspace_id: UUID,
    user_id: UUID,
) -> WorkspaceMember:
    member = await repository.get(workspace_id, user_id)
    if member is None:
        raise resource_not_found()
    return member
