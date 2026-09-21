# Alembic Migration Guide

**Last updated:** 2026-09-21

---

## Environment Note

In GitHub Codespaces, use the override file:

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic <command>

On a local Linux machine with working bridge networking:

    docker compose exec backend alembic <command>

---

## Common Commands

Check current revision:

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic current

Show migration history (full chain):

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic history

Show heads (must be a single line):

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic heads

Apply all pending migrations:

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic upgrade head

Apply one step:

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic upgrade +1

Rollback one step:

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic downgrade -1

Rollback everything:

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic downgrade base

---

## Creating a New Migration

Manual migration (recommended for this project — explicit and predictable):

1. Create a new file in backend/alembic/versions/
2. Use a sequential revision id (e.g., 0010_<short_name>)
3. Set down_revision to the current head
4. Write upgrade() and downgrade() as mirror operations
5. Run py_compile:

    python3 -m py_compile backend/alembic/versions/0010_<name>.py && echo "OK"

6. Apply and verify:

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic upgrade head
    docker compose -f docker-compose.codespaces.yml exec -T backend alembic current

7. Test round-trip (mandatory before commit):

    docker compose -f docker-compose.codespaces.yml exec -T backend alembic downgrade -1
    docker compose -f docker-compose.codespaces.yml exec -T backend alembic upgrade head

---

## Rules

1. Every migration must have a working downgrade().
2. Never edit an applied migration. Create a new one.
3. Never use autogenerate for ENUMs — pgvector and composite FKs are not
   detected reliably. Write the migration explicitly.
4. Test round-trip before committing.
5. One concern per migration.

---

## Migration Naming Convention

    0001_extensions
    0002_enums
    0003_m1_identity
    0004_m2_jobs
    0005_m3_candidates
    0006_m4_screening
    0007_m5_subscriptions
    0008_m6_scoring_notifications
    0009_permissions
    00NN_<short_snake_case_description>

- Sequence prefix: 4 digits
- Module reference (if applicable): m1_, m2_, ...
- Short description: what the migration does
- Single-line revision id string matching the filename (without .py)
