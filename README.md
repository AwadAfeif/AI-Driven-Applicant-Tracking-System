# AI-Driven Applicant Tracking System

Multi-Tenant ATS with Blind Recruitment, Semantic Matching, and AI Screening.

[![Phase](https://img.shields.io/badge/Phase-2%20Complete-brightgreen)]()
[![Database](https://img.shields.io/badge/Database-20%20tables-blue)]()
[![Migrations](https://img.shields.io/badge/Migrations-9%20reversible-blueviolet)]()

---

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 (async) + Alembic
- **Database:** PostgreSQL 16 + pgvector
- **Auth:** JWT (Access + Refresh Rotation) — Phase 3
- **AI:** Provider-agnostic — Phase 5

---

## Quick Start

    cp .env.example .env
    # edit .env: SECRET_KEY (>= 32 chars), POSTGRES_PASSWORD

    # GitHub Codespaces
    docker compose -f docker-compose.codespaces.yml up -d

    # Local Linux
    docker compose up -d

    # Apply migrations
    docker compose -f docker-compose.codespaces.yml exec -T backend alembic upgrade head

- Backend:   http://localhost:8000
- API docs:  http://localhost:8000/docs
- Health:    http://localhost:8000/health

---

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Requirements & Screen Analysis | ✅ Completed |
| 1 | Database Architecture (20 tables) | ✅ Frozen (v1.0-REV1) |
| 2 | Backend Foundation (FastAPI + Alembic) | ✅ Complete |
| 3 | Authentication & Multi-Tenancy | ⬜ Next |
| 4 | Recruitment Core (Jobs, Applications) | ⬜ |
| 5 | AI Engine (Parsing, Matching, Screening) | ⬜ |
| 6 | Frontend | ⬜ |
| 7 | Testing & Security | ⬜ |
| 8 | Docker / CI / Documentation | ⬜ |
| 9 | Final GitHub Release | ⬜ |

---

## Documentation

- **Database Schema:** docs/database/FINAL_SCHEMA_v1.0.md
- **Migration Guide:** docs/database/migration-guide.md
- **Architecture Rules:** docs/architecture/rules.md
- **Phase 2 Summary:** docs/architecture/phase-2-summary.md
- **Backend README:** backend/README.md

---

## Repository Layout

    .
    ├── backend/          FastAPI + SQLAlchemy + Alembic
    ├── frontend/         (Phase 6)
    ├── docs/             Architecture & database documentation
    ├── docker-compose.yml
    ├── docker-compose.codespaces.yml
    ├── .env.example
    ├── CONTRIBUTING.md
    └── README.md

---

## License

MIT (or per your institution's policy).
