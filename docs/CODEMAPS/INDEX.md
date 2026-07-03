# Repository Codemaps

**Last Updated:** 2026-07-03
**Scope:** Top-level architecture maps for backend, frontend, data model, workers, and integrations.

## Areas

- [Backend](./backend.md) — FastAPI v1/v2 routers, services, and execution pipeline.
- [Frontend](./frontend.md) — React routes, pages, components, and service layer.
- [Database](./database.md) — SQLAlchemy models and key relationships.
- [Integrations](./integrations.md) — LLM providers, browser automation, ReqIQ, Hermes.
- [Workers](./workers.md) — Queue manager, scheduler, cooperative cancel, workflow orchestration.

## Repository Entry Points

| Area | Path |
|------|------|
| Backend API | `backend/app/main.py` |
| API v1 router | `backend/app/api/v1/api.py` |
| API v2 router | `backend/app/api/v2/api.py` |
| Frontend app | `frontend/src/main.tsx`, `frontend/src/App.tsx` |
| Multi-agent code | `backend/agents/` |
| Infrastructure | `docker-compose.yml` (PostgreSQL 15, Redis 7) |

## Recent Changes (2026-07)

- **Execution cancel (ADR-009):** `DELETE /api/v1/executions/{id}/cancel` — cooperative stop for 3-tier runs; see [Workers](./workers.md).
- **GAN harness:** Stop Execution feature spec and eval report in `gan-harness/`.
- **Test categories (ADR-008):** User-defined saved-test organization via `/api/v1/test-categories`.

## Notes

- Codemaps are generated from current repository structure and source modules.
- Update this set when routes, models, or core services change.
- Version references align with `.cursorrules` and `package.json` / `requirements.txt` / `docker-compose.yml`.
