"""
Tier 3: Stagehand Only Execution
Full AI reasoning with Stagehand act() for complex interactions
Sprint 5.5: 3-Tier Execution Engine
"""
import asyncio
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
            action = step.get("action")
            if action:
                action = action.lower()
            else:
                # If no action provided, try to infer from instruction
                instruction = step.get("instruction", "")
                if any(word in instruction.lower() for word in ["sign", "signature", "draw"]):
                    action = "draw_signature"
                else:
                    # Let Stagehand handle it with act()
                    action = "act"
            
            instruction = step.get("instruction", "")
            value = step.get("value", "")
            file_path = step.get("file_path", "")
            
            logger.info(f"[Tier 3] Executing step with full AI reasoning: {instruction}")
            
            # Check if this is a navigation action (button text contains navigation keywords)
            instruction_lower = instruction.lower()
            is_navigation_action = any(
                keyword in instruction_lower 
                for keyword in ["next", "continue", "submit", "proceed", "upload", "confirm", "click", "checkout", "payment", "pay"]
            )
            
            # Capture current URL before action to detect navigation
            current_url = self.stagehand.page.url
            
            # Build action instruction for Stagehand
            if action == "navigate":
                # Use goto instead of act for navigation
                url = value or instruction
                await self.stagehand.page.goto(url, timeout=self.timeout_ms, wait_until="networkidle")
                
            elif action in ["fill", "type"] and value:
                # Combine action with value for better instruction
                full_instruction = f"{instruction} with value '{value}'"
                result = await self.stagehand.page.act(full_instruction)
                
            elif action == "select" and value:
                # Handle dropdown/select actions with explicit value
                full_instruction = f"{instruction}. Select option with value or text '{value}'"
                logger.info(f"[Tier 3] 🎯 Dropdown select: {full_instruction}")
                result = await self.stagehand.page.act(full_instruction)
                
                # Small delay for onChange handlers
                await asyncio.sleep(0.3)
                
            elif action in ["assert", "verify"]:
                # Use extract to verify content
                extract_instruction = f"Get the text that should contain: {value}"
                result = await self.stagehand.page.extract(extract_instruction)
                
                if value not in str(result):
                    raise AssertionError(
                        f"Expected '{value}' in extracted text, got '{result}'"
                    )
            
            elif action == "upload_file":
                # Handle file upload action
                upload_file_path = file_path or value
                if not upload_file_path:
                    raise ValueError("No file_path provided for upload_file action")
                
                import os
                if not os.path.exists(upload_file_path):
                    raise FileNotFoundError(f"File not found: {upload_file_path}")
                
                logger.info(f"[Tier 3] 📤 Uploading file: {upload_file_path}")
                
                # Try AI act() first with file upload instruction
                try:
                    # Attempt to use Stagehand's AI to find and interact with file input
                    upload_instruction = f"{instruction}. File path: {upload_file_path}"
                    result = await self.stagehand.page.act(upload_instruction)
                    logger.info(f"[Tier 3] ✅ File upload via AI act() succeeded")
                except Exception as act_error:
                    # Fallback: Use programmatic file input
                    logger.warning(f"[Tier 3] ⚠️ AI act() failed for upload, using fallback: {str(act_error)}")
                    
                    # Find file input element programmatically
                    file_input = self.stagehand.page.locator("input[type='file']").first
                    await file_input.wait_for(state="attached", timeout=self.timeout_ms)
                    await file_input.set_input_files(upload_file_path, timeout=self.timeout_ms)
                    logger.info(f"[Tier 3] ✅ File uploaded via fallback method")
                
                # Small delay to allow file upload handlers to complete
                await asyncio.sleep(0.5)
            
            elif action == "draw_signature" or action == "sign":
                # Draw signature on canvas element
                logger.info(f"[Tier 3] ✍️ Drawing signature using AI reasoning")
                
                # Try to use AI to find and draw on signature canvas
                try:
                    signature_instruction = f"{instruction}. Draw a signature on the signature pad or canvas."
                    result = await self.stagehand.page.act(signature_instruction)
                    logger.info(f"[Tier 3] ✅ Signature drawn via AI act()")
                except Exception as act_error:
                    # Fallback: Find canvas programmatically and draw
                    logger.warning(f"[Tier 3] ⚠️ AI act() failed for signature, using fallback: {str(act_error)}")
                    await self._execute_draw_signature_fallback()
                    
            else:
                # Use act() for all other actions
                result = await self.stagehand.page.act(instruction)
                
                # Wait for page to stabilize after navigation actions
                if is_navigation_action:
                    logger.info(f"[Tier 3] 🔄 Navigation action detected - waiting for page to stabilize")
                    
                    # Wait a bit for any redirect/navigation to start
                    await asyncio.sleep(0.5)
                    
                    # Check if URL changed (indicates navigation/redirect)
                    url_changed = self.stagehand.page.url != current_url
                    if url_changed:
                        logger.info(f"[Tier 3] 🌐 URL changed from {current_url} to {self.stagehand.page.url} - waiting for new page to load")
                        # Wait for the new page to fully load
                        try:
                            await self.stagehand.page.wait_for_load_state("load", timeout=self.timeout_ms)
                            logger.debug(f"[Tier 3] ✅ New page loaded")
                        except Exception:
                            logger.warning(f"[Tier 3] ⚠️ New page load timeout")
                    
                    try:
                        await self.stagehand.page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
                        logger.debug(f"[Tier 3] ✅ Page state stabilized after action")
                    except Exception as e:
                        # If network doesn't idle, wait for DOM ready
                        try:
                            await self.stagehand.page.wait_for_load_state("domcontentloaded", timeout=5000)
                            logger.debug(f"[Tier 3] ⚠️ DOM loaded after action (network still active)")
                        except Exception:
                            # Last resort: fixed delay
                            await asyncio.sleep(1.5)
                            logger.warning(f"[Tier 3] ⚠️ Using fixed delay after action")
                    
                    # Wait for common loading indicators to disappear
                    try:
                        # Check for loading overlays, spinners, or "loading" text
                        loading_selectors = [
                            "[class*='loading']",
                            "[class*='spinner']",
                            "[class*='overlay']",
                            "[aria-busy='true']",
                            ".loading",
                            ".spinner",
                            ".overlay",
                            # Payment gateway specific loaders
                            "iframe[class*='load']",
                            "[id*='loading']",
                            "[id*='spinner']"
                        ]
                        
                        for selector in loading_selectors:
                            try:
                                loading_element = self.stagehand.page.locator(selector).first
                                # If loading element exists and is visible, wait for it to be hidden
                                if await loading_element.count() > 0:
                                    logger.info(f"[Tier 3] ⏳ Detected loading indicator: {selector}")
                                    await loading_element.wait_for(state="hidden", timeout=15000)  # Increased to 15s for payment gateways
                                    logger.info(f"[Tier 3] ✅ Loading indicator disappeared")
                                    break
                            except Exception:
                                # This selector doesn't match any element, try next
                                continue
                    except Exception as e:
                        logger.debug(f"[Tier 3] No loading indicators found or error checking: {str(e)}")
                    
                    # Additional fixed delay to ensure content is fully rendered (especially for payment gateways)
                    await asyncio.sleep(3.0)  # Increased from 2.0s to 3.0s for payment gateway loading
                    logger.debug(f"[Tier 3] ⏱️ Additional 3.0s wait after navigation action")
                    
                    # CRITICAL FIX: For checkout/payment buttons, wait for payment gateway input fields to appear
                    if "checkout" in instruction_lower or "payment" in instruction_lower or "pay" in instruction_lower:
                        logger.info(f"[Tier 3] 💳 Checkout/payment button detected - waiting for payment gateway input fields...")
                        # Wait for common payment gateway input fields to appear
                        payment_input_selectors = [
                            "input[name*='card']",  # Card number input
                            "input[placeholder*='card']",
                            "input[id*='card']",
                            "input[type='tel'][maxlength='19']",  # Common for card number fields
                            "input[autocomplete='cc-number']",
                            "input[name*='cardnumber']",
                            "iframe[name*='card']",  # Payment gateway iframes
                            "iframe[src*='payment']",
                        ]
                        
                        input_found = False
                        for selector in payment_input_selectors:
                            try:
                                payment_input = self.stagehand.page.locator(selector).first
                                await payment_input.wait_for(state="visible", timeout=10000)
                                logger.info(f"[Tier 3] ✅ Payment input field found: {selector}")
                                input_found = True
                                break
                            except Exception:
                                continue
                        
                        if input_found:
                            # Additional small delay to ensure field is fully interactive
                            await asyncio.sleep(1.0)
                            logger.info(f"[Tier 3] ✅ Payment gateway ready")
                        else:
                            logger.warning(f"[Tier 3] ⚠️ No payment input fields detected (may be non-standard gateway)")
            
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
    
    async def _execute_draw_signature_fallback(self):
        """
        Fallback method to draw signature programmatically when AI act() fails.
        Finds canvas element and draws a signature pattern.
        """
        import asyncio
        
        # Find canvas element (common selectors for signature pads)
        canvas_selectors = [
            "canvas.signature-pad",
            "canvas[id*='signature']",
            "canvas[class*='signature']",
            "canvas",  # Last resort: any canvas
        ]
        
        canvas_element = None
        for selector in canvas_selectors:
            try:
                element = self.stagehand.page.locator(selector).first
                if await element.count() > 0:
                    canvas_element = element
                    logger.info(f"[Tier 3] 🎯 Found canvas using selector: {selector}")
                    break
            except Exception:
                continue
        
        if not canvas_element:
            raise ValueError("No canvas element found for signature drawing")
        
        await canvas_element.wait_for(state="visible", timeout=self.timeout_ms)
        
        # Get canvas dimensions and position
        bbox = await canvas_element.bounding_box()
        if not bbox:
            raise ValueError("Cannot get bounding box for signature canvas")
        
        # Draw a simple signature path (cursive line pattern)
        logger.info(f"[Tier 3] ✍️ Drawing signature programmatically")
        
        # Calculate signature path within canvas
        canvas_x = bbox['x']
        canvas_y = bbox['y']
        canvas_width = bbox['width']
        canvas_height = bbox['height']
        
        # Start position (left side, middle)
        start_x = canvas_x + canvas_width * 0.1
        start_y = canvas_y + canvas_height * 0.5
        
        # Create a cursive signature pattern with mouse movements
        signature_points = [
            (start_x, start_y),  # Start
            (start_x + canvas_width * 0.2, start_y - canvas_height * 0.15),  # Up
            (start_x + canvas_width * 0.35, start_y + canvas_height * 0.1),  # Down
            (start_x + canvas_width * 0.5, start_y - canvas_height * 0.05),  # Up slight
            (start_x + canvas_width * 0.65, start_y + canvas_height * 0.15),  # Down
            (start_x + canvas_width * 0.8, start_y),  # End middle
        ]
        
        # Move to start position
        await self.stagehand.page.mouse.move(signature_points[0][0], signature_points[0][1])
        await self.stagehand.page.mouse.down()
        
        # Draw the signature path
        for x, y in signature_points[1:]:
            await self.stagehand.page.mouse.move(x, y, steps=5)
            await asyncio.sleep(0.01)  # Small delay for natural drawing
        
        await self.stagehand.page.mouse.up()
        
        logger.info(f"[Tier 3] ✅ Signature drawn successfully via fallback")


# Import asyncio for timeout handling
import asyncio

