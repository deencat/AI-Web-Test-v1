# Implementation Spec: Defer Agent Workflow & Agent Console Nav

> Generated from brief: *Remove "Agent Workflow" and "Agent Console" tabs from the frontend sidebar navigation because they are not fully ready. Defer to a later phase. Update ADR-004-agent-workflow.md to reflect this deferral.*

## Scope

Hide incomplete agent-facing UI from end-user navigation. **Do not delete** backend APIs, feature modules, or Settings configuration — only remove discoverability via sidebar (and optionally gate direct URL access).

## Current State (codebase audit)

| Item | In sidebar? | Route in `App.tsx`? | Notes |
|------|-------------|---------------------|-------|
| **Agent Workflow** | Yes — `Sidebar.tsx` line 13 | Yes — `/agent-workflow` → `AgentWorkflowPage` | Only agent nav entry today |
| **Agent Console** | **No** | **No** | Planned Phase 2 (`docs/Hermes_QA_Autonomous_Workflow_v5.md` §8); nothing to remove yet |

**Out of scope (unless product says otherwise):** Settings → "Agent Workflow Configuration" (`AgentWorkflowSettings.tsx` on `SettingsPage`) — per-agent model overrides; backend `/api/v2` agent workflow APIs remain live.

---

## 1. Files Likely Needing Changes

### Must change

| File | Change |
|------|--------|
| `frontend/src/components/layout/Sidebar.tsx` | Remove `{ path: '/agent-workflow', icon: Bot, label: 'Agent Workflow' }` from `navItems`. Remove unused `Bot` import if no longer referenced. |
| `documentation/ADR-004-agent-workflow.md` | Add frontend exposure deferral (see §3 below). |

### Should change (recommended)

| File | Change |
|------|--------|
| `frontend/src/App.tsx` | Replace `/agent-workflow` page route with `<Navigate to="/dashboard" replace />` (or remove route and add catch-all redirect). Keeps `AgentWorkflowPage` import removable or commented for lint cleanliness. |

### Optional / follow-up

| File | Change |
|------|--------|
| `frontend/README.md` | If it lists Agent Workflow in nav inventory, align with deferred state. |
| `frontend/src/components/layout/__tests__/Sidebar.test.tsx` | **Does not exist today** — add only if team wants regression guard on nav labels. |
| `frontend/src/App.tsx` tests | None exist for route list; manual verification sufficient for this scope. |

### No change required (re-enable later)

- `frontend/src/pages/AgentWorkflowPage.tsx`
- `frontend/src/features/agent-workflow/**`
- `frontend/src/services/agentWorkflowService.ts`
- `frontend/src/components/AgentWorkflowSettings.tsx`
- Backend `backend/app/api/v2/**`, agents, orchestration

### Agent Console

No frontend files to edit. When Phase 2 adds it, gate behind the same pattern (nav + route) from day one.

---

## 2. Routes: Nav-Only vs Redirect?

**Recommendation: remove from nav + redirect direct URLs.**

| Approach | Pros | Cons |
|----------|------|------|
| **Nav-only** | Smallest diff; devs can hit `/agent-workflow` | Bookmarks, docs, and shared links expose half-ready UI |
| **Nav + redirect** | Users cannot stumble into incomplete UX | Devs need to temporarily restore route or use API/Settings for testing |

**Implementation:**

1. Delete Agent Workflow from `navItems` in `Sidebar.tsx`.
2. In `App.tsx`, change the `/agent-workflow` route to redirect to `/dashboard` (or `/settings` if agent config testing is the main internal entry).

```tsx
<Route path="/agent-workflow" element={<Navigate to="/dashboard" replace />} />
```

3. Do **not** remove `AgentWorkflowPage`, feature folder, or API v2 — preserves Sprint 10 work for re-enable.

**Alternative (internal-only):** Keep route active but guard with env flag `VITE_ENABLE_AGENT_WORKFLOW_NAV=true` — only if team needs frequent QA without code churn. For this small scope, a redirect is simpler.

---

## 3. ADR-004 Updates

ADR-004 documents **ObservationAgent auth, browser-use, and `AgentWorkflowTrigger` fields** — not sidebar IA. Deferral is about **end-user UI exposure**, not reversing accepted backend decisions.

### Sections to update

| Section | Update |
|---------|--------|
| **Header block** (lines 1–8) | Add line: `**Frontend exposure:** Deferred — Agent Workflow page removed from sidebar nav (Phase 3.x / Sprint TBD). Backend and trigger implementation remain accepted.` Bump `Last Amended` date. |
| **New subsection after Context** (or before Status) | **`## Frontend Exposure Deferral`** — 3–5 sentences: dedicated Agent Workflow nav and page are hidden until Agent Console + factory job monitor ship; API v2 and Settings agent config remain for power users/integrations; re-enable checklist points to `Sidebar.tsx` + `App.tsx`. |
| **`## Status`** (lines 375–401) | Change closing line from "ready for production" to clarify **API/backend production-ready**; **product UI nav deferred**. Add bullet under "What Was Fixed / Added" is not needed — deferral is separate from technical fixes. |
| **Related Files** (lines 9–26) | Add `frontend/src/components/layout/Sidebar.tsx` and `frontend/src/App.tsx` with note "(nav gating)". |

### Do not change

- ADR decision sections (ADR-004-1 through ADR-004-8) — still valid.
- Test coverage tables — tests remain green; deferral does not remove code.
- Implementation detail for CDP auth, file upload, etc.

---

## 4. Verification Checklist

- [ ] Log in → sidebar shows: Dashboard, Tests, Step Library, Crawl & Save, Test Suites, Executions, Knowledge Base, Settings — **no** Agent Workflow or Agent Console.
- [ ] Navigate manually to `/agent-workflow` → redirects to dashboard (if redirect implemented) or confirm intentional dev-only behavior.
- [ ] Settings page still loads; "Agent Workflow Configuration" section still present (expected unless product opts to hide).
- [ ] `npm run build` (or `tsc`) in `frontend/` — no unused-import errors after removing `Bot` from Sidebar.
- [ ] Existing tests pass: `AgentWorkflowPage.test.tsx`, `AgentWorkflowTrigger.test.tsx` (page still exists in codebase).
- [ ] ADR-004 header and Status section reflect deferral without contradicting accepted technical ADRs.

---

## 5. Risks & Re-Enable Follow-Ups

| Risk | Mitigation |
|------|------------|
| Users with bookmarked `/agent-workflow` | Redirect to dashboard with optional one-time toast: "Agent Workflow coming in a future release." |
| Docs/PM plans still list nav item | Update Phase3 PM plan or nav diagrams in a separate docs pass (not blocking this change). |
| Settings exposes agent config while page is hidden | Acceptable for power users; or hide Settings section in same PR if product wants zero agent UI. |
| Agent Console never existed in nav | No code change; spec future work: page + `/agent-console` route + nav entry together. |

### Re-enable checklist (later phase)

1. Restore `navItems` entry in `Sidebar.tsx` (and add Agent Console entry when built).
2. Restore `App.tsx` route to `AgentWorkflowPage` (and `AgentConsolePage`).
3. Remove deferral note from ADR-004 Status; set `Frontend exposure: Active`.
4. Run E2E: trigger workflow from UI, SSE progress, job monitor (per Hermes v5 Phase 2).
5. Consider feature flag instead of hard remove if staggered rollout to beta users.

---

## Effort Estimate

**Small** — ~30–60 minutes: 2 frontend files, 1 ADR edit, manual smoke test. No backend changes.

## Sprint Assignment

**Sprint 1 equivalent (single PR):** Nav removal + route redirect + ADR amendment.
