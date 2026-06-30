# Database Codemap

**Last Updated:** 2026-06-30  
**Entry Points:** `backend/app/db/session.py`, `backend/app/models/__init__.py`

## Architecture

```
SQLAlchemy 2.x
    ├── engine (DATABASE_URL from config)
    ├── SessionLocal (request-scoped via deps.get_db)
    ├── Base.metadata.create_all (startup in main.py)
    └── run_migrations.py (incremental column/table changes)
```

**Default dev:** SQLite (`sqlite:///./aiwebtest.db`)  
**Production:** PostgreSQL (`postgresql://...` in `.env`) — see `backend/env.example`

## Entity Relationship (Simplified)

```
User ──┬── TestCase ──┬── TestExecution ── TestExecutionStep
       │              ├── TestVersion
       │              └── (steps JSON)
       ├── ExecutionSettings ── XPathCache
       │                    └── TierExecutionLog
       ├── BrowserProfile
       ├── EmailCredential
       ├── UserSetting
       ├── KBDocument ── KBCategory
       ├── TestSuite ── TestSuiteItem
       ├── DebugSession ── DebugStepExecution
       ├── ExecutionFeedback
       └── StepLibraryModule
```

## Models — `backend/app/models/`

| Model | File | Purpose |
| --- | --- | --- |
| `User` | `user.py` | Accounts, roles |
| `UserSession` | `user_session.py` | Active sessions |
| `PasswordResetToken` | `password_reset.py` | Password reset flow |
| `TestCase` | `test_case.py` | Test definitions, steps JSON |
| `TestVersion` | `test_version.py` | Version history |
| `TestExecution` | `test_execution.py` | Run records |
| `TestExecutionStep` | `test_execution.py` | Per-step results |
| `StepSessionSnapshot` | `test_execution.py` | Resume-from-step browser state (ADR-002-44) |
| `ExecutionSettings` | `execution_settings.py` | Tier strategy, timeouts |
| `XPathCache` | `execution_settings.py` | Cached selectors (ADR-002-3) |
| `TierExecutionLog` | `execution_settings.py` | Per-tier attempt logs |
| `ExecutionFeedback` | `execution_feedback.py` | Human corrections + RCA |
| `KBDocument` | `kb_document.py` | Knowledge base files |
| `KBCategory` | `kb_document.py` | KB categories |
| `TestTemplate` | `test_template.py` | System/user templates |
| `TestScenario` | `test_scenario.py` | Scenario metadata |
| `TestSuite` | `test_suite.py` | Suite grouping |
| `TestSuiteItem` | `test_suite.py` | Suite membership |
| `SuiteExecution` | `test_suite.py` | Suite run records |
| `TestSchedule` | `test_schedule.py` | Cron schedules |
| `BrowserProfile` | `browser_profile.py` | Browser storage state |
| `EmailCredential` | `email_credential.py` | Encrypted IMAP creds (ADR-002-38) |
| `StepLibraryModule` | `step_library_module.py` | Reusable step modules |
| `DebugSession` | `debug_session.py` | Debug mode sessions |
| `DebugStepExecution` | `debug_session.py` | Debug step runs |
| `UserSetting` | `user_settings.py` | Key-value user prefs |
| `ABTestResult` | `ab_test_result.py` | Prompt variant A/B tests |

## CRUD Layer — `backend/app/crud/`

| Module | Models |
| --- | --- |
| `test_case.py` | TestCase |
| `test_execution.py` | TestExecution, steps |
| `execution_settings.py` | ExecutionSettings, XPathCache |
| `execution_feedback.py` | ExecutionFeedback |
| `kb_document.py` | KBDocument |
| `user.py` | User |
| `browser_profile.py` | BrowserProfile |
| `step_library.py` | StepLibraryModule |
| `test_schedule.py` | TestSchedule |
| `crud_test_suite.py` | TestSuite |
| `step_session_snapshot.py` | Resume snapshots (ADR-002-44) |

## Migrations — `backend/migrations/`

Auto-applied on server start via `run_all_migrations_auto()`. Examples:

- `add_root_cause_analysis_column.py`
- `add_step_library_modules_table.py`
- `add_requires_runtime_credentials.py`
- `add_custom_models_registry.py`
- `add_browser_profile_session_storage.py`

## Execution-Related Tables (ADR-002)

| Table / model | ADR | Notes |
| --- | --- | --- |
| `execution_settings` | 002-1 | `fallback_strategy` enum (A/B/C) |
| `xpath_cache` | 002-3, 002-45 | Instruction → selector, TTL, invalidation |
| `tier_execution_log` | 002-26 | Per-tier attempt audit trail |
| `execution_feedback` | 002-43 | RCA text, user corrections |
| `email_credentials` | 002-38 | Fernet-encrypted IMAP |
| `step_session_snapshots` | 002-44 | Resume-from-step state |

## Initialization

| Script | Purpose |
| --- | --- |
| `app/db/init_db.py` | Default admin user, sample data |
| `app/db/init_templates.py` | System test templates |
| `app/db/init_kb_categories.py` | Default KB categories |
| `create_test_user.py` | Dev user helper (repo root script) |

## Related Codemaps

- [backend.md](./backend.md) — services using these models
- [execution-engine.md](./execution-engine.md) — execution persistence flow
