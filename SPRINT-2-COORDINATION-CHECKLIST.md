# Sprint 2 Coordination Checklist
## Daily Sync & Task Tracking

**Team:** Frontend Developer (VS Code) + Backend Developer (Cursor)  
**Duration:** 2 weeks (10 working days)  
**Goal:** Test Generation Feature Complete

---

## 📅 Week 3: Test Generation Feature

### **Day 1 (Monday)**

#### **Backend Tasks**
- [x] Get OpenRouter API key (https://openrouter.ai/keys) ✅
- [x] Add `OPENROUTER_API_KEY` to `backend/.env` ✅
- [x] Create `app/services/openrouter.py` ✅
- [x] Test OpenRouter API connection ✅
- [x] Create basic prompt template ✅

**Deliverable:** ✅ OpenRouter integration working (using Claude 3.5 Sonnet)

#### **Frontend Tasks**
- [ ] Design test generation UI mockup
- [ ] Create `TestGenerationPage.tsx` skeleton
- [ ] Create input form component
- [ ] Add basic styling

**Deliverable:** UI mockup ready

#### **Sync Points**
- [ ] Backend shares OpenRouter response format
- [ ] Frontend shares UI mockup
- [ ] Agree on API contract for `/tests/generate`

---

### **Day 2 (Tuesday)**

#### **Backend Tasks**
- [ ] Create `app/services/generation.py`
- [ ] Implement test case parsing logic
- [ ] Test with various prompts
- [ ] Refine prompt template

**Deliverable:** Test generation service working

#### **Frontend Tasks**
- [ ] Build test generation form
- [ ] Add loading states
- [ ] Add error handling
- [ ] Create mock response for testing

**Deliverable:** Form UI complete (with mocks)

#### **Sync Points**
- [ ] Backend shares sample generated test cases
- [ ] Frontend confirms UI can display them
- [ ] Discuss any prompt improvements needed

---

### **Day 3 (Wednesday)**

#### **Backend Tasks**
- [ ] Create `app/models/test.py` (SQLAlchemy)
- [ ] Create `app/schemas/test.py` (Pydantic)
- [ ] Create `app/crud/test.py` (CRUD operations)
- [ ] Create database migration
- [ ] Apply migration

**Deliverable:** Database schema ready

#### **Frontend Tasks**
- [ ] Create `TestCaseCard` component
- [ ] Create `TestCaseList` component
- [ ] Add filtering UI
- [ ] Style components

**Deliverable:** Test case display components ready

#### **Sync Points**
- [ ] Backend shares TestCase schema
- [ ] Frontend updates `types/api.ts`
- [ ] Confirm all fields needed by frontend

---

### **Day 4 (Thursday)**

#### **Backend Tasks**
- [ ] Create `app/api/v1/endpoints/tests.py`
- [ ] Implement `POST /tests/generate`
- [ ] Implement `GET /tests`
- [ ] Implement `GET /tests/{id}`
- [ ] Test all endpoints in Swagger UI

**Deliverable:** Test CRUD API complete

#### **Frontend Tasks**
- [ ] Create `testService.ts`
- [ ] Implement `generateTests()` method
- [ ] Implement `getTests()` method
- [ ] Connect form to API

**Deliverable:** Frontend-backend integration working

#### **Sync Points**
- [ ] Backend confirms endpoints are ready
- [ ] Frontend tests with real API
- [ ] Fix any integration issues together

---

### **Day 5 (Friday)**

#### **Backend Tasks**
- [ ] Implement `PUT /tests/{id}`
- [ ] Implement `DELETE /tests/{id}`
- [ ] Add error handling
- [ ] Write test scripts
- [ ] Update API documentation

**Deliverable:** Test API fully functional

#### **Frontend Tasks**
- [ ] Add edit functionality
- [ ] Add delete functionality
- [ ] Update Playwright tests
- [ ] Fix any bugs

**Deliverable:** Test generation feature complete

#### **Sync Points**
- [ ] Both test end-to-end flow
- [ ] Fix any bugs found
- [ ] Prepare demo for Monday

---

## 📅 Week 4: Knowledge Base & Polish

### **Day 6 (Monday)**

#### **Backend Tasks**
- [ ] Create `app/models/kb.py`
- [ ] Create `app/schemas/kb.py`
- [ ] Create `app/crud/kb.py`
- [ ] Create database migration
- [ ] Plan file storage strategy

**Deliverable:** KB database schema ready

#### **Frontend Tasks**
- [ ] Create `KBUploadForm` component
- [ ] Add drag-and-drop functionality
- [ ] Add file type validation
- [ ] Style upload UI

**Deliverable:** KB upload UI ready

#### **Sync Points**
- [ ] Backend shares KB document schema
- [ ] Frontend updates types
- [ ] Discuss file size limits

---

### **Day 7 (Tuesday)**

#### **Backend Tasks**
- [ ] Implement file upload endpoint
- [ ] Add file type validation
- [ ] Store files (local or S3)
- [ ] Extract text from files
- [ ] Test with PDF, DOCX, TXT

**Deliverable:** File upload working

#### **Frontend Tasks**
- [ ] Create `KBDocumentList` component
- [ ] Add document preview
- [ ] Add category selector
- [ ] Connect to API

**Deliverable:** KB document list working

#### **Sync Points**
- [ ] Backend confirms upload endpoint ready
- [ ] Frontend tests file upload
- [ ] Discuss text extraction results

---

### **Day 8 (Wednesday)**

#### **Backend Tasks**
- [ ] Implement `GET /kb/documents`
- [ ] Implement `DELETE /kb/documents/{id}`
- [ ] Add search functionality
- [ ] Optimize queries

**Deliverable:** KB CRUD complete

#### **Frontend Tasks**
- [ ] Add search to KB page
- [ ] Add delete functionality
- [ ] Add document details view
- [ ] Update tests

**Deliverable:** KB feature complete

#### **Sync Points**
- [ ] Test KB feature end-to-end
- [ ] Fix any issues
- [ ] Discuss improvements

---

### **Day 9 (Thursday)**

#### **Backend Tasks**
- [ ] Performance optimization
- [ ] Add caching (if needed)
- [ ] Write comprehensive tests
- [ ] Update API documentation
- [ ] Code cleanup

**Deliverable:** Backend polished

#### **Frontend Tasks**
- [ ] Add dashboard charts (Recharts)
- [ ] Update stats with real data
- [ ] Polish UI/UX
- [ ] Update all Playwright tests
- [ ] Code cleanup

**Deliverable:** Frontend polished

#### **Sync Points**
- [ ] Review code together
- [ ] Identify any technical debt
- [ ] Plan Sprint 3 tasks

---

### **Day 10 (Friday)**

#### **Backend Tasks**
- [ ] Final testing
- [ ] Fix any bugs
- [ ] Update documentation
- [ ] Prepare for deployment

**Deliverable:** Sprint 2 backend complete

#### **Frontend Tasks**
- [ ] Final testing
- [ ] Fix any bugs
- [ ] Update documentation
- [ ] Verify all tests pass

**Deliverable:** Sprint 2 frontend complete

#### **Sync Points**
- [ ] Full Sprint 2 demo
- [ ] Retrospective meeting
- [ ] Celebrate! 🎉

---

## 🔄 Daily Sync Template

**Time:** 10:00 AM (or agreed time)  
**Duration:** 10-15 minutes  
**Format:** Call or chat

### **Questions to Answer:**

1. **What did you complete yesterday?**
   - Backend: _____
   - Frontend: _____

2. **What are you working on today?**
   - Backend: _____
   - Frontend: _____

3. **Any blockers or questions?**
   - Backend: _____
   - Frontend: _____

4. **Any API changes needed?**
   - Yes/No: _____
   - Details: _____

---

## 📋 API Contract Tracking

### **Endpoints to Implement**

| Endpoint | Method | Backend Status | Frontend Status | Notes |
|----------|--------|----------------|-----------------|-------|
| `/tests/generate` | POST | ⬜ Not Started | ⬜ Not Started | Test generation |
| `/tests` | GET | ⬜ Not Started | ⬜ Not Started | List all tests |
| `/tests/{id}` | GET | ⬜ Not Started | ⬜ Not Started | Get one test |
| `/tests/{id}` | PUT | ⬜ Not Started | ⬜ Not Started | Update test |
| `/tests/{id}` | DELETE | ⬜ Not Started | ⬜ Not Started | Delete test |
| `/kb/upload` | POST | ⬜ Not Started | ⬜ Not Started | Upload document |
| `/kb/documents` | GET | ⬜ Not Started | ⬜ Not Started | List documents |
| `/kb/documents/{id}` | GET | ⬜ Not Started | ⬜ Not Started | Get document |
| `/kb/documents/{id}` | DELETE | ⬜ Not Started | ⬜ Not Started | Delete document |

**Status Legend:**
- ⬜ Not Started
- 🟡 In Progress
- ✅ Complete
- 🔴 Blocked

---

## 🐛 Issue Tracking

### **Issues Found**

| Date | Issue | Severity | Assigned To | Status |
|------|-------|----------|-------------|--------|
| | | | | |

**Severity:**
- 🔴 Critical (blocking)
- 🟡 High (important)
- 🟢 Low (nice to have)

---

## 📝 Decision Log

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|
| | | | |

---

## ✅ Sprint 2 Definition of Done

### **Test Generation Feature**
- [ ] User can enter natural language prompt
- [ ] User can click "Generate Tests"
- [ ] System generates 5-10 test cases
- [ ] Test cases are saved to database
- [ ] Test cases display in UI
- [ ] User can view test case details
- [ ] User can edit test cases
- [ ] User can delete test cases
- [ ] All Playwright tests passing
- [ ] API documented in Swagger
- [ ] Code reviewed and merged

### **Knowledge Base Feature**
- [ ] User can upload documents (PDF, DOCX, TXT)
- [ ] Documents are stored securely
- [ ] Text is extracted from documents
- [ ] Documents display in list view
- [ ] User can search documents
- [ ] User can delete documents
- [ ] All Playwright tests passing
- [ ] API documented in Swagger
- [ ] Code reviewed and merged

### **Quality Checks**
- [ ] No TypeScript errors
- [ ] No Python errors
- [ ] No console errors
- [ ] All tests passing (frontend + backend)
- [ ] Code follows existing patterns
- [ ] Documentation updated
- [ ] Git commits are clean
- [ ] No merge conflicts

---

## 🎯 Success Metrics

**Target:**
- [ ] Test generation works in < 10 seconds
- [ ] Can generate 10 test cases from one prompt
- [ ] Can upload documents up to 10MB
- [ ] All features work on localhost
- [ ] 100% of planned features complete
- [ ] Zero critical bugs
- [ ] Both developers happy with code quality

---

## 📞 Emergency Contacts

**Backend Developer (You):**
- Name: _____
- Contact: _____
- Available: _____

**Frontend Developer (Your Friend):**
- Name: _____
- Contact: _____
- Available: _____

**Escalation:**
- If blocked > 2 hours: Contact each other
- If major issue: Schedule emergency sync
- If architecture decision needed: Both discuss

---

## 🎉 Sprint 2 Completion Checklist

- [ ] All endpoints implemented and tested
- [ ] All UI components implemented and tested
- [ ] Frontend-backend integration working
- [ ] All Playwright tests passing
- [ ] Documentation updated
- [ ] Code reviewed and merged to main
- [ ] Sprint 2 demo completed
- [ ] Retrospective completed
- [ ] Sprint 3 planning started

---

**Print this checklist and track progress daily!** ✅

**Good luck with Sprint 2!** 🚀

