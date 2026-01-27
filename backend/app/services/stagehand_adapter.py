"""
Abstract base class for Stagehand adapters.

This adapter pattern allows switching between Python and TypeScript Stagehand providers
without changing the rest of the codebase.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from sqlalchemy.orm import Session
from app.models.test_case import TestCase


class StagehandAdapter(ABC):
    """
    Abstract base class for Stagehand provider adapters.
    
    Implementations:
    - PythonStagehandAdapter: Wraps existing Python Stagehand (default)
    - TypeScriptStagehandAdapter: Communicates with Node.js microservice
    """
    
    @abstractmethod
    async def initialize(self, user_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the Stagehand browser instance.
        
        Args:
            user_config: Optional configuration overrides from user settings
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up resources (close browser, terminate connections).
        """
        pass
    
    @abstractmethod
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
        Execute a complete test case.
        
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
        pass
    
    @abstractmethod
    async def execute_single_step(
        self,
        step_description: str,
        step_number: int,
        execution_id: int
    ) -> Dict[str, Any]:
        """
        Execute a single step (for debug mode).
        
        Args:
            step_description: Step description to execute
            step_number: Step number (for logging/screenshots)
            execution_id: Execution ID (for screenshot naming)
            
        Returns:
            Dict with:
                - success: bool
                - error: Optional[str]
                - actual: str (what happened)
                - expected: str (what should happen)
                - screenshot_path: Optional[str]
                - duration_seconds: float
                - tokens_used: int (estimated)
        """
        pass
    
    @abstractmethod
    async def initialize_persistent(
        self,
        session_id: str,
        test_id: int,
        user_id: int,
        db: Session,
        user_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize a persistent debug session.
        
        Args:
            session_id: Unique session identifier
            test_id: Test case ID being debugged
            user_id: User ID
            db: Database session
            user_config: Optional configuration overrides
            
        Returns:
            Dict with browser_pid, browser_port, and other metadata
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the provider name ('python' or 'typescript').
        """
        pass
