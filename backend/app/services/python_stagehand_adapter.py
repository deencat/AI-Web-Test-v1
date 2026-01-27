"""
Python Stagehand adapter - wraps the existing StagehandExecutionService.

This adapter maintains zero changes to existing code - it simply delegates
all calls to the current Python Stagehand implementation.
"""
from typing import Dict, Any, Optional, Callable
from sqlalchemy.orm import Session

from app.services.stagehand_adapter import StagehandAdapter
from app.services.stagehand_service import StagehandExecutionService
from app.models.test_case import TestCase


class PythonStagehandAdapter(StagehandAdapter):
    """
    Adapter for Python Stagehand provider.
    
    This is a simple wrapper that delegates all calls to the existing
    StagehandExecutionService without modification. This ensures zero
    breaking changes while enabling the adapter pattern.
    """
    
    def __init__(
        self,
        browser: str = "chromium",
        headless: bool = True,
        screenshot_dir: str = "./screenshots",
        video_dir: str = "./videos"
    ):
        """
        Initialize Python Stagehand adapter.
        
        Args:
            browser: Browser type (chromium, firefox, webkit)
            headless: Whether to run browser in headless mode
            screenshot_dir: Directory to save screenshots
            video_dir: Directory to save videos
        """
        self._service = StagehandExecutionService(
            browser=browser,
            headless=headless,
            screenshot_dir=screenshot_dir,
            video_dir=video_dir
        )
    
    async def initialize(self, user_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the Python Stagehand browser.
        
        Args:
            user_config: Optional configuration overrides from user settings
        """
        await self._service.initialize(user_config)
    
    async def cleanup(self) -> None:
        """
        Clean up Python Stagehand resources.
        """
        await self._service.cleanup()
    
    async def execute_test(
        self,
        db: Session,
        test_case: TestCase,
        execution_id: int,
        user_id: int,
        base_url: str,
        environment: str = "dev",
        progress_callback: Optional[Callable] = None,
        skip_navigation: bool = False
    ) -> Any:
        """
        Execute a complete test case using Python Stagehand.
        
        Args:
            db: Database session
            test_case: Test case to execute
            execution_id: Pre-created execution record ID
            user_id: ID of user triggering execution
            base_url: Base URL for the application under test
            environment: Environment name (dev, staging, production)
            progress_callback: Optional callback for progress updates
            skip_navigation: If True, skip navigating to base_url
            
        Returns:
            TestExecution object with results
        """
        return await self._service.execute_test(
            db=db,
            test_case=test_case,
            execution_id=execution_id,
            user_id=user_id,
            base_url=base_url,
            environment=environment,
            progress_callback=progress_callback,
            skip_navigation=skip_navigation
        )
    
    async def execute_single_step(
        self,
        step_description: str,
        step_number: int,
        execution_id: int
    ) -> Dict[str, Any]:
        """
        Execute a single step using Python Stagehand (for debug mode).
        
        Args:
            step_description: Step description to execute
            step_number: Step number (for logging/screenshots)
            execution_id: Execution ID (for screenshot naming)
            
        Returns:
            Dict with execution results
        """
        return await self._service.execute_single_step(
            step_description=step_description,
            step_number=step_number,
            execution_id=execution_id
        )
    
    async def initialize_persistent(
        self,
        session_id: str,
        test_id: int,
        user_id: int,
        db: Session,
        user_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize a persistent debug session using Python Stagehand.
        
        Args:
            session_id: Unique session identifier
            test_id: Test case ID being debugged
            user_id: User ID
            db: Database session
            user_config: Optional configuration overrides
            
        Returns:
            Dict with browser_pid, browser_port, and other metadata
        """
        from pathlib import Path
        
        # Build user data directory path (consistent with debug_session_service)
        user_data_base = Path("artifacts/debug_sessions")
        user_data_dir = user_data_base / session_id
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Call the underlying service with correct parameters
        return await self._service.initialize_persistent(
            user_data_dir=str(user_data_dir),
            user_config=user_config,
            devtools=True
        )
    
    @property
    def provider_name(self) -> str:
        """
        Return the provider name.
        
        Returns:
            'python'
        """
        return "python"
