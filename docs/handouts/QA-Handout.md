# QA Handout — AI Web Test, ReqIQ & Hermes

**For:** QA engineers building tests when requirements arrive late or incomplete.

---

## Your problem (we get it)

- Test cases written from partial specs  
- Full picture often only after UAT starts  
- Always behind the release train  
- Pressure from UAT and Dev when automation does not exist yet

## What changes for you

You shift from **writing every step from scratch** to **governing coverage and refining drafts**.

```
ReqIQ (readiness)  →  Planner (gaps)  →  Test-gen (drafts)  →  YOU (review)  →  Regression (24×7)
```

| Tool | Your role |
|------|-----------|
| **ReqIQ** | Keep wiki/docs uploaded; readiness ≥ 60 unlocks auto-generation |
| **Journey Registry** | Maintain UAT URLs, login modules, tags (`/journey-registry`) |
| **Backlog** | Monitor queue; factory drains automatically (`/backlog`) |
| **Hermes planner** | Fills gaps from coverage matrix (when Ubuntu node deployed) |
| **Heal Review** | Triage escalations with Dev (`/heal-review`) |

## Your core screens

| Screen | Path | Role |
|--------|------|------|
| **Journey Registry** | `/journey-registry` | Add/edit journeys (`admin`+ to edit) |
| **Backlog** | `/backlog` | See pending → in-progress → done |
| **Tests** | `/tests` | Review and edit auto-generated cases |
| **Test Suites** | `/test-suites` | Group regression suites |
| **Executions** | `/executions` | Pass/fail trends |
| **Agent Console** | `/agent-console` | Trigger: `drain backlog`, `scan changes`, `run regression` |
| **Crawl & Save** | `/crawl-and-save` | Manual one-off generation when needed |

## QA workflow (simplified)

1. **Maintain ReqIQ** — upload BRD, Confluence exports, acceptance criteria per feature.  
2. **Seed registry** — one row per major UAT journey (URL, slug, login module, tags).  
3. **Let factory run** — planner enqueues gaps; test-gen creates drafts (3–15 min each).  
4. **Review drafts** — fix assertions, add business rules, tag `regression` for nightly runs.  
5. **Govern Heal Review** — only ~10% of failures should reach you after self-heal.

## Readiness gate (important)

Hermes **qa-journey-planner** will **not** auto-generate if ReqIQ readiness **&lt; 60**.  
That is intentional — it stops garbage tests from thin air.  
**Action:** improve ReqIQ content or pair with BA on missing sections.

## Tags to agree with the team

Example for Three-HK:

- `regression` — must pass every 2 hours + nightly  
- `three-hk` — project filter  
- Journey slug tags — e.g. `diy-dashboard`

Document the list in Confluence; apply in registry and test cases.

## 5G 流動寬頻 program (PG-5G)

Pilot product program using **DT platform LEGO bricks** (WebApp, CRM, Billing, Matrixx, Provisioning, e-Coupon, MIS). **MCS/BAU plan tables are reference-only** — not automated.

- Architecture & phases: [programs/5g-mobile-broadband/](../programs/5g-mobile-broadband/README.md)  
- Tag journeys with `dt_components` and `capability_keys` when seeding registry  
- CRM tests: enable **CRM login required** on test case (ephemeral password)

## One sentence

> *I don’t wait for perfect requirements — ReqIQ and the factory build from what we have, and I refine.*

## Need help?

- **Ops / superadmin** — enable scheduler, bridge URL in Settings  
- **ReqIQ admin** — project ID, document compile  
- **Week 1 setup:** [Week-1-Checklist.md](Week-1-Checklist.md)
