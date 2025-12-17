"""Debug session API endpoints for Local Persistent Browser Debug Mode."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.debug_session import DebugSessionStatus
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
    DebugSessionListResponse
)
from app.services.debug_session_service import get_debug_session_service
from app.services.user_settings_service import UserSettingsService
from app.crud import debug_session as crud_debug

router = APIRouter()


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
        # Get user's execution settings (for correct model configuration)
        settings_service = UserSettingsService()
        user_config = settings_service.get_provider_config(
            db=db,
            user_id=current_user.id,
            config_type="execution"
        )
        
        # Start debug session
        session = await debug_service.start_session(
            db=db,
            user_id=current_user.id,
            request=request,
            user_config=user_config
        )
        
        # Build DevTools URL if available
        devtools_url = None
        if session.browser_port:
            devtools_url = f"http://localhost:{session.browser_port}"
        elif session.browser_pid:
            devtools_url = "Browser DevTools opened automatically (check browser window)"
        
        # Build response message
        if request.mode == "auto":
            message = (
                f"Debug session started with AUTO mode. "
                f"AI is executing {session.prerequisite_steps_count} prerequisite steps. "
                f"This will take approximately {session.prerequisite_steps_count * 6} seconds."
            )
        else:
            message = (
                f"Debug session started with MANUAL mode. "
                f"Please complete {session.prerequisite_steps_count} setup steps manually. "
                f"Use GET /debug/{session.session_id}/instructions to view steps."
            )
        
        return DebugSessionStartResponse(
            session_id=session.session_id,
            mode=session.mode,
            status=session.status,
            target_step_number=session.target_step_number,
            prerequisite_steps_count=session.prerequisite_steps_count,
            message=message,
            devtools_url=devtools_url
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
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
