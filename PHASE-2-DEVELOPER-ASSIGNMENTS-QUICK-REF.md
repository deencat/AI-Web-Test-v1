# Phase 2 Developer Assignments - Quick Reference

**Date:** December 18, 2025  
**Print This:** 📋 Stick on wall for daily reference

---

## 🎯 The Big Picture

```
┌─────────────────────────────────────────────────────────────┐
│  OLD WAY (Phase 1)          →    NEW WAY (Phase 2)          │
├─────────────────────────────────────────────────────────────┤
│  Dev A: All Frontend        →    Dev A: Features 1,3,5      │
│  Dev B: All Backend         →    Dev B: Features 2,4,6      │
│                                                              │
│  ❌ Blocking dependencies    →    ✅ Parallel work          │
│  ❌ Constant handoffs       →    ✅ End-to-end ownership    │
│  ❌ Slow integration        →    ✅ Continuous integration  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📅 6-Week Sprint Calendar

```
┌─────────────────────────────────────────────────────────────────┐
│ Sprint 4: Dec 9-20 (Week 9-10)  - FOUNDATION FEATURES          │
├─────────────────────────────────────────────────────────────────┤
│ Dev A: Feature 1 - Test Editing & Versioning (80 hours)        │
│ Dev B: Feature 2 - Feedback Collection (80 hours)              │
│ Merge: Friday Dec 20                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Sprint 5: Dec 23-Jan 3 (Week 11-12) - INTELLIGENCE FEATURES    │
├─────────────────────────────────────────────────────────────────┤
│ Dev A: Feature 3 - Pattern Recognition (90 hours)              │
│ Dev B: Feature 4 - KB Enhancement (75 hours)                   │
│ Merge: Friday Jan 3                                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Sprint 6: Jan 6-17 (Week 13-14) - VISIBILITY FEATURES          │
├─────────────────────────────────────────────────────────────────┤
│ Dev A: Feature 5 - Learning Dashboard (85 hours)               │
│ Dev B: Feature 6 - Prompt A/B Testing (80 hours)               │
│ Merge: Friday Jan 17 → PHASE 2 COMPLETE 🎉                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 👤 Developer A - Features 1, 3, 5

### Sprint 4: Feature 1 - Test Editing & Versioning
**Branch:** `feature/test-editing`  
**Complexity:** Medium (40 hours/week × 2 weeks)

**Backend (Week 9):**
- `test_versions` table and model
- `PUT /api/v1/tests/{id}/steps` endpoint
- Version control service (save, retrieve, rollback)

**Frontend (Week 10):**
- Inline step editor component
- Version history viewer modal
- Rollback UI

**Merge:** Friday Week 10 (Dec 20)

---

### Sprint 5: Feature 3 - Pattern Recognition & Auto-Fix
**Branch:** `feature/pattern-recognition`  
**Complexity:** High (45 hours/week × 2 weeks)

**Backend (Week 11):**
- `PatternAnalyzer` service class
- Similarity scoring algorithms
- `GET /api/v1/suggestions/{test_id}` endpoint
- Confidence calculation

**Frontend (Week 12):**
- Suggestions panel component
- Auto-fix preview modal
- Apply/dismiss controls

**Merge:** Friday Week 12 (Jan 3)

---

### Sprint 6: Feature 5 - Learning Insights Dashboard
**Branch:** `feature/learning-dashboard`  
**Complexity:** High (42.5 hours/week × 2 weeks)

**Backend (Week 13):**
- `GET /api/v1/learning/insights` endpoint
- Aggregation queries (failure analysis)
- Success trend calculation

**Frontend (Week 14):**
- New `/learning-insights` page
- Recharts visualizations (bar, line, table)
- Real-time data refresh

**Merge:** Friday Week 14 (Jan 17)

---

## 👤 Developer B - Features 2, 4, 6

### Sprint 4: Feature 2 - Feedback Collection System
**Branch:** `feature/feedback-collection`  
**Complexity:** Medium (40 hours/week × 2 weeks)

**Backend (Week 9):**
- `execution_feedback` table and model
- Enhance execution service (capture context)
- `POST /api/v1/executions/{id}/feedback` endpoint

**Frontend (Week 10):**
- Feedback viewer component
- Correction form UI
- Submission flow

**Merge:** Friday Week 10 (Dec 20)

---

### Sprint 5: Feature 4 - KB Enhancement & Auto-Learning
**Branch:** `feature/kb-enhancement`  
**Complexity:** Medium (37.5 hours/week × 2 weeks)

**Backend (Week 11):**
- New KB categories (test_patterns, failure_lessons, selector_library)
- Auto-population service
- Enhanced generation prompts with KB context

**Frontend (Week 12):**
- KB category browser
- Pattern library viewer
- Auto-learned pattern indicators

**Merge:** Friday Week 12 (Jan 3)

---

### Sprint 6: Feature 6 - Prompt Template Library & A/B Testing
**Branch:** `feature/prompt-ab-testing`  
**Complexity:** Medium (40 hours/week × 2 weeks)

**Backend (Week 13):**
- `prompt_templates` table and model
- A/B testing selection logic (weighted random)
- Performance tracking (running averages)

**Frontend (Week 14):**
- Prompt management page
- Template editor component
- A/B config UI + performance view

**Merge:** Friday Week 14 (Jan 17)

---

## 🔄 Daily Workflow

### Every Morning (9:00 AM):
```
1. Daily Standup (10 minutes)
   - What did you complete yesterday?
   - What will you complete today?
   - Any blockers?
   - Any API contract changes?

2. Deep Work (9:10 AM - 12:00 PM)
   - No interruptions
   - Focus on feature development
```

### Every Afternoon:
```
1:00-3:00 PM:  Continue development
3:00-3:30 PM:  Code review time (if peer has PR)
3:30-5:00 PM:  Testing, documentation, or help peer
```

### Every Friday:
```
9:00-12:00 PM: Final polish + last commits
1:00-3:00 PM:  Integration testing (BOTH DEVELOPERS)
3:00-4:00 PM:  Code review + merge
4:00-5:00 PM:  Demo + retrospective
```

---

## 🤝 Collaboration Points

### Monday Week 9 (Sprint 4 Start):
- **9:00-10:00 AM:** Kickoff meeting
  - Review API contracts
  - Agree on database conventions
  - Set up feature branches

### Friday Week 10 (Sprint 4 End):
- **1:00-3:00 PM:** Integration test (TOGETHER)
  - Test editing → Verify version saved
  - Execute test → Verify feedback captured
- **3:00 PM:** Merge to main (Dev B first, then Dev A)

### Monday Week 11 (Sprint 5 Start):
- **9:00-9:30 AM:** API contract review
  - Pattern recognition endpoints
  - KB enhancement endpoints

### Friday Week 12 (Sprint 5 End):
- **1:00-4:00 PM:** Integration test (TOGETHER)
  - Feedback → Pattern recognition → Suggestion
  - KB generation → Check pattern usage
- **4:00 PM:** Merge to main

### Monday Week 13 (Sprint 6 Start):
- **9:00-9:30 AM:** Data format alignment
  - Dashboard insights API
  - Prompt performance metrics

### Friday Week 14 (Sprint 6 End):
- **1:00-5:00 PM:** Final integration test (TOGETHER)
  - Complete Phase 2 user journey
  - Dashboard + A/B testing flow
- **5:00 PM:** PHASE 2 COMPLETE 🎉

---

## 🧪 Testing Responsibilities

### Each Developer Tests:
- ✅ Unit tests (80% coverage)
- ✅ Integration tests (backend + frontend)
- ✅ E2E tests (Playwright)

### Both Developers Together:
- ✅ Cross-feature integration (Fridays)
- ✅ Sprint demo validation
- ✅ User acceptance testing

---

## 📊 Workload Summary

| Developer | Total Hours | Overtime | Features Owned |
|-----------|------------|----------|----------------|
| **Dev A** | 255 hours  | 15 hours | 1, 3, 5        |
| **Dev B** | 235 hours  | 0 hours  | 2, 4, 6        |

**Balance:** ✅ Well-distributed (Dev A has 8% more, Dev B has buffer to help)

---

## 🚨 When to Ask for Help

### Dev A Should Ping Dev B If:
- Stuck on feedback collection integration (Week 10)
- Need KB data format clarified (Week 12)
- Dashboard insights API questions (Week 13)

### Dev B Should Ping Dev A If:
- Stuck on version control integration (Week 10)
- Need pattern recognition algorithm help (Week 12)
- Dashboard data aggregation questions (Week 14)

### Both Should Escalate If:
- Feature slipping >1 day behind
- Critical bug blocking merge
- API contract needs major change

---

## ✅ Definition of Done (Per Feature)

**Before Merging to Main:**
- [ ] Backend: Models, endpoints, tests (80% coverage)
- [ ] Frontend: Components, API integration, tests
- [ ] E2E test covering main flow
- [ ] Code reviewed and approved by peer
- [ ] No console errors or linter warnings
- [ ] Integration test passed (both developers)

---

## 🎯 Success Metrics

**By End of Week 14:**
- ✅ All 6 features delivered
- ✅ 100+ unit tests passing
- ✅ 20+ integration tests passing
- ✅ Test generation success rate: 85%+
- ✅ Manual corrections reduced 60%
- ✅ User satisfaction: >80%

---

## 📞 Emergency Contacts

**Blocking Issue:**
- Ping peer immediately
- Standup discussion

**Critical Bug:**
- Create GitHub issue
- Notify team lead
- Coordinate hotfix

**Schedule Conflict:**
- Notify 24 hours in advance
- Reschedule integration test
- Update sprint plan

---

## 🎓 Learning Goals

### Dev A (primarily backend experience):
- Learn React component patterns
- Master TailwindCSS styling
- Practice frontend state management

### Dev B (primarily frontend experience):
- Learn FastAPI patterns
- Master SQLAlchemy ORM
- Practice database design

**By Week 14:** Both developers should be **full-stack capable**

---

## 🗓️ Key Dates

- **Dec 9 (Mon):**   Sprint 4 kickoff
- **Dec 20 (Fri):**  Sprint 4 merge (Features 1+2)
- **Dec 23 (Mon):**  Sprint 5 kickoff
- **Jan 3 (Fri):**   Sprint 5 merge (Features 3+4)
- **Jan 6 (Mon):**   Sprint 6 kickoff
- **Jan 17 (Fri):**  **PHASE 2 COMPLETE 🎉**

---

## 💡 Pro Tips

1. **Define API contracts Monday** (before implementation)
2. **Use mocks for parallel work** (don't wait for real API)
3. **Merge frequently** (every 2 weeks, not daily)
4. **Communicate before changing shared code**
5. **Review PRs within 24 hours**
6. **Test together on Fridays** (integration)
7. **Demo features weekly** (show and tell)
8. **Ask for help early** (don't struggle for >2 hours)

---

**🖨️ PRINT THIS AND STICK ON WALL**  
**📅 Update every Monday after standup**

---

**Document Status:** ✅ READY  
**Date:** December 18, 2025
