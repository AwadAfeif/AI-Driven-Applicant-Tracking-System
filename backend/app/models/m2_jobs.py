"""M2 — Jobs & Requirements."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, CHAR, CheckConstraint, DateTime, ForeignKey, Index, Integer,
    Numeric, String, Text, UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


UUID_PK = dict(primary_key=True, server_default=text("gen_random_uuid()"))


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_by_snapshot: Mapped[dict | None] = mapped_column(JSONB)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))

    employment_type: Mapped[str] = mapped_column(
        ENUM("full_time", "part_time", "contract", "internship",
             "temporary", "freelance",
             name="employment_type", create_type=False),
        nullable=False, server_default=text("'full_time'"),
    )
    work_mode: Mapped[str] = mapped_column(
        ENUM("onsite", "hybrid", "remote", name="work_mode", create_type=False),
        nullable=False, server_default=text("'onsite'"),
    )
    seniority: Mapped[str | None] = mapped_column(
        ENUM("intern", "junior", "mid", "senior", "lead", "principal", "director",
             name="seniority_level", create_type=False),
    )

    location_country: Mapped[str | None] = mapped_column(CHAR(2))
    location_city: Mapped[str | None] = mapped_column(String(100))

    salary_min: Mapped[float | None] = mapped_column(Numeric(12, 2))
    salary_max: Mapped[float | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(CHAR(3))
    salary_period: Mapped[str | None] = mapped_column(
        ENUM("hourly", "monthly", "yearly", name="salary_period", create_type=False),
    )

    experience_min: Mapped[float | None] = mapped_column(Numeric(4, 1))
    experience_max: Mapped[float | None] = mapped_column(Numeric(4, 1))

    openings_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1"),
    )
    blind_screening: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"),
    )

    status: Mapped[str] = mapped_column(
        ENUM("draft", "published", "paused", "closed", "archived",
             name="job_status", create_type=False),
        nullable=False, server_default=text("'draft'"),
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    application_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("company_id", "slug", name="uq_jobs_company_slug"),
        UniqueConstraint("company_id", "id", name="uq_jobs_company_id_pair"),

        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="chk_jobs_salary_range",
        ),
        CheckConstraint(
            "(salary_min IS NULL OR salary_min >= 0) AND "
            "(salary_max IS NULL OR salary_max >= 0)",
            name="chk_jobs_salary_nonneg",
        ),
        CheckConstraint(
            "(salary_min IS NULL AND salary_max IS NULL) OR "
            "(currency IS NOT NULL AND salary_period IS NOT NULL)",
            name="chk_jobs_salary_completeness",
        ),
        CheckConstraint(
            "experience_min IS NULL OR experience_max IS NULL "
            "OR experience_min <= experience_max",
            name="chk_jobs_experience_range",
        ),
        CheckConstraint(
            "(experience_min IS NULL OR experience_min >= 0) AND "
            "(experience_max IS NULL OR experience_max >= 0)",
            name="chk_jobs_experience_nonneg",
        ),
        CheckConstraint("openings_count > 0", name="chk_jobs_openings_positive"),
        CheckConstraint(
            "status <> 'published' OR published_at IS NOT NULL",
            name="chk_jobs_published_at",
        ),
        CheckConstraint(
            "status <> 'closed' OR closed_at IS NOT NULL",
            name="chk_jobs_closed_at",
        ),
        CheckConstraint(
            "status NOT IN ('draft','archived') OR "
            "(published_at IS NULL AND closed_at IS NULL)",
            name="chk_jobs_draft_purity",
        ),
        CheckConstraint(
            "work_mode = 'remote' OR location_country IS NOT NULL",
            name="chk_jobs_location",
        ),

        Index("ix_jobs_company_status", "company_id", "status",
              postgresql_where=text("deleted_at IS NULL")),
        Index("ix_jobs_company_created", "company_id", "created_at",
              postgresql_where=text("deleted_at IS NULL")),
        Index("ix_jobs_public_listing", "status", "published_at",
              postgresql_where=text("deleted_at IS NULL AND status = 'published'")),
        Index("ix_jobs_deadline_sweep", "application_deadline",
              postgresql_where=text("status = 'published' AND application_deadline IS NOT NULL")),
        Index("ix_jobs_country", "location_country",
              postgresql_where=text("deleted_at IS NULL AND status = 'published'")),
        Index("ix_jobs_employment_type", "employment_type",
              postgresql_where=text("deleted_at IS NULL AND status = 'published'")),
    )


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), **UUID_PK)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False,
    )

    requirement_type: Mapped[str] = mapped_column(
        ENUM("skill", "education", "certification", "experience",
             "language", "tool", "domain_knowledge", "other",
             name="requirement_type", create_type=False),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text)

    is_mandatory: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"),
    )
    weight: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, server_default=text("1.00"),
    )
    minimum_years: Mapped[float | None] = mapped_column(Numeric(4, 1))
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint("weight >= 0", name="chk_job_req_weight_nonneg"),
        CheckConstraint(
            "minimum_years IS NULL OR minimum_years >= 0",
            name="chk_job_req_min_years_nonneg",
        ),
        CheckConstraint(
            "LENGTH(TRIM(name)) > 0", name="chk_job_req_name_not_empty",
        ),
        CheckConstraint("sort_order >= 0", name="chk_job_req_sort_order"),

        Index("ix_job_req_job_sort", "job_id", "sort_order", "created_at"),
        Index("ix_job_req_type", "job_id", "requirement_type"),
        Index("ix_job_req_mandatory", "job_id",
              postgresql_where=text("is_mandatory = TRUE")),
        Index("ix_job_req_min_years", "job_id",
              postgresql_where=text("minimum_years IS NOT NULL")),
    )
