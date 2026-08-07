from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.models import (
    ActivityLog,
    Base,
    Notification,
    Workspace,
    WorkspaceInvitation,
    WorkspaceRole,
)
from app.models.base import UTCDateTime


def _constraint_names(table_name: str, kind: type) -> set[str | None]:
    return {
        constraint.name
        for constraint in Base.metadata.tables[table_name].constraints
        if isinstance(constraint, kind)
    }


def _index_names(table_name: str) -> set[str | None]:
    return {
        index.name for index in Base.metadata.tables[table_name].indexes if isinstance(index, Index)
    }


def test_workspace_role_values_are_stable() -> None:
    assert {role.value for role in WorkspaceRole} == {
        "OWNER",
        "ADMIN",
        "PROJECT_MANAGER",
        "MEMBER",
    }


def test_workspace_and_member_invariants_are_declared() -> None:
    assert Workspace.__table__.c.owner_id.nullable is False
    assert isinstance(Workspace.__table__.c.archived_at.type, UTCDateTime)
    assert "uq_workspace_members_workspace_user" in _constraint_names(
        "workspace_members", UniqueConstraint
    )
    assert {
        "ix_workspace_members_user_id",
        "ix_workspace_members_workspace_role",
    }.issubset(_index_names("workspace_members"))
    assert Workspace.members.property.cascade.delete_orphan is True
    assert Workspace.members.property.passive_deletes is True


def test_invitation_only_persists_hash_and_has_lifecycle_constraints() -> None:
    table = WorkspaceInvitation.__table__

    assert "token" not in table.c
    assert table.c.token_hash.type.length == 64
    assert {
        "uq_workspace_invitations_workspace_email",
        "uq_workspace_invitations_token_hash",
    }.issubset(_constraint_names("workspace_invitations", UniqueConstraint))
    assert "ck_workspace_invitations_role_not_owner" in _constraint_names(
        "workspace_invitations", CheckConstraint
    )


def test_activity_and_notification_have_private_scoped_indexes() -> None:
    assert {
        "ix_activity_logs_workspace_created",
        "ix_activity_logs_entity",
    }.issubset(_index_names("activity_logs"))
    assert {
        "ix_notifications_user_created",
        "ix_notifications_user_unread",
    }.issubset(_index_names("notifications"))
    assert "uq_notifications_dedupe_key" in _constraint_names("notifications", UniqueConstraint)
    assert ActivityLog.__table__.c.details.nullable is False
    assert Notification.__table__.c.user_id.nullable is False
    assert isinstance(Notification.__table__.c.created_at.type, UTCDateTime)
