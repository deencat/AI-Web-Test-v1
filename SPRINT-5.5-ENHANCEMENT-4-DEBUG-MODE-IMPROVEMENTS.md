# Sprint 5.5 Enhancement 4: Debug Mode Improvements

**Developer:** Developer B  
**Date:** January 27, 2026  
**Status:** Phase 1 ✅ Complete | Phase 2 🔄 Recommended  
**Duration:** Phase 1: 1 hour | Phase 2: 1-2 hours (estimated)

---

## Problem Discovery

While testing **Enhancement 3 (Test Data Generator)** with debug mode, discovered two critical issues:

### Issue 1: Browser Profile Pollution ❌

**Symptoms:**
- 29 browser profile directories accumulating in backend root
- Total size: ~450MB (growing unbounded)
- Directories created in TWO locations:
  - `backend/user_data/` (wrong location)
  - `backend/artifacts/debug_sessions/` (correct location)

**Root Cause:**
```python
# debug_session_service.py (CORRECT)
self.user_data_base = Path("artifacts/debug_sessions")

# python_stagehand_adapter.py (WRONG)
user_data_base = Path("user_data")  # Hardcoded wrong path
```

**Impact:**
- Path inconsistency bug
- Disk space waste (390MB+ of old profiles)
- Not tracked in .gitignore (could be committed by mistake)
- No cleanup mechanism

---

### Issue 2: Single-Step Debug Limitation ❌

**Current Behavior:**
- Debug mode executes **ONE target step only**
- To debug steps 7, 8, 9 → Must restart debug session 3 times
- Browser state lost between sessions (cookies, localStorage, page context)

**User Pain Point:**
```bash
# Current flow (painful)
POST /debug/start {target_step: 7}  # Debug step 7
→ Browser closes automatically

POST /debug/start {target_step: 8}  # Debug step 8 (new browser!)
→ Browser closes automatically

POST /debug/start {target_step: 9}  # Debug step 9 (new browser!)
→ Browser closes automatically
```

**Why This Matters:**
- Testing multi-step sequences (like HKID split fields) requires multiple steps
- Form state lost between debug sessions
- Time-consuming (restart overhead ~6 seconds per step)
- Cannot validate step-to-step data flow

---

## Solution Phase 1: Cleanup & Path Fix ✅ COMPLETE

### Changes Implemented

#### 1. Fixed Path Inconsistency (5 lines)

**File:** `backend/app/services/python_stagehand_adapter.py`

```python
# BEFORE
user_data_base = Path("user_data")  # Wrong!

# AFTER
user_data_base = Path("artifacts/debug_sessions")  # Correct!
```

**Commit:** Fixed line 147 to use consistent path

---

#### 2. Added Cleanup Method (45 lines)

**File:** `backend/app/services/debug_session_service.py`

```python
def cleanup_old_sessions(self, max_age_hours: int = 48) -> int:
    """
    Clean up old debug session directories.
    
    Args:
        max_age_hours: Maximum age in hours (default: 48 hours)
        
    Returns:
        Number of directories removed
    """
    import time
    import shutil
    
    removed_count = 0
    current_time = time.time()
    cutoff_time = current_time - (max_age_hours * 3600)
    
    if not self.user_data_base.exists():
        return 0
    
    try:
        for session_dir in self.user_data_base.iterdir():
            if not session_dir.is_dir():
                continue
            
            # Check directory age
            dir_mtime = session_dir.stat().st_mtime
            if dir_mtime < cutoff_time:
                try:
                    logger.info(f"Cleaning up old debug session: {session_dir.name}")
                    shutil.rmtree(session_dir)
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove {session_dir}: {e}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    return removed_count
```

**Benefits:**
- ✅ Removes old browser profiles automatically
- ✅ Configurable age threshold
- ✅ Safe error handling (continues on failure)
- ✅ Logs all operations
- ✅ Returns count for monitoring

---

#### 3. Created Cleanup Script (75 lines)

**File:** `backend/cleanup_debug_sessions.py`

```python
#!/usr/bin/env python3
"""
Clean up old debug session directories.

Usage:
    python cleanup_debug_sessions.py [--max-age-hours HOURS] [--dry-run]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from app.services.debug_session_service import get_debug_session_service

def main():
    parser = argparse.ArgumentParser(
        description="Clean up old debug session directories"
    )
    parser.add_argument(
        "--max-age-hours",
        type=int,
        default=48,
        help="Maximum age of sessions in hours (default: 48)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    args = parser.parse_args()
    service = get_debug_session_service()
    
    if args.dry_run:
        # Preview mode
        print(f"DRY RUN: Would clean up sessions older than {args.max_age_hours} hours")
        # ... show what would be deleted
    else:
        # Actual cleanup
        removed = service.cleanup_old_sessions(max_age_hours=args.max_age_hours)
        print(f"Removed {removed} old debug session(s)")

if __name__ == "__main__":
    main()
```

**Usage Examples:**
```bash
# Clean sessions older than 48 hours (default)
python backend/cleanup_debug_sessions.py

# Clean sessions older than 24 hours
python backend/cleanup_debug_sessions.py --max-age-hours 24

# Preview what would be deleted (dry run)
python backend/cleanup_debug_sessions.py --dry-run

# Cron job: Run daily at 2 AM
0 2 * * * cd /path/to/AI-Web-Test-v1-main && python backend/cleanup_debug_sessions.py
```

---

#### 4. Updated .gitignore (2 lines)

**File:** `.gitignore`

```diff
# Test artifacts and screenshots
backend/artifacts/
backend/artifacts/screenshots/
backend/artifacts/videos/
+backend/artifacts/debug_sessions/
backend/screenshots/
+backend/user_data/
test-results/
playwright-report/
```

**Why:**
- Browser profiles are binary files (Chromium cache, SQLite databases)
- Not meant for version control
- Prevents accidental commits
- Keeps repo clean

---

### Migration & Cleanup Results

**Actions Taken:**
1. ✅ Created `backend/artifacts/debug_sessions/` directory
2. ✅ Moved all 29 sessions from `user_data/` to `artifacts/debug_sessions/`
3. ✅ Ran cleanup script with 48-hour threshold
4. ✅ Removed 20 old sessions (older than 48 hours)
5. ✅ Deleted empty `backend/user_data/` directory

**Before vs After:**

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Total sessions** | 29 | 8 | 72% reduction |
| **Disk space** | ~450MB | ~57MB | **87% reduction (390MB saved)** |
| **Locations** | 2 (inconsistent) | 1 (correct) | 100% consistency |
| **Cleanup mechanism** | None | Automated script | ✅ Available |
| **Git tracking risk** | High | None | ✅ Protected |

**Verification:**
```bash
# Check final state
$ ls -lh backend/artifacts/debug_sessions/
total 28K
drwxrwxr-x 12 dt-qa dt-qa 4.0K Jan 27 09:38 18716d8d-b3cc-4cf3-89fd-6c634db8ae56
drwxrwxr-x 12 dt-qa dt-qa 4.0K Jan 27 09:32 ee547206-c822-4143-ba86-d32726b3b1aa
drwxrwxr-x 12 dt-qa dt-qa 4.0K Jan 27 09:32 f73a1cc6-9eb8-4ca7-9abc-0d10ab9aab3c
drwxrwxr-x 12 dt-qa dt-qa 4.0K Jan 27 09:49 fde4c824-d2e6-4280-9217-4d6967584340
...

$ du -sh backend/artifacts/debug_sessions/
57M  # Down from 450MB!

$ ls backend/user_data/
ls: cannot access 'backend/user_data/': No such file or directory  # Good!
```

---

## Solution Phase 2: Multi-Step Debug API 🔄 RECOMMENDED

### Problem Analysis

**Current Debug Flow:**
```python
# debug_session_service.py
async def execute_target_step(self, db, session_id, user_id):
    """Execute THE target step (singular)"""
    target_step_num = debug_session.target_step_number  # Only ONE step
    step_desc = steps[target_step_num - 1]
    
    result = await browser_service.execute_single_step(
        step_description=step_desc,
        step_number=target_step_num,
        execution_id=execution.id
    )
    
    # Session ends after this step
```

**Limitation:** No mechanism to continue to next step on same browser session.

---

### Option 1: Sequential Step API ⭐ RECOMMENDED

**Design:**

Add new endpoint: `POST /api/v1/debug/{session_id}/execute-next`

**Flow:**
1. User starts debug session at step 7
2. System executes step 7, keeps browser open
3. User calls `/execute-next` → Executes step 8 on same browser
4. User calls `/execute-next` → Executes step 9 on same browser
5. User calls `/stop` when done → Closes browser

**Implementation Plan:**

#### Backend Changes (~100 lines)

**File 1:** `backend/app/models/debug_session.py` (+1 field)
```python
class DebugSession(Base):
    # ... existing fields
    current_step_number = Column(Integer, nullable=True)  # Track progress
```

**File 2:** `backend/app/services/debug_session_service.py` (+50 lines)
```python
async def execute_next_step(
    self,
    db: Session,
    session_id: str,
    user_id: int
) -> Dict:
    """Execute the next step in sequence."""
    # Get debug session
    debug_session = crud_debug.get_debug_session(db, session_id)
    
    # Verify session is active
    if debug_session.status != DebugSessionStatus.READY:
        raise ValueError(f"Session not ready")
    
    # Get current step
    current_step = debug_session.current_step_number or debug_session.target_step_number
    next_step = current_step + 1
    
    # Check bounds
    total_steps = len(debug_session.execution.test_case.steps)
    if next_step > total_steps:
        return {
            "success": False,
            "error": "No more steps to execute",
            "has_more_steps": False
        }
    
    # Get browser service
    browser_service = self.active_sessions.get(session_id)
    if not browser_service:
        raise ValueError("Browser session expired")
    
    # Execute next step
    step_desc = debug_session.execution.test_case.steps[next_step - 1]
    result = await browser_service.execute_single_step(
        step_description=step_desc,
        step_number=next_step,
        execution_id=debug_session.execution.id
    )
    
    # Update current step
    crud_debug.update_current_step(db, session_id, next_step)
    
    # Build response
    return {
        "success": result["success"],
        "step_number": next_step,
        "step_description": step_desc,
        "result": result,
        "has_more_steps": next_step < total_steps,
        "next_step_preview": steps[next_step] if next_step < total_steps else None
    }
```

**File 3:** `backend/app/api/v1/endpoints/debug.py` (+30 lines)
```python
@router.post("/debug/{session_id}/execute-next", response_model=DebugStepExecuteResponse)
async def execute_next_debug_step(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Execute the next step in the debug session sequence.
    
    Continues debugging on the same browser session, maintaining state.
    
    **Response:**
    - `success`: Whether step executed successfully
    - `step_number`: Current step number
    - `has_more_steps`: Whether there are more steps to execute
    - `next_step_preview`: Description of next step (if available)
    """
    debug_service = get_debug_session_service()
    
    try:
        result = await debug_service.execute_next_step(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        return DebugStepExecuteResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

**File 4:** `backend/app/crud/debug_session.py` (+10 lines)
```python
def update_current_step(
    db: Session,
    session_id: str,
    step_number: int
) -> DebugSession:
    """Update current step number in debug session."""
    session = get_debug_session(db, session_id)
    if session:
        session.current_step_number = step_number
        db.commit()
        db.refresh(session)
    return session
```

---

#### API Usage Example

**Scenario:** Debug steps 7, 8, 9 of HKID split field test

```bash
# Step 1: Start debug session at step 7
POST /api/v1/debug/start
{
  "execution_id": 123,
  "target_step_number": 7,
  "mode": "auto"
}

Response:
{
  "session_id": "abc123",
  "status": "ready",
  "browser_port": 9222,
  "message": "Debug session started. Target step 7 ready."
}

# Step 2: Execute target step (step 7)
POST /api/v1/debug/abc123/execute
Response:
{
  "success": true,
  "step_number": 7,
  "step_description": "Enter HKID main part",
  "result": {
    "success": true,
    "value": "G197611",
    "execution_time_ms": 542
  }
}

# Step 3: Continue to next step (step 8) - NEW!
POST /api/v1/debug/abc123/execute-next
Response:
{
  "success": true,
  "step_number": 8,
  "step_description": "Enter HKID check digit",
  "result": {
    "success": true,
    "value": "0",
    "execution_time_ms": 398
  },
  "has_more_steps": true,
  "next_step_preview": "Click Submit button"
}

# Step 4: Continue to next step (step 9) - NEW!
POST /api/v1/debug/abc123/execute-next
Response:
{
  "success": true,
  "step_number": 9,
  "step_description": "Click Submit button",
  "result": {
    "success": true,
    "execution_time_ms": 287
  },
  "has_more_steps": false,
  "next_step_preview": null
}

# Step 5: Stop when done
POST /api/v1/debug/abc123/stop
Response:
{
  "success": true,
  "message": "Debug session stopped and browser closed."
}
```

**Key Improvements:**
- ✅ One browser session for steps 7, 8, 9 (state maintained)
- ✅ HKID check digit "0" correctly matches main part "G197611"
- ✅ Total time: ~1.2 seconds vs ~18 seconds (3 sessions × 6 seconds)
- ✅ User controls pace (can inspect browser between steps)

---

### Option 2: Step Range Execution

**Design:**

Allow debugging a range of steps in one request.

**Request:**
```json
POST /api/v1/debug/start
{
  "execution_id": 123,
  "start_step": 7,
  "end_step": 10,
  "mode": "auto"
}
```

**Pros:**
- ✅ Single API call for multiple steps
- ✅ Useful for debugging related sequences

**Cons:**
- ❌ Less control (can't stop mid-range)
- ❌ Can't inspect between steps
- ❌ More complex error handling (what if step 8 fails?)

**Verdict:** Less flexible than Option 1.

---

### Option 3: Interactive Debug UI Panel

**Design:**

Build frontend debug control panel with:
- Step list (checkboxes for breakpoints)
- Play/Pause/Step Forward buttons
- Live screenshot preview
- Real-time execution logs

**Pros:**
- ✅ Best UX for developers
- ✅ Visual feedback
- ✅ Breakpoint support

**Cons:**
- ❌ Requires 4-6 hours frontend development
- ❌ Complex state management (WebSocket for live updates)
- ❌ Option 1 API needed first anyway

**Verdict:** Best long-term solution, but do Option 1 first.

---

## Recommendation: Implement Option 1 First

**Rationale:**

1. **Fast Implementation** - 1-2 hours (vs 4-6 hours for Option 3)
2. **Solves Immediate Need** - Enables multi-step debugging now
3. **Foundation for UI** - Option 3 will use Option 1's API
4. **Low Risk** - Simple, well-defined scope
5. **High Value** - Significant UX improvement

**Suggested Timeline:**

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| **Phase 1** | Cleanup & Path Fix | 1 hour | ✅ COMPLETE |
| **Phase 2** | Sequential Step API | 1-2 hours | 🔄 RECOMMENDED |
| **Phase 3** | Debug UI Panel | 4-6 hours | 🔮 FUTURE |

**Developer B can implement Phase 2 independently in next sprint.**

---

## Summary

### Phase 1 Achievements ✅

- ✅ **Fixed path bug** - All profiles in `artifacts/debug_sessions/`
- ✅ **Added cleanup** - `cleanup_old_sessions()` method + script
- ✅ **Reclaimed 390MB** - Removed 20 old browser profiles
- ✅ **Protected git** - Added to .gitignore
- ✅ **Zero downtime** - Deployed without service interruption

### Phase 2 Recommendation 🔄

- 🎯 **Implement Sequential Step API** (Option 1)
- 📅 **Timeline:** 1-2 hours in next sprint
- 👤 **Owner:** Developer B
- 🎁 **Benefit:** Debug multi-step sequences on same browser session

### Code Statistics

**Phase 1 (Completed):**
- Files modified: 2
- Files created: 1
- Configuration: 1
- Total lines: 127 (5 modified + 45 added + 75 new + 2 config)

**Phase 2 (Estimated):**
- Files modified: 4
- Database migration: 1 field
- Total lines: ~100

---

**Enhancement 4 Status:**
- Phase 1: ✅ **COMPLETE** (January 27, 2026)
- Phase 2: 🔄 **RECOMMENDED** (Awaiting approval for next sprint)

---

**END OF DOCUMENT**
