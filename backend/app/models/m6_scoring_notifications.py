"""M6 — Application Scores & Notifications."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint,
    Index, Numeric, String, Text, func, text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


UUID_PK = dict(primary_key=True, server_default=text("gen_random_uuid()"))


class ApplicationScore(Base):
    __tablename__ = "application_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    matching_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    screening_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    final_score: Mapped[float | None] = mapped_column(Numeric(6, 2))

    ranking_version: Mapped[str] = mapped_column(String(50), nullable=False)
    score_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    trigger_type: Mapped[str] = mapped_column(
        ENUM("initial", "resume_updated", "screening_completed",
             "manual_recalculation", "algorithm_recalculation",
             name="scoring_trigger", create_type=False),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "application_id"],
            ["applications.company_id", "applications.id"],
            name="fk_scores_company_application", ondelete="RESTRICT",
        ),
        CheckConstraint(
            "matching_score IS NULL OR matching_score BETWEEN 0 AND 100",
            name="chk_scores_matching_bounds"),
        CheckConstraint(
            "screening_score IS NULL OR screening_score BETWEEN 0 AND 100",
            name="chk_scores_screening_bounds"),
        CheckConstraint(
            "final_score IS NULL OR final_score BETWEEN 0 AND 100",
            name="chk_scores_final_bounds"),
        CheckConstraint(
            "matching_score IS NOT NULL OR screening_score IS NOT NULL "
            "OR final_score IS NOT NULL",
            name="chk_scores_at_least_one"),
        CheckConstraint(
            "LENGTH(TRIM(ranking_version)) > 0",
            name="chk_scores_ranking_version"),

        Index("ix_scores_application_time", "application_id", "created_at"),
        Index("ix_scores_company_time", "company_id", "created_at"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
    )
    recipient_kind: Mapped[str] = mapped_column(
        ENUM("company_member", "candidate", "system",
             name="recipient_kind", create_type=False),
        nullable=False,
    )
    notification_type: Mapped[str] = mapped_column(
        ENUM("application_update", "screening_invitation", "screening_reminder",
             "ai_processing", "subscription", "system", "marketing",
             name="notification_type", create_type=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB)

    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "recipient_kind <> 'company_member' OR company_id IS NOT NULL",
            name="chk_notif_company_member"),
        CheckConstraint("LENGTH(TRIM(title)) > 0", name="chk_notif_title_not_empty"),
        CheckConstraint("LENGTH(TRIM(message)) > 0", name="chk_notif_message_not_empty"),
        CheckConstraint(
            "expires_at IS NULL OR expires_at >= created_at",
            name="chk_notif_expires"),

        Index("ix_notif_user_time", "user_id", "created_at"),
        Index("ix_notif_user_unread", "user_id", "created_at",
              postgresql_where=text("read_at IS NULL")),
        Index("ix_notif_company_time", "company_id", "created_at",
              postgresql_where=text("company_id IS NOT NULL")),
        Index("ix_notif_expiry_sweep", "expires_at",
              postgresql_where=text("expires_at IS NOT NULL AND read_at IS NULL")),
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True,
    )
    notification_type: Mapped[str] = mapped_column(
        ENUM("application_update", "screening_invitation", "screening_reminder",
             "ai_processing", "subscription", "system", "marketing",
             name="notification_type", create_type=False),
        primary_key=True,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "notification_type <> 'system' OR enabled = TRUE",
            name="chk_pref_system_always_enabled"),
    )
