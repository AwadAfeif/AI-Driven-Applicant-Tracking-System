"""Create 24 PostgreSQL ENUM types.

Revision ID: 0002_enums
Revises: 0001_extensions
Create Date: 2026-09-20

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_enums"
down_revision: Union[str, None] = "0001_extensions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ENUMS: dict[str, list[str]] = {
    "user_platform_role":       ["user", "super_admin"],
    "company_status":           ["active", "suspended", "archived"],
    "company_member_role":      ["owner", "admin", "recruiter", "viewer"],
    "company_member_status":    ["invited", "active", "suspended"],
    "employment_type":          ["full_time", "part_time", "contract",
                                 "internship", "temporary", "freelance"],
    "work_mode":                ["onsite", "hybrid", "remote"],
    "seniority_level":          ["intern", "junior", "mid", "senior",
                                 "lead", "principal", "director"],
    "salary_period":            ["hourly", "monthly", "yearly"],
    "job_status":               ["draft", "published", "paused",
                                 "closed", "archived"],
    "requirement_type":         ["skill", "education", "certification",
                                 "experience", "language", "tool",
                                 "domain_knowledge", "other"],
    "resume_status":            ["uploaded", "processing", "processed",
                                 "failed", "archived"],
    "application_status":       ["submitted", "under_review", "screening",
                                 "shortlisted", "interview", "offer",
                                 "rejected", "withdrawn", "hired"],
    "screening_session_status": ["pending", "active", "submitted",
                                 "evaluated", "expired", "terminated"],
    "question_type":            ["text", "scenario",
                                 "single_choice", "multi_choice"],
    "evaluation_mode":          ["ai", "deterministic"],
    "answer_status":            ["draft", "submitted", "late", "invalidated"],
    "evaluator_type":           ["ai", "human", "hybrid"],
    "subscription_status":      ["trialing", "active", "past_due",
                                 "canceled", "expired"],
    "billing_cycle":            ["monthly", "yearly"],
    "ai_operation_type":        ["resume_parsing", "resume_embedding",
                                 "semantic_matching", "screening_generation",
                                 "screening_evaluation", "other"],
    "ai_usage_status":          ["success", "failed", "rate_limited",
                                 "timeout", "rejected"],
    "scoring_trigger":          ["initial", "resume_updated",
                                 "screening_completed", "manual_recalculation",
                                 "algorithm_recalculation"],
    "notification_type":        ["application_update", "screening_invitation",
                                 "screening_reminder", "ai_processing",
                                 "subscription", "system", "marketing"],
    "recipient_kind":           ["company_member", "candidate", "system"],
}


def upgrade() -> None:
    for name, values in ENUMS.items():
        values_sql = ", ".join(f"'{v}'" for v in values)
        op.execute(f"CREATE TYPE {name} AS ENUM ({values_sql})")


def downgrade() -> None:
    for name in reversed(list(ENUMS.keys())):
        op.execute(f"DROP TYPE IF EXISTS {name}")
