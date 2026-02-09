"""
3-Tier Execution Service with Configurable Fallback Strategies
Sprint 5.5: Main execution service with Options A, B, C
"""
import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from playwright.async_api import Page
from sqlalchemy.orm import Session
from stagehand import Stagehand
import logging

from app.services.tier1_playwright import Tier1PlaywrightExecutor
from app.services.tier2_hybrid import Tier2HybridExecutor
from app.services.tier3_stagehand import Tier3StagehandExecutor
from app.services.xpath_extractor import XPathExtractor
from app.models.execution_settings import ExecutionSettings, TierExecutionLog
from app.schemas.execution_settings import FallbackStrategy

logger = logging.getLogger(__name__)


class ExecutionFailedError(Exception):
    """Exception raised when all execution tiers are exhausted"""
    
    def __init__(self, message: str, execution_history: List[Dict[str, Any]]):
        self.message = message
        self.execution_history = execution_history
        super().__init__(self.message)


class ThreeTierExecutionService:
    """
    3-Tier Execution Service with configurable fallback strategies.
    
    Supports three execution strategies:
    - Option A: Tier 1 → Tier 2 (Cost-conscious, 90-95% success)
    - Option B: Tier 1 → Tier 3 (AI-first, 92-94% success)
    - Option C: Tier 1 → Tier 2 → Tier 3 (Maximum reliability, 97-99% success)
    """
    
    def __init__(
        self,
        db: Session,
        page: Page,
        stagehand: Optional[Stagehand] = None,
        user_settings: Optional[ExecutionSettings] = None,
        cdp_endpoint: Optional[str] = None,
        user_ai_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize 3-Tier execution service.
        
        Args:
            db: Database session
            page: Playwright Page object
            stagehand: Optional Stagehand instance for Tier 2 and Tier 3
            user_settings: Optional user execution settings
            cdp_endpoint: Optional CDP endpoint URL to connect Stagehand to existing browser
            user_ai_config: Optional user AI provider configuration (provider, model, temperature, max_tokens)
        """
        self.db = db
        self.page = page
        self.stagehand = stagehand
        self.user_settings = user_settings or self._get_default_settings()
        self.cdp_endpoint = cdp_endpoint  # Store CDP endpoint for shared browser context
        self.user_ai_config = user_ai_config  # Store user's AI provider config
        
        # Initialize tier executors
        timeout_ms = self.user_settings.timeout_per_tier_seconds * 1000
        
        self.tier1_executor = Tier1PlaywrightExecutor(timeout_ms=timeout_ms)
        
        # Tier 2 and 3 will be initialized lazily when needed
        self.tier2_executor = None
        self.tier3_executor = None
        self.xpath_extractor = None
    
    def _get_default_settings(self) -> ExecutionSettings:
        """Get default execution settings"""
        settings = ExecutionSettings()
        settings.fallback_strategy = "option_c"
        settings.max_retry_per_tier = 1
        settings.timeout_per_tier_seconds = 30
        settings.track_fallback_reasons = True
        settings.track_strategy_effectiveness = True
        return settings
    
    async def _ensure_tier2_initialized(self):
        """Lazy initialization of Tier 2 executor with shared browser context"""
        if not self.tier2_executor:
            if not self.xpath_extractor:
                self.xpath_extractor = XPathExtractor(stagehand=self.stagehand)
                if not self.stagehand:
                    # Initialize with CDP endpoint and user's AI config to share browser context
                    await self.xpath_extractor.initialize(
                        cdp_endpoint=self.cdp_endpoint,
                        user_config=self.user_ai_config
                    )
                    self.stagehand = self.xpath_extractor.stagehand
            
            timeout_ms = self.user_settings.timeout_per_tier_seconds * 1000
            self.tier2_executor = Tier2HybridExecutor(
                db=self.db,
                xpath_extractor=self.xpath_extractor,
                timeout_ms=timeout_ms
            )
    
    async def _ensure_tier3_initialized(self):
        """Lazy initialization of Tier 3 executor with shared browser context"""
        if not self.tier3_executor:
            if not self.stagehand:
                # Initialize Stagehand with CDP endpoint and user's AI config to share browser context
                self.xpath_extractor = XPathExtractor()
                await self.xpath_extractor.initialize(
                    cdp_endpoint=self.cdp_endpoint,
                    user_config=self.user_ai_config
                )
                self.stagehand = self.xpath_extractor.stagehand
            
            timeout_ms = self.user_settings.timeout_per_tier_seconds * 1000
            self.tier3_executor = Tier3StagehandExecutor(
                stagehand=self.stagehand,
                timeout_ms=timeout_ms
            )
    
    async def execute_step(
        self,
        step: Dict[str, Any],
        execution_id: Optional[int] = None,
        step_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute test step with configured fallback strategy.
        
        Args:
            step: Step dictionary with action, instruction, selector, value
            execution_id: Optional execution ID for logging
            step_index: Optional step index for logging
            
        Returns:
            Execution result with tier, success, timing, and error info
        """
        execution_history = []
        overall_start_time = time.time()
        
        strategy = self.user_settings.fallback_strategy
        
        logger.info(
            f"[3-Tier] Executing step with strategy {strategy}: "
            f"{step.get('action')} - {step.get('instruction')}"
        )
        
        # TIER 1: Always attempt Playwright Direct first
        tier1_result = await self._execute_tier1(step)
        execution_history.append(tier1_result)
        
        if tier1_result["success"]:
            # Success at Tier 1!
            total_time_ms = (time.time() - overall_start_time) * 1000
            
            result = {
                **tier1_result,
                "total_time_ms": total_time_ms,
                "execution_history": execution_history,
                "strategy_used": strategy
            }
            
            # Log tier execution
            if execution_id is not None and step_index is not None:
                await self._log_tier_execution(
                    execution_id=execution_id,
                    step_index=step_index,
                    strategy=strategy,
                    final_tier=1,
                    success=True,
                    execution_history=execution_history,
                    total_time_ms=total_time_ms
                )
            
            return result
        
        # Tier 1 failed, proceed with selected fallback strategy
        logger.info(f"[3-Tier] Tier 1 failed, falling back to strategy {strategy}")
        
        try:
            if strategy == "option_a":
                result = await self._execute_option_a(step, execution_history)
            elif strategy == "option_b":
                result = await self._execute_option_b(step, execution_history)
            elif strategy == "option_c":
                result = await self._execute_option_c(step, execution_history)
            else:
                raise ValueError(f"Unknown fallback strategy: {strategy}")
            
            total_time_ms = (time.time() - overall_start_time) * 1000
            result["total_time_ms"] = total_time_ms
            result["strategy_used"] = strategy
            
            # Log tier execution
            if execution_id is not None and step_index is not None:
                await self._log_tier_execution(
                    execution_id=execution_id,
                    step_index=step_index,
                    strategy=strategy,
                    final_tier=result["tier"],
                    success=result["success"],
                    execution_history=execution_history,
                    total_time_ms=total_time_ms
                )
            
            return result
            
        except ExecutionFailedError as e:
            total_time_ms = (time.time() - overall_start_time) * 1000
            
            logger.error(f"[3-Tier] ❌ All tiers exhausted: {e.message}")
            
            result = {
                "success": False,
                "tier": None,
                "total_time_ms": total_time_ms,
                "execution_history": e.execution_history,
                "strategy_used": strategy,
                "error": e.message,
                "error_type": "all_tiers_exhausted"
            }
            
            # Log tier execution
            if execution_id is not None and step_index is not None:
                await self._log_tier_execution(
                    execution_id=execution_id,
                    step_index=step_index,
                    strategy=strategy,
                    final_tier=None,
                    success=False,
                    execution_history=e.execution_history,
                    total_time_ms=total_time_ms
                )
            
            return result
    
    async def _execute_tier1(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Tier 1 (Playwright Direct)"""
        try:
            result = await self.tier1_executor.execute_step(self.page, step)
            return result
        except Exception as e:
            logger.error(f"[Tier 1] Unexpected error: {e}")
            return {
                "success": False,
                "tier": 1,
                "execution_time_ms": 0,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _execute_option_a(
        self,
        step: Dict[str, Any],
        execution_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Option A: Tier 1 → Tier 2
        Cost-conscious approach, 90-95% success rate
        """
        await self._ensure_tier2_initialized()
        
        tier2_result = await self.tier2_executor.execute_step(self.page, step)
        execution_history.append(tier2_result)
        
        if tier2_result["success"]:
            logger.info(f"[3-Tier] ✅ Option A succeeded at Tier 2")
            return tier2_result
        
        raise ExecutionFailedError(
            message="Option A failed: Tier 1 and Tier 2 exhausted",
            execution_history=execution_history
        )
    
    async def _execute_option_b(
        self,
        step: Dict[str, Any],
        execution_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Option B: Tier 1 → Tier 3 (skip Tier 2)
        AI-first approach, 92-94% success rate
        """
        await self._ensure_tier3_initialized()
        
        tier3_result = await self.tier3_executor.execute_step(step)
        execution_history.append(tier3_result)
        
        if tier3_result["success"]:
            logger.info(f"[3-Tier] ✅ Option B succeeded at Tier 3")
            return tier3_result
        
        raise ExecutionFailedError(
            message="Option B failed: Tier 1 and Tier 3 exhausted",
            execution_history=execution_history
        )
    
    async def _execute_option_c(
        self,
        step: Dict[str, Any],
        execution_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Option C: Tier 1 → Tier 2 → Tier 3 (full cascade)
        Maximum reliability approach, 97-99% success rate
        """
        # Try Tier 2 first
        await self._ensure_tier2_initialized()
        
        tier2_result = await self.tier2_executor.execute_step(self.page, step)
        execution_history.append(tier2_result)
        
        if tier2_result["success"]:
            logger.info(f"[3-Tier] ✅ Option C succeeded at Tier 2")
            return tier2_result
        
        # Tier 2 failed, try Tier 3 as last resort
        logger.info(f"[3-Tier] Tier 2 failed, trying Tier 3 as last resort")
        
        await self._ensure_tier3_initialized()
        
        tier3_result = await self.tier3_executor.execute_step(step)
        execution_history.append(tier3_result)
        
        if tier3_result["success"]:
            logger.info(f"[3-Tier] ✅ Option C succeeded at Tier 3")
            return tier3_result
        
        raise ExecutionFailedError(
            message="Option C failed: All tiers exhausted (Tier 1, 2, 3)",
            execution_history=execution_history
        )
    
    async def _log_tier_execution(
        self,
        execution_id: int,
        step_index: int,
        strategy: str,
        final_tier: Optional[int],
        success: bool,
        execution_history: List[Dict[str, Any]],
        total_time_ms: float
    ):
        """Log tier execution for analytics"""
        if not self.user_settings.track_strategy_effectiveness:
            return
        
        try:
            # Extract timing info per tier
            tier1_time = None
            tier2_time = None
            tier3_time = None
            tier1_error = None
            tier2_error = None
            tier3_error = None
            
            tiers_attempted = []
            
            for result in execution_history:
                tier = result.get("tier")
                if tier == 1:
                    tier1_time = result.get("execution_time_ms")
                    tier1_error = result.get("error")
                    tiers_attempted.append(1)
                elif tier == 2:
                    tier2_time = result.get("execution_time_ms")
                    tier2_error = result.get("error")
                    tiers_attempted.append(2)
                elif tier == 3:
                    tier3_time = result.get("execution_time_ms")
                    tier3_error = result.get("error")
                    tiers_attempted.append(3)
            
            # Create log entry
            log_entry = TierExecutionLog(
                execution_id=execution_id,
                step_index=step_index,
                fallback_strategy=strategy,
                final_tier=final_tier or 0,
                success=success,
                tiers_attempted=json.dumps(tiers_attempted),
                total_execution_time_ms=total_time_ms,
                tier1_time_ms=tier1_time,
                tier2_time_ms=tier2_time,
                tier3_time_ms=tier3_time,
                tier1_error=tier1_error[:500] if tier1_error else None,
                tier2_error=tier2_error[:500] if tier2_error else None,
                tier3_error=tier3_error[:500] if tier3_error else None
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"[3-Tier] Failed to log tier execution: {e}")
            # Don't fail the execution if logging fails
            pass
