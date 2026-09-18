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
