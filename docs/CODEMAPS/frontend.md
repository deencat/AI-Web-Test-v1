# Frontend Codemap

**Last Updated:** 2026-07-03
**Entry Points:** `frontend/src/main.tsx`, `frontend/src/App.tsx`
**Stack:** React 19, Vite 7, TypeScript 5.9, Tailwind CSS 4, Vitest 4

## Architecture

```text
React + React Router (BrowserRouter)
  -> EphemeralCredentialProvider (runtime login creds for runs)
  -> ProtectedRoute (JWT in localStorage)
  -> Layout (Sidebar + pages)
  -> Service layer (frontend/src/services/*)
  -> Types (frontend/src/types/*)
  -> API base: VITE_API_BASE_URL (default http://127.0.0.1:8000/api/v1)
```

## Route Map

| Path | Page | Notes |
|---|---|---|
| `/login` | `LoginPage` | Public |
| `/dashboard` | `DashboardPage` | Agent workflow trigger + status |
| `/tests` | `GenerateTestsPage` | AI test generation |
| `/tests/saved` | `SavedTestsPage` | Saved tests + categories |
| `/tests/:testId` | `TestDetailPage` | Test editor and run |
| `/test-suites` | `TestSuitesPage` | Suite management |
| `/knowledge-base` | `KnowledgeBasePage` | KB documents |
| `/settings` | `SettingsPage` | Providers, execution, email creds |
| `/executions` | `ExecutionHistoryPage` | History + filters |
| `/executions/:executionId` | `ExecutionProgressPage` | Live progress + **Stop** button |
| `/debug/:executionId/:targetStep/:mode` | `DebugSessionPage` | Step debug |
| `/debug/:executionId/:targetStep/:endStep/:mode` | `DebugSessionPage` | Range debug |
| `/step-library` | `StepLibraryPage` | Reusable modules |
| `/crawl-and-save` | `CrawlAndSavePage` | Browser-use crawl workflow |
| `/feedback` | `FeedbackListPage` | Execution feedback |
| `/agent-workflow` | — | Redirects to `/dashboard` |

## Sidebar Navigation (`components/layout/Sidebar.tsx`)

Dashboard → Generate Tests → Saved Tests → Step Library → Crawl & Save → Test Suites → Executions → Knowledge Base → Settings

## Key Feature Modules

| Area | Components / Pages |
|---|---|
| Execution | `StopExecutionButton`, `RunTestButton`, `ReRunFromStepButton`, `RootCauseAnalysisPanel` |
| Agent workflow | `features/agent-workflow/*` — `AgentWorkflowTrigger`, `StopAgentButton`, SSE progress |
| Test editing | `TestStepEditor`, `InlineTitleEditor`, `InsertModulePicker` |
| Settings | `AgentModelConfig`, `ExecutionSettingsPanel`, `XPathCachePanel`, `EmailCredentialsSection` |
| Credentials | `CredentialPromptModal`, `EphemeralCredentialContext` |

## Service Layer

| Service | Backend area |
|---|---|
| `api.ts` | Shared axios client + auth headers |
| `authService.ts` | `/auth/*` |
| `testsService.ts` | `/tests/*` |
| `testCategoriesService.ts` | `/test-categories/*` |
| `executionService.ts` | `/executions/*` incl. `cancelExecution()` |
| `testSuitesService.ts` | `/suites/*` |
| `knowledgeBaseService.ts` | `/kb/*` |
| `settingsService.ts` | `/settings/*` |
| `schedulesService.ts` | `/schedules/*` |
| `stepLibraryService.ts` | `/step-library/*` |
| `requirementsService.ts` | `/requirements/*` (ReqIQ proxy) |
| `agentWorkflowService.ts` | `/api/v2/*` workflows |
| `sseService.ts` | SSE stream for workflow progress |
| `debugService.ts` | `/debug/*` |
| `feedbackService.ts` | `/feedback/*` |
| `browserProfileService.ts` | `/browser-profiles/*` |

## Testing

- Unit/component tests: Vitest + Testing Library (`frontend/src/**/__tests__/*`)
- E2E: root `@playwright/test` (`tests/e2e/*`)

## Related Areas

- [Backend](./backend.md)
- [Execution Engine](./execution-engine.md)
- [Integrations](./integrations.md)
