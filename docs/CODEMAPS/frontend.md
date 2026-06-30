# Frontend Codemap

**Last Updated:** 2026-06-30  
**Entry Points:** `frontend/src/main.tsx`, `frontend/src/App.tsx`

## Architecture

```
main.tsx
    └── App.tsx (React Router)
            ├── EphemeralCredentialContext (runtime creds for UAT)
            ├── pages/* (route targets)
            ├── components/* (shared UI)
            ├── features/* (domain modules)
            └── services/* → api.ts → backend /api/v1 | /api/v2
```

## Routes — `frontend/src/App.tsx`

| Path | Page | Purpose |
| --- | --- | --- |
| `/login` | `LoginPage.tsx` | JWT authentication |
| `/dashboard` | `DashboardPage.tsx` | Stats, agent workflow entry |
| `/tests` | `TestsPage.tsx` | Test list |
| `/tests/saved` | `SavedTestsPage.tsx` | Saved test cases |
| `/tests/:testId` | `TestDetailPage.tsx` | Edit steps, run test |
| `/test-suites` | `TestSuitesPage.tsx` | Suite management |
| `/knowledge-base` | `KnowledgeBasePage.tsx` | KB documents |
| `/settings` | `SettingsPage.tsx` | Profile, execution settings, XPath cache |
| `/executions` | `ExecutionHistoryPage.tsx` | Execution list |
| `/executions/:executionId` | `ExecutionProgressPage.tsx` | Live progress, RCA, screenshots |
| `/debug/:executionId/...` | `DebugSessionPage.tsx` | Interactive debug |
| `/step-library` | `StepLibraryPage.tsx` | Reusable step modules |
| `/crawl-and-save` | `CrawlAndSavePage.tsx` | URL crawl workflow |
| `/feedback` | `FeedbackListPage.tsx` | Execution feedback |
| `/agent-workflow` | Redirect → `/dashboard` | Legacy route |

## Services — `frontend/src/services/`

| Service | Backend API | Purpose |
| --- | --- | --- |
| `api.ts` | Base client, auth headers | Shared fetch wrapper |
| `authService.ts` | `/api/v1/auth/*` | Login, token storage |
| `testsService.ts` | `/api/v1/tests/*` | Test CRUD, generation |
| `executionService.ts` | `/api/v1/executions/*` | Run, poll, resume |
| `executionFeedbackService.ts` | execution feedback | Submit corrections |
| `feedbackService.ts` | Feedback list | Human feedback UI |
| `settingsService.ts` | `/api/v1/settings/*` | Execution tier settings, XPath cache |
| `knowledgeBaseService.ts` | `/api/v1/kb/*` | Document upload/list |
| `testSuitesService.ts` | `/api/v1/suites/*` | Suite CRUD/run |
| `stepLibraryService.ts` | step-library | Module CRUD |
| `browserProfileService.ts` | browser-profiles | Profile management |
| `requirementsService.ts` | `/api/v1/requirements/*` | ReqIQ proxy |
| `agentWorkflowService.ts` | `/api/v2/*` | Agent pipeline triggers |
| `sseService.ts` | `/api/v2/workflows/*/stream` | SSE progress |
| `debugService.ts` | debug endpoints | Debug sessions |
| `schedulesService.ts` | schedules | Scheduled runs |

## Feature Modules — `frontend/src/features/`

### Agent Workflow — `features/agent-workflow/`

| Component | Purpose |
| --- | --- |
| `AgentWorkflowTrigger.tsx` | Start multi-agent pipeline |
| `AgentProgressPipeline.tsx` | Visual pipeline stages |
| `AgentStatusMonitor.tsx` | Real-time agent status |
| `StopAgentButton.tsx` | Cancel workflow |
| `WorkflowResults.tsx` | Display workflow output |
| `useWorkflowProgress.ts` | SSE hook |

### Settings — `features/settings/`

| Component | Purpose |
| --- | --- |
| `EmailCredentialsSection.tsx` | IMAP OTP credential UI (ADR-002-38) |

## Key Components — `frontend/src/components/`

| Component | Execution relevance |
| --- | --- |
| `RunTestButton.tsx` | Triggers execution (ADR-002-14: no profile picker in saved-test flow) |
| `ExecutionSettingsPanel.tsx` | Fallback strategy A/B/C selection |
| `XPathCachePanel.tsx` | XPath cache management (ADR-002-45) |
| `execution/RootCauseAnalysisPanel.tsx` | AI RCA display (ADR-002-43) |
| `execution/ScreenshotGallery.tsx` | Step screenshots |
| `execution/ExecutionFeedbackViewer.tsx` | Feedback on failures |
| `CredentialPromptModal.tsx` | Ephemeral UAT credentials |
| `InteractiveDebugPanel.tsx` | Debug mode controls |
| `TierAnalyticsPanel.tsx` | Per-tier execution analytics |
| `QueueStatusWidget.tsx` | Queue depth display |
| `layout/Layout.tsx`, `Header.tsx`, `Sidebar.tsx` | App shell |

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | `http://127.0.0.1:8000/api/v1` | Backend base URL |
| `VITE_USE_MOCK` | `false` | Mock vs live API |

## Data Flow — Run Test

```
TestDetailPage / SavedTestsPage
    → RunTestButton
    → executionService.startExecution(testId)
    → POST /api/v1/executions/tests/{id}/execute
    → navigate to /executions/{executionId}
    → ExecutionProgressPage polls step results
    → RootCauseAnalysisPanel (on failure)
```

## Technology Stack

- React 18, TypeScript, Vite 6
- React Router 7
- TailwindCSS 3
- Lucide icons
- Vitest for unit tests (`src/**/__tests__/`)

## Related Codemaps

- [execution-engine.md](./execution-engine.md) — backend tier behavior reflected in UI
- [backend.md](./backend.md) — API endpoints consumed by services
- [integrations.md](./integrations.md) — ReqIQ proxy via `requirementsService`
