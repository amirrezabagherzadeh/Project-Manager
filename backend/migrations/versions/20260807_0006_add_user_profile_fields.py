"""add user profile fields

Revision ID: 20260807_0006
Revises: 20260807_0005
"""

import sqlalchemy as sa
from alembic import op

revision = "20260807_0006"
down_revision = "20260807_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC")
        )
        batch.add_column(sa.Column("avatar_storage_name", sa.String(length=80), nullable=True))
        batch.add_column(sa.Column("avatar_content_type", sa.String(length=120), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_column("avatar_content_type")
        batch.drop_column("avatar_storage_name")
        batch.drop_column("timezone")
