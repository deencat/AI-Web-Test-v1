"""Debug Session Service for Local Persistent Browser Debug Mode."""
import asyncio
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.models.debug_session import DebugSession, DebugMode, DebugSessionStatus
from app.models.test_execution import TestExecution
from app.crud import debug_session as crud_debug
from app.crud import test_execution as crud_execution
from app.schemas.debug_session import (
    DebugSessionStartRequest,
    ManualSetupInstruction
)
from app.services.stagehand_factory import get_stagehand_adapter
from app.services.stagehand_adapter import StagehandAdapter


class DebugSessionService:
    """Service for managing debug sessions with persistent browsers."""
    
    def __init__(self):
        """Initialize debug session service."""
        # Track active sessions in memory: session_id -> browser instance
        self.active_sessions: Dict[str, StagehandAdapter] = {}
        
        # Base directory for user data dirs
        self.user_data_base = Path("artifacts/debug_sessions")
        self.user_data_base.mkdir(parents=True, exist_ok=True)
    
    async def start_session(
        self,
        db: Session,
        user_id: int,
        request: DebugSessionStartRequest,
        user_config: Optional[Dict] = None
    ) -> DebugSession:
        """
        Start a new debug session.
        
        Args:
            db: Database session
            user_id: User ID
            request: Debug session start request
            user_config: Optional user execution configuration
            
        Returns:
            DebugSession object
        """
        # Verify execution exists
        execution = crud_execution.get_execution(db, request.execution_id)
        if not execution:
            raise ValueError(f"Execution {request.execution_id} not found")
        
        # Verify target step exists
        if request.target_step_number < 1 or request.target_step_number > execution.total_steps:
            raise ValueError(
                f"Target step {request.target_step_number} out of range "
                f"(execution has {execution.total_steps} steps)"
            )
        
        # Verify end step if provided
        if request.end_step_number:
            if request.end_step_number < request.target_step_number:
                raise ValueError(
                    f"End step {request.end_step_number} must be >= start step {request.target_step_number}"
                )
            if request.end_step_number > execution.total_steps:
                raise ValueError(
                    f"End step {request.end_step_number} out of range "
                    f"(execution has {execution.total_steps} steps)"
                )
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create debug session record
        debug_session = crud_debug.create_debug_session(
            db=db,
            user_id=user_id,
            request=request,
            session_id=session_id
        )
        
        try:
            # Create user data directory for this session
            user_data_dir = self.user_data_base / session_id
            user_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize persistent browser using factory
            browser_service = get_stagehand_adapter(
                db=db,
                user_id=user_id,
                browser="chromium",
                headless=False,  # Always visible for debug mode
                screenshot_dir=f"artifacts/screenshots/debug_{session_id}"
            )
            
            try:
                browser_metadata = await browser_service.initialize_persistent(
                    session_id=session_id,
                    test_id=execution.test_case_id,
                    user_id=user_id,
                    db=db,
                    user_config=user_config
                )
            except Exception as browser_error:
                print(f"[ERROR] Failed to initialize persistent browser: {browser_error}")
                # Clean up and raise
                crud_debug.update_debug_session_status(
                    db=db,
                    session_id=session_id,
                    status=DebugSessionStatus.FAILED
                )
                raise ValueError(f"Failed to initialize browser: {str(browser_error)}")
            
            # Update session with browser info
            crud_debug.update_debug_session_browser_info(
                db=db,
                session_id=session_id,
                user_data_dir=str(user_data_dir),
                browser_port=browser_metadata.get("browser_port"),
                browser_pid=browser_metadata.get("browser_pid")
            )
            
            # Store browser instance in memory
            self.active_sessions[session_id] = browser_service
            
            # Execute prerequisite steps based on mode and skip_prerequisites flag
            # Note: For range debugging (target_step > 1), we MUST execute prerequisites
            # even in Manual mode, otherwise browser will be at homepage instead of target step
            should_auto_setup = (
                (request.mode == DebugMode.AUTO and not request.skip_prerequisites) or
                (request.target_step_number > 1 and not request.skip_prerequisites)
            )
            
            if should_auto_setup:
                # Execute steps 1 to target-1 with AI to reach the target step
                await self._execute_auto_setup(
                    db=db,
                    session_id=session_id,
                    execution=execution,
                    target_step=request.target_step_number,
                    browser_service=browser_service
                )
            else:
                # Skip prerequisites: Update status to ready
                # (Assumes user has already manually navigated to the target step)
                crud_debug.update_debug_session_status(
                    db=db,
                    session_id=session_id,
                    status=DebugSessionStatus.READY
                )
                # Mark setup as completed since we're skipping it
                if request.skip_prerequisites:
                    crud_debug.mark_setup_completed(db, session_id)
            
            # Refresh session from DB
            debug_session = crud_debug.get_debug_session(db, session_id)
            return debug_session
            
        except Exception as e:
            # Mark session as failed
            crud_debug.update_debug_session_status(
                db=db,
                session_id=session_id,
                status=DebugSessionStatus.FAILED,
                error_message=str(e)
            )
            
            # Cleanup browser if initialized
            if session_id in self.active_sessions:
                try:
                    await self.active_sessions[session_id].cleanup()
                except:
                    pass
                del self.active_sessions[session_id]
            
            raise
    
    async def _execute_auto_setup(
        self,
        db: Session,
        session_id: str,
        execution: TestExecution,
        target_step: int,
        browser_service: StagehandAdapter
    ):
        """
        Execute prerequisite steps automatically (auto mode).
        
        Args:
            db: Database session
            session_id: Debug session ID
            execution: Original test execution
            target_step: Target step number
            browser_service: Browser service instance (adapter)
        """
        # Update status to setup in progress
        crud_debug.update_debug_session_status(
            db=db,
            session_id=session_id,
            status=DebugSessionStatus.SETUP_IN_PROGRESS
        )
        
        # Get test case
        test_case = execution.test_case
        if not test_case:
            raise ValueError(f"Test case not found for execution {execution.id}")
        
        # Get base URL from execution
        base_url = execution.base_url or os.getenv("BASE_URL", "https://www.three.com.hk")
        
        # Parse steps
        import json
        steps = test_case.steps
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except:
                steps = [steps]
        elif not isinstance(steps, list):
            steps = []
        
        # Execute steps 1 to target-1
        prerequisite_steps = target_step - 1
        total_tokens = 0
        
        print(f"[DEBUG] Auto-setup: Executing {prerequisite_steps} prerequisite steps")
        
        # Verify browser page is ready
        if not browser_service.page:
            raise ValueError("Browser page not initialized")
        
        # Navigate to base URL first
        await browser_service.page.goto(base_url)
        await asyncio.sleep(1)
        
        for step_num in range(1, target_step):
            if step_num > len(steps):
                break
            
            step_desc = steps[step_num - 1]
            print(f"[DEBUG] Auto-setup step {step_num}/{prerequisite_steps}: {step_desc}")
            
            try:
                # Execute step
                result = await browser_service.execute_single_step(
                    step_description=step_desc,
                    step_number=step_num,
                    execution_id=execution.id
                )
                
                # Track tokens
                tokens_used = result.get("tokens_used", 100)
                total_tokens += tokens_used
                
                # Record step execution
                crud_debug.create_debug_step_execution(
                    db=db,
                    session_id=session_id,
                    step_number=step_num,
                    step_description=step_desc,
                    success=result["success"],
                    error_message=result.get("error"),
                    screenshot_path=result.get("screenshot_path"),
                    duration_seconds=result.get("duration_seconds"),
                    tokens_used=tokens_used
                )
                
                if not result["success"]:
                    raise Exception(f"Step {step_num} failed: {result.get('error')}")
                
            except Exception as e:
                # Mark session as failed
                crud_debug.update_debug_session_status(
                    db=db,
                    session_id=session_id,
                    status=DebugSessionStatus.FAILED,
                    error_message=f"Auto-setup failed at step {step_num}: {str(e)}"
                )
                raise
        
        # Update tokens used
        crud_debug.increment_debug_session_tokens(db, session_id, total_tokens)
        
        # Mark setup as completed
        crud_debug.mark_setup_completed(db, session_id)
        
        print(f"[DEBUG] Auto-setup complete. Tokens used: {total_tokens}")
    
    async def execute_target_step(
        self,
        db: Session,
        session_id: str,
        user_id: int
    ) -> Dict:
        """
        Execute the target step in a debug session.
        
        Args:
            db: Database session
            session_id: Debug session ID
            user_id: User ID (for authorization)
            
        Returns:
            Dict with execution result
        """
        # Get debug session
        debug_session = crud_debug.get_debug_session(db, session_id)
        if not debug_session:
            raise ValueError(f"Debug session {session_id} not found")
        
        # Verify ownership
        if debug_session.user_id != user_id:
            raise PermissionError("Not authorized to access this debug session")
        
        # Verify session is ready
        if debug_session.status not in [DebugSessionStatus.READY, DebugSessionStatus.EXECUTING]:
            raise ValueError(f"Debug session not ready (current status: {debug_session.status})")
        
        # Get browser service
        if session_id not in self.active_sessions:
            raise ValueError(f"Browser session {session_id} not found (may have expired)")
        
        browser_service = self.active_sessions[session_id]
        
        # Update status to executing
        crud_debug.update_debug_session_status(
            db=db,
            session_id=session_id,
            status=DebugSessionStatus.EXECUTING
        )
        
        try:
            # Get execution and test case
            execution = debug_session.execution
            test_case = execution.test_case
            
            # Parse steps
            import json
            steps = test_case.steps
            if isinstance(steps, str):
                try:
                    steps = json.loads(steps)
                except:
                    steps = [steps]
            elif not isinstance(steps, list):
                steps = []
            
            # Get target step description
            target_step_num = debug_session.target_step_number
            if target_step_num > len(steps):
                raise ValueError(f"Target step {target_step_num} out of range")
            
            step_desc = steps[target_step_num - 1]
            
            # Apply test data substitution (for {generate:hkid:main}, etc.)
            from app.services.execution_service import ExecutionService
            execution_service = ExecutionService(db)
            step_desc_substituted = execution_service._substitute_test_data_patterns(
                step_desc, 
                execution.id
            )
            logger.info(f"[DEBUG] Test data substitution: '{step_desc}' -> '{step_desc_substituted}'")
            
            # Execute target step with substituted description
            result = await browser_service.execute_single_step(
                step_description=step_desc_substituted,
                step_number=target_step_num,
                execution_id=execution.id
            )
            
            # Record step execution
            tokens_used = result.get("tokens_used", 100)
            crud_debug.create_debug_step_execution(
                db=db,
                session_id=session_id,
                step_number=target_step_num,
                step_description=step_desc,
                success=result["success"],
                error_message=result.get("error"),
                screenshot_path=result.get("screenshot_path"),
                duration_seconds=result.get("duration_seconds"),
                tokens_used=tokens_used
            )
            
            # Update session tracking
            crud_debug.increment_debug_session_tokens(db, session_id, tokens_used)
            crud_debug.increment_debug_session_iterations(db, session_id)
            
            # Update status back to ready
            crud_debug.update_debug_session_status(
                db=db,
                session_id=session_id,
                status=DebugSessionStatus.READY
            )
            
            return result
            
        except Exception as e:
            # Mark session as failed
            crud_debug.update_debug_session_status(
                db=db,
                session_id=session_id,
                status=DebugSessionStatus.FAILED,
                error_message=str(e)
            )
            raise
    
    async def execute_next_step(
        self,
        db: Session,
        session_id: str,
        user_id: int
    ) -> Dict:
        """
        Execute the next step in sequence (multi-step debugging).
        
        This enables debugging multiple consecutive steps on the same browser session,
        maintaining state (cookies, localStorage, page context) between steps.
        
        Args:
            db: Database session
            session_id: Debug session ID
            user_id: User ID (for authorization)
            
        Returns:
            Dict with execution result and navigation info:
            {
                "success": bool,
                "step_number": int,
                "step_description": str,
                "error_message": Optional[str],
                "screenshot_path": Optional[str],
                "duration_seconds": float,
                "tokens_used": int,
                "has_more_steps": bool,
                "next_step_preview": Optional[str],
                "total_steps": int
            }
        """
        # Get debug session
        debug_session = crud_debug.get_debug_session(db, session_id)
        if not debug_session:
            raise ValueError(f"Debug session {session_id} not found")
        
        # Verify ownership
        if debug_session.user_id != user_id:
            raise PermissionError("Not authorized to access this debug session")
        
        # Verify session is ready
        if debug_session.status not in [DebugSessionStatus.READY, DebugSessionStatus.EXECUTING]:
            raise ValueError(f"Debug session not ready (current status: {debug_session.status})")
        
        # Get browser service
        if session_id not in self.active_sessions:
            raise ValueError(f"Browser session {session_id} not found (may have expired)")
        
        browser_service = self.active_sessions[session_id]
        
        # Determine next step number
        # Priority: current_step + 1, or target_step_number if no current_step set
        if debug_session.current_step:
            next_step_num = debug_session.current_step + 1
        else:
            # First time executing after setup
            next_step_num = debug_session.target_step_number
        
        # Get execution and test case
        execution = debug_session.execution
        test_case = execution.test_case
        
        # Parse steps
        import json
        steps = test_case.steps
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except:
                steps = [steps]
        elif not isinstance(steps, list):
            steps = []
        
        total_steps = len(steps)
        
        # Check bounds
        if next_step_num > total_steps:
            return {
                "session_id": session_id,
                "success": False,
                "step_number": debug_session.current_step or debug_session.target_step_number,
                "step_description": "",
                "error_message": f"No more steps to execute (total: {total_steps})",
                "screenshot_path": None,
                "duration_seconds": 0.0,
                "tokens_used": 0,
                "has_more_steps": False,
                "next_step_preview": None,
                "total_steps": total_steps,
                "end_step_number": debug_session.end_step_number,
                "range_complete": True
            }
        
        # Check if we've reached the end of the range (if end_step_number is set)
        if debug_session.end_step_number and next_step_num > debug_session.end_step_number:
            return {
                "session_id": session_id,
                "success": True,
                "step_number": debug_session.current_step or debug_session.end_step_number,
                "step_description": "",
                "error_message": None,
                "screenshot_path": None,
                "duration_seconds": 0.0,
                "tokens_used": 0,
                "has_more_steps": False,
                "next_step_preview": None,
                "total_steps": total_steps,
                "end_step_number": debug_session.end_step_number,
                "range_complete": True
            }
        
        # Update status to executing
        crud_debug.update_debug_session_status(
            db=db,
            session_id=session_id,
            status=DebugSessionStatus.EXECUTING
        )
        
        try:
            # Get step description
            step_desc = steps[next_step_num - 1]
            
            # Apply test data substitution (for {generate:hkid:main}, etc.)
            from app.services.execution_service import ExecutionService
            execution_service = ExecutionService(db)
            step_desc_substituted = execution_service._substitute_test_data_patterns(
                step_desc, 
                execution.id
            )
            logger.info(f"[DEBUG] Multi-step: Executing step {next_step_num}: '{step_desc}' -> '{step_desc_substituted}'")
            
            # Execute step
            result = await browser_service.execute_single_step(
                step_description=step_desc_substituted,
                step_number=next_step_num,
                execution_id=execution.id
            )
            
            # Record step execution
            tokens_used = result.get("tokens_used", 100)
            crud_debug.create_debug_step_execution(
                db=db,
                session_id=session_id,
                step_number=next_step_num,
                step_description=step_desc,
                success=result["success"],
                error_message=result.get("error"),
                screenshot_path=result.get("screenshot_path"),
                duration_seconds=result.get("duration_seconds"),
                tokens_used=tokens_used
            )
            
            # Update session tracking
            crud_debug.increment_debug_session_tokens(db, session_id, tokens_used)
            crud_debug.increment_debug_session_iterations(db, session_id)
            crud_debug.update_current_step(db, session_id, next_step_num)
            
            # Update status back to ready
            crud_debug.update_debug_session_status(
                db=db,
                session_id=session_id,
                status=DebugSessionStatus.READY
            )
            
            # Determine if more steps available
            # If end_step_number is set, check against that; otherwise check against total_steps
            if debug_session.end_step_number:
                has_more = next_step_num < debug_session.end_step_number
                range_complete = next_step_num >= debug_session.end_step_number
            else:
                has_more = next_step_num < total_steps
                range_complete = False
            
            next_preview = steps[next_step_num] if (next_step_num < total_steps and has_more) else None
            
            # Build response
            return {
                "session_id": session_id,
                "success": result["success"],
                "step_number": next_step_num,
                "step_description": step_desc,
                "error_message": result.get("error"),
                "screenshot_path": result.get("screenshot_path"),
                "duration_seconds": result.get("duration_seconds", 0.0),
                "tokens_used": tokens_used,
                "has_more_steps": has_more,
                "next_step_preview": next_preview,
                "total_steps": total_steps,
                "end_step_number": debug_session.end_step_number,
                "range_complete": range_complete
            }
            
        except Exception as e:
            # Mark session as failed
            error_msg = str(e)
            crud_debug.update_debug_session_status(
                db=db,
                session_id=session_id,
                status=DebugSessionStatus.FAILED,
                error_message=error_msg
            )
            
            # Return error response instead of raising
            return {
                "session_id": session_id,
                "success": False,
                "step_number": next_step_num,
                "step_description": step_desc if 'step_desc' in locals() else "",
                "error_message": error_msg,
                "screenshot_path": None,
                "duration_seconds": 0.0,
                "tokens_used": 0,
                "has_more_steps": False,
                "next_step_preview": None,
                "total_steps": total_steps,
                "end_step_number": debug_session.end_step_number,
                "range_complete": False
            }
    
    async def stop_session(
        self,
        db: Session,
        session_id: str,
        user_id: int
    ) -> DebugSession:
        """
        Stop a debug session and cleanup browser.
        
        Args:
            db: Database session
            session_id: Debug session ID
            user_id: User ID (for authorization)
            
        Returns:
            Updated DebugSession object
        """
        # Get debug session
        debug_session = crud_debug.get_debug_session(db, session_id)
        if not debug_session:
            raise ValueError(f"Debug session {session_id} not found")
        
        # Verify ownership
        if debug_session.user_id != user_id:
            raise PermissionError("Not authorized to access this debug session")
        
        # Cleanup browser
        if session_id in self.active_sessions:
            try:
                await self.active_sessions[session_id].cleanup()
            except Exception as e:
                print(f"[DEBUG] Error cleaning up browser: {e}")
            
            del self.active_sessions[session_id]
        
        # Update session status
        debug_session = crud_debug.update_debug_session_status(
            db=db,
            session_id=session_id,
            status=DebugSessionStatus.COMPLETED
        )
        
        return debug_session
    
    def get_manual_instructions(
        self,
        db: Session,
        session_id: str,
        user_id: int
    ) -> tuple[List[ManualSetupInstruction], str]:
        """
        Get manual setup instructions for a debug session.
        
        Args:
            db: Database session
            session_id: Debug session ID
            user_id: User ID (for authorization)
            
        Returns:
            Tuple of (instructions_list, summary_text)
        """
        # Get debug session
        debug_session = crud_debug.get_debug_session(db, session_id)
        if not debug_session:
            raise ValueError(f"Debug session {session_id} not found")
        
        # Verify ownership
        if debug_session.user_id != user_id:
            raise PermissionError("Not authorized to access this debug session")
        
        # Get execution and test case
        execution = debug_session.execution
        test_case = execution.test_case
        
        # Parse steps
        import json
        steps = test_case.steps
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except:
                steps = [steps]
        elif not isinstance(steps, list):
            steps = []
        
        # Generate instructions for prerequisite steps
        instructions = []
        target_step = debug_session.target_step_number
        
        for step_num in range(1, target_step):
            if step_num > len(steps):
                break
            
            step_desc = steps[step_num - 1]
            
            # Parse step description to extract action details
            action_type = "action"
            target_element = None
            input_value = None
            
            desc_lower = step_desc.lower()
            if "click" in desc_lower:
                action_type = "click"
                # Try to extract target (words after "click")
                parts = step_desc.split("click", 1)
                if len(parts) > 1:
                    target_element = parts[1].strip()
            elif "type" in desc_lower or "enter" in desc_lower:
                action_type = "type"
                # Try to extract value and target
                if "'" in step_desc or '"' in step_desc:
                    # Extract quoted text as value
                    import re
                    matches = re.findall(r'["\']([^"\']+)["\']', step_desc)
                    if matches:
                        input_value = matches[0]
            elif "navigate" in desc_lower or "goto" in desc_lower or "open" in desc_lower:
                action_type = "navigate"
            
            instructions.append(ManualSetupInstruction(
                step_number=step_num,
                action=action_type,
                description=step_desc,
                target=target_element,
                value=input_value
            ))
        
        # Generate summary
        base_url = execution.base_url or os.getenv("BASE_URL", "https://www.three.com.hk")
        summary = (
            f"Manual Setup Instructions for Debugging Step {target_step}:\n\n"
            f"1. A browser window has been opened with DevTools\n"
            f"2. Please perform the following {len(instructions)} steps manually:\n\n"
        )
        
        for inst in instructions:
            summary += f"   Step {inst.step_number}: {inst.description}\n"
        
        summary += (
            f"\n3. Once you've completed all steps above, return to this page and click 'Confirm Setup Complete'\n"
            f"4. Then you can debug step {target_step} repeatedly\n\n"
            f"Starting URL: {base_url}"
        )
        
        return instructions, summary
    
    def confirm_manual_setup(
        self,
        db: Session,
        session_id: str,
        user_id: int
    ) -> DebugSession:
        """
        Confirm that manual setup is complete.
        
        Args:
            db: Database session
            session_id: Debug session ID
            user_id: User ID (for authorization)
            
        Returns:
            Updated DebugSession object
        """
        # Get debug session
        debug_session = crud_debug.get_debug_session(db, session_id)
        if not debug_session:
            raise ValueError(f"Debug session {session_id} not found")
        
        # Verify ownership
        if debug_session.user_id != user_id:
            raise PermissionError("Not authorized to access this debug session")
        
        # Mark setup as completed
        debug_session = crud_debug.mark_setup_completed(db, session_id)
        
        return debug_session
    
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


# Singleton instance
_debug_session_service: Optional[DebugSessionService] = None


def get_debug_session_service() -> DebugSessionService:
    """Get or create debug session service singleton."""
    global _debug_session_service
    if _debug_session_service is None:
        _debug_session_service = DebugSessionService()
    return _debug_session_service
