"""M3 — Candidates, Profiles, Resumes, Applications."""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint,
    Index, Integer, Numeric, String, Text, UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


UUID_PK = dict(primary_key=True, server_default=text("gen_random_uuid()"))


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    candidate_code: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(
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
        UniqueConstraint("user_id", name="uq_candidates_user_id"),
        UniqueConstraint("candidate_code", name="uq_candidates_code"),
        CheckConstraint(
            "candidate_code ~ '^CND-[A-Z0-9]+$'",
            name="chk_candidate_code_format",
        ),
        Index("ix_candidates_active", "is_active",
              postgresql_where=text("is_active = TRUE")),
    )


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )

    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    headline: Mapped[str | None] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(200))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    years_experience: Mapped[float | None] = mapped_column(Numeric(4, 1))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0",
            name="chk_profile_exp_positive",
        ),
        Index("ix_cand_profiles_exp", "years_experience",
              postgresql_where=text("years_experience IS NOT NULL")),
    )


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False,
    )

    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"),
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"),
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    status: Mapped[str] = mapped_column(
        ENUM("uploaded", "processing", "processed", "failed", "archived",
             name="resume_status", create_type=False),
        nullable=False, server_default=text("'uploaded'"),
    )

    raw_text: Mapped[str | None] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    anonymized_text: Mapped[str | None] = mapped_column(Text)
    anonymization_meta: Mapped[dict | None] = mapped_column(JSONB)
    parsed_json: Mapped[dict | None] = mapped_column(JSONB)
    parse_error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("candidate_id", "id", name="uq_resumes_candidate_id_pair"),
        CheckConstraint("version > 0", name="chk_resume_version_positive"),
        CheckConstraint(
            "file_size_bytes > 0 AND file_size_bytes <= 10485760",
            name="chk_resume_file_size",
        ),
        CheckConstraint(
            "status <> 'failed' OR parse_error IS NOT NULL",
            name="chk_resume_failed_error",
        ),
        Index("uq_resumes_candidate_version", "candidate_id", "version",
              unique=True, postgresql_where=text("deleted_at IS NULL")),
        Index("uq_resumes_candidate_primary", "candidate_id",
              unique=True, postgresql_where=text("is_primary = TRUE AND deleted_at IS NULL")),
        Index("uq_resumes_candidate_hash", "candidate_id", "content_hash",
              unique=True, postgresql_where=text("deleted_at IS NULL")),
        Index("ix_resumes_status_pending", "status",
              postgresql_where=text("status IN ('uploaded','processing')")),
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    cover_letter: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(50))

    status: Mapped[str] = mapped_column(
        ENUM("submitted", "under_review", "screening", "shortlisted",
             "interview", "offer", "rejected", "withdrawn", "hired",
             name="application_status", create_type=False),
        nullable=False, server_default=text("'submitted'"),
    )
    status_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )

    identity_revealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    identity_revealed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
    )

    matching_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    screening_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    final_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    ranking_version: Mapped[str | None] = mapped_column(String(50))
    explanation_version: Mapped[str | None] = mapped_column(String(50))
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB)

    decision_reason: Mapped[str | None] = mapped_column(Text)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("job_id", "candidate_id", name="uq_applications_job_candidate"),
        UniqueConstraint("company_id", "id", name="uq_applications_company_id_pair"),

        ForeignKeyConstraint(
            ["company_id", "job_id"], ["jobs.company_id", "jobs.id"],
            name="fk_applications_job_company", ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["candidate_id", "resume_id"], ["resumes.candidate_id", "resumes.id"],
            name="fk_applications_candidate_resume", ondelete="RESTRICT",
        ),

        CheckConstraint(
            "matching_score IS NULL OR matching_score BETWEEN 0 AND 100",
            name="chk_app_matching_bounds"),
        CheckConstraint(
            "screening_score IS NULL OR screening_score BETWEEN 0 AND 100",
            name="chk_app_screening_bounds"),
        CheckConstraint(
            "final_score IS NULL OR final_score BETWEEN 0 AND 100",
            name="chk_app_final_bounds"),
        CheckConstraint(
            "(identity_revealed_at IS NULL) = (identity_revealed_by IS NULL)",
            name="chk_app_identity_reveal_consistency"),

        Index("ix_applications_job_status", "job_id", "status",
              postgresql_where=text("deleted_at IS NULL")),
        Index("ix_applications_candidate", "candidate_id",
              postgresql_where=text("deleted_at IS NULL")),
        Index("ix_applications_company_status", "company_id", "status",
              postgresql_where=text("deleted_at IS NULL")),
        Index("ix_applications_company_applied", "company_id", "applied_at",
              postgresql_where=text("deleted_at IS NULL")),
        Index("ix_applications_identity_revealed", "company_id", "identity_revealed_at",
              postgresql_where=text("identity_revealed_at IS NOT NULL")),
    )
