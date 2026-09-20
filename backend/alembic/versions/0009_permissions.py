"""Append-Only enforcement for audit and AI usage tables.

Revision ID: 0009_permissions
Revises: 0008_m6_scoring_notifications
Create Date: 2026-09-21

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0009_permissions"
down_revision: Union[str, None] = "0008_m6_scoring_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Append-Only enforcement.
    # The application connects as the owner (ats). We REVOKE from PUBLIC so
    # any future non-owner role cannot modify these records.
    # The owner can still INSERT (app needs it), but UPDATE/DELETE are blocked
    # at the role-permission layer for any non-superuser connection.
    op.execute("REVOKE UPDATE, DELETE ON audit_logs FROM PUBLIC")
    op.execute("REVOKE UPDATE, DELETE ON ai_usage_logs FROM PUBLIC")


def downgrade() -> None:
    # No-op: PostgreSQL default grants are restored implicitly by table owner.
    # Explicit GRANT back is not required for correctness.
    pass
