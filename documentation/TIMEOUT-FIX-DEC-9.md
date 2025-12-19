# Test Generation Timeout Fix - December 9, 2025

## Issue
When generating test cases from the frontend, users experienced **timeout errors (30000ms exceeded)** even though OpenRouter API calls were being made successfully.

## Root Cause
**Timeout mismatch** between frontend and backend:
- **Frontend (Axios)**: 30 seconds timeout
- **Backend (OpenRouter API)**: 60 seconds timeout
- **AI Model Response Time**: Can take 40-90 seconds for complex test generation

This meant the frontend would timeout before the backend could receive and return the AI-generated test cases.

## Solution Applied

### 1. Frontend Timeout Increase
**File**: `frontend/src/services/api.ts`

Changed Axios timeout from **30s → 120s**:
```typescript
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // Increased from 30000ms to 120000ms (120 seconds)
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### 2. Backend Timeout Increase
**File**: `backend/app/services/openrouter.py`

Changed OpenRouter API client timeout from **60s → 90s**:
```python
async with httpx.AsyncClient(timeout=90.0) as client:  # Increased from 60.0
```

## Timeout Architecture (After Fix)

```
User Request → Frontend (120s timeout)
                    ↓
              Backend API (no timeout on route)
                    ↓
              OpenRouter Service (90s timeout)
                    ↓
              OpenRouter API (AI Model Processing)
                    ↓
              Response ← Back to User
```

**Safety margins**:
- Frontend has 120s to wait for backend
- Backend has 90s to wait for OpenRouter
- 30s buffer for processing and network overhead

## Testing
After applying this fix:
1. ✅ Backend still running on port 8000
2. ✅ Frontend restarted successfully
3. 🔄 Test generation requests should now complete without timeout

## Next Steps
1. Test the generation feature with a real requirement
2. Monitor response times in production
3. Consider adding:
   - Loading progress indicator in UI
   - Streaming responses for long operations
   - Retry logic with exponential backoff

## Files Modified
- `frontend/src/services/api.ts` - Increased Axios timeout to 120s
- `backend/app/services/openrouter.py` - Increased OpenRouter client timeout to 90s

## Sprint Context
- **Sprint**: 1-3 Integration Testing
- **Date**: December 9, 2025
- **Branch**: integration/sprint-3
- **Feature**: AI Test Generation
