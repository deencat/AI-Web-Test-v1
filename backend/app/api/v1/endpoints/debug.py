"""Debug session API endpoints for Local Persistent Browser Debug Mode."""
from typing import Optional
import logging
import traceback
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.debug_session import DebugSessionStatus, DebugMode
from app.schemas.debug_session import (
    DebugSessionStartRequest,
    DebugSessionStartResponse,
    DebugStepExecuteRequest,
    DebugStepExecuteResponse,
    DebugSessionStatusResponse,
    DebugSessionStopRequest,
    DebugSessionStopResponse,
    DebugSessionInstructionsResponse,
    DebugSessionConfirmSetupRequest,
    DebugSessionConfirmSetupResponse,
    DebugSessionListResponse,
    DebugNextStepResponse
)
from app.services.debug_session_service import get_debug_session_service
from app.services.user_settings_service import UserSettingsService
from app.crud import debug_session as crud_debug

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/debug/start", response_model=DebugSessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_debug_session(
    request: DebugSessionStartRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Start a new debug session for a specific test execution step.
    
    **Authentication required**
    
    Creates a persistent browser session with userDataDir for debugging individual steps.
    
    **Modes:**
    - **auto**: AI executes prerequisite steps automatically (~600 tokens, 6 seconds)
    - **manual**: User follows manual instructions (0 tokens, 2-3 minutes)
    
    **Request Body:**
    - `execution_id`: Test execution ID to debug
    - `target_step_number`: Step number to debug (1-based)
    - `mode`: Debug mode (auto or manual)
    
    **Example:**
    ```json
    {
        "execution_id": 123,
        "target_step_number": 7,
        "mode": "auto"
    }
    ```
    """
    debug_service = get_debug_session_service()
    
    try:
        logger.info(f"Starting debug session for user {current_user.id}, execution {request.execution_id}, step {request.target_step_number}, mode {request.mode}")
        
        # Get user's execution settings (for correct model configuration)
        settings_service = UserSettingsService()
        logger.debug(f"Fetching user config for user {current_user.id}")
        user_config = settings_service.get_provider_config(
            db=db,
            user_id=current_user.id,
            config_type="execution"
        )
        logger.debug(f"User config retrieved: {user_config}")
        
        # Start debug session
        logger.info(f"Calling debug_service.start_session...")
        session = await debug_service.start_session(
            db=db,
            user_id=current_user.id,
            request=request,
            user_config=user_config
        )
        logger.info(f"Debug session created successfully: {session.session_id}")
        
        # Build DevTools URL if available
        devtools_url = None
        if session.browser_port:
            devtools_url = f"http://localhost:{session.browser_port}"
        elif session.browser_pid:
            devtools_url = "Browser DevTools opened automatically (check browser window)"
        
        # Build response message
        if request.mode == "auto":
            if request.skip_prerequisites:
                message = (
                    f"Debug session started with AUTO mode (prerequisites skipped). "
                    f"Browser ready for debugging step {session.target_step_number}"
                    + (f" to {session.end_step_number}." if session.end_step_number else ".")
                )
            else:
                message = (
                    f"Debug session started with AUTO mode. "
                    f"AI is executing {session.prerequisite_steps_count} prerequisite steps. "
                    f"This will take approximately {session.prerequisite_steps_count * 6} seconds."
                )
        else:
            if request.skip_prerequisites:
                message = (
                    f"Debug session started with MANUAL mode (prerequisites skipped). "
                    f"Using current browser state. Ready to debug step {session.target_step_number}"
                    + (f" to {session.end_step_number}." if session.end_step_number else ".")
                )
            else:
                message = (
                    f"Debug session started with MANUAL mode. "
                    f"Please complete {session.prerequisite_steps_count} setup steps manually. "
                    f"Use GET /debug/{session.session_id}/instructions to view steps."
                )
        
        # Add range info to message if applicable
        if session.end_step_number:
            message += f" Debugging step range: {session.target_step_number} to {session.end_step_number}."
        
        return DebugSessionStartResponse(
            session_id=session.session_id,
            mode=session.mode,
            status=session.status,
            target_step_number=session.target_step_number,
            end_step_number=session.end_step_number,
            prerequisite_steps_count=session.prerequisite_steps_count,
            skip_prerequisites=session.skip_prerequisites,
            message=message,
            devtools_url=devtools_url
        )
        
    except ValueError as e:
        logger.error(f"ValueError starting debug session: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"CRITICAL ERROR starting debug session: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        logger.error(f"Request details - execution_id: {request.execution_id}, target_step: {request.target_step_number}, mode: {request.mode}")
        logger.error(f"User ID: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start debug session: {str(e)}"
        )


@router.post("/debug/execute-step", response_model=DebugStepExecuteResponse)
async def execute_debug_step(
    request: DebugStepExecuteRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Execute the target step in an active debug session.
    
    **Authentication required**
    
    Executes the target step that user wants to debug. Can be called multiple times
    to iterate on the same step.
    
    **Request Body:**
    - `session_id`: Debug session ID
    
    **Example:**
    ```json
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    """
    debug_service = get_debug_session_service()
    
    try:
        result = await debug_service.execute_target_step(
            db=db,
            session_id=request.session_id,
            user_id=current_user.id
        )
        
        # Get updated session info
        session = crud_debug.get_debug_session(db, request.session_id)
        
        return DebugStepExecuteResponse(
            session_id=request.session_id,
            step_number=session.target_step_number,
            success=result["success"],
            error_message=result.get("error"),
            screenshot_path=result.get("screenshot_path"),
            duration_seconds=result.get("duration_seconds", 0.0),
            tokens_used=result.get("tokens_used", 0),
            iterations_count=session.iterations_count
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute debug step: {str(e)}"
        )


@router.post("/debug/{session_id}/execute-next", response_model=DebugNextStepResponse)
async def execute_next_debug_step(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Execute the next step in the debug session sequence.
    
    **Authentication required**
    
    Continues debugging on the same browser session, maintaining state
    (cookies, localStorage, page context) between steps. This enables
    multi-step debugging without restarting the browser.
    
    **Use Case:**
    - Debug steps 7, 8, 9 in sequence without losing form state
    - Test split field scenarios (HKID main + check digit)
    - Validate multi-step workflows with state dependencies
    
    **Path Parameters:**
    - `session_id`: Debug session ID
    
    **Response:**
    - `success`: Whether step executed successfully
    - `step_number`: Current step number that was executed
    - `step_description`: Description of the executed step
    - `has_more_steps`: Whether there are more steps to execute
    - `next_step_preview`: Description of next step (if available)
    - `total_steps`: Total number of steps in test case
    
    **Example:**
    ```bash
    # After starting debug session and executing target step 7
    POST /api/v1/debug/{session_id}/execute-next
    
    # Response shows step 8 executed, can continue to step 9
    {
      "success": true,
      "step_number": 8,
      "step_description": "Enter HKID check digit",
      "has_more_steps": true,
      "next_step_preview": "Click Submit button",
      "total_steps": 10
    }
    ```
    """
    debug_service = get_debug_session_service()
    
    try:
        result = await debug_service.execute_next_step(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        return DebugNextStepResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute next debug step: {str(e)}"
        )


@router.get("/debug/{session_id}/status", response_model=DebugSessionStatusResponse)
async def get_debug_session_status(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Get the status of a debug session.
    
    **Authentication required**
    
    Returns detailed information about the debug session including progress,
    token usage, and browser status.
    """
    session = crud_debug.get_debug_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debug session {session_id} not found"
        )
    
    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this debug session"
        )
    
    # Build DevTools URL if available
    devtools_url = None
    if session.browser_port:
        devtools_url = f"http://localhost:{session.browser_port}"
    elif session.browser_pid:
        devtools_url = "Browser DevTools opened automatically (check browser window)"
    
    return DebugSessionStatusResponse(
        session_id=session.session_id,
        mode=session.mode,
        status=session.status,
        target_step_number=session.target_step_number,
        prerequisite_steps_count=session.prerequisite_steps_count,
        current_step=session.current_step,
        setup_completed=session.setup_completed,
        tokens_used=session.tokens_used,
        iterations_count=session.iterations_count,
        started_at=session.started_at,
        setup_completed_at=session.setup_completed_at,
        last_activity_at=session.last_activity_at,
        ended_at=session.ended_at,
        error_message=session.error_message,
        devtools_url=devtools_url,
        browser_pid=session.browser_pid
    )


@router.post("/debug/stop", response_model=DebugSessionStopResponse)
async def stop_debug_session(
    request: DebugSessionStopRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Stop a debug session and cleanup browser resources.
    
    **Authentication required**
    
    Closes the browser and marks the debug session as completed.
    
    **Request Body:**
    - `session_id`: Debug session ID
    
    **Example:**
    ```json
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    """
    debug_service = get_debug_session_service()
    
    try:
        session = await debug_service.stop_session(
            db=db,
            session_id=request.session_id,
            user_id=current_user.id
        )
        
        # Calculate total duration
        duration_seconds = 0.0
        if session.ended_at and session.started_at:
            duration_seconds = (session.ended_at - session.started_at).total_seconds()
        
        return DebugSessionStopResponse(
            session_id=session.session_id,
            status=session.status,
            total_tokens_used=session.tokens_used,
            total_iterations=session.iterations_count,
            duration_seconds=duration_seconds,
            message=f"Debug session stopped. Used {session.tokens_used} tokens across {session.iterations_count} iterations."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop debug session: {str(e)}"
        )


@router.get("/debug/{session_id}/instructions", response_model=DebugSessionInstructionsResponse)
async def get_manual_setup_instructions(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Get manual setup instructions for a debug session (manual mode only).
    
    **Authentication required**
    
    Returns step-by-step instructions for manually completing prerequisite steps.
    Only available for sessions started in manual mode.
    """
    debug_service = get_debug_session_service()
    
    session = crud_debug.get_debug_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debug session {session_id} not found"
        )
    
    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this debug session"
        )
    
    # Verify manual mode
    if session.mode != "manual":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instructions only available for manual mode sessions"
        )
    
    try:
        instructions, summary = debug_service.get_manual_instructions(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        # Build DevTools URL
        devtools_url = None
        if session.browser_port:
            devtools_url = f"http://localhost:{session.browser_port}"
        elif session.browser_pid:
            devtools_url = "Browser DevTools opened automatically (check browser window)"
        
        # Estimate time (1 minute per 3 steps)
        estimated_time = max(2, len(instructions) // 3)
        
        return DebugSessionInstructionsResponse(
            session_id=session.session_id,
            mode=session.mode,
            target_step_number=session.target_step_number,
            prerequisite_steps=instructions,
            instructions_summary=summary,
            estimated_time_minutes=estimated_time,
            devtools_url=devtools_url
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate instructions: {str(e)}"
        )


@router.post("/debug/confirm-setup", response_model=DebugSessionConfirmSetupResponse)
async def confirm_manual_setup(
    request: DebugSessionConfirmSetupRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Confirm that manual setup steps have been completed.
    
    **Authentication required**
    
    Marks the debug session as ready for debugging the target step.
    Only available for manual mode sessions.
    
    **Request Body:**
    - `session_id`: Debug session ID
    - `setup_completed`: Whether user completed manual setup
    
    **Example:**
    ```json
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "setup_completed": true
    }
    ```
    """
    debug_service = get_debug_session_service()
    
    try:
        session = debug_service.confirm_manual_setup(
            db=db,
            session_id=request.session_id,
            user_id=current_user.id
        )
        
        return DebugSessionConfirmSetupResponse(
            session_id=session.session_id,
            status=session.status,
            message=(
                f"Manual setup confirmed. You can now debug step {session.target_step_number} "
                f"by calling POST /debug/execute-step"
            ),
            ready_for_debug=session.status == DebugSessionStatus.READY
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm setup: {str(e)}"
        )


@router.get("/debug/sessions", response_model=DebugSessionListResponse)
async def list_debug_sessions(
    status_filter: Optional[str] = Query(None, description="Filter by status (pending, ready, completed, failed, cancelled)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    List user's debug sessions with optional filtering.
    
    **Authentication required**
    
    Returns a paginated list of the user's debug sessions.
    
    **Query Parameters:**
    - `status_filter`: Filter by session status
    - `limit`: Maximum number of results (default: 50, max: 100)
    - `offset`: Number of results to skip (for pagination)
    """
    # Parse status filter
    status_enum = None
    if status_filter:
        try:
            status_enum = DebugSessionStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status_filter}"
            )
    
    # Get sessions
    sessions, total = crud_debug.get_user_debug_sessions(
        db=db,
        user_id=current_user.id,
        status=status_enum,
        limit=limit,
        offset=offset
    )
    
    return DebugSessionListResponse(
        total=total,
        sessions=sessions
    )


@router.post("/debug/standalone-browser", response_model=DebugSessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_standalone_browser(
    browser: str = Query("chromium", description="Browser type: chromium, firefox, or webkit"),
    headless: bool = Query(False, description="Run browser in headless mode"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    Start a standalone browser session for manual browsing/login (for browser profile export).
    
    **Authentication required**
    
    This endpoint creates a persistent browser session WITHOUT requiring an execution_id.
    Use this for:
    - Exporting browser profiles after manual login
    - Testing website navigation
    - Capturing session data (cookies, localStorage, sessionStorage)
    
    **Query Parameters:**
    - `browser`: Browser type (chromium, firefox, webkit) - default: chromium
    - `headless`: Run in headless mode - default: false
    
    **Returns:**
    - `session_id`: Unique session identifier (use this for profile export)
    - `browser_url`: DevTools URL (if available)
    - `message`: Instructions for next steps
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/debug/standalone-browser?browser=chromium&headless=false" \
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    
    **Workflow:**
    1. Call this endpoint to start browser
    2. Browser window opens automatically
    3. Manually navigate and log in to your website
    4. Use the returned `session_id` to sync profile via `/browser-profiles/{id}/sync`
    """
    debug_service = get_debug_session_service()
    
    try:
        logger.info(f"Starting standalone browser session for user {current_user.id}, browser {browser}, headless {headless}")
        
        # Generate unique session ID
        session_id = f"standalone_{uuid.uuid4().hex[:12]}"
        
        # Create browser instance
        from app.services.stagehand_factory import get_stagehand_adapter
        
        stagehand = get_stagehand_adapter(
            db=db,
            user_id=current_user.id,
            browser=browser,
            headless=headless
        )
        
        # Initialize browser with persistent context
        user_data_dir = debug_service.user_data_base / session_id
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initializing browser with userDataDir: {user_data_dir}")
        
        # Initialize persistent browser session (no test_id needed for standalone)
        browser_metadata = await stagehand.initialize_persistent(
            session_id=session_id,
            test_id=None,  # No test associated with standalone session
            user_id=current_user.id,
            db=db,
            user_config=None  # Use default config
        )
        
        # Store in active sessions
        debug_service.active_sessions[session_id] = stagehand
        logger.info(f"Standalone browser session {session_id} stored in active sessions")
        
        # Note: We don't create a DB record for standalone sessions because:
        # 1. They're temporary (only used for profile export)
        # 2. DebugSession model requires execution_id and target_step_number (not applicable here)
        # 3. The session is tracked in memory via debug_service.active_sessions
        
        logger.info(f"✅ Standalone browser session {session_id} created successfully")
        
        return DebugSessionStartResponse(
            session_id=session_id,
            mode=DebugMode.MANUAL,
            status=DebugSessionStatus.READY,
            target_step_number=None,  # No target step for standalone sessions
            prerequisite_steps_count=None,  # No prerequisites for standalone sessions
            message=(
                "Standalone browser session started! "
                "Navigate to your website and log in manually. "
                "Keep the browser window open, then use this session_id to export your browser profile."
            ),
            devtools_url=None  # Not exposing DevTools URL for standalone sessions
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start standalone browser: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start standalone browser: {str(e)}"
        )
