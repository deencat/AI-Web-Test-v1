# Frontend Codemap

**Last Updated:** 2026-07-02
**Entry Points:** `frontend/src/main.tsx`, `frontend/src/App.tsx`

## Architecture

```text
React + React Router app
  -> Protected route wrapper (token in localStorage)
  -> Primary pages (dashboard, tests, executions, KB, settings)
  -> Service layer (frontend/src/services)
  -> API contracts (frontend/src/types/api.ts)
```

## Route Map

- `/login`
- `/dashboard`
- `/tests` -> `GenerateTestsPage`
- `/tests/saved` -> `SavedTestsPage`
- `/tests/:testId` -> `TestDetailPage`
- `/test-suites`
- `/knowledge-base`
- `/settings`
- `/executions`
- `/executions/:executionId`
- `/debug/:executionId/:targetStep/:mode`
- `/debug/:executionId/:targetStep/:endStep/:mode`
- `/step-library`
- `/crawl-and-save`
- `/feedback`

## Key Modules

| Module | Purpose | Dependencies |
|---|---|---|
| `src/App.tsx` | Route composition and auth gate | `react-router-dom`, page modules |
| `src/pages/*` | Feature pages and user workflows | components, services |
| `src/services/*` | Backend API calls | fetch/axios wrapper patterns |
| `src/types/api.ts` | API payload and response contracts | backend schemas |

## Related Areas

- [Backend](./backend.md)
- [Integrations](./integrations.md)
