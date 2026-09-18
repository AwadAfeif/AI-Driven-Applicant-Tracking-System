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
