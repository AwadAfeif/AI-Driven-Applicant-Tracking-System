# Backend — AI-Driven ATS

FastAPI + SQLAlchemy 2.0 (async) + Alembic + PostgreSQL 16 + pgvector.

---

## Requirements

- Docker + Docker Compose
- (or) Python 3.12+ with PostgreSQL 16 and pgvector locally

---

## Quick Start

From the repository root:

1. Copy environment template and edit:

    cp .env.example .env
    # set SECRET_KEY (>= 32 chars), POSTGRES_PASSWORD

2. Start services:

    # GitHub Codespaces
    docker compose -f docker-compose.codespaces.yml up -d

    # Local Linux
    docker compose up -d

3. Apply migrations:

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic upgrade head

4. Verify:

    curl -s http://localhost:8000/health
    # {"status":"ok","version":"0.1.0"}

Docs UI: http://localhost:8000/docs

---

## Project Layout

    backend/
    ├── alembic/                 Migration environment
    │   ├── versions/            9 migrations (0001 -> 0009)
    │   ├── env.py
    │   └── script.py.mako
    ├── alembic.ini
    ├── app/
    │   ├── api/                 HTTP routes (Phase 3+)
    │   ├── core/                Settings, security (Phase 3+)
    │   ├── db/                  Async engine + Base
    │   ├── models/              20 SQLAlchemy 2.0 models
    │   ├── schemas/             Pydantic schemas (Phase 3+)
    │   ├── services/            Business logic (Phase 3+)
    │   ├── repositories/        Data access (Phase 3+)
    │   ├── ai/                  AI pipelines (Phase 5+)
    │   └── main.py              FastAPI app
    ├── tests/                   pytest (Phase 3+)
    ├── Dockerfile
    └── requirements.txt

---

## Environment Variables

See .env.example at repository root.

Required:
- SECRET_KEY (>= 32 characters)
- POSTGRES_PASSWORD

---

## Database

Reference: docs/database/FINAL_SCHEMA_v1.0.md

20 project tables across 6 modules:

- M1 Identity & Tenant: users, refresh_tokens, companies, company_members, audit_logs
- M2 Jobs: jobs, job_requirements
- M3 Candidates: candidates, candidate_profiles, resumes, applications
- M4 Screening: screening_sessions, screening_questions, screening_answers, screening_evaluations
- M5 Subscriptions: subscriptions, ai_usage_logs
- M6 Scoring & Notifications: application_scores, notifications, notification_preferences

---

## Migrations

See docs/database/migration-guide.md.

---

## Development Notes

- All timestamps are server-generated (PostgreSQL NOW()).
- ENUMs are created via migration 0002 and reused with create_type=False in models.
- Two tables are append-only at the DB permission layer: audit_logs, ai_usage_logs.
- Composite foreign keys enforce tenant integrity at the DB level.
