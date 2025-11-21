# Sprint 2 Day 4 - Knowledge Base System

**Date:** November 19, 2025  
**Status:** 📋 Planning → 🚀 Starting  
**Prerequisites:** ✅ Days 1-3 Complete

---

## 🎯 **Day 4 Goals**

Build the Knowledge Base (KB) system for document upload, storage, and retrieval.

**Deliverables:**
1. ✅ Database model for KB documents
2. ✅ File upload handling (PDF, DOCX, TXT)
3. ✅ Document storage and metadata
4. ✅ Category management
5. ✅ KB CRUD API endpoints
6. ✅ Full API documentation

---

## 📋 **Tasks Breakdown**

### **Task 1: Database Models** (30 mins)

**File:** `backend/app/models/kb_document.py`

**Requirements:**
- Create `KBDocument` SQLAlchemy model
- Create `KBCategory` model for categorization
- Fields for KBDocument:
  - `id`: Integer, primary key
  - `title`: String(255), required
  - `description`: Text, optional
  - `filename`: String(255), original filename
  - `file_path`: String(500), storage path
  - `file_type`: Enum (pdf, docx, txt, md)
  - `file_size`: Integer, bytes
  - `content`: Text, extracted text content
  - `category_id`: ForeignKey to KBCategory
  - `user_id`: ForeignKey to User
  - `created_at`: DateTime, auto
  - `updated_at`: DateTime, auto
  - `referenced_count`: Integer, default 0

- Fields for KBCategory:
  - `id`: Integer, primary key
  - `name`: String(100), required, unique
  - `description`: Text, optional
  - `color`: String(20), hex color
  - `icon`: String(50), optional

**Relationships:**
- User → KBDocument (one-to-many)
- KBCategory → KBDocument (one-to-many)

---

### **Task 2: Pydantic Schemas** (30 mins)

**File:** `backend/app/schemas/kb_document.py`

**Requirements:**
- `KBCategoryBase`: Base category schema
- `KBCategoryCreate`: For creating categories
- `KBCategoryResponse`: Category response
- `KBDocumentBase`: Base document schema
- `KBDocumentCreate`: For uploads
- `KBDocumentUpdate`: For updates
- `KBDocumentResponse`: Full document response
- `KBDocumentListResponse`: Paginated list
- `KBUploadResponse`: Upload result
- `KBStatistics`: Document statistics

**Validation:**
- File types: pdf, docx, txt, md
- Max file size: 10MB (configurable)
- Title: 1-255 characters
- Category validation

---

### **Task 3: File Upload Service** (45 mins)

**File:** `backend/app/services/file_upload.py`

**Requirements:**
- Handle multipart/form-data uploads
- Validate file type and size
- Generate unique filenames (UUID + original extension)
- Store files in `uploads/kb/` directory
- Extract text content from files:
  - PDF: Use PyPDF2 or pdfplumber
  - DOCX: Use python-docx
  - TXT/MD: Direct read
- Return file metadata

**Security:**
- Sanitize filenames
- Validate MIME types
- Check for malicious content (basic)
- Limit upload size

---

### **Task 4: CRUD Operations** (45 mins)

**File:** `backend/app/crud/kb_document.py`

**Requirements:**
- `create_category(db, category)` - Create category
- `get_categories(db)` - List all categories
- `create_document(db, document, user_id)` - Create document
- `get_document(db, doc_id)` - Get by ID
- `get_documents(db, filters, skip, limit)` - List with filters
- `update_document(db, doc_id, updates)` - Update metadata
- `delete_document(db, doc_id)` - Delete document + file
- `increment_reference_count(db, doc_id)` - Track usage
- `get_kb_statistics(db, user_id)` - Get stats

**Filtering:**
- By category
- By file type
- By user
- By date range
- Search by title/content

---

### **Task 5: KB API Endpoints** (60 mins)

**File:** `backend/app/api/v1/endpoints/kb.py`

**Endpoints:**

1. **`GET /api/v1/kb/categories`** - List categories
   - Returns all predefined + custom categories
   - No authentication required (read-only)

2. **`POST /api/v1/kb/categories`** - Create category (admin only)
   - Body: `KBCategoryCreate`
   - Response: Created category

3. **`POST /api/v1/kb/upload`** - Upload document
   - Multipart form data: file + metadata
   - Authentication required
   - Returns: Document ID + metadata

4. **`GET /api/v1/kb`** - List documents
   - Query params: category, file_type, search, skip, limit
   - Authentication required
   - Returns: Paginated list

5. **`GET /api/v1/kb/{id}`** - Get document details
   - Path param: document ID
   - Authentication required
   - Returns: Full document metadata + content preview

6. **`PUT /api/v1/kb/{id}`** - Update document metadata
   - Path param: document ID
   - Body: `KBDocumentUpdate` (title, description, category)
   - Authentication required
   - Returns: Updated document

7. **`DELETE /api/v1/kb/{id}`** - Delete document
   - Path param: document ID
   - Authentication required
   - Deletes file from storage
   - Returns: 204 No Content

8. **`GET /api/v1/kb/{id}/download`** - Download file
   - Path param: document ID
   - Authentication required
   - Returns: File stream

9. **`GET /api/v1/kb/stats`** - Get statistics
   - Authentication required
   - Returns: Total docs, by category, by type, total size

---

### **Task 6: Predefined Categories** (15 mins)

**File:** `backend/app/db/init_kb_categories.py`

**Predefined Categories:**
1. **CRM Systems** (color: #3B82F6, icon: users)
2. **Billing & Payment** (color: #10B981, icon: credit-card)
3. **5G Products** (color: #8B5CF6, icon: signal)
4. **Login Flows** (color: #F59E0B, icon: lock)
5. **API Documentation** (color: #EF4444, icon: code)
6. **User Guides** (color: #06B6D4, icon: book)
7. **Test Cases** (color: #EC4899, icon: check-circle)
8. **Bug Reports** (color: #DC2626, icon: alert-circle)

**Implementation:**
- Create on app startup (if not exists)
- Add to `init_db.py`

---

### **Task 7: Dependencies & Configuration** (15 mins)

**Update:** `backend/requirements.txt`

```txt
# Existing dependencies...

# File handling
PyPDF2==3.0.1          # PDF parsing
python-docx==1.1.0     # DOCX parsing
python-multipart==0.0.6 # File uploads
aiofiles==23.2.1       # Async file I/O
```

**Update:** `backend/app/core/config.py`

```python
# File upload settings
UPLOAD_DIR: str = "uploads"
KB_UPLOAD_DIR: str = "uploads/kb"
MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES: list[str] = ["pdf", "docx", "txt", "md"]
```

---

### **Task 8: Testing & Verification** (45 mins)

**Create:** `backend/test_kb_api.py`

**Tests:**
1. **Category Management:**
   - List predefined categories
   - Create custom category (admin)

2. **File Upload:**
   - Upload TXT file
   - Upload PDF file (if available)
   - Validate file size limit
   - Validate file type

3. **Document Management:**
   - List documents
   - Get document by ID
   - Update document metadata
   - Delete document
   - Filter by category
   - Search by title

4. **Statistics:**
   - Get KB statistics
   - Verify counts

5. **Authorization:**
   - User can only access their own docs
   - Admin can access all docs

**Run:**
```powershell
cd backend
.\venv\Scripts\python.exe test_kb_api.py
```

---

## 🔧 **Implementation Order**

1. ✅ **Install dependencies** (PyPDF2, python-docx, etc.)
2. ✅ **Database models** (KBDocument, KBCategory)
3. ✅ **Pydantic schemas** (validation)
4. ✅ **File upload service** (handle uploads)
5. ✅ **CRUD operations** (database layer)
6. ✅ **API endpoints** (REST API)
7. ✅ **Predefined categories** (init data)
8. ✅ **Router integration** (connect to app)
9. ✅ **Testing** (verify all works)
10. ✅ **Documentation** (update guides)

---

## 📁 **Files to Create**

### **New Files (7):**
1. `backend/app/models/kb_document.py` - Database models
2. `backend/app/schemas/kb_document.py` - Pydantic schemas
3. `backend/app/services/file_upload.py` - Upload service
4. `backend/app/crud/kb_document.py` - CRUD operations
5. `backend/app/api/v1/endpoints/kb.py` - API endpoints
6. `backend/app/db/init_kb_categories.py` - Category seeding
7. `backend/test_kb_api.py` - Testing script

### **Files to Modify (3):**
1. `backend/requirements.txt` - Add dependencies
2. `backend/app/core/config.py` - Add KB settings
3. `backend/app/api/v1/api.py` - Add KB router
4. `backend/app/db/init_db.py` - Add category init

---

## ✅ **Success Criteria**

- [ ] KBDocument and KBCategory models created
- [ ] File upload working (TXT, PDF, DOCX)
- [ ] Files stored in uploads/kb/ directory
- [ ] Text extraction working
- [ ] 9 API endpoints functional
- [ ] 8 predefined categories seeded
- [ ] All tests passing
- [ ] Authentication enforced
- [ ] Authorization working (user ownership)
- [ ] API documentation generated
- [ ] No errors in logs

---

## 🧪 **Testing Checklist**

### **Manual Testing (Swagger UI):**
1. Go to `http://localhost:8000/docs`
2. Authenticate with admin/admin123
3. Test category endpoints
4. Upload a TXT file
5. List documents
6. Get document details
7. Update document
8. Delete document
9. Get statistics

### **Automated Testing:**
```powershell
.\venv\Scripts\python.exe test_kb_api.py
# Expected: All tests passing
```

---

## 📊 **Estimated Time**

| Task | Time | Cumulative |
|------|------|------------|
| Dependencies | 15 min | 15 min |
| Database Models | 30 min | 45 min |
| Pydantic Schemas | 30 min | 1h 15m |
| File Upload Service | 45 min | 2h |
| CRUD Operations | 45 min | 2h 45m |
| API Endpoints | 60 min | 3h 45m |
| Predefined Categories | 15 min | 4h |
| Testing & Verification | 45 min | 4h 45m |

**Total:** ~4.75 hours (similar to Day 3)

---

## 🎯 **Definition of Done**

- [ ] All code committed to `backend-dev-sprint-2` branch
- [ ] All tests passing
- [ ] API documentation complete
- [ ] No linter errors
- [ ] File uploads working
- [ ] Text extraction working
- [ ] Day 4 completion report created

---

**Ready to start Day 4!** 🚀

Let's build the Knowledge Base system!

