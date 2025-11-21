# Sprint 2 Day 3 - Database Models & API Endpoints

**Date:** November 19, 2025  
**Status:** 📋 Planning  
**Prerequisites:** ✅ Days 1 & 2 Complete and Verified

---

## 🎯 **Day 3 Goals**

Build the database layer and REST API endpoints for test case management and generation.

**Deliverables:**
1. ✅ Database models for test cases
2. ✅ Pydantic schemas for API validation
3. ✅ CRUD operations for test cases
4. ✅ API endpoint for test generation
5. ✅ API endpoints for test management (CRUD)
6. ✅ API documentation (Swagger/OpenAPI)

---

## 📋 **Tasks Breakdown**

### **Task 1: Database Models** (30 mins)

**File:** `backend/app/models/test_case.py`

**Requirements:**
- Create `TestCase` SQLAlchemy model
- Fields:
  - `id`: Integer, primary key
  - `title`: String(255), required
  - `description`: Text, required
  - `test_type`: Enum (e2e, unit, integration, api)
  - `priority`: Enum (high, medium, low)
  - `status`: Enum (pending, in_progress, passed, failed)
  - `steps`: JSON field (array of strings)
  - `expected_result`: Text
  - `preconditions`: Text, optional
  - `test_data`: JSON field, optional
  - `created_at`: DateTime, auto
  - `updated_at`: DateTime, auto
  - `user_id`: ForeignKey to User (for tracking who created it)

**Testing:**
- Create migration
- Test model creation
- Verify constraints

---

### **Task 2: Pydantic Schemas** (30 mins)

**File:** `backend/app/schemas/test_case.py`

**Requirements:**
- `TestCaseBase`: Base schema with common fields
- `TestCaseCreate`: For POST requests
- `TestCaseUpdate`: For PUT/PATCH requests
- `TestCaseInDB`: DB model representation
- `TestCaseResponse`: API response format
- `TestGenerationRequest`: For generation endpoint
- `TestGenerationResponse`: Generation result

**Validation:**
- Enum validation for test_type, priority, status
- Required field validation
- Max length validation
- JSON field validation

---

### **Task 3: CRUD Operations** (45 mins)

**File:** `backend/app/crud/test_case.py`

**Requirements:**
- `create_test_case(db, test_case, user_id)`
- `get_test_case(db, test_case_id)`
- `get_test_cases(db, skip, limit, filters)`
- `update_test_case(db, test_case_id, updates)`
- `delete_test_case(db, test_case_id)`
- `get_test_cases_by_user(db, user_id)`
- `get_test_cases_by_type(db, test_type)`
- `get_test_cases_by_status(db, status)`

**Testing:**
- Test each CRUD operation
- Test filtering and pagination
- Test error cases

---

### **Task 4: Test Generation API Endpoint** (45 mins)

**File:** `backend/app/api/v1/endpoints/test_generation.py`

**Endpoint:** `POST /api/v1/tests/generate`

**Request:**
```json
{
  "requirement": "User login with username and password",
  "test_type": "e2e",
  "num_tests": 3,
  "model": "mistralai/mixtral-8x7b-instruct"  // optional
}
```

**Response:**
```json
{
  "test_cases": [
    {
      "title": "...",
      "description": "...",
      ...
    }
  ],
  "metadata": {
    "requirement": "...",
    "model": "...",
    "tokens": 268
  }
}
```

**Features:**
- Authentication required
- Rate limiting (optional)
- Error handling
- Logging

---

### **Task 5: Test Case CRUD API Endpoints** (60 mins)

**File:** `backend/app/api/v1/endpoints/tests.py`

**Endpoints:**
1. `GET /api/v1/tests` - List all test cases
   - Query params: `skip`, `limit`, `test_type`, `status`, `priority`
   - Response: Paginated list

2. `POST /api/v1/tests` - Create test case
   - Body: `TestCaseCreate` schema
   - Response: Created test case

3. `GET /api/v1/tests/{id}` - Get single test case
   - Path param: `id`
   - Response: Test case details

4. `PUT /api/v1/tests/{id}` - Update test case
   - Path param: `id`
   - Body: `TestCaseUpdate` schema
   - Response: Updated test case

5. `DELETE /api/v1/tests/{id}` - Delete test case
   - Path param: `id`
   - Response: Success message

6. `GET /api/v1/tests/stats` - Get statistics
   - Response: Count by status, type, priority

**Features:**
- Authentication required
- User can only modify their own tests (or admin)
- Input validation
- Error handling
- OpenAPI documentation

---

### **Task 6: API Router Integration** (15 mins)

**File:** `backend/app/api/v1/api.py`

**Updates:**
- Import test generation router
- Import tests CRUD router
- Add to API router

**File:** `backend/app/main.py`

**Updates:**
- Ensure routers are included
- Test API documentation at `/docs`

---

### **Task 7: Testing & Verification** (45 mins)

**Create:** `backend/test_api_endpoints.py`

**Tests:**
1. Test generation endpoint
   - Valid request
   - Invalid request
   - Authentication required
   
2. CRUD endpoints
   - Create test case
   - List test cases
   - Get test case by ID
   - Update test case
   - Delete test case
   - Filtering and pagination
   
3. Error cases
   - 401 Unauthorized
   - 404 Not Found
   - 400 Bad Request
   - 422 Validation Error

**Run:**
```powershell
cd backend
.\venv\Scripts\python.exe test_api_endpoints.py
```

---

## 🔧 **Implementation Order**

1. ✅ **Database Model** (TestCase)
2. ✅ **Pydantic Schemas** (validation)
3. ✅ **CRUD Operations** (database layer)
4. ✅ **API Endpoints** (REST API)
5. ✅ **Router Integration** (connect to app)
6. ✅ **Testing** (verify all works)
7. ✅ **Documentation** (OpenAPI/Swagger)

---

## 📝 **Files to Create**

### **New Files:**
1. `backend/app/models/test_case.py` - SQLAlchemy model
2. `backend/app/schemas/test_case.py` - Pydantic schemas
3. `backend/app/crud/test_case.py` - CRUD operations
4. `backend/app/api/v1/endpoints/test_generation.py` - Generation endpoint
5. `backend/app/api/v1/endpoints/tests.py` - CRUD endpoints
6. `backend/test_api_endpoints.py` - API testing script

### **Files to Modify:**
1. `backend/app/api/v1/api.py` - Add new routers
2. `backend/app/main.py` - Ensure integration
3. `backend/app/models/__init__.py` - Import TestCase model

---

## ✅ **Success Criteria**

- [ ] TestCase model created and migrated
- [ ] All schemas validate correctly
- [ ] CRUD operations work
- [ ] POST /api/v1/tests/generate returns test cases
- [ ] All CRUD endpoints working
- [ ] Authentication enforced
- [ ] API documentation generated
- [ ] All tests passing
- [ ] No errors in logs

---

## 🧪 **Testing Checklist**

### **Manual Testing (Swagger UI):**
1. Go to `http://localhost:8000/docs`
2. Authenticate using `/api/v1/auth/login`
3. Test `/api/v1/tests/generate` endpoint
4. Test `/api/v1/tests` CRUD endpoints
5. Verify responses match schemas

### **Automated Testing:**
```powershell
# Run all tests
.\venv\Scripts\python.exe test_api_endpoints.py

# Expected: All tests passing
```

---

## 📚 **API Documentation Preview**

### **OpenAPI/Swagger:**
- Auto-generated at `http://localhost:8000/docs`
- ReDoc at `http://localhost:8000/redoc`
- OpenAPI JSON at `http://localhost:8000/openapi.json`

### **Endpoints Summary:**
```
POST   /api/v1/tests/generate     # Generate test cases with LLM
GET    /api/v1/tests               # List all test cases
POST   /api/v1/tests               # Create a test case
GET    /api/v1/tests/{id}          # Get test case by ID
PUT    /api/v1/tests/{id}          # Update test case
DELETE /api/v1/tests/{id}          # Delete test case
GET    /api/v1/tests/stats         # Get statistics
```

---

## 🚨 **Potential Issues & Solutions**

### **Issue 1: JSON Field Support**
**Problem:** SQLite doesn't support JSON natively in older versions  
**Solution:** Use Text field with JSON serialization/deserialization

### **Issue 2: Enum Validation**
**Problem:** Enum values must match between model and schema  
**Solution:** Define enums in separate file, import in both

### **Issue 3: User Association**
**Problem:** Tests need to be associated with users  
**Solution:** Add `user_id` foreign key, validate in endpoints

### **Issue 4: Large Test Data**
**Problem:** test_data field can be large  
**Solution:** Add max size validation (e.g., 10KB limit)

---

## 💡 **Best Practices**

1. **Use Async Everywhere:**
   - `async def` for all endpoint functions
   - `await` for database operations

2. **Validate Early:**
   - Use Pydantic schemas for request validation
   - Return 422 for validation errors

3. **Error Handling:**
   - Use FastAPI's HTTPException
   - Return appropriate status codes
   - Include helpful error messages

4. **Security:**
   - Require authentication for all endpoints
   - Validate user ownership before updates/deletes
   - Sanitize inputs

5. **Testing:**
   - Test happy path
   - Test error cases
   - Test edge cases
   - Test authentication

---

## 📊 **Estimated Time**

| Task | Time | Cumulative |
|------|------|------------|
| Database Models | 30 min | 30 min |
| Pydantic Schemas | 30 min | 1 hour |
| CRUD Operations | 45 min | 1h 45m |
| Generation Endpoint | 45 min | 2h 30m |
| CRUD Endpoints | 60 min | 3h 30m |
| Router Integration | 15 min | 3h 45m |
| Testing & Verification | 45 min | 4h 30m |

**Total:** ~4.5 hours

---

## 🎯 **Definition of Done**

- [ ] All code committed to `backend-dev-sprint-2` branch
- [ ] All tests passing
- [ ] API documentation complete
- [ ] No linter errors
- [ ] README updated if needed
- [ ] Day 3 completion report created

---

**Ready to start Day 3?** 🚀

Let's build the database and API layer!

