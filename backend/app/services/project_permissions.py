from collections.abc import Collection
from typing import Protocol
from uuid import UUID

from app.core.exceptions import permission_denied, resource_not_found
from app.models.project import Project, ProjectMember, ProjectRole
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.repositories.project import ProjectMemberRepository

PROJECT_MUTATION_ROLES = frozenset(
    {WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.PROJECT_MANAGER}
)
WORKSPACE_OWNER_ADMIN = frozenset({WorkspaceRole.OWNER, WorkspaceRole.ADMIN})


class MembershipResolver(Protocol):
    async def get(self, project_id: UUID, user_id: UUID) -> ProjectMember | None: ...


def require_role(
    member: WorkspaceMember,
    allowed_roles: Collection[WorkspaceRole],
) -> None:
    if member.role not in allowed_roles:
        raise permission_denied()


def require_project_mutation_role(
    member: WorkspaceMember,
    project_member: ProjectMember | None,
) -> None:
    if member.role in WORKSPACE_OWNER_ADMIN:
        return
    if member.role == WorkspaceRole.PROJECT_MANAGER:
        return
    if project_member is not None and project_member.role == ProjectRole.MANAGER:
        return
    raise permission_denied()


async def resolve_project_membership(
    repository: ProjectMemberRepository,
    *,
    project_id: UUID,
    user_id: UUID,
) -> ProjectMember | None:
    return await repository.get(project_id, user_id)


async def require_project_access(
    repository: ProjectMemberRepository,
    *,
    project: Project,
    workspace_member: WorkspaceMember,
    user_id: UUID,
) -> ProjectMember | None:
    project_member = await resolve_project_membership(
        repository,
        project_id=project.id,
        user_id=user_id,
    )
    if not project.is_private:
        return project_member
    if workspace_member.role in WORKSPACE_OWNER_ADMIN:
        return project_member
    if project_member is None:
        raise resource_not_found()
    return project_member
