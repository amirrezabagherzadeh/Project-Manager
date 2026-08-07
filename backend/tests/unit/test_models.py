from sqlalchemy import Index, UniqueConstraint

from app.models import Base, RefreshSession, User
from app.models.base import UTCDateTime


def _unique_constraint_names(table_name: str) -> set[str | None]:
    table = Base.metadata.tables[table_name]
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def _index_names(table_name: str) -> set[str | None]:
    table = Base.metadata.tables[table_name]
    return {index.name for index in table.indexes if isinstance(index, Index)}


def test_user_model_has_private_hash_and_normalized_email_constraints() -> None:
    table = User.__table__

    assert table.c.id.primary_key
    assert table.c.email.nullable is False
    assert table.c.password_hash.nullable is False
    assert table.c.password_hash.type.length == 512
    assert "uq_users_email" in _unique_constraint_names("users")
    assert "ix_users_email" in _index_names("users")
    assert isinstance(table.c.created_at.type, UTCDateTime)
    assert isinstance(table.c.updated_at.type, UTCDateTime)


def test_refresh_session_model_has_hash_chain_and_query_indexes() -> None:
    table = RefreshSession.__table__
    foreign_keys = {foreign_key.target_fullname for foreign_key in table.foreign_keys}

    assert table.c.token_hash.type.length == 64
    assert "users.id" in foreign_keys
    assert "refresh_sessions.id" in foreign_keys
    assert "uq_refresh_sessions_token_hash" in _unique_constraint_names("refresh_sessions")
    assert "uq_refresh_sessions_replaced_by_id" in _unique_constraint_names("refresh_sessions")
    assert {
        "ix_refresh_sessions_user_id",
        "ix_refresh_sessions_expires_at",
        "ix_refresh_sessions_user_active",
    }.issubset(_index_names("refresh_sessions"))


def test_refresh_sessions_are_owned_by_user_with_delete_orphan_cascade() -> None:
    relationship = User.refresh_sessions.property

    assert relationship.back_populates == "user"
    assert relationship.passive_deletes is True
    assert relationship.cascade.delete_orphan is True
