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
