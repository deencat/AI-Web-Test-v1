"""
TypeScript Stagehand adapter - communicates with Node.js microservice via HTTP.

This adapter sends test execution requests to a separate Node.js service
running @browserbasehq/stagehand (TypeScript implementation).
"""
import aiohttp
import os
from typing import Dict, Any, Optional, Callable
from sqlalchemy.orm import Session

from app.services.stagehand_adapter import StagehandAdapter
from app.models.test_case import TestCase


class TypeScriptStagehandAdapter(StagehandAdapter):
    """
    Adapter for TypeScript Stagehand provider.
    
    This adapter communicates with a Node.js microservice running the
    TypeScript @browserbasehq/stagehand implementation via HTTP API.
    
    Service URL is configured via STAGEHAND_TYPESCRIPT_URL environment variable.
    Default: http://localhost:3001
    """
    
    def __init__(
        self,
        service_url: Optional[str] = None,
        timeout: int = 300  # 5 minutes default timeout
    ):
        """
        Initialize TypeScript Stagehand adapter.
        
        Args:
            service_url: URL of Node.js Stagehand microservice (overrides env var)
            timeout: Request timeout in seconds
        """
        self.service_url = service_url or os.getenv(
            "STAGEHAND_TYPESCRIPT_URL",
            "http://localhost:3001"
        )
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
        self._browser_session_id: Optional[str] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create HTTP session.
        
        Returns:
            Active aiohttp ClientSession
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session
    
    async def initialize(self, user_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize TypeScript Stagehand browser via HTTP API.
        
        Args:
            user_config: Optional configuration overrides from user settings
        
        Raises:
            aiohttp.ClientError: If service is unreachable
            ValueError: If initialization fails
        """
        session = await self._get_session()
        
        payload = {
            "user_config": user_config or {}
        }
        
        try:
            async with session.post(
                f"{self.service_url}/api/initialize",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(
                        f"Failed to initialize TypeScript Stagehand: {error_text}"
                    )
                
                data = await response.json()
                self._browser_session_id = data.get("session_id")
                
                print(f"[TypeScript Adapter] Initialized browser session: {self._browser_session_id}")
        
        except aiohttp.ClientError as e:
            raise ConnectionError(
                f"Cannot connect to TypeScript Stagehand service at {self.service_url}: {e}"
            )
    
    async def cleanup(self) -> None:
        """
        Clean up TypeScript Stagehand resources via HTTP API.
        """
        if self._browser_session_id is None:
            return
        
        session = await self._get_session()
        
        try:
            async with session.post(
                f"{self.service_url}/api/cleanup",
                json={"session_id": self._browser_session_id}
            ) as response:
                if response.status == 200:
                    print(f"[TypeScript Adapter] Cleaned up session: {self._browser_session_id}")
                else:
                    print(f"[TypeScript Adapter] Cleanup warning: {response.status}")
        
        except aiohttp.ClientError as e:
            print(f"[TypeScript Adapter] Cleanup error: {e}")
        
        finally:
            self._browser_session_id = None
            
            # Close HTTP session
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
    
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
        Execute a complete test case using TypeScript Stagehand.
        
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
        
        Note:
            This implementation is a placeholder. The Node.js service will
            return step results, and this adapter will update the database
            using the same CRUD operations as Python adapter.
        """
        if self._browser_session_id is None:
            raise ValueError("Browser not initialized. Call initialize() first.")
        
        session = await self._get_session()
        
        # Prepare test steps
        import json
        steps = test_case.steps
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except:
                steps = [steps]
        elif not isinstance(steps, list):
            steps = []
        
        payload = {
            "session_id": self._browser_session_id,
            "test_case_id": test_case.id,
            "execution_id": execution_id,
            "base_url": base_url,
            "steps": steps,
            "environment": environment,
            "skip_navigation": skip_navigation
        }
        
        try:
            async with session.post(
                f"{self.service_url}/api/execute-test",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(
                        f"Test execution failed: {error_text}"
                    )
                
                result = await response.json()
                
                # TODO: Update database with results from TypeScript service
                # For now, import CRUD and update execution record
                from app.crud import crud_execution
                from app.models.test_execution import ExecutionResult
                
                # Mark execution as complete
                if result.get("success"):
                    execution = crud_execution.complete_execution(
                        db,
                        execution_id,
                        ExecutionResult.PASS
                    )
                else:
                    execution = crud_execution.complete_execution(
                        db,
                        execution_id,
                        ExecutionResult.FAIL,
                        error_message=result.get("error_message")
                    )
                
                return execution
        
        except aiohttp.ClientError as e:
            raise ConnectionError(
                f"Failed to execute test via TypeScript Stagehand: {e}"
            )
    
    async def execute_single_step(
        self,
        step_description: str,
        step_number: int,
        execution_id: int
    ) -> Dict[str, Any]:
        """
        Execute a single step using TypeScript Stagehand (for debug mode).
        
        Args:
            step_description: Step description to execute
            step_number: Step number (for logging/screenshots)
            execution_id: Execution ID (for screenshot naming)
            
        Returns:
            Dict with execution results
        """
        if self._browser_session_id is None:
            raise ValueError("Browser not initialized. Call initialize() first.")
        
        session = await self._get_session()
        
        payload = {
            "session_id": self._browser_session_id,
            "step_description": step_description,
            "step_number": step_number,
            "execution_id": execution_id
        }
        
        try:
            async with session.post(
                f"{self.service_url}/api/execute-step",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "actual": "Failed to communicate with TypeScript service",
                        "expected": step_description,
                        "screenshot_path": None,
                        "duration_seconds": 0.0,
                        "tokens_used": 0
                    }
                
                result = await response.json()
                return result
        
        except aiohttp.ClientError as e:
            return {
                "success": False,
                "error": str(e),
                "actual": "Failed to communicate with TypeScript service",
                "expected": step_description,
                "screenshot_path": None,
                "duration_seconds": 0.0,
                "tokens_used": 0
            }
    
    async def initialize_persistent(
        self,
        session_id: str,
        test_id: int,
        user_id: int,
        db: Session,
        user_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize a persistent debug session using TypeScript Stagehand.
        
        Args:
            session_id: Unique session identifier
            test_id: Test case ID being debugged
            user_id: User ID
            db: Database session
            user_config: Optional configuration overrides
        """
        session = await self._get_session()
        
        payload = {
            "session_id": session_id,
            "test_id": test_id,
            "user_id": user_id,
            "user_config": user_config or {}
        }
        
        try:
            async with session.post(
                f"{self.service_url}/api/initialize-persistent",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(
                        f"Failed to initialize persistent session: {error_text}"
                    )
                
                data = await response.json()
                self._browser_session_id = data.get("browser_session_id")
                
                print(f"[TypeScript Adapter] Initialized persistent session: {session_id}")
        
        except aiohttp.ClientError as e:
            raise ConnectionError(
                f"Cannot initialize persistent session: {e}"
            )
    
    @property
    def provider_name(self) -> str:
        """
        Return the provider name.
        
        Returns:
            'typescript'
        """
        return "typescript"
