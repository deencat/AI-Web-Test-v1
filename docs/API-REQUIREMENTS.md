# API Requirements Document
**Project:** AI Web Test v1.0  
**Version:** 1.0  
**Date:** November 11, 2025  
**Purpose:** Define backend API endpoints based on frontend implementation

---

## Overview

This document specifies the RESTful API endpoints required by the frontend application. All request/response formats are derived from the frontend mock data structures implemented in Design Mode (Day 1-2).

**Base URL:** `http://localhost:8000/api`

---

## Authentication Endpoints

### POST /auth/login
**Description:** Authenticate user and return JWT token

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "role": "string"
  },
  "token": "string (JWT)"
}
```

**Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": "Invalid credentials"
}
```

---

## Dashboard Endpoints

### GET /dashboard/stats
**Description:** Get dashboard statistics

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "total_tests": 156,
  "passed": 142,
  "failed": 8,
  "running": 6,
  "active_agents": 4,
  "pass_rate": 91.0,
  "last_run": "2025-11-01T13:30:00Z"
}
```

### GET /dashboard/recent-tests
**Description:** Get recent test results (limit: 5)

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "tests": [
    {
      "id": "TEST-001",
      "name": "Login Flow Test",
      "description": "Test the Three Hong Kong customer login flow",
      "status": "passed",
      "priority": "high",
      "agent": "Explorer Agent",
      "created_at": "2025-11-01T10:00:00Z",
      "execution_time": 45.2
    }
  ]
}
```

### GET /dashboard/agent-activity
**Description:** Get current agent activity status

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "agents": [
    {
      "id": "1",
      "agent": "Explorer Agent",
      "status": "active",
      "current_task": "Generating test cases for checkout flow",
      "last_activity": "2025-11-10T10:30:00Z"
    }
  ]
}
```

---

## Test Case Endpoints

### GET /tests
**Description:** Get all test cases with optional filtering

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
- `status` (optional): Filter by status (passed, failed, pending, running)
- `priority` (optional): Filter by priority (high, medium, low)
- `agent` (optional): Filter by agent name
- `limit` (optional): Limit results (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response (200 OK):**
```json
{
  "tests": [
    {
      "id": "TEST-001",
      "name": "Login Flow Test",
      "description": "Test the Three Hong Kong customer login flow",
      "status": "passed",
      "priority": "high",
      "agent": "Explorer Agent",
      "created_at": "2025-11-01T10:00:00Z",
      "execution_time": 45.2
    }
  ],
  "total": 156,
  "limit": 100,
  "offset": 0
}
```

### GET /tests/{test_id}
**Description:** Get detailed information for a specific test

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "id": "TEST-001",
  "name": "Login Flow Test",
  "description": "Test the Three Hong Kong customer login flow",
  "status": "passed",
  "priority": "high",
  "agent": "Explorer Agent",
  "created_at": "2025-11-01T10:00:00Z",
  "execution_time": 45.2,
  "steps": [
    {
      "step_number": 1,
      "action": "Navigate to login page",
      "expected_result": "Login form displayed",
      "actual_result": "Login form displayed",
      "status": "passed"
    }
  ],
  "screenshots": [
    {
      "step_number": 1,
      "url": "https://storage.example.com/screenshots/test-001-step-1.png"
    }
  ]
}
```

### POST /tests
**Description:** Create a new test case

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (required)",
  "description": "string (required)",
  "priority": "high | medium | low",
  "agent": "string",
  "steps": [
    {
      "action": "string",
      "expected_result": "string"
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": "TEST-157",
  "name": "New Test",
  "description": "Test description",
  "status": "pending",
  "priority": "medium",
  "agent": "Explorer Agent",
  "created_at": "2025-11-11T10:00:00Z"
}
```

### PUT /tests/{test_id}
**Description:** Update a test case

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "priority": "high | medium | low (optional)",
  "status": "passed | failed | pending | running (optional)"
}
```

**Response (200 OK):**
```json
{
  "id": "TEST-001",
  "name": "Updated Test Name",
  "description": "Updated description",
  "status": "passed",
  "priority": "high",
  "updated_at": "2025-11-11T10:00:00Z"
}
```

### DELETE /tests/{test_id}
**Description:** Delete a test case

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (204 No Content)**

---

## Knowledge Base Endpoints

### GET /knowledge-base/documents
**Description:** Get all knowledge base documents with optional filtering

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
- `category` (optional): Filter by category
- `search` (optional): Search in name, description, tags
- `limit` (optional): Limit results (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response (200 OK):**
```json
{
  "documents": [
    {
      "id": "KB-001",
      "name": "Three HK Login Flow Guide.pdf",
      "category": "System Guide",
      "document_type": "system_guide",
      "file_size": "2.4 MB",
      "uploaded_by": "QA Manager",
      "uploaded_at": "2025-11-05T09:30:00Z",
      "tags": ["login", "authentication", "three-hk"],
      "description": "Complete guide for Three Hong Kong customer login flow"
    }
  ],
  "total": 15,
  "limit": 100,
  "offset": 0
}
```

### GET /knowledge-base/documents/{doc_id}
**Description:** Get a specific knowledge base document details

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "id": "KB-001",
  "name": "Three HK Login Flow Guide.pdf",
  "category": "System Guide",
  "document_type": "system_guide",
  "file_size": "2.4 MB",
  "file_path": "s3://bucket/kb-documents/KB-001.pdf",
  "uploaded_by": "QA Manager",
  "uploaded_at": "2025-11-05T09:30:00Z",
  "tags": ["login", "authentication", "three-hk"],
  "description": "Complete guide for Three Hong Kong customer login flow",
  "download_url": "https://storage.example.com/kb-documents/KB-001.pdf?token=..."
}
```

### POST /knowledge-base/documents
**Description:** Upload a new knowledge base document

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data
```

**Request Body (multipart/form-data):**
```
file: binary (PDF, DOCX, TXT, etc.)
name: string
category: string
document_type: system_guide | product | process | reference
description: string (optional)
tags: array of strings (optional)
```

**Response (201 Created):**
```json
{
  "id": "KB-016",
  "name": "New Document.pdf",
  "category": "System Guide",
  "document_type": "system_guide",
  "file_size": "1.5 MB",
  "uploaded_by": "Current User",
  "uploaded_at": "2025-11-11T10:00:00Z",
  "upload_status": "success"
}
```

### DELETE /knowledge-base/documents/{doc_id}
**Description:** Delete a knowledge base document

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (204 No Content)**

### GET /knowledge-base/categories
**Description:** Get all knowledge base categories with document counts

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "categories": [
    {
      "id": "1",
      "name": "System Guide",
      "count": 5,
      "color": "blue",
      "description": "System user guides and technical documentation"
    }
  ],
  "total": 4
}
```

### POST /knowledge-base/categories
**Description:** Create a new knowledge base category

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (required)",
  "color": "blue | green | purple | orange | gray (optional, default: gray)",
  "description": "string (optional)"
}
```

**Response (201 Created):**
```json
{
  "id": "5",
  "name": "New Category",
  "count": 0,
  "color": "blue",
  "description": "Category description"
}
```

### GET /knowledge-base/stats
**Description:** Get knowledge base statistics

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "total_documents": 15,
  "total_size": "45.6 MB",
  "categories": 4,
  "last_upload": "2025-11-05T09:30:00Z"
}
```

---

## Settings Endpoints

### GET /settings
**Description:** Get current application settings

**Headers:**
```
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "general": {
    "project_name": "AI Web Test v1.0",
    "default_timeout": 30
  },
  "notifications": {
    "email_notifications": true,
    "slack_notifications": false,
    "test_failure_alerts": true
  },
  "agent_config": {
    "model": "claude-3-opus-20240229",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "api": {
    "backend_url": "http://localhost:8000/api",
    "openrouter_key": "sk-or-••••••••••••••••••••••••••••"
  }
}
```

### PUT /settings
**Description:** Update application settings

**Headers:**
```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "general": {
    "project_name": "string (optional)",
    "default_timeout": number (optional)
  },
  "notifications": {
    "email_notifications": boolean (optional),
    "slack_notifications": boolean (optional),
    "test_failure_alerts": boolean (optional)
  },
  "agent_config": {
    "model": "string (optional)",
    "temperature": number (optional, 0.0-1.0)",
    "max_tokens": number (optional)
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Settings updated successfully",
  "updated_at": "2025-11-11T10:00:00Z"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid request parameters",
  "details": {
    "field_name": "error description"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "request_id": "uuid"
}
```

---

## Common Response Headers

All responses include:
```
Content-Type: application/json
X-Request-ID: uuid
X-Rate-Limit-Limit: 1000
X-Rate-Limit-Remaining: 999
X-Rate-Limit-Reset: 1699999999
```

---

## Authentication

All endpoints (except `/auth/login`) require JWT authentication:

**Header Format:**
```
Authorization: Bearer <jwt_token>
```

**Token Expiration:** 24 hours  
**Refresh Token:** Not implemented in MVP (Phase 1)

---

## Rate Limiting

- **Rate Limit:** 1000 requests per hour per user
- **Burst Limit:** 100 requests per minute
- **Response Header:** `X-Rate-Limit-*` headers included in all responses

---

## Pagination

Endpoints supporting pagination use:
- `limit`: Number of items per page (default: 100, max: 1000)
- `offset`: Number of items to skip (default: 0)

**Response includes:**
```json
{
  "items": [...],
  "total": number,
  "limit": number,
  "offset": number
}
```

---

## File Upload Specifications

### Supported File Types
- **PDF:** `.pdf`
- **Word:** `.doc`, `.docx`
- **Text:** `.txt`, `.md`
- **Images:** `.png`, `.jpg`, `.jpeg` (for screenshots)

### Size Limits
- **Max File Size:** 50 MB
- **Max Files Per Request:** 1

### Storage
- **Backend:** FastAPI file upload handling
- **Storage:** S3/MinIO object storage
- **URL Generation:** Presigned URLs for downloads (expires in 1 hour)

---

## WebSocket Endpoints (Future - Phase 2)

### WS /ws/test-execution/{test_id}
**Description:** Real-time test execution updates

**Message Format:**
```json
{
  "event": "step_completed | test_completed | error",
  "data": {
    "step_number": 1,
    "status": "passed | failed",
    "message": "string",
    "timestamp": "ISO 8601"
  }
}
```

---

## Implementation Priority

### Phase 1 (Sprint 1-4) - MVP
1. ✅ Authentication endpoints
2. ✅ Dashboard stats and recent tests
3. ✅ Test case CRUD operations
4. ✅ Knowledge base document CRUD
5. ✅ Settings management

### Phase 2 (Sprint 5-8) - Enhanced
1. ⏳ WebSocket for real-time updates
2. ⏳ Advanced filtering and search
3. ⏳ Batch operations
4. ⏳ Export/import functionality

### Phase 3 (Sprint 9-12) - Enterprise
1. ⏳ CI/CD integration endpoints
2. ⏳ JIRA integration
3. ⏳ Webhook notifications
4. ⏳ Advanced analytics

---

## Development Notes

1. **Mock Data Alignment:** All response formats match frontend mock data structures
2. **Validation:** Use Pydantic models for request/response validation
3. **Error Handling:** Consistent error response format across all endpoints
4. **Logging:** Log all requests with request ID for traceability
5. **Testing:** Each endpoint should have integration tests
6. **Documentation:** Auto-generate OpenAPI/Swagger docs from FastAPI

---

**Next Steps for Backend Developer:**
1. Review this specification
2. Create Pydantic models matching these structures
3. Implement endpoints in FastAPI
4. Add authentication middleware
5. Test against frontend application
6. Update OpenAPI documentation

---

**Document Version:** 1.0  
**Last Updated:** November 11, 2025  
**Maintained By:** Development Team

