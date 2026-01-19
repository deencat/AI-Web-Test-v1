"""
Tier 3: Stagehand Only Execution
Full AI reasoning with Stagehand act() for complex interactions
Sprint 5.5: 3-Tier Execution Engine
"""
import time
from typing import Dict, Any, Optional
from stagehand import Stagehand
import logging

logger = logging.getLogger(__name__)


class Tier3StagehandExecutor:
    """
    Tier 3: Full Stagehand act() execution with AI reasoning.
    
    This is the last resort fallback when Tier 1 and Tier 2 fail.
    Uses full LLM reasoning to understand and interact with the page.
    
    Expected success rate: 60-70% (when Tier 1 and Tier 2 fail)
    Cost: High (full LLM reasoning for each action)
    Speed: Slowest (full AI processing)
    """
    
    def __init__(
        self,
        stagehand: Stagehand,
        timeout_ms: int = 30000
    ):
        """
        Initialize Tier 3 executor.
        
        Args:
            stagehand: Stagehand instance for execution
            timeout_ms: Timeout in milliseconds for each action
        """
        self.stagehand = stagehand
        self.timeout_ms = timeout_ms
    
    async def execute_step(
        self,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single test step using full Stagehand act().
        
        Args:
            step: Step dictionary containing action, instruction, value, etc.
            
        Returns:
            Result dictionary with success status, timing, and error info
        """
        start_time = time.time()
        
        try:
            action = step.get("action", "").lower()
            instruction = step.get("instruction", "")
            value = step.get("value", "")
            
            logger.info(f"[Tier 3] Executing step with full AI reasoning: {instruction}")
            
            # Build action instruction for Stagehand
            if action == "navigate":
                # Use goto instead of act for navigation
                url = value or instruction
                await self.stagehand.page.goto(url, timeout=self.timeout_ms, wait_until="networkidle")
                
            elif action in ["fill", "type"] and value:
                # Combine action with value for better instruction
                full_instruction = f"{instruction} with value '{value}'"
                result = await self.stagehand.act(full_instruction)
                
            elif action in ["assert", "verify"]:
                # Use extract to verify content
                extract_instruction = f"Get the text that should contain: {value}"
                result = await self.stagehand.extract(extract_instruction)
                
                if value not in str(result):
                    raise AssertionError(
                        f"Expected '{value}' in extracted text, got '{result}'"
                    )
                    
            else:
                # Use act() for all other actions
                result = await self.stagehand.act(instruction)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"[Tier 3] ✅ Step succeeded in {execution_time_ms:.2f}ms")
            
            return {
                "success": True,
                "tier": 3,
                "execution_time_ms": execution_time_ms,
                "error": None
            }
            
        except asyncio.TimeoutError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Timeout after {self.timeout_ms}ms: {str(e)}"
            logger.warning(f"[Tier 3] ⏰ Timeout: {error_msg}")
            
            return {
                "success": False,
                "tier": 3,
                "execution_time_ms": execution_time_ms,
                "error": error_msg,
                "error_type": "timeout"
            }
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.warning(f"[Tier 3] ❌ Failed: {error_msg}")
            
            return {
                "success": False,
                "tier": 3,
                "execution_time_ms": execution_time_ms,
                "error": error_msg,
                "error_type": type(e).__name__
            }


# Import asyncio for timeout handling
import asyncio
