"""M1 — Identity & Tenant Core.

Revision ID: 0003_m1_identity
Revises: 0002_enums
Create Date: 2026-09-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_m1_identity"
down_revision: Union[str, None] = "0002_enums"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID_PK = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("platform_role",
                  postgresql.ENUM("user", "super_admin",
                                  name="user_platform_role", create_type=False),
                  server_default=sa.text("'user'"), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.execute("CREATE UNIQUE INDEX uq_users_email_lower ON users (LOWER(email))")

    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID_PK, nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("family_id", UUID_PK, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_id", UUID_PK, nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", postgresql.INET, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_refresh_tokens"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                ondelete="CASCADE", name="fk_rt_user"),
        sa.ForeignKeyConstraint(["replaced_by_id"], ["refresh_tokens.id"],
                                ondelete="SET NULL", name="fk_rt_replaced_by"),
    )
    op.create_index("uq_refresh_tokens_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_user", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_family", "refresh_tokens", ["family_id"])
    op.execute("CREATE INDEX ix_refresh_tokens_expiry_sweep "
               "ON refresh_tokens (expires_at) WHERE revoked_at IS NULL")

    op.create_table(
        "companies",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("slug", sa.String(150), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("status",
                  postgresql.ENUM("active", "suspended", "archived",
                                  name="company_status", create_type=False),
                  server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_companies"),
    )
    op.create_index("uq_companies_slug", "companies", ["slug"], unique=True)

    op.create_table(
        "company_members",
        sa.Column("company_id", UUID_PK, nullable=False),
        sa.Column("user_id", UUID_PK, nullable=False),
        sa.Column("role",
                  postgresql.ENUM("owner", "admin", "recruiter", "viewer",
                                  name="company_member_role", create_type=False),
                  nullable=False),
        sa.Column("status",
                  postgresql.ENUM("invited", "active", "suspended",
                                  name="company_member_status", create_type=False),
                  server_default=sa.text("'active'"), nullable=False),
        sa.Column("invited_by", UUID_PK, nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("company_id", "user_id", name="pk_company_members"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"],
                                ondelete="CASCADE", name="fk_cm_company"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                ondelete="CASCADE", name="fk_cm_user"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"],
                                ondelete="SET NULL", name="fk_cm_invited_by"),
    )
    op.create_index("ix_company_members_user", "company_members", ["user_id"])
    op.create_index("ix_company_members_role", "company_members", ["company_id", "role"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger, autoincrement=True, nullable=False),
        sa.Column("actor_user_id", UUID_PK, nullable=True),
        sa.Column("company_id", UUID_PK, nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", UUID_PK, nullable=True),
        sa.Column("ip_address", postgresql.INET, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("request_id", UUID_PK, nullable=True),
        sa.Column("context_details", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"],
                                ondelete="SET NULL", name="fk_audit_actor"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"],
                                ondelete="SET NULL", name="fk_audit_company"),
    )
    op.create_index("ix_audit_company_time", "audit_logs", ["company_id", "created_at"])
    op.create_index("ix_audit_actor_time", "audit_logs", ["actor_user_id", "created_at"])
    op.create_index("ix_audit_action", "audit_logs", ["action"])
    op.create_index("ix_audit_target", "audit_logs", ["target_type", "target_id"])
    op.execute("CREATE INDEX ix_audit_request ON audit_logs (request_id) "
               "WHERE request_id IS NOT NULL")


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("company_members")
    op.drop_table("companies")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
