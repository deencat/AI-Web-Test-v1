# Test Execution Engine Codemap

**Last Updated:** 2026-07-16  
**Canonical ADR:** [`documentation/ADR-002-test-execution-engine.md`](../../documentation/ADR-002-test-execution-engine.md) (Accepted, March 2026 — 52 sub-decisions)  
**Timed wait:** [`documentation/ADR-010-timed-wait-step.md`](../../documentation/ADR-010-timed-wait-step.md)

## Overview

The execution engine runs saved test steps against a live browser. **ADR-002-1** defines a three-tier architecture with user-configurable fallback strategies. `ExecutionService` owns browser lifecycle; `ThreeTierExecutionService` dispatches each step to the appropriate tier.

## Tier Architecture

```
                    ┌─────────────────────────────────┐
                    │     ExecutionService            │
                    │  Browser · CDP · screenshots    │
                    │  OTP expand · module resolve    │
                    │  timed wait short-circuit (ADR-010) │
                    └───────────────┬─────────────────┘
                                    │ per step
                    ┌───────────────┴─────────────────┐
                    │ timed wait? → chunked cancel-aware │
                    │ sleep → return (no tiers)          │
                    └───────────────┬─────────────────┘
                                    │ else
                                    ▼
                    ┌─────────────────────────────────┐
                    │   ThreeTierExecutionService     │
                    │   step boundary readiness wait  │
                    └───────────────┬─────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ Tier 1          │    │ Tier 2              │    │ Tier 3              │
│ Playwright      │    │ Hybrid              │    │ Stagehand           │
│ Direct selector │    │ observe() → XPath   │    │ act() full AI       │
│ Zero LLM cost   │    │ Low–medium LLM      │    │ High LLM            │
│ ~85–90% success │    │ ~90–95% on T1 fail  │    │ ~60–70% on T1+T2 fail│
└─────────────────┘    └─────────────────────┘    └─────────────────────┘
 tier1_playwright.py    tier2_hybrid.py             tier3_stagehand.py
```

**Timed wait (ADR-010):** User steps like `wait: 10s` / `Wait 10 seconds` are handled in `ExecutionService` via `timed_wait.py` **before** tier dispatch. Cancel-aware chunked sleep (ADR-009). Distinct from ADR-002 readiness (`post_click_readiness.py`). Never Stagehand `act("wait…")`.

**Signature pad ink verify (Feature 5):** For `draw_signature` / `sign`, programmatic stroke + ink verification in `signature_pad.py` is the source of truth. Tier 3 must **never** PASS on soft Stagehand `act()` (`scrollIntoView` / locator-only) with a blank canvas. Tier 2 tries canvas DOM heuristics when observe returns empty (canvas often absent from a11y tree). Prefer pointer/mouse/touch events over ctx-only paint (SignaturePad `isEmpty`). Lazy Tier 2/3 init unchanged (ADR-002-1).
## Fallback Strategies (ExecutionSettings)

Configured via `ExecutionSettings.fallback_strategy` (`app/schemas/execution_settings.py`):

| Option | Path | Use case |
| --- | --- | --- |
| **A** | Tier 1 → Tier 2 | Cost-conscious (default) |
| **B** | Tier 1 → Tier 3 | AI-first, skip observe |
| **C** | Tier 1 → Tier 2 → Tier 3 | Maximum reliability |

Tier 2/3 are **lazily initialized** — Stagehand CDP connects only when Tier 1 fails (ADR-002-1).

## Module Map

| Module | Role |
| --- | --- |
| `execution_service.py` | Entry point: launch browser, iterate steps, timed-wait short-circuit, call three-tier, persist results |
| `timed_wait.py` | Parse NL/canonical/structured timed waits; cancel-aware chunked sleep (ADR-010) |
| `signature_pad.py` | Locate canvas, multi-strategy stroke, ink verify for `draw_signature`/`sign` (Feature 5) |
| `three_tier_execution_service.py` | Strategy dispatch, execution history, tier logging |
| `tier1_playwright.py` | `Tier1PlaywrightExecutor` — direct locator actions |
| `tier2_hybrid.py` | `Tier2HybridExecutor` — observe + Playwright |
| `tier3_stagehand.py` | `Tier3StagehandExecutor` — Stagehand act |
| `xpath_extractor.py` | `observe()` → XPath string (ADR-002-2) |
| `xpath_cache_service.py` | DB cache, self-healing invalidation (ADR-002-3, ADR-002-45) |
| `post_click_readiness.py` | Payment/SPA/modal waits (ADR-002-4–7, 19–20, 25) |
| `step_progress_guard.py` | Stuck confirm-step detection (ADR-002-29) |
| `step_module_resolver.py` | `@module:` expansion (ADR-002-42) |
| `email_otp_service.py` | IMAP OTP (ADR-002-38–41) |
| `preprod_otp_service.py` | HTTP OTP API (ADR-002-47) |
| `otp_source_router.py` | Routes OTP source by step context |
| `resume_guard.py` | Re-run from failed step validation (ADR-002-44) |
| `root_cause_analysis_service.py` | Post-failure AI RCA (ADR-002-43) |
| `screenshot_verification_service.py` | Visual verification steps |
| `stagehand_factory.py` | Python vs TypeScript Stagehand adapter |
| `stagehand_service.py` | Stagehand session, Azure LiteLLM routing (ADR-002-11) |

## Execution Flow (Single Step)

```
1. step_module_resolver expands @module: references
2. OTP steps expanded JIT (email_otp / preprod_otp)
3. wait_for_step_boundary_readiness (loading indicators, modals)
4. If timed wait (ADR-010): sleep_cancel_aware → return (skip tiers)
5. Else ThreeTierExecutionService.execute_step(step)
   a. Tier 1: pre-defined selector / action
   b. On failure → Tier 2 (if strategy A or C)
      - xpath_cache lookup
      - xpath_extractor.observe() on cache miss
      - Playwright execute cached XPath
   c. On failure → Tier 3 (if strategy B or C)
      - stagehand.act(instruction)
6. post_click_readiness waits (navigation, payment gateways)
7. step_progress_guard checks confirm-step progress
8. Persist step result, screenshot, tier_execution_log
```

## API Surface

| Endpoint | Module | Action |
| --- | --- | --- |
| `POST /api/v1/executions/tests/{id}/execute` | `executions.py` | Start run |
| `GET /api/v1/executions/{id}` | `executions.py` | Status + steps |
| `GET /api/v1/executions/{id}/step-results` | `executions.py` | Step details + RCA |
| `POST .../resume` | `executions.py` | Re-run from step (ADR-002-44) |
| `GET/PUT /api/v1/settings/execution` | `settings.py` | Tier strategy config |
| XPath cache CRUD | `settings.py` | ADR-002-45 |

## Frontend Integration

| UI | Backend concern |
| --- | --- |
| `RunTestButton.tsx` | Starts execution; UAT cred auto-inject (ADR-002-12, 13) |
| `ExecutionSettingsPanel.tsx` | Fallback strategy A/B/C |
| `ExecutionProgressPage.tsx` | Polls step results, tier logs |
| `RootCauseAnalysisPanel.tsx` | Displays RCA (ADR-002-43) |
| `XPathCachePanel.tsx` | Cache invalidation UI (ADR-002-45) |
| `EmailCredentialsSection.tsx` | IMAP OTP setup (ADR-002-38) |

## Stagehand Providers

| Provider | Path | When used |
| --- | --- | --- |
| Python Stagehand | `python_stagehand_adapter.py` | Default; in-process CDP |
| TypeScript microservice | `typescript_stagehand_adapter.py` → `stagehand-service/` | User setting `stagehand_provider=typescript` |

## Key ADR-002 Decision Groups

| ADRs | Topic |
| --- | --- |
| 002-1–3 | Three-tier architecture, observe XPath, PG cache |
| 002-4–7, 19–20, 25, 34–35 | Post-click readiness, navigation, modals |
| 002-8–10, 27 | Iframes, field validation, enabled polling |
| 002-11 | Azure LiteLLM for Stagehand |
| 002-12–14 | UAT HTTP creds, URL scan, run flow UX |
| 002-15–18, 48–49 | Payment gateway direct handlers, gw-proxy |
| 002-21–22, 31–33, 36–37, 50–52 | Three HK site-specific handlers |
| 002-38–41, 47 | OTP (IMAP + preprod API) |
| 002-42 | Step library `@module:` |
| 002-43–45 | RCA, resume, XPath cache UI |
| 002-46 | Stagehand LLM JSONL logging |

Full decision text: [`documentation/ADR-002-test-execution-engine.md`](../../documentation/ADR-002-test-execution-engine.md)

## Related Codemaps

- [backend.md](./backend.md) — full service list
- [database.md](./database.md) — `ExecutionSettings`, `XPathCache`, `TierExecutionLog`
- [integrations.md](./integrations.md) — Stagehand microservice, LLM providers
