"""Add full_name to users.

Revision ID: 0010_users_full_name
Revises: 0009_permissions
Create Date: 2026-09-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_users_full_name"
down_revision: Union[str, None] = "0009_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("full_name", sa.String(150), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "full_name")
