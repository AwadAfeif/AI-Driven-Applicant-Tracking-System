"""M4 — Screening & AI Evaluation.

Revision ID: 0006_m4_screening
Revises: 0005_m3_candidates
Create Date: 2026-09-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_m4_screening"
down_revision: Union[str, None] = "0005_m3_candidates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID_PK = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    # ═══ screening_sessions ═══
    op.create_table(
        "screening_sessions",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("application_id", UUID_PK, nullable=False),
        sa.Column("company_id", UUID_PK, nullable=False),
        sa.Column("job_id", UUID_PK, nullable=False),
        sa.Column("candidate_id", UUID_PK, nullable=False),
        sa.Column("duration_seconds", sa.Integer, nullable=False),
        sa.Column("question_count", sa.Integer, nullable=False),
        sa.Column("status",
                  postgresql.ENUM("pending", "active", "submitted", "evaluated",
                                  "expired", "terminated",
                                  name="screening_session_status", create_type=False),
                  server_default=sa.text("'pending'"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("terminated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("max_possible_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_screening_sessions"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"],
                                ondelete="CASCADE", name="fk_sessions_company"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"],
                                ondelete="CASCADE", name="fk_sessions_candidate"),
        sa.ForeignKeyConstraint(
            ["company_id", "application_id"],
            ["applications.company_id", "applications.id"],
            name="fk_sessions_company_application", ondelete="CASCADE",
        ),
        sa.UniqueConstraint("application_id", name="uq_sessions_application"),
        sa.UniqueConstraint("company_id", "id", name="uq_sessions_company_id_pair"),
        sa.CheckConstraint("duration_seconds BETWEEN 300 AND 28800",
                           name="chk_session_duration"),
        sa.CheckConstraint("question_count BETWEEN 1 AND 50",
                           name="chk_session_question_count"),
        sa.CheckConstraint("total_score IS NULL OR total_score >= 0",
                           name="chk_session_total_score"),
        sa.CheckConstraint("max_possible_score IS NULL OR max_possible_score > 0",
                           name="chk_session_max_score"),
        sa.CheckConstraint(
            "total_score IS NULL OR max_possible_score IS NULL "
            "OR total_score <= max_possible_score",
            name="chk_session_score_bounds",
        ),
        sa.CheckConstraint(
            "(status <> 'active'    OR (started_at IS NOT NULL AND expires_at IS NOT NULL)) AND "
            "(status <> 'submitted' OR submitted_at IS NOT NULL) AND "
            "(status <> 'evaluated' OR (submitted_at IS NOT NULL AND evaluated_at IS NOT NULL)) AND "
            "(status <> 'expired'   OR (started_at IS NOT NULL AND expired_at IS NOT NULL)) AND "
            "(status <> 'terminated' OR terminated_at IS NOT NULL)",
            name="chk_session_state_timestamps",
        ),
        sa.CheckConstraint(
            "started_at IS NULL OR expires_at IS NULL OR expires_at > started_at",
            name="chk_session_expires_after_start",
        ),
        sa.CheckConstraint(
            "submitted_at IS NULL OR started_at IS NULL OR submitted_at >= started_at",
            name="chk_session_submit_after_start",
        ),
    )
    op.create_index("ix_sessions_company_status", "screening_sessions",
                    ["company_id", "status"])
    op.create_index("ix_sessions_job", "screening_sessions", ["job_id"])
    op.create_index("ix_sessions_candidate", "screening_sessions", ["candidate_id"])
    op.execute("CREATE INDEX ix_sessions_expiry_sweep ON screening_sessions (expires_at) "
               "WHERE status = 'active'")
    op.execute("CREATE INDEX ix_sessions_pending_eval ON screening_sessions (submitted_at) "
               "WHERE status = 'submitted'")

    # ═══ screening_questions ═══
    op.create_table(
        "screening_questions",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", UUID_PK, nullable=False),
        sa.Column("question_order", sa.Integer, nullable=False),
        sa.Column("question_type",
                  postgresql.ENUM("text", "scenario", "single_choice", "multi_choice",
                                  name="question_type", create_type=False),
                  nullable=False),
        sa.Column("evaluation_mode",
                  postgresql.ENUM("ai", "deterministic",
                                  name="evaluation_mode", create_type=False),
                  server_default=sa.text("'ai'"), nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("options", postgresql.JSONB, nullable=True),
        sa.Column("evaluation_rubric", postgresql.JSONB,
                  server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("max_score", sa.Numeric(6, 2),
                  server_default=sa.text("10"), nullable=False),
        sa.Column("generation_model", sa.String(100), nullable=True),
        sa.Column("generation_version", sa.String(50), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_screening_questions"),
        sa.ForeignKeyConstraint(["session_id"], ["screening_sessions.id"],
                                ondelete="CASCADE", name="fk_questions_session"),
        sa.UniqueConstraint("session_id", "question_order",
                            name="uq_questions_session_order"),
        sa.UniqueConstraint("session_id", "id",
                            name="uq_questions_session_id_pair"),
        sa.CheckConstraint("question_order > 0", name="chk_question_order_positive"),
        sa.CheckConstraint("max_score > 0", name="chk_question_max_score"),
        sa.CheckConstraint("LENGTH(TRIM(question_text)) > 0",
                           name="chk_question_text_not_empty"),
        sa.CheckConstraint(
            "question_type NOT IN ('single_choice','multi_choice') OR options IS NOT NULL",
            name="chk_question_options_required",
        ),
        sa.CheckConstraint(
            "(question_type IN ('text','scenario') AND evaluation_mode = 'ai') OR "
            "(question_type IN ('single_choice','multi_choice') "
            " AND evaluation_mode = 'deterministic')",
            name="chk_question_evaluation_mode",
        ),
    )

    # ═══ screening_answers ═══
    op.create_table(
        "screening_answers",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", UUID_PK, nullable=False),
        sa.Column("question_id", UUID_PK, nullable=False),
        sa.Column("answer_text", sa.Text, nullable=True),
        sa.Column("answer_payload", postgresql.JSONB, nullable=True),
        sa.Column("served_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_spent_seconds", sa.Integer, nullable=True),
        sa.Column("answer_status",
                  postgresql.ENUM("draft", "submitted", "late", "invalidated",
                                  name="answer_status", create_type=False),
                  server_default=sa.text("'draft'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_screening_answers"),
        sa.ForeignKeyConstraint(
            ["session_id", "question_id"],
            ["screening_questions.session_id", "screening_questions.id"],
            name="fk_answers_session_question", ondelete="CASCADE",
        ),
        sa.UniqueConstraint("question_id", name="uq_answers_question"),
        sa.CheckConstraint(
            "(answer_text IS NULL AND answer_payload IS NULL) OR "
            "(answer_text IS NOT NULL AND answer_payload IS NULL) OR "
            "(answer_text IS NULL AND answer_payload IS NOT NULL)",
            name="chk_answer_payload_exclusive",
        ),
        sa.CheckConstraint(
            "submitted_at IS NULL OR submitted_at >= served_at",
            name="chk_answer_submitted_after_served",
        ),
        sa.CheckConstraint(
            "time_spent_seconds IS NULL OR time_spent_seconds >= 0",
            name="chk_answer_time_spent_nonneg",
        ),
        sa.CheckConstraint(
            "(submitted_at IS NULL) = (answer_status = 'draft')",
            name="chk_answer_status_submitted",
        ),
    )
    op.create_index("ix_answers_session", "screening_answers", ["session_id"])
    op.create_index("ix_answers_status", "screening_answers", ["answer_status"])

    # ═══ screening_evaluations ═══
    op.create_table(
        "screening_evaluations",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("answer_id", UUID_PK, nullable=False),
        sa.Column("evaluator_type",
                  postgresql.ENUM("ai", "human", "hybrid",
                                  name="evaluator_type", create_type=False),
                  server_default=sa.text("'ai'"), nullable=False),
        sa.Column("score", sa.Numeric(6, 2), nullable=False),
        sa.Column("max_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("feedback", sa.Text, nullable=True),
        sa.Column("justification", sa.Text, nullable=True),
        sa.Column("matched_concepts", postgresql.JSONB, nullable=True),
        sa.Column("missed_concepts", postgresql.JSONB, nullable=True),
        sa.Column("evaluation_model", sa.String(100), nullable=True),
        sa.Column("evaluation_version", sa.String(50), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("raw_response", postgresql.JSONB, nullable=True),
        sa.Column("request_id", UUID_PK, nullable=True),
        sa.Column("evaluated_by", UUID_PK, nullable=True),
        sa.Column("override_reason", sa.Text, nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_screening_evaluations"),
        sa.ForeignKeyConstraint(["answer_id"], ["screening_answers.id"],
                                ondelete="CASCADE", name="fk_eval_answer"),
        sa.ForeignKeyConstraint(["evaluated_by"], ["users.id"],
                                ondelete="SET NULL", name="fk_eval_user"),
        sa.UniqueConstraint("request_id", name="uq_eval_request_id"),
        sa.CheckConstraint("score >= 0 AND score <= max_score",
                           name="chk_eval_score_bounds"),
        sa.CheckConstraint("max_score > 0", name="chk_eval_max_score"),
        sa.CheckConstraint("evaluator_type <> 'human' OR evaluated_by IS NOT NULL",
                           name="chk_eval_human_required"),
        sa.CheckConstraint("evaluated_by IS NULL OR override_reason IS NOT NULL",
                           name="chk_eval_override_reason"),
    )
    op.create_index("ix_eval_answer_latest", "screening_evaluations",
                    ["answer_id", "evaluated_at", "id"])
    op.create_index("ix_eval_type", "screening_evaluations",
                    ["evaluator_type", "evaluated_at"])
    op.execute("CREATE INDEX ix_eval_request ON screening_evaluations (request_id) "
               "WHERE request_id IS NOT NULL")

    # ═══ Triggers ═══
    op.execute("""
        CREATE OR REPLACE FUNCTION sync_session_from_application()
        RETURNS TRIGGER AS $func$
        BEGIN
            SELECT a.job_id, a.candidate_id
            INTO NEW.job_id, NEW.candidate_id
            FROM applications a
            WHERE a.id = NEW.application_id;

            IF NOT FOUND THEN
                RAISE EXCEPTION 'application_id does not exist: %', NEW.application_id;
            END IF;
            RETURN NEW;
        END;
        $func$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_session_sync
        BEFORE INSERT OR UPDATE OF application_id ON screening_sessions
        FOR EACH ROW EXECUTE FUNCTION sync_session_from_application()
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_answer_mutation()
        RETURNS TRIGGER AS $func$
        BEGIN
            IF OLD.answer_status IN ('submitted','late','invalidated') THEN
                IF NEW.answer_text         IS DISTINCT FROM OLD.answer_text
                OR NEW.answer_payload      IS DISTINCT FROM OLD.answer_payload
                OR NEW.submitted_at        IS DISTINCT FROM OLD.submitted_at
                OR NEW.time_spent_seconds  IS DISTINCT FROM OLD.time_spent_seconds
                OR NEW.answer_status       IS DISTINCT FROM OLD.answer_status
                THEN
                    RAISE EXCEPTION 'Answer is immutable after submission';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $func$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_prevent_answer_mutation
        BEFORE UPDATE ON screening_answers
        FOR EACH ROW EXECUTE FUNCTION prevent_answer_mutation()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_answer_mutation ON screening_answers")
    op.execute("DROP TRIGGER IF EXISTS trg_session_sync ON screening_sessions")
    op.execute("DROP FUNCTION IF EXISTS prevent_answer_mutation()")
    op.execute("DROP FUNCTION IF EXISTS sync_session_from_application()")
    op.drop_table("screening_evaluations")
    op.drop_table("screening_answers")
    op.drop_table("screening_questions")
    op.drop_table("screening_sessions")
