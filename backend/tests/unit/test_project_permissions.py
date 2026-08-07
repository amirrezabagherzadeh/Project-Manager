import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.exceptions import DomainError
from app.models.project import Project, ProjectMember, ProjectRole
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.services.project_permissions import (
    PROJECT_MUTATION_ROLES,
    require_project_access,
    require_project_mutation_role,
    require_role,
)

_TS = datetime.now(UTC)


def _workspace_member(role: WorkspaceRole) -> WorkspaceMember:
    return WorkspaceMember(
        workspace_id=uuid4(),
        user_id=uuid4(),
        role=role,
        joined_at=_TS,
    )


def _project_member(role: ProjectRole) -> ProjectMember:
    return ProjectMember(
        project_id=uuid4(),
        user_id=uuid4(),
        role=role,
        joined_at=_TS,
    )


@pytest.mark.parametrize(
    ("workspace_role", "allowed"),
    [
        (WorkspaceRole.OWNER, True),
        (WorkspaceRole.ADMIN, True),
        (WorkspaceRole.PROJECT_MANAGER, True),
        (WorkspaceRole.MEMBER, False),
    ],
)
def test_project_creation_role_gate(
    workspace_role: WorkspaceRole,
    allowed: bool,
) -> None:
    member = _workspace_member(workspace_role)
    if allowed:
        require_role(member, PROJECT_MUTATION_ROLES)
    else:
        with pytest.raises(DomainError) as error:
            require_role(member, PROJECT_MUTATION_ROLES)
        assert error.value.status_code == 403


@pytest.mark.parametrize(
    ("workspace_role", "project_role", "allowed"),
    [
        (WorkspaceRole.OWNER, None, True),
        (WorkspaceRole.ADMIN, None, True),
        (WorkspaceRole.PROJECT_MANAGER, None, True),
        (WorkspaceRole.MEMBER, ProjectRole.MANAGER, True),
        (WorkspaceRole.MEMBER, ProjectRole.MEMBER, False),
        (WorkspaceRole.MEMBER, None, False),
    ],
)
def test_project_mutation_role_matrix(
    workspace_role: WorkspaceRole,
    project_role: ProjectRole | None,
    allowed: bool,
) -> None:
    member = _workspace_member(workspace_role)
    project_member = _project_member(project_role) if project_role else None
    if allowed:
        require_project_mutation_role(member, project_member)
    else:
        with pytest.raises(DomainError) as error:
            require_project_mutation_role(member, project_member)
        assert error.value.status_code == 403


def test_private_project_read_is_denied_for_non_member() -> None:
    async def scenario() -> None:
        project = Project(
            workspace_id=uuid4(),
            name="Private",
            key="PVT",
            is_private=True,
        )
        member = _workspace_member(WorkspaceRole.MEMBER)

        class EmptyRepository:
            async def get(self, _project_id, _user_id):
                return None

        with pytest.raises(DomainError) as error:
            await require_project_access(
                EmptyRepository(),  # type: ignore[arg-type]
                project=project,
                workspace_member=member,
                user_id=uuid4(),
            )
        assert error.value.status_code == 404
        assert error.value.code == "resource_not_found"

    asyncio.run(scenario())


def test_public_project_is_readable_by_any_workspace_member() -> None:
    async def scenario() -> None:
        project = Project(
            workspace_id=uuid4(),
            name="Public",
            key="PUB",
            is_private=False,
        )
        member = _workspace_member(WorkspaceRole.MEMBER)

        class EmptyRepository:
            async def get(self, _project_id, _user_id):
                return None

        resolved = await require_project_access(
            EmptyRepository(),  # type: ignore[arg-type]
            project=project,
            workspace_member=member,
            user_id=uuid4(),
        )
        assert resolved is None

    asyncio.run(scenario())


def test_workspace_owner_admin_bypasses_private_gate() -> None:
    async def scenario() -> None:
        project = Project(
            workspace_id=uuid4(),
            name="Private",
            key="PVT",
            is_private=True,
        )
        owner = _workspace_member(WorkspaceRole.OWNER)

        class EmptyRepository:
            async def get(self, _project_id, _user_id):
                return None

        resolved = await require_project_access(
            EmptyRepository(),  # type: ignore[arg-type]
            project=project,
            workspace_member=owner,
            user_id=uuid4(),
        )
        assert resolved is None

    asyncio.run(scenario())


def test_private_project_member_is_admitted() -> None:
    async def scenario() -> None:
        project = Project(
            workspace_id=uuid4(),
            name="Private",
            key="PVT",
            is_private=True,
        )
        member = _workspace_member(WorkspaceRole.MEMBER)

        class FilledRepository:
            async def get(self, _project_id, _user_id):
                return _project_member(ProjectRole.MEMBER)

        resolved = await require_project_access(
            FilledRepository(),  # type: ignore[arg-type]
            project=project,
            workspace_member=member,
            user_id=uuid4(),
        )
        assert resolved is not None
        assert resolved.role == ProjectRole.MEMBER

    asyncio.run(scenario())
