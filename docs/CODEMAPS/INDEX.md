# Repository Codemaps

**Last Updated:** 2026-07-02
**Scope:** Top-level architecture maps for backend, frontend, data model, and integrations.

## Areas

- [Backend](./backend.md) - FastAPI services, API layers, and execution services.
- [Frontend](./frontend.md) - React routes, pages, and service layer.
- [Database](./database.md) - SQLAlchemy models and key relationships.
- [Integrations](./integrations.md) - External LLM, browser automation, and service integrations.
- [Workers](./workers.md) - Background processing and scheduler behavior.

## Repository Entry Points

- Backend API: `backend/app/main.py`
- Frontend app: `frontend/src/main.tsx` and `frontend/src/App.tsx`
- Backend APIs: `backend/app/api/v1/api.py`, `backend/app/api/v2/api.py`

## Notes

- These codemaps are generated from current repository structure and source modules.
- Update this set whenever routes, models, or core services change.
