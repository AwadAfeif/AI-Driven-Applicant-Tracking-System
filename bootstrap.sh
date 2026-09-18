#!/usr/bin/env bash
# ═════════════════════════════════════════════════════════════════
#  AI-Driven ATS — Commit #1 Final Bootstrap (Termux-friendly)
#  Idempotent. Usage: bash bootstrap.sh
# ═════════════════════════════════════════════════════════════════
set -euo pipefail

REPO_URL="https://github.com/AwadAfeif/AI-Driven-Applicant-Tracking-System.git"

echo "▸ Working in: $PWD"

# ─── 1. Directories ─────────────────────────────────────────────
mkdir -p backend/app/{api,core,db,models,schemas,services,repositories,ai}
mkdir -p backend/tests backend/alembic/versions
mkdir -p frontend docs/architecture docs/database

# ─── 2. Empty package markers ───────────────────────────────────
for f in \
  backend/app/__init__.py \
  backend/app/api/__init__.py \
  backend/app/core/__init__.py \
  backend/app/db/__init__.py \
  backend/app/models/__init__.py \
  backend/app/schemas/__init__.py \
  backend/app/services/__init__.py \
  backend/app/repositories/__init__.py \
  backend/app/ai/__init__.py \
  backend/tests/__init__.py \
  backend/alembic/versions/.gitkeep
do : > "$f"; done

# ─── 3. .gitignore ──────────────────────────────────────────────
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
env/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.env
.env.local
.env.*.local
.vscode/
.idea/
*.swp
.DS_Store
Thumbs.db
*.log
postgres_data/
node_modules/
dist/
build/
EOF

# ─── 4. .env.example ────────────────────────────────────────────
cat > .env.example << 'EOF'
APP_NAME=AI-Driven ATS
APP_ENV=development
APP_DEBUG=true
APP_VERSION=0.1.0
API_V1_PREFIX=/api/v1

SECRET_KEY=change-me-to-a-random-32-byte-secret-key-please
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_ALGORITHM=HS256

POSTGRES_USER=ats
POSTGRES_PASSWORD=ats_password
POSTGRES_DB=ats_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DB_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
EOF

# ─── 5. docker-compose.yml ──────────────────────────────────────
cat > docker-compose.yml << 'EOF'
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: ats_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-ats}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-ats_password}
      POSTGRES_DB: ${POSTGRES_DB:-ats_db}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-ats} -d ${POSTGRES_DB:-ats_db}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ats_backend
    restart: unless-stopped
    env_file:
      - .env
    environment:
      POSTGRES_HOST: postgres
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
EOF

# ─── 6. backend/Dockerfile ──────────────────────────────────────
cat > backend/Dockerfile << 'EOF'
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# ─── 7. backend/requirements.txt ────────────────────────────────
cat > backend/requirements.txt << 'EOF'
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.13.3
psycopg2-binary==2.9.10
pydantic==2.9.2
pydantic-settings==2.5.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
python-dotenv==1.0.1
EOF

# ─── 8. backend/app/core/config.py ──────────────────────────────
cat > backend/app/core/config.py << 'EOF'
from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        case_sensitive=False, extra="ignore",
    )
    APP_NAME: str = "AI-Driven ATS"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "HS256"

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "ats"
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = "ats_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
EOF

# ─── 9. backend/app/db/base.py ──────────────────────────────────
cat > backend/app/db/base.py << 'EOF'
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base for all ORM models."""
    pass
EOF

# ─── 10. backend/app/db/session.py ──────────────────────────────
cat > backend/app/db/session.py << 'EOF'
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine,
)
from app.core.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession,
    expire_on_commit=False, autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
EOF

# ─── 11. backend/app/main.py ────────────────────────────────────
cat > backend/app/main.py << 'EOF'
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.db.session import engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.APP_VERSION}
EOF

# ─── 12. backend/alembic.ini ────────────────────────────────────
cat > backend/alembic.ini << 'EOF'
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url =

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

# ─── 13. backend/alembic/env.py ─────────────────────────────────
cat > backend/alembic/env.py << 'EOF'
import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from app.core.config import get_settings
from app.db.base import Base

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.", poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

# ─── 14. backend/alembic/script.py.mako ─────────────────────────
cat > backend/alembic/script.py.mako << 'EOF'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
EOF

# ─── 15. README.md ──────────────────────────────────────────────
cat > README.md << 'EOF'
# AI-Driven Applicant Tracking System

Multi-Tenant ATS with Blind Recruitment, Semantic Matching, and AI Screening.

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 (async) + Alembic
- **Database:** PostgreSQL 16 + pgvector
- **Auth:** JWT (Access + Refresh Rotation)
- **AI:** Provider-agnostic (Phase 5)

## Quick Start

    cp .env.example .env
    # edit .env: SECRET_KEY (>= 32 chars), POSTGRES_PASSWORD
    docker compose up --build

- Backend: http://localhost:8000
- Docs:    http://localhost:8000/docs
- Health:  http://localhost:8000/health

## Documentation

- Database Schema: `docs/database/FINAL_SCHEMA_v1.0.md`
- Architecture:    `docs/architecture/`

## Project Status

- Phase 1 — Database Architecture: FROZEN (v1.0-REV1)
- Phase 2 — Backend Foundation: IN PROGRESS
EOF

# ─── 16. CONTRIBUTING.md ────────────────────────────────────────
cat > CONTRIBUTING.md << 'EOF'
# Contributing

## Development Workflow

1. Create a feature branch from `develop`.
2. Make focused commits with clear messages.
3. Run tests locally before pushing.
4. Open a pull request against `develop`.

## Commit Convention

Use Conventional Commits:

| Prefix | Purpose |
|---------|---------|
| `feat:` | new functionality |
| `fix:` | bug fix |
| `chore:` | maintenance |
| `docs:` | documentation |
| `refactor:` | restructuring |
| `test:` | tests |

## Branch Strategy

- `main` — production-ready only
- `develop` — integration branch
- `feature/*` — short-lived feature branches
EOF

echo "▸ Base files created. Now writing docs..."

# ─── 17. docs/architecture/rules.md ─────────────────────────────
cat > docs/architecture/rules.md << 'EOF'
# Architecture Rules

## Rule 1 — Tenant Isolation
Every tenant-scoped table must be isolatable either directly (via `company_id`)
or through a trusted parent relationship. Direct `company_id` is preferred for
high-sensitivity tables and frequently-queried tables.

## Rule 2 — PII Isolation via API Projection
Candidate PII (`first_name`, `last_name`, `phone`) lives in `candidate_profiles`.
It is protected by FastAPI Schemas, not by a separate table in v1.
`SELECT *` on `candidate_profiles` must always be reviewed.

## Rule 3 — Server-Side Timestamps
Every `*_at` column is filled by the server. Any timestamp received from a client
is discarded and logged in `audit_logs` as `SECURITY_VIOLATION_CLIENT_TIMESTAMP`.

## Rule 4 — Rubric-Only Scoring
Every evaluation (AI or deterministic) is read from `evaluation_rubric`.
No hard-coded scoring in Service Layer.

## Rule 5 — Metered Multi-Tenancy
Every measurable AI operation is logged in `ai_usage_logs` with `company_id`
and `estimated_cost`. No exceptions.

## Rule 6 — Anti-Cheat Principle
Decisions affecting candidates are never based on Frontend signals.
Only Server-Side Timestamps + actual submitted answers.

## Rule 7 — Application Immutability
After the first `ai_usage_logs` or `application_scores` row is linked to an
application, physical deletion is blocked at the DB level (`ON DELETE RESTRICT`).
The normal path is `deleted_at = NOW()` (soft delete).

---

## Known Limitations (v1.0)

| # | Item | Impact | Priority |
|---|------|--------|----------|
| 1 | PII in `candidate_profiles` (no separate PII table) | Protected only via API | Medium |
| 2 | `users` has no `deleted_at` | Soft delete via `is_active` only | Low |
| 3 | No `pgvector` column in v1 | Deferred to Phase 5 | Planned |
| 4 | No `attempt_number` (no re-attempts) | Reapplication not supported | Medium |
| 5 | RLS not enabled yet | Planned for Phase 3 | Planned |
| 6 | `application_deadline` sweep needs background job | Operational gap | Low |
| 7 | No `plan_limits` lookup table | Inline limits on `subscriptions` | Low |
EOF

# ─── 18. docs/database/FINAL_SCHEMA_v1.0.md ─────────────────────
cat > docs/database/FINAL_SCHEMA_v1.0.md << 'SCHEMA_EOF'
# FINAL SCHEMA — v1.0-REV1

**Status:** 🔒 FROZEN
**Total Tables:** 20
**Total Enums:** 24

> Reference for Alembic Migrations (Phase 2). No changes without explicit revision.

---

## Module Map

| Module | Tables |
|--------|--------|
| M1 — Identity & Tenant | `users`, `refresh_tokens`, `companies`, `company_members`, `audit_logs` |
| M2 — Jobs | `jobs`, `job_requirements` |
| M3 — Candidates | `candidates`, `candidate_profiles`, `resumes`, `applications` |
| M4 — Screening & AI | `screening_sessions`, `screening_questions`, `screening_answers`, `screening_evaluations` |
| M5 — Subscriptions & AI Usage | `subscriptions`, `ai_usage_logs` |
| M6 — Scoring & Notifications | `application_scores`, `notifications`, `notification_preferences` |

---

## ENUMs (24)

    user_platform_role       : user | super_admin
    company_status           : active | suspended | archived
    company_member_role      : owner | admin | recruiter | viewer
    company_member_status    : invited | active | suspended
    employment_type          : full_time | part_time | contract | internship | temporary | freelance
    work_mode                : onsite | hybrid | remote
    seniority_level          : intern | junior | mid | senior | lead | principal | director
    salary_period            : hourly | monthly | yearly
    job_status               : draft | published | paused | closed | archived
    requirement_type         : skill | education | certification | experience | language | tool | domain_knowledge | other
    resume_status            : uploaded | processing | processed | failed | archived
    application_status       : submitted | under_review | screening | shortlisted | interview | offer | rejected | withdrawn | hired
    screening_session_status : pending | active | submitted | evaluated | expired | terminated
    question_type            : text | scenario | single_choice | multi_choice
    evaluation_mode          : ai | deterministic
    answer_status            : draft | submitted | late | invalidated
    evaluator_type           : ai | human | hybrid
    subscription_status      : trialing | active | past_due | canceled | expired
    billing_cycle            : monthly | yearly
    ai_operation_type        : resume_parsing | resume_embedding | semantic_matching | screening_generation | screening_evaluation | other
    ai_usage_status          : success | failed | rate_limited | timeout | rejected
    scoring_trigger          : initial | resume_updated | screening_completed | manual_recalculation | algorithm_recalculation
    notification_type        : application_update | screening_invitation | screening_reminder | ai_processing | subscription | system | marketing
    recipient_kind           : company_member | candidate | system

---

## Tables (20)

> Full DDL is defined incrementally in Alembic migrations (see `backend/alembic/versions/`).
> Each migration is named after its module (0003_identity_tenant, etc.).

### M1 — Identity & Tenant

#### users
- `id` UUID PK
- `email` VARCHAR(255) NOT NULL — unique via `LOWER(email)` index
- `password_hash` VARCHAR(255) NOT NULL
- `platform_role` user_platform_role NOT NULL DEFAULT 'user'
- `is_active` BOOLEAN NOT NULL DEFAULT TRUE
- `email_verified_at`, `last_login_at` TIMESTAMPTZ NULL
- `created_at`, `updated_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

#### refresh_tokens
- `id` UUID PK
- `user_id` UUID NOT NULL FK → users(id) ON DELETE CASCADE
- `token_hash` VARCHAR(255) NOT NULL UNIQUE
- `family_id` UUID NOT NULL
- `expires_at`, `revoked_at`, `replaced_by_id`, `last_used_at`, `ip_address` INET, `user_agent` TEXT
- `created_at`

#### companies
- `id` UUID PK
- `name` VARCHAR(150) NOT NULL
- `slug` VARCHAR(150) NOT NULL UNIQUE
- `industry`, `website` NULL
- `status` company_status NOT NULL DEFAULT 'active'
- `created_at`, `updated_at`

#### company_members
- PK composite: `(company_id, user_id)`
- `role` company_member_role NOT NULL
- `status` company_member_status NOT NULL DEFAULT 'active'
- `invited_by` NULL
- `joined_at`, `created_at`

#### audit_logs  (Append-Only)
- `id` BIGSERIAL PK
- `actor_user_id`, `company_id` (both nullable FK)
- `action` VARCHAR(100) NOT NULL
- `target_type`, `target_id`, `ip_address` INET, `user_agent`, `request_id`, `context_details` JSONB
- `created_at`

---

### M2 — Jobs & Requirements

#### jobs
- `id` UUID PK, `company_id` NOT NULL, `created_by` NULL, `created_by_snapshot` JSONB
- `title`, `slug` (unique per company), `description`, `department`
- `employment_type`, `work_mode`, `seniority`
- `location_country`, `location_city`
- `salary_min`, `salary_max`, `currency`, `salary_period`
- `experience_min`, `experience_max`
- `openings_count` INT NOT NULL DEFAULT 1
- `blind_screening` BOOLEAN NOT NULL DEFAULT TRUE
- `status`, `published_at`, `application_deadline`, `closed_at`
- `created_at`, `updated_at`, `deleted_at`
- **UNIQUE (company_id, id)** → for composite FK targets

#### job_requirements
- `id` UUID PK, `job_id` FK → jobs(id) ON DELETE CASCADE
- `requirement_type`, `name`, `description`, `normalized_text`
- `is_mandatory`, `weight` NUMERIC(5,2), `minimum_years`, `sort_order`
- `created_at`, `updated_at`
- (embedding column deferred to Phase 5)

---

### M3 — Candidates & Applications

#### candidates
- `id` UUID PK, `user_id` UUID NOT NULL UNIQUE → users(id)
- `candidate_code` VARCHAR(50) NOT NULL (format: `^CND-[A-Z0-9]+$`)
- `is_active`, `created_at`, `updated_at`

#### candidate_profiles
- `id` UUID PK, `candidate_id` UUID NOT NULL UNIQUE → candidates(id)
- `first_name`, `last_name`, `headline`, `summary`, `phone`, `location`
- `linkedin_url`, `github_url`, `portfolio_url`
- `years_experience` NUMERIC(4,1)
- `created_at`, `updated_at`

#### resumes
- `id` UUID PK, `candidate_id` FK → candidates(id)
- `version` INT, `is_primary` BOOLEAN
- `file_name`, `storage_key`, `mime_type`, `file_size_bytes`, `content_hash`
- `status` resume_status
- `raw_text`, `normalized_text`, `anonymized_text`, `anonymization_meta` JSONB, `parsed_json` JSONB, `parse_error`
- `created_at`, `updated_at`, `deleted_at`
- **UNIQUE (candidate_id, id)** → for composite FK targets
- Partial unique: `(candidate_id)` where `is_primary=TRUE` and `deleted_at IS NULL`

#### applications
- `id` UUID PK
- `company_id` UUID NOT NULL, `job_id` UUID NOT NULL, `candidate_id` UUID NOT NULL, `resume_id` UUID NOT NULL
- `cover_letter`, `source`
- `status` application_status
- `status_updated_at`
- `identity_revealed_at`, `identity_revealed_by`
- `matching_score`, `screening_score`, `final_score`, `ranking_version`, `explanation_version`, `score_breakdown` JSONB
- `decision_reason`, `withdrawn_at`, `rejected_at`
- `applied_at`, `updated_at`, `deleted_at`
- **UNIQUE (company_id, id)** for composite FK targets
- **UNIQUE (job_id, candidate_id)** — one application per job
- Composite FK: `(company_id, job_id)` → jobs(company_id, id)
- Composite FK: `(candidate_id, resume_id)` → resumes(candidate_id, id) ON DELETE RESTRICT

---

### M4 — Screening & AI Evaluation

#### screening_sessions
- `id` UUID PK, `application_id` UUID NOT NULL UNIQUE
- `company_id`, `job_id`, `candidate_id` (denormalized for RLS/analytics)
- `duration_seconds`, `question_count`
- `status` screening_session_status
- Server timestamps: `started_at`, `expires_at`, `submitted_at`, `evaluated_at`, `expired_at`, `terminated_at`, `last_activity_at`
- `total_score`, `max_possible_score`
- `created_at`, `updated_at`
- **UNIQUE (company_id, id)** for composite FK targets
- Composite FK: `(company_id, application_id)` → applications(company_id, id)
- Trigger: `sync_session_from_application()` → fills `job_id`, `candidate_id`

#### screening_questions
- `id` UUID PK, `session_id` FK → screening_sessions(id)
- `question_order` INT, `question_type`, `evaluation_mode`
- `question_text`, `options` JSONB, `evaluation_rubric` JSONB (server-only)
- `max_score` NUMERIC(6,2)
- `generation_model`, `generation_version`, `prompt_hash`
- `created_at`
- **UNIQUE (session_id, question_order)**
- **UNIQUE (session_id, id)** for composite FK targets

#### screening_answers
- `id` UUID PK, `session_id` UUID NOT NULL, `question_id` UUID NOT NULL UNIQUE
- `answer_text` TEXT, `answer_payload` JSONB
- `served_at`, `submitted_at`, `time_spent_seconds`
- `answer_status`
- `created_at`, `updated_at`
- Composite FK: `(session_id, question_id)` → screening_questions(session_id, id)
- Trigger: `prevent_answer_mutation()` — no changes after submission

#### screening_evaluations
- `id` UUID PK, `answer_id` FK → screening_answers(id)
- `evaluator_type` evaluator_type NOT NULL DEFAULT 'ai'
- `score`, `max_score`, `feedback`, `justification`, `matched_concepts`, `missed_concepts`
- `evaluation_model`, `evaluation_version`, `prompt_hash`, `raw_response` JSONB
- `request_id` UUID UNIQUE
- `evaluated_by`, `override_reason`
- `evaluated_at`, `created_at`

---

### M5 — Subscriptions & AI Usage

#### subscriptions
- `id` UUID PK, `company_id` FK → companies(id)
- `plan_code`, `status`, `billing_cycle`
- `current_period_start`, `current_period_end`
- `ai_tokens_limit`, `ai_tokens_used`, `ai_tokens_reserved` BIGINT
- `max_users`, `max_active_jobs`
- `started_at`, `canceled_at`, `created_at`, `updated_at`
- Partial unique: `(company_id)` where `status IN ('trialing','active','past_due')`
- CHECK: `ai_tokens_used + ai_tokens_reserved <= ai_tokens_limit`

#### ai_usage_logs  (Append-Only)
- `id` BIGSERIAL PK
- `company_id` FK, `user_id` NULL, `application_id` NULL
- `operation_type`, `provider`, `model`
- `request_id` UUID NOT NULL UNIQUE
- `prompt_hash`, `response_hash`
- `input_tokens`, `output_tokens`, `total_tokens` BIGINT
- `estimated_cost` NUMERIC(12,6)
- `status`, `error_code`, `latency_ms`
- `created_at`, `completed_at`
- Composite FK: `(company_id, application_id)` → applications(company_id, id) ON DELETE RESTRICT
- Note: no `screening_answer_id`; link via `request_id` to `screening_evaluations`

---

### M6 — Scoring & Notifications

#### application_scores
- `id` UUID PK, `company_id` UUID NOT NULL, `application_id` UUID NOT NULL
- `matching_score`, `screening_score`, `final_score` NUMERIC(6,2)
- `ranking_version` VARCHAR(50), `score_breakdown` JSONB, `trigger_type` scoring_trigger
- `created_at`
- Composite FK: `(company_id, application_id)` → applications(company_id, id) ON DELETE RESTRICT
- CHECK: at least one score NOT NULL

#### notifications
- `id` UUID PK
- `user_id` UUID NOT NULL FK → users(id)
- `company_id` UUID NULL FK → companies(id)
- `recipient_kind` recipient_kind NOT NULL
- `notification_type` notification_type NOT NULL
- `title`, `message`, `data` JSONB
- `read_at`, `expires_at`, `created_at`
- CHECK: `recipient_kind <> 'company_member' OR company_id IS NOT NULL`

#### notification_preferences
- PK composite: `(user_id, notification_type)`
- `enabled` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at`, `updated_at`
- CHECK: `notification_type <> 'system' OR enabled = TRUE`

---

## Composite Foreign Keys — Master List

| From | Columns | References | ON DELETE |
|------|---------|-----------|-----------|
| `applications` | `(company_id, job_id)` | `jobs(company_id, id)` | CASCADE |
| `applications` | `(candidate_id, resume_id)` | `resumes(candidate_id, id)` | RESTRICT |
| `screening_sessions` | `(company_id, application_id)` | `applications(company_id, id)` | CASCADE |
| `screening_answers` | `(session_id, question_id)` | `screening_questions(session_id, id)` | CASCADE |
| `ai_usage_logs` | `(company_id, application_id)` | `applications(company_id, id)` | RESTRICT |
| `application_scores` | `(company_id, application_id)` | `applications(company_id, id)` | RESTRICT |

---

## Required UNIQUE Constraints (Composite FK targets)

- `jobs(company_id, id)`
- `resumes(candidate_id, id)`
- `applications(company_id, id)`
- `screening_questions(session_id, id)`

---

## Alembic Migration Order

    0001  Extensions (pgcrypto, vector)
    0002  24 ENUMs
    0003  M1 — users, refresh_tokens, companies, company_members, audit_logs
    0004  M2 — jobs, job_requirements
    0005  M3 — candidates, candidate_profiles, resumes, applications
    0006  M4 — screening_sessions, screening_questions, screening_answers, screening_evaluations
    0007  M5 — subscriptions, ai_usage_logs
    0008  M6 — application_scores, notifications, notification_preferences
    0009  Triggers (session sync, answer immutability)
    0010  Permissions (REVOKE UPDATE/DELETE on append-only tables)
    0011  Additional partial indexes

---

## Rules

See `docs/architecture/rules.md` (Rules 1–7 + Known Limitations).
SCHEMA_EOF

# ─── 19. .env ───────────────────────────────────────────────────
if [ ! -f .env ]; then
    cp .env.example .env
    echo "▸ .env created. ⚠️  Edit SECRET_KEY (>= 32 chars)."
fi

# ─── 20. Git ────────────────────────────────────────────────────
echo "▸ Initializing Git..."
if [ ! -d .git ]; then
    git init
    git branch -M main
fi

if ! git remote | grep -q '^origin$'; then
    git remote add origin "$REPO_URL"
fi

echo ""
echo "════════════════════════════════════════════════"
echo "✅ Bootstrap complete."
echo "════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Edit .env — set SECRET_KEY and POSTGRES_PASSWORD"
echo "  2. find . -type f -not -path './.git/*' | sort   # verify"
echo "  3. git add . && git status"
echo "  4. git commit -m 'chore(repo): bootstrap monorepo structure'"
echo "  5. git push -u origin main"
