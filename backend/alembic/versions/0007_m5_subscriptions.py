"""M5 — Subscriptions & AI Usage.

Revision ID: 0007_m5_subscriptions
Revises: 0006_m4_screening
Create Date: 2026-09-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_m5_subscriptions"
down_revision: Union[str, None] = "0006_m4_screening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID_PK = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    # ═══ subscriptions ═══
    op.create_table(
        "subscriptions",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", UUID_PK, nullable=False),
        sa.Column("plan_code", sa.String(50), nullable=False),
        sa.Column("status",
                  postgresql.ENUM("trialing", "active", "past_due", "canceled", "expired",
                                  name="subscription_status", create_type=False),
                  server_default=sa.text("'trialing'"), nullable=False),
        sa.Column("billing_cycle",
                  postgresql.ENUM("monthly", "yearly",
                                  name="billing_cycle", create_type=False),
                  server_default=sa.text("'monthly'"), nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ai_tokens_limit", sa.BigInteger, nullable=False),
        sa.Column("ai_tokens_used", sa.BigInteger,
                  server_default=sa.text("0"), nullable=False),
        sa.Column("ai_tokens_reserved", sa.BigInteger,
                  server_default=sa.text("0"), nullable=False),
        sa.Column("max_users", sa.Integer, nullable=False),
        sa.Column("max_active_jobs", sa.Integer, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_subscriptions"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"],
                                ondelete="CASCADE", name="fk_subscriptions_company"),
        sa.CheckConstraint("ai_tokens_limit >= 0", name="chk_sub_tokens_limit"),
        sa.CheckConstraint("ai_tokens_used >= 0", name="chk_sub_tokens_used"),
        sa.CheckConstraint("ai_tokens_reserved >= 0", name="chk_sub_tokens_reserved"),
        sa.CheckConstraint(
            "ai_tokens_used + ai_tokens_reserved <= ai_tokens_limit",
            name="chk_sub_tokens_total",
        ),
        sa.CheckConstraint("max_users > 0", name="chk_sub_max_users"),
        sa.CheckConstraint("max_active_jobs >= 0", name="chk_sub_max_jobs"),
        sa.CheckConstraint(
            "current_period_end > current_period_start",
            name="chk_sub_period",
        ),
        sa.CheckConstraint(
            "canceled_at IS NULL OR canceled_at >= started_at",
            name="chk_sub_canceled",
        ),
        sa.CheckConstraint(
            "status <> 'canceled' OR canceled_at IS NOT NULL",
            name="chk_sub_status_canceled",
        ),
    )
    op.execute("CREATE UNIQUE INDEX uq_active_company_subscription "
               "ON subscriptions (company_id) "
               "WHERE status IN ('trialing','active','past_due')")
    op.execute("CREATE INDEX ix_subscriptions_period_end ON subscriptions (current_period_end) "
               "WHERE status IN ('active','trialing')")
    op.execute("CREATE INDEX ix_subscriptions_rollover "
               "ON subscriptions (company_id, current_period_end) "
               "WHERE status = 'active'")

    # ═══ ai_usage_logs ═══
    op.create_table(
        "ai_usage_logs",
        sa.Column("id", sa.BigInteger, autoincrement=True, nullable=False),
        sa.Column("company_id", UUID_PK, nullable=False),
        sa.Column("user_id", UUID_PK, nullable=True),
        sa.Column("application_id", UUID_PK, nullable=True),
        sa.Column("operation_type",
                  postgresql.ENUM("resume_parsing", "resume_embedding", "semantic_matching",
                                  "screening_generation", "screening_evaluation", "other",
                                  name="ai_operation_type", create_type=False),
                  nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("request_id", UUID_PK, nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("response_hash", sa.String(64), nullable=True),
        sa.Column("input_tokens", sa.BigInteger,
                  server_default=sa.text("0"), nullable=False),
        sa.Column("output_tokens", sa.BigInteger,
                  server_default=sa.text("0"), nullable=False),
        sa.Column("total_tokens", sa.BigInteger,
                  server_default=sa.text("0"), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("status",
                  postgresql.ENUM("success", "failed", "rate_limited", "timeout", "rejected",
                                  name="ai_usage_status", create_type=False),
                  nullable=False),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_ai_usage_logs"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"],
                                ondelete="CASCADE", name="fk_ai_usage_company"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                ondelete="SET NULL", name="fk_ai_usage_user"),
        sa.ForeignKeyConstraint(
            ["company_id", "application_id"],
            ["applications.company_id", "applications.id"],
            name="fk_ai_usage_company_application", ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("request_id", name="uq_ai_usage_request"),
        sa.CheckConstraint("input_tokens >= 0", name="chk_ai_input_tokens"),
        sa.CheckConstraint("output_tokens >= 0", name="chk_ai_output_tokens"),
        sa.CheckConstraint("total_tokens >= 0", name="chk_ai_total_tokens"),
        sa.CheckConstraint(
            "estimated_cost IS NULL OR estimated_cost >= 0",
            name="chk_ai_estimated_cost",
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="chk_ai_latency",
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= created_at",
            name="chk_ai_completed",
        ),
        sa.CheckConstraint(
            "status <> 'failed' OR error_code IS NOT NULL",
            name="chk_ai_failed_error",
        ),
    )
    op.create_index("ix_ai_usage_company_time", "ai_usage_logs",
                    ["company_id", "created_at"])
    op.create_index("ix_ai_usage_company_feature", "ai_usage_logs",
                    ["company_id", "operation_type", "created_at"])


def downgrade() -> None:
    op.drop_table("ai_usage_logs")
    op.drop_table("subscriptions")
