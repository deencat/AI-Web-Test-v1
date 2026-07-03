# Database Codemap

**Last Updated:** 2026-07-03
**Entry Points:** `backend/app/db/session.py`, `backend/app/models/*`, `backend/run_migrations.py`

## Architecture

```text
DATABASE_URL (PostgreSQL 15 in docker-compose; SQLite for local dev)
  -> SQLAlchemy 2.0 engine/session
  -> ORM models (app/models)
  -> CRUD modules (app/crud)
  -> Auto-migrations on startup (run_all_migrations_auto)
```

## Core Entities

| Model | Table | Purpose |
|---|---|---|
| `User` | `users` | Authentication and ownership root |
| `UserSession` | `user_sessions` | Active JWT sessions |
| `PasswordResetToken` | `password_reset_tokens` | Password reset flow |
| `TestCase` | `test_cases` | Generated/saved tests |
| `TestCategory` | `test_categories` | User-defined saved-test folders |
| `TestCaseVersion` | `test_versions` | Version history snapshots |
| `KBCategory` / `KBDocument` | `kb_categories`, `kb_documents` | Knowledge base |
| `TestExecution` / `TestExecutionStep` | `test_executions`, `test_execution_steps` | Runs and step traces |
| `TestSuite` / `TestSuiteItem` / `SuiteExecution` | `test_suites`, `test_suite_items`, `suite_executions` | Grouped runs |
| `TestTemplate` | `test_templates` | Reusable templates |
| `TestScenario` | `test_scenarios` | Faker-driven scenarios |
| `TestSchedule` | `test_schedules` | Cron/interval schedules |
| `UserSetting` | `user_settings` | Per-user provider preferences |
| `ExecutionSettings` | `execution_settings` | Tier strategy preferences |
| `XPathCache` / `TierExecutionLog` | `xpath_cache`, `tier_execution_logs` | Self-healing analytics |
| `ExecutionFeedback` | `execution_feedback` | Human corrections |
| `DebugSession` / `DebugStepExecution` | `debug_sessions`, `debug_step_executions` | Debug mode |
| `BrowserProfile` | `browser_profiles` | Persistent browser state |
| `EmailCredential` | `email_credentials` | IMAP OTP credentials |
| `StepLibraryModule` | `step_library_modules` | Reusable step modules |
| `ABTestResult` | `ab_test_results` | Prompt variant A/B tests |

## Key Relationships

- `test_cases.user_id` → `users.id`
- `test_cases.test_category_id` → `test_categories.id`
- `test_cases.category_id` → `kb_categories.id` (optional KB context)
- `test_executions.test_case_id` → `test_cases.id`
- `test_execution_steps.execution_id` → `test_executions.id`
- `test_versions.test_case_id` → `test_cases.id`
- `test_schedules.test_case_id` → `test_cases.id`
- `kb_documents.category_id` → `kb_categories.id`
- `suite_executions.suite_id` → `test_suites.id`

## Execution Status Values

`TestExecution.status`: `pending`, `running`, `passed`, `failed`, `cancelled`, `skipped`

Cancel finalization sets `cancelled` via `crud/test_execution.cancel_execution()` (ADR-009).

## Migration Notes

- `run_all_migrations_auto()` runs on every server start from `app/main.py`.
- Additional scripts under `backend/migrations/`.
- Alembic is listed in `requirements.txt`; runtime uses custom migration runner.

## Infrastructure (docker-compose.yml)

| Service | Image | Port |
|---|---|---|
| `db` | `postgres:15-alpine` | 5432 |
| `redis` | `redis:7-alpine` | 6379 |
| `backend` | `backend/Dockerfile` (Python 3.11) | 8000 |

## Related Areas

- [Backend](./backend.md)
- [Workers](./workers.md)
