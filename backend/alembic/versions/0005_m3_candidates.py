"""M3 — Candidates, Profiles, Resumes, Applications.

Revision ID: 0005_m3_candidates
Revises: 0004_m2_jobs
Create Date: 2026-09-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_m3_candidates"
down_revision: Union[str, None] = "0004_m2_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID_PK = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    # ═══ candidates ═══
    op.create_table(
        "candidates",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID_PK, nullable=False),
        sa.Column("candidate_code", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_candidates"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],
                                ondelete="CASCADE", name="fk_candidates_user"),
        sa.UniqueConstraint("user_id", name="uq_candidates_user_id"),
        sa.UniqueConstraint("candidate_code", name="uq_candidates_code"),
        sa.CheckConstraint("candidate_code ~ '^CND-[A-Z0-9]+$'",
                           name="chk_candidate_code_format"),
    )
    op.execute("CREATE INDEX ix_candidates_active ON candidates (is_active) "
               "WHERE is_active = TRUE")

    # ═══ candidate_profiles ═══
    op.create_table(
        "candidate_profiles",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("candidate_id", UUID_PK, nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("headline", sa.String(200), nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("github_url", sa.String(500), nullable=True),
        sa.Column("portfolio_url", sa.String(500), nullable=True),
        sa.Column("years_experience", sa.Numeric(4, 1), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_candidate_profiles"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"],
                                ondelete="CASCADE", name="fk_cand_profiles_candidate"),
        sa.UniqueConstraint("candidate_id", name="uq_cand_profiles_candidate"),
        sa.CheckConstraint("years_experience IS NULL OR years_experience >= 0",
                           name="chk_profile_exp_positive"),
    )
    op.execute("CREATE INDEX ix_cand_profiles_exp ON candidate_profiles (years_experience) "
               "WHERE years_experience IS NOT NULL")

    # ═══ resumes ═══
    op.create_table(
        "resumes",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("candidate_id", UUID_PK, nullable=False),
        sa.Column("version", sa.Integer, server_default=sa.text("1"), nullable=False),
        sa.Column("is_primary", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("status",
                  postgresql.ENUM("uploaded", "processing", "processed", "failed", "archived",
                                  name="resume_status", create_type=False),
                  server_default=sa.text("'uploaded'"), nullable=False),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("normalized_text", sa.Text, nullable=True),
        sa.Column("anonymized_text", sa.Text, nullable=True),
        sa.Column("anonymization_meta", postgresql.JSONB, nullable=True),
        sa.Column("parsed_json", postgresql.JSONB, nullable=True),
        sa.Column("parse_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_resumes"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"],
                                ondelete="CASCADE", name="fk_resumes_candidate"),
        sa.UniqueConstraint("candidate_id", "id", name="uq_resumes_candidate_id_pair"),
        sa.CheckConstraint("version > 0", name="chk_resume_version_positive"),
        sa.CheckConstraint("file_size_bytes > 0 AND file_size_bytes <= 10485760",
                           name="chk_resume_file_size"),
        sa.CheckConstraint("status <> 'failed' OR parse_error IS NOT NULL",
                           name="chk_resume_failed_error"),
    )
    op.execute("CREATE UNIQUE INDEX uq_resumes_candidate_version "
               "ON resumes (candidate_id, version) WHERE deleted_at IS NULL")
    op.execute("CREATE UNIQUE INDEX uq_resumes_candidate_primary "
               "ON resumes (candidate_id) WHERE is_primary = TRUE AND deleted_at IS NULL")
    op.execute("CREATE UNIQUE INDEX uq_resumes_candidate_hash "
               "ON resumes (candidate_id, content_hash) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX ix_resumes_status_pending ON resumes (status) "
               "WHERE status IN ('uploaded','processing')")

    # ═══ applications ═══
    op.create_table(
        "applications",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", UUID_PK, nullable=False),
        sa.Column("job_id", UUID_PK, nullable=False),
        sa.Column("candidate_id", UUID_PK, nullable=False),
        sa.Column("resume_id", UUID_PK, nullable=False),
        sa.Column("cover_letter", sa.Text, nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("status",
                  postgresql.ENUM("submitted", "under_review", "screening", "shortlisted",
                                  "interview", "offer", "rejected", "withdrawn", "hired",
                                  name="application_status", create_type=False),
                  server_default=sa.text("'submitted'"), nullable=False),
        sa.Column("status_updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("identity_revealed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("identity_revealed_by", UUID_PK, nullable=True),
        sa.Column("matching_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("screening_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("final_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("ranking_version", sa.String(50), nullable=True),
        sa.Column("explanation_version", sa.String(50), nullable=True),
        sa.Column("score_breakdown", postgresql.JSONB, nullable=True),
        sa.Column("decision_reason", sa.Text, nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_applications"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"],
                                ondelete="CASCADE", name="fk_applications_candidate"),
        sa.ForeignKeyConstraint(["identity_revealed_by"], ["users.id"],
                                ondelete="SET NULL", name="fk_applications_revealed_by"),
        sa.ForeignKeyConstraint(
            ["company_id", "job_id"], ["jobs.company_id", "jobs.id"],
            name="fk_applications_job_company", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id", "resume_id"], ["resumes.candidate_id", "resumes.id"],
            name="fk_applications_candidate_resume", ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("job_id", "candidate_id",
                            name="uq_applications_job_candidate"),
        sa.UniqueConstraint("company_id", "id",
                            name="uq_applications_company_id_pair"),
        sa.CheckConstraint("matching_score IS NULL OR matching_score BETWEEN 0 AND 100",
                           name="chk_app_matching_bounds"),
        sa.CheckConstraint("screening_score IS NULL OR screening_score BETWEEN 0 AND 100",
                           name="chk_app_screening_bounds"),
        sa.CheckConstraint("final_score IS NULL OR final_score BETWEEN 0 AND 100",
                           name="chk_app_final_bounds"),
        sa.CheckConstraint("(identity_revealed_at IS NULL) = (identity_revealed_by IS NULL)",
                           name="chk_app_identity_reveal_consistency"),
    )
    op.execute("CREATE INDEX ix_applications_job_status "
               "ON applications (job_id, status) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX ix_applications_candidate "
               "ON applications (candidate_id) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX ix_applications_company_status "
               "ON applications (company_id, status) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX ix_applications_company_applied "
               "ON applications (company_id, applied_at) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX ix_applications_identity_revealed "
               "ON applications (company_id, identity_revealed_at) "
               "WHERE identity_revealed_at IS NOT NULL")


def downgrade() -> None:
    op.drop_table("applications")
    op.drop_table("resumes")
    op.drop_table("candidate_profiles")
    op.drop_table("candidates")
