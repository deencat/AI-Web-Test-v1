# UAT Handout — AI Web Test & QA Factory

**For:** UAT testers facing endless CRs and limited people.

---

## Your problem (we get it)

- Too many features and CRs to test fully  
- Repeated manual regression on the same stable flows  
- Blamed for missed defects or for blocking releases  
- IT quality feels poor because testing starts too late

## What changes for you

**Automation handles boring regression.** You focus on **new behaviour, business rules, and edge cases** that scripts cannot judge.

| What runs while you sleep | Your higher-value work |
|---------------------------|------------------------|
| Nightly + 2-hourly **regression** on core journeys | Exploratory testing on **new/changed** features |
| **Change scanner** flags pages that changed vs last week | Business sign-off on critical paths |
| **Auto-generated** baseline tests from registry + ReqIQ | Usability and “does this match the business intent?” |
| **Self-heal** retries flaky automation | **Heal Review** only when automation is stuck |

## Your weekly rhythm

| Day | Suggested focus |
|-----|-----------------|
| **Monday** | Check `/executions` or ask QA: “What failed over the weekend?” — don’t re-run passed stable flows manually |
| **Daily** | Test **new/changed** CRs only |
| **As needed** | `/heal-review` — items escalated after 2 auto-heal attempts (~5–10 min each) |

## Screens you will use

| Screen | Path | When |
|--------|------|------|
| **Executions** | `/executions` | See what regression already ran and results |
| **Heal Review** | `/heal-review` | Triage stuck automation (with Dev/QA) |
| **Agent Console** | `/agent-console` | Ask: “What failed in regression last night?” (needs `agent_operator` role) |
| **Tests** | `/tests` | Open a specific failed case for context |

## What you can stop doing

- Re-testing login, standard checkout, and dashboard flows every release if they are in the **regression** tag set  
- Assuming “nobody tested” — check **executions** first; the factory may have already run  

## What still needs humans (you)

- Edge cases and negative scenarios automation did not imagine  
- Cross-system business rules (billing, promotions, eligibility)  
- Final sign-off on go-live risk  

## One sentence

> *I don’t re-test what the factory proved overnight; I test what’s new, risky, or business-critical.*

## Need help?

- **QA** — which journeys are in nightly regression, registry gaps  
- **Developers** — defects from Heal Review  
- **Week 1 setup:** [Week-1-Checklist.md](Week-1-Checklist.md)
