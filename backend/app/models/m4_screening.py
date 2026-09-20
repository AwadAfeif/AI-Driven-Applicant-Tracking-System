"""M4 — Screening & AI Evaluation."""
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint,
    Index, Integer, Numeric, String, Text, UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


UUID_PK = dict(primary_key=True, server_default=text("gen_random_uuid()"))


class ScreeningSession(Base):
    __tablename__ = "screening_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False,
    )

    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(
        ENUM("pending", "active", "submitted", "evaluated", "expired", "terminated",
             name="screening_session_status", create_type=False),
        nullable=False, server_default=text("'pending'"),
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    terminated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    total_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    max_possible_score: Mapped[float | None] = mapped_column(Numeric(6, 2))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("company_id", "id", name="uq_sessions_company_id_pair"),
        ForeignKeyConstraint(
            ["company_id", "application_id"],
            ["applications.company_id", "applications.id"],
            name="fk_sessions_company_application", ondelete="CASCADE",
        ),
        CheckConstraint("duration_seconds BETWEEN 300 AND 28800",
                        name="chk_session_duration"),
        CheckConstraint("question_count BETWEEN 1 AND 50",
                        name="chk_session_question_count"),
        CheckConstraint("total_score IS NULL OR total_score >= 0",
                        name="chk_session_total_score"),
        CheckConstraint("max_possible_score IS NULL OR max_possible_score > 0",
                        name="chk_session_max_score"),
        CheckConstraint(
            "total_score IS NULL OR max_possible_score IS NULL "
            "OR total_score <= max_possible_score",
            name="chk_session_score_bounds",
        ),
        CheckConstraint(
            "(status <> 'active'    OR (started_at IS NOT NULL AND expires_at IS NOT NULL)) AND "
            "(status <> 'submitted' OR submitted_at IS NOT NULL) AND "
            "(status <> 'evaluated' OR (submitted_at IS NOT NULL AND evaluated_at IS NOT NULL)) AND "
            "(status <> 'expired'   OR (started_at IS NOT NULL AND expired_at IS NOT NULL)) AND "
            "(status <> 'terminated' OR terminated_at IS NOT NULL)",
            name="chk_session_state_timestamps",
        ),
        CheckConstraint(
            "started_at IS NULL OR expires_at IS NULL OR expires_at > started_at",
            name="chk_session_expires_after_start",
        ),
        CheckConstraint(
            "submitted_at IS NULL OR started_at IS NULL OR submitted_at >= started_at",
            name="chk_session_submit_after_start",
        ),

        Index("ix_sessions_company_status", "company_id", "status"),
        Index("ix_sessions_expiry_sweep", "expires_at",
              postgresql_where=text("status = 'active'")),
        Index("ix_sessions_pending_eval", "submitted_at",
              postgresql_where=text("status = 'submitted'")),
        Index("ix_sessions_job", "job_id"),
        Index("ix_sessions_candidate", "candidate_id"),
    )


class ScreeningQuestion(Base):
    __tablename__ = "screening_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("screening_sessions.id", ondelete="CASCADE"), nullable=False,
    )

    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(
        ENUM("text", "scenario", "single_choice", "multi_choice",
             name="question_type", create_type=False),
        nullable=False,
    )
    evaluation_mode: Mapped[str] = mapped_column(
        ENUM("ai", "deterministic", name="evaluation_mode", create_type=False),
        nullable=False, server_default=text("'ai'"),
    )

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict | None] = mapped_column(JSONB)
    # SERVER-ONLY: never sent to candidate Frontend
    evaluation_rubric: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb"),
    )

    max_score: Mapped[float] = mapped_column(
        Numeric(6, 2), nullable=False, server_default=text("10"),
    )

    generation_model: Mapped[str | None] = mapped_column(String(100))
    generation_version: Mapped[str | None] = mapped_column(String(50))
    prompt_hash: Mapped[str | None] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("session_id", "question_order",
                         name="uq_questions_session_order"),
        UniqueConstraint("session_id", "id",
                         name="uq_questions_session_id_pair"),
        CheckConstraint("question_order > 0", name="chk_question_order_positive"),
        CheckConstraint("max_score > 0", name="chk_question_max_score"),
        CheckConstraint("LENGTH(TRIM(question_text)) > 0",
                        name="chk_question_text_not_empty"),
        CheckConstraint(
            "question_type NOT IN ('single_choice','multi_choice') OR options IS NOT NULL",
            name="chk_question_options_required",
        ),
        CheckConstraint(
            "(question_type IN ('text','scenario') AND evaluation_mode = 'ai') OR "
            "(question_type IN ('single_choice','multi_choice') "
            " AND evaluation_mode = 'deterministic')",
            name="chk_question_evaluation_mode",
        ),
    )


class ScreeningAnswer(Base):
    __tablename__ = "screening_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True,
    )

    answer_text: Mapped[str | None] = mapped_column(Text)
    answer_payload: Mapped[dict | None] = mapped_column(JSONB)

    served_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer)

    answer_status: Mapped[str] = mapped_column(
        ENUM("draft", "submitted", "late", "invalidated",
             name="answer_status", create_type=False),
        nullable=False, server_default=text("'draft'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id", "question_id"],
            ["screening_questions.session_id", "screening_questions.id"],
            name="fk_answers_session_question", ondelete="CASCADE",
        ),
        CheckConstraint(
            "(answer_text IS NULL AND answer_payload IS NULL) OR "
            "(answer_text IS NOT NULL AND answer_payload IS NULL) OR "
            "(answer_text IS NULL AND answer_payload IS NOT NULL)",
            name="chk_answer_payload_exclusive",
        ),
        CheckConstraint(
            "submitted_at IS NULL OR submitted_at >= served_at",
            name="chk_answer_submitted_after_served",
        ),
        CheckConstraint(
            "time_spent_seconds IS NULL OR time_spent_seconds >= 0",
            name="chk_answer_time_spent_nonneg",
        ),
        CheckConstraint(
            "(submitted_at IS NULL) = (answer_status = 'draft')",
            name="chk_answer_status_submitted",
        ),

        Index("ix_answers_session", "session_id"),
        Index("ix_answers_status", "answer_status"),
    )


class ScreeningEvaluation(Base):
    __tablename__ = "screening_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    answer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("screening_answers.id", ondelete="CASCADE"), nullable=False,
    )

    evaluator_type: Mapped[str] = mapped_column(
        ENUM("ai", "human", "hybrid", name="evaluator_type", create_type=False),
        nullable=False, server_default=text("'ai'"),
    )

    score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text)
    justification: Mapped[str | None] = mapped_column(Text)
    matched_concepts: Mapped[dict | None] = mapped_column(JSONB)
    missed_concepts: Mapped[dict | None] = mapped_column(JSONB)

    evaluation_model: Mapped[str | None] = mapped_column(String(100))
    evaluation_version: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_hash: Mapped[str | None] = mapped_column(String(64))
    raw_response: Mapped[dict | None] = mapped_column(JSONB)
    request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), unique=True,
    )

    evaluated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
    )
    override_reason: Mapped[str | None] = mapped_column(Text)

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= max_score",
                        name="chk_eval_score_bounds"),
        CheckConstraint("max_score > 0", name="chk_eval_max_score"),
        CheckConstraint("evaluator_type <> 'human' OR evaluated_by IS NOT NULL",
                        name="chk_eval_human_required"),
        CheckConstraint("evaluated_by IS NULL OR override_reason IS NOT NULL",
                        name="chk_eval_override_reason"),

        Index("ix_eval_answer_latest", "answer_id", "evaluated_at", "id"),
        Index("ix_eval_type", "evaluator_type", "evaluated_at"),
        Index("ix_eval_request", "request_id",
              postgresql_where=text("request_id IS NOT NULL")),
    )
