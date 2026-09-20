"""M5 — Subscriptions & AI Usage Governance."""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint,
    Index, Integer, Numeric, String, Text, UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


UUID_PK = dict(primary_key=True, server_default=text("gen_random_uuid()"))


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False,
    )

    plan_code: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        ENUM("trialing", "active", "past_due", "canceled", "expired",
             name="subscription_status", create_type=False),
        nullable=False, server_default=text("'trialing'"),
    )
    billing_cycle: Mapped[str] = mapped_column(
        ENUM("monthly", "yearly", name="billing_cycle", create_type=False),
        nullable=False, server_default=text("'monthly'"),
    )

    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    ai_tokens_limit: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ai_tokens_used: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0"),
    )
    ai_tokens_reserved: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0"),
    )

    max_users: Mapped[int] = mapped_column(Integer, nullable=False)
    max_active_jobs: Mapped[int] = mapped_column(Integer, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("ai_tokens_limit >= 0", name="chk_sub_tokens_limit"),
        CheckConstraint("ai_tokens_used >= 0", name="chk_sub_tokens_used"),
        CheckConstraint("ai_tokens_reserved >= 0", name="chk_sub_tokens_reserved"),
        CheckConstraint(
            "ai_tokens_used + ai_tokens_reserved <= ai_tokens_limit",
            name="chk_sub_tokens_total",
        ),
        CheckConstraint("max_users > 0", name="chk_sub_max_users"),
        CheckConstraint("max_active_jobs >= 0", name="chk_sub_max_jobs"),
        CheckConstraint(
            "current_period_end > current_period_start",
            name="chk_sub_period",
        ),
        CheckConstraint(
            "canceled_at IS NULL OR canceled_at >= started_at",
            name="chk_sub_canceled",
        ),
        CheckConstraint(
            "status <> 'canceled' OR canceled_at IS NOT NULL",
            name="chk_sub_status_canceled",
        ),

        Index("uq_active_company_subscription", "company_id",
              unique=True,
              postgresql_where=text("status IN ('trialing','active','past_due')")),
        Index("ix_subscriptions_period_end", "current_period_end",
              postgresql_where=text("status IN ('active','trialing')")),
        Index("ix_subscriptions_rollover", "company_id", "current_period_end",
              postgresql_where=text("status = 'active'")),
    )


class AiUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    operation_type: Mapped[str] = mapped_column(
        ENUM("resume_parsing", "resume_embedding", "semantic_matching",
             "screening_generation", "screening_evaluation", "other",
             name="ai_operation_type", create_type=False),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)

    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True,
    )
    prompt_hash: Mapped[str | None] = mapped_column(String(64))
    response_hash: Mapped[str | None] = mapped_column(String(64))

    input_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0"),
    )
    output_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0"),
    )
    total_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0"),
    )

    estimated_cost: Mapped[float | None] = mapped_column(Numeric(12, 6))

    status: Mapped[str] = mapped_column(
        ENUM("success", "failed", "rate_limited", "timeout", "rejected",
             name="ai_usage_status", create_type=False),
        nullable=False,
    )
    error_code: Mapped[str | None] = mapped_column(String(100))
    latency_ms: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "application_id"],
            ["applications.company_id", "applications.id"],
            name="fk_ai_usage_company_application", ondelete="RESTRICT",
        ),
        CheckConstraint("input_tokens >= 0", name="chk_ai_input_tokens"),
        CheckConstraint("output_tokens >= 0", name="chk_ai_output_tokens"),
        CheckConstraint("total_tokens >= 0", name="chk_ai_total_tokens"),
        CheckConstraint(
            "estimated_cost IS NULL OR estimated_cost >= 0",
            name="chk_ai_estimated_cost",
        ),
        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="chk_ai_latency",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= created_at",
            name="chk_ai_completed",
        ),
        CheckConstraint(
            "status <> 'failed' OR error_code IS NOT NULL",
            name="chk_ai_failed_error",
        ),

        Index("ix_ai_usage_company_time", "company_id", "created_at"),
        Index("ix_ai_usage_company_feature", "company_id", "operation_type", "created_at"),
    )
