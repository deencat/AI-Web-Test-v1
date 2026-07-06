# Developer Handout — AI Web Test & QA Factory

**For:** Developers under tight deadlines who rarely have time to test before handoff.

---

## Your problem (we get it)

- Context-switching all day  
- Testing is “when I have a moment” — and that moment never comes  
- UAT finds regressions you would have caught with a proper smoke pass  
- You get blamed for “poor IT quality” even when you wanted to test

## What changes for you

**You do not become a tester.** A **background factory** runs regression on core journeys while you work on the next ticket.

| What runs automatically | What you do |
|-------------------------|-------------|
| Regression every **2 hours** + **nightly** on tagged tests | Nothing |
| **Site change detection** on UAT URLs → queue updated tests | Nothing |
| **Self-heal** for many flaky/UI-drift failures | Nothing |
| Escalation only when heal fails **twice** | Fix real bugs (~10 min when notified) |

## Your 3-minute checklist (per major CR)

1. **New URL or flow?** Ask QA/Admin to add one row in **Journey Registry** (`/journey-registry`) — or add it yourself if you have `admin` access.  
2. **CR notes / design doc?** Upload or link in **ReqIQ** so readiness score can reach ≥ 60 before UAT.  
3. **Optional:** After merge, open **Agent Console** (`/agent-console`) and send: `run regression` — or rely on the 2-hourly schedule.

## When you need to act

| Signal | Where | Action |
|--------|-------|--------|
| Heal Review item assigned | `/heal-review` | Investigate real defect vs environment issue |
| Notification: regression failed | Bell icon (superadmin) or ask QA | Check execution in `/executions` |
| Readiness &lt; 60 for your feature | ReqIQ | Add missing spec — UAT will struggle without it |

## What you can stop doing

- Manually re-clicking login → dashboard → checkout before every release  
- Feeling guilty about “untested” handoffs when **factory regression** already ran overnight  

## One sentence

> *I commit; the factory tests stable journeys while I build the next feature.*

## Need help?

- **QA** — registry entries, test tags, regression scope  
- **Ops / superadmin** — scheduler, bridge, notifications  
- **Week 1 setup:** [Week-1-Checklist.md](Week-1-Checklist.md)
