"""M6 — Application Scores & Notifications.

Revision ID: 0008_m6_scoring_notifications
Revises: 0007_m5_subscriptions
Create Date: 2026-09-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_m6_scoring_notifications"
down_revision: Union[str, None] = "0007_m5_subscriptions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID_PK = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    # ═══ application_scores ═══
    op.create_table(
        "application_scores",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", UUID_PK, nullable=False),
        sa.Column("application_id", UUID_PK, nullable=False),
        sa.Column("matching_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("screening_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("final_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("ranking_version", sa.String(50), nullable=False),
        sa.Column("score_breakdown", postgresql.JSONB, nullable=False),
        sa.Column("trigger_type",
                  postgresql.ENUM("initial", "resume_updated", "screening_completed",
                                  "manual_recalculation", "algorithm_recalculation",
                                  name="scoring_trigger", create_type=False),
                  nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_application_scores"),
        sa.ForeignKeyConstraint(
            ["company_id", "application_id"],
            ["applications.company_id", "applications.id"],
            name="fk_scores_company_application", ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "matching_score IS NULL OR matching_score BETWEEN 0 AND 100",
            name="chk_scores_matching_bounds"),
        sa.CheckConstraint(
            "screening_score IS NULL OR screening_score BETWEEN 0 AND 100",
            name="chk_scores_screening_bounds"),
        sa.CheckConstraint(
            "final_score IS NULL OR final_score BETWEEN 0 AND 100",
            name="chk_scores_final_bounds"),
        sa.CheckConstraint(
            "matching_score IS NOT NULL OR screening_score IS NOT NULL "
            "OR final_score IS NOT NULL",
            name="chk_scores_at_least_one"),
        sa.CheckConstraint(
            "LENGTH(TRIM(ranking_version)) > 0",
            name="chk_scores_ranking_version"),
    )
    op.create_index("ix_scores_application_time", "application_scores",
                    ["application_id", "created_at"])
    op.create_index("ix_scores_company_time", "application_scores",
                    ["company_id", "created_at"])

    # ═══ notifications ═══
    op.create_table(
        "notifications",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID_PK, nullable=False),
        sa.Column("company_id", UUID_PK, nullable=True),
        sa.Column("recipient_kind",
                  postgresql.ENUM("company_member", "candidate", "system",
                                  name="recipient_kind", create_type=False),
                  nullable=False),
        sa.Column("notification_type",
                  postgresql.ENUM("application_update", "screening_invitation",
                                  "screening_reminder", "ai_processing",
                                  "subscription", "system", "marketing",
                                  name="notification_type", create_type=False),
                  nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("data", postgresql.JSONB, nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_notifications"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                ondelete="CASCADE", name="fk_notifications_user"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"],
                                ondelete="CASCADE", name="fk_notifications_company"),
        sa.CheckConstraint(
            "recipient_kind <> 'company_member' OR company_id IS NOT NULL",
            name="chk_notif_company_member"),
        sa.CheckConstraint("LENGTH(TRIM(title)) > 0", name="chk_notif_title_not_empty"),
        sa.CheckConstraint("LENGTH(TRIM(message)) > 0", name="chk_notif_message_not_empty"),
        sa.CheckConstraint(
            "expires_at IS NULL OR expires_at >= created_at",
            name="chk_notif_expires"),
    )
    op.create_index("ix_notif_user_time", "notifications", ["user_id", "created_at"])
    op.execute("CREATE INDEX ix_notif_user_unread ON notifications (user_id, created_at) "
               "WHERE read_at IS NULL")
    op.execute("CREATE INDEX ix_notif_company_time ON notifications (company_id, created_at) "
               "WHERE company_id IS NOT NULL")
    op.execute("CREATE INDEX ix_notif_expiry_sweep ON notifications (expires_at) "
               "WHERE expires_at IS NOT NULL AND read_at IS NULL")

    # ═══ notification_preferences ═══
    op.create_table(
        "notification_preferences",
        sa.Column("user_id", UUID_PK, nullable=False),
        sa.Column("notification_type",
                  postgresql.ENUM("application_update", "screening_invitation",
                                  "screening_reminder", "ai_processing",
                                  "subscription", "system", "marketing",
                                  name="notification_type", create_type=False),
                  nullable=False),
        sa.Column("enabled", sa.Boolean,
                  server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "notification_type",
                                name="pk_notification_preferences"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                ondelete="CASCADE", name="fk_notif_pref_user"),
        sa.CheckConstraint(
            "notification_type <> 'system' OR enabled = TRUE",
            name="chk_pref_system_always_enabled"),
    )


def downgrade() -> None:
    op.drop_table("notification_preferences")
    op.drop_table("notifications")
    op.drop_table("application_scores")
