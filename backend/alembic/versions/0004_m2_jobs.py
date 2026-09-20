"""M2 — Jobs & Requirements.

Revision ID: 0004_m2_jobs
Revises: 0003_m1_identity
Create Date: 2026-09-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_m2_jobs"
down_revision: Union[str, None] = "0003_m1_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID_PK = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    # ═══ jobs ═══
    op.create_table(
        "jobs",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", UUID_PK, nullable=False),
        sa.Column("created_by", UUID_PK, nullable=True),
        sa.Column("created_by_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(220), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("employment_type",
                  postgresql.ENUM("full_time", "part_time", "contract", "internship",
                                  "temporary", "freelance",
                                  name="employment_type", create_type=False),
                  server_default=sa.text("'full_time'"), nullable=False),
        sa.Column("work_mode",
                  postgresql.ENUM("onsite", "hybrid", "remote",
                                  name="work_mode", create_type=False),
                  server_default=sa.text("'onsite'"), nullable=False),
        sa.Column("seniority",
                  postgresql.ENUM("intern", "junior", "mid", "senior", "lead",
                                  "principal", "director",
                                  name="seniority_level", create_type=False),
                  nullable=True),
        sa.Column("location_country", sa.CHAR(2), nullable=True),
        sa.Column("location_city", sa.String(100), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.CHAR(3), nullable=True),
        sa.Column("salary_period",
                  postgresql.ENUM("hourly", "monthly", "yearly",
                                  name="salary_period", create_type=False),
                  nullable=True),
        sa.Column("experience_min", sa.Numeric(4, 1), nullable=True),
        sa.Column("experience_max", sa.Numeric(4, 1), nullable=True),
        sa.Column("openings_count", sa.Integer,
                  server_default=sa.text("1"), nullable=False),
        sa.Column("blind_screening", sa.Boolean,
                  server_default=sa.text("true"), nullable=False),
        sa.Column("status",
                  postgresql.ENUM("draft", "published", "paused", "closed", "archived",
                                  name="job_status", create_type=False),
                  server_default=sa.text("'draft'"), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("application_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_jobs"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"],
                                ondelete="CASCADE", name="fk_jobs_company"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"],
                                ondelete="SET NULL", name="fk_jobs_created_by"),
        sa.UniqueConstraint("company_id", "slug", name="uq_jobs_company_slug"),
        sa.UniqueConstraint("company_id", "id", name="uq_jobs_company_id_pair"),
        sa.CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="chk_jobs_salary_range"),
        sa.CheckConstraint(
            "(salary_min IS NULL OR salary_min >= 0) AND "
            "(salary_max IS NULL OR salary_max >= 0)",
            name="chk_jobs_salary_nonneg"),
        sa.CheckConstraint(
            "(salary_min IS NULL AND salary_max IS NULL) OR "
            "(currency IS NOT NULL AND salary_period IS NOT NULL)",
            name="chk_jobs_salary_completeness"),
        sa.CheckConstraint(
            "experience_min IS NULL OR experience_max IS NULL "
            "OR experience_min <= experience_max",
            name="chk_jobs_experience_range"),
        sa.CheckConstraint(
            "(experience_min IS NULL OR experience_min >= 0) AND "
            "(experience_max IS NULL OR experience_max >= 0)",
            name="chk_jobs_experience_nonneg"),
        sa.CheckConstraint("openings_count > 0", name="chk_jobs_openings_positive"),
        sa.CheckConstraint(
            "status <> 'published' OR published_at IS NOT NULL",
            name="chk_jobs_published_at"),
        sa.CheckConstraint(
            "status <> 'closed' OR closed_at IS NOT NULL",
            name="chk_jobs_closed_at"),
        sa.CheckConstraint(
            "status NOT IN ('draft','archived') OR "
            "(published_at IS NULL AND closed_at IS NULL)",
            name="chk_jobs_draft_purity"),
        sa.CheckConstraint(
            "work_mode = 'remote' OR location_country IS NOT NULL",
            name="chk_jobs_location"),
    )
    op.execute("CREATE INDEX ix_jobs_company_status ON jobs (company_id, status) "
               "WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX ix_jobs_company_created ON jobs (company_id, created_at) "
               "WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX ix_jobs_public_listing ON jobs (status, published_at) "
               "WHERE deleted_at IS NULL AND status = 'published'")
    op.execute("CREATE INDEX ix_jobs_deadline_sweep ON jobs (application_deadline) "
               "WHERE status = 'published' AND application_deadline IS NOT NULL")
    op.execute("CREATE INDEX ix_jobs_country ON jobs (location_country) "
               "WHERE deleted_at IS NULL AND status = 'published'")
    op.execute("CREATE INDEX ix_jobs_employment_type ON jobs (employment_type) "
               "WHERE deleted_at IS NULL AND status = 'published'")

    # ═══ job_requirements ═══
    op.create_table(
        "job_requirements",
        sa.Column("id", UUID_PK, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("job_id", UUID_PK, nullable=False),
        sa.Column("requirement_type",
                  postgresql.ENUM("skill", "education", "certification", "experience",
                                  "language", "tool", "domain_knowledge", "other",
                                  name="requirement_type", create_type=False),
                  nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("normalized_text", sa.Text, nullable=True),
        sa.Column("is_mandatory", sa.Boolean,
                  server_default=sa.text("false"), nullable=False),
        sa.Column("weight", sa.Numeric(5, 2),
                  server_default=sa.text("1.00"), nullable=False),
        sa.Column("minimum_years", sa.Numeric(4, 1), nullable=True),
        sa.Column("sort_order", sa.Integer,
                  server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_job_requirements"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"],
                                ondelete="CASCADE", name="fk_job_req_job"),
        sa.CheckConstraint("weight >= 0", name="chk_job_req_weight_nonneg"),
        sa.CheckConstraint(
            "minimum_years IS NULL OR minimum_years >= 0",
            name="chk_job_req_min_years_nonneg"),
        sa.CheckConstraint(
            "LENGTH(TRIM(name)) > 0", name="chk_job_req_name_not_empty"),
        sa.CheckConstraint("sort_order >= 0", name="chk_job_req_sort_order"),
    )
    op.create_index("ix_job_req_job_sort", "job_requirements",
                    ["job_id", "sort_order", "created_at"])
    op.create_index("ix_job_req_type", "job_requirements",
                    ["job_id", "requirement_type"])
    op.execute("CREATE INDEX ix_job_req_mandatory ON job_requirements (job_id) "
               "WHERE is_mandatory = TRUE")
    op.execute("CREATE INDEX ix_job_req_min_years ON job_requirements (job_id) "
               "WHERE minimum_years IS NOT NULL")


def downgrade() -> None:
    op.drop_table("job_requirements")
    op.drop_table("jobs")
