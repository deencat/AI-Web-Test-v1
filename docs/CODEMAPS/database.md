# Database Codemap

**Last Updated:** 2026-07-02
**Entry Points:** `backend/app/db/session.py`, `backend/app/models/*`

## Architecture

```text
DATABASE_URL -> SQLAlchemy engine/session
  -> ORM models in app/models
  -> CRUD modules in app/crud
  -> FastAPI endpoints via dependency-injected DB session
```

## Core Entities

| Model | Table | Purpose |
|---|---|---|
| `User` | `users` | Authentication and ownership root |
| `TestCase` | `test_cases` | Generated/saved tests and metadata |
| `TestCategory` | `test_categories` | User-defined saved test organization |
| `KBCategory` / `KBDocument` | `kb_categories`, `kb_documents` | Knowledge base taxonomy and documents |
| `TestExecution` / `TestExecutionStep` | `test_executions`, `test_execution_steps` | Execution records and step-level traces |
| `TestSuite` / `TestSuiteItem` | `test_suites`, `test_suite_items` | Grouped execution collections |

## Key Relationships

- `test_cases.user_id` -> `users.id`
- `test_cases.test_category_id` -> `test_categories.id`
- `test_cases.category_id` -> `kb_categories.id` (KB context linkage)
- `test_executions.test_case_id` -> `test_cases.id`
- `kb_documents.category_id` -> `kb_categories.id`
- `kb_documents.user_id` -> `users.id`

## Migration Notes

- Runtime migration helper is triggered from `backend/app/main.py` via `run_all_migrations_auto()`.
- Additional migration scripts are stored under `backend/migrations`.

## Related Areas

- [Backend](./backend.md)
