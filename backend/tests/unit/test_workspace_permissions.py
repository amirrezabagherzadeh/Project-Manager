import asyncio
from uuid import uuid4

import pytest

from app.core.exceptions import DomainError
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.services.workspace_permissions import ADMIN_ROLES, ALL_ROLES, require_role


@pytest.mark.parametrize("role", list(WorkspaceRole))
def test_every_workspace_role_can_read(role: WorkspaceRole) -> None:
    require_role(
        WorkspaceMember(
            workspace_id=uuid4(),
            user_id=uuid4(),
            role=role,
            joined_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        ),
        ALL_ROLES,
    )


@pytest.mark.parametrize(
    ("role", "allowed"),
    [
        (WorkspaceRole.OWNER, True),
        (WorkspaceRole.ADMIN, True),
        (WorkspaceRole.PROJECT_MANAGER, False),
        (WorkspaceRole.MEMBER, False),
    ],
)
def test_admin_permission_matrix(role: WorkspaceRole, allowed: bool) -> None:
    member = WorkspaceMember(
        workspace_id=uuid4(),
        user_id=uuid4(),
        role=role,
        joined_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
    )
    if allowed:
        require_role(member, ADMIN_ROLES)
    else:
        with pytest.raises(DomainError) as error:
            require_role(member, ADMIN_ROLES)
        assert error.value.status_code == 403


def test_missing_membership_is_enumeration_safe() -> None:
    from app.services.workspace_permissions import resolve_membership

    class MissingRepository:
        async def get(self, _workspace_id, _user_id):
            return None

    with pytest.raises(DomainError) as error:
        asyncio.run(
            resolve_membership(
                MissingRepository(),  # type: ignore[arg-type]
                workspace_id=uuid4(),
                user_id=uuid4(),
            )
        )
    assert error.value.status_code == 404
    assert error.value.code == "resource_not_found"
