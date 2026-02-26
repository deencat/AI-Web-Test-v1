"""
EvolutionAgent - Test Code Generator
Converts BDD scenarios (Given/When/Then) into executable test steps and stores in database

Industry Standards:
- BDD (Behavior-Driven Development): Gherkin syntax
- Test steps format: Array of strings for Phase 2 execution engine
- Database integration: Stores TestCase objects for frontend visibility
- Test code quality: Maintainability, readability, best practices
"""
from agents.base_agent import BaseAgent, AgentCapability, TaskContext, TaskResult
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import asyncio
import time
import json
import logging
import uuid
import hashlib
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EvolutionAgent(BaseAgent):
    """
    Generates executable test steps from BDD scenarios and stores in database.
    
    Input: BDD scenarios (Given/When/Then) from RequirementsAgent/AnalysisAgent
    Output: TestCase objects stored in database (test steps as array of strings)
    
    Process:
    1. Receives BDD scenarios with risk scores and prioritization
    2. Converts each scenario to executable test steps using LLM or template
    3. Stores test cases in database (TestCase objects)
    4. Returns database IDs and metadata (generation_id, confidence, etc.)
    """
    
    def __init__(self, agent_id: str, agent_type: str, priority: int, 
                 message_queue, config: Optional[Dict] = None):
        """Initialize EvolutionAgent with optional LLM, caching, and database support"""
        super().__init__(agent_id, agent_type, priority, message_queue, config)
        
        # Database session (for storing test cases)
        self.db = config.get("db") if config else None
        if self.db:
            logger.info("EvolutionAgent initialized with database session")
        else:
            logger.warning("EvolutionAgent initialized without database - test cases will not be stored")
        
        # Initialize LLM client if enabled
        self.use_llm = config.get("use_llm", True) if config else True
        self.llm_client = None
        if self.use_llm:
            from llm.azure_client import get_azure_client
            self.llm_client = get_azure_client()
            if self.llm_client and self.llm_client.enabled:
                logger.info("EvolutionAgent initialized with LLM enhancement (Azure OpenAI)")
            else:
                logger.warning("LLM requested but not available, using template-based generation")
                self.use_llm = False
        
        # Caching for step generation (30% cost reduction)
        self.cache_enabled = config.get("cache_enabled", True) if config else True
        self.steps_cache: Dict[str, Dict] = {}  # In-memory cache (can be replaced with Redis)
        
        # Prompt variants for A/B testing (Sprint 8 requirement)
        self.prompt_variants = {
            "variant_1": self._build_prompt_variant_1,  # Detailed, explicit
            "variant_2": self._build_prompt_variant_2,  # Concise, focused
            "variant_3": self._build_prompt_variant_3,  # Pattern-based, reusable
        }
        self.current_variant = config.get("prompt_variant", "variant_1") if config else "variant_1"
        
        logger.info(f"EvolutionAgent initialized with prompt variant: {self.current_variant}")
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                "test_generation", 
                "1.0.0", 
                confidence_threshold=0.7,
                description="Converts BDD scenarios to executable test steps and stores in database"
            ),
            AgentCapability(
                "code_generation", 
                "1.0.0", 
                confidence_threshold=0.75,
                description="Generates executable test steps from test requirements"
            )
        ]
    
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """Check if agent can handle task"""
        if task.task_type in ["test_generation", "code_generation"]:
            scenarios = task.payload.get("scenarios", [])
            if len(scenarios) > 0:
                # Higher confidence with more scenarios (up to 0.95)
                confidence = min(0.95, 0.7 + (len(scenarios) / 50) * 0.25)
                return True, confidence
            return True, 0.7
        return False, 0.0
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """Generate test steps from BDD scenarios and store in database"""
        start_time = time.time()
        generation_id = str(uuid.uuid4())
        
        try:
            # Extract input data
            scenarios = task.payload.get("scenarios", [])
            risk_scores = task.payload.get("risk_scores", [])
            prioritization = task.payload.get("final_prioritization", [])
            page_context = task.payload.get("page_context", {})
            test_data = task.payload.get("test_data", [])
            user_instruction = task.payload.get("user_instruction", "")  # Get user instruction for goal-aware generation
            login_credentials = task.payload.get("login_credentials", {})  # Get login credentials if provided
            progress_callback = task.payload.get("progress_callback")
            cancel_check = task.payload.get("cancel_check")
            
            # Get database session from config or task payload
            db_session = self.db or task.payload.get("db")
            
            logger.info(f"EvolutionAgent processing {len(scenarios)} scenarios (generation_id: {generation_id})")
            
            if not scenarios:
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error="No scenarios provided in payload",
                    confidence=0.0,
                    execution_time_seconds=time.time() - start_time
                )
            
            # Generate test steps for each scenario
            generated_test_cases = []
            total_tokens = 0

            def _emit_progress(progress: float, message: str, **extra: Any) -> None:
                if not callable(progress_callback):
                    return
                payload = {
                    "progress": max(0.0, min(1.0, float(progress))),
                    "message": message,
                    **extra,
                }
                try:
                    progress_callback(payload)
                except Exception:
                    logger.debug("EvolutionAgent: progress_callback raised error", exc_info=True)
            
            logger.info(f"EvolutionAgent: Generating test steps for {len(scenarios)} scenarios...")
            _emit_progress(0.03, f"Preparing generation for {len(scenarios)} scenarios...", scenarios_total=len(scenarios), scenarios_processed=0)
            for idx, scenario in enumerate(scenarios, 1):
                if callable(cancel_check) and cancel_check():
                    logger.info(f"EvolutionAgent: Cancellation requested before scenario {idx}/{len(scenarios)}. Returning partial result.")
                    break

                scenario_id = scenario.get("scenario_id", "UNKNOWN")
                scenario_title = scenario.get("title", "Unknown")[:50]  # Truncate long titles
                
                logger.info(f"EvolutionAgent: Processing scenario {idx}/{len(scenarios)}: {scenario_id} - {scenario_title}")
                _emit_progress(
                    min(0.95, max(0.05, idx / max(1, len(scenarios)))),
                    f"Processing scenario {idx}/{len(scenarios)}: {scenario_id}",
                    scenarios_total=len(scenarios),
                    scenarios_processed=idx - 1,
                    current_scenario_id=scenario_id,
                )
                
                # Check cache first (if enabled)
                cache_key = self._generate_cache_key(scenario, page_context)
                if self.cache_enabled and cache_key in self.steps_cache:
                    logger.info(f"EvolutionAgent: Cache hit for scenario {scenario_id}")
                    cached_result = self.steps_cache[cache_key]
                    generated_test_cases.append({
                        "scenario_id": scenario_id,
                        "steps": cached_result["steps"],
                        "confidence": cached_result["confidence"],
                        "from_cache": True
                    })
                    logger.debug(f"EvolutionAgent: Cached scenario {scenario_id} has {len(cached_result['steps'])} steps")
                    _emit_progress(
                        min(0.95, idx / max(1, len(scenarios))),
                        f"Generated scenario {idx}/{len(scenarios)} from cache",
                        scenarios_total=len(scenarios),
                        scenarios_processed=idx,
                        current_scenario_id=scenario_id,
                    )
                    continue
                
                # Generate test steps using LLM or template
                logger.debug(f"EvolutionAgent: Generating steps for scenario {scenario_id} using {'LLM' if (self.use_llm and self.llm_client) else 'template'}")
                if self.use_llm and self.llm_client:
                    steps_result = await self._generate_test_steps_with_llm(
                        scenario, risk_scores, prioritization, page_context, test_data, user_instruction, login_credentials
                    )
                else:
                    steps_result = self._generate_test_steps_from_template(
                        scenario, page_context
                    )
                
                if steps_result:
                    steps_count = len(steps_result.get("steps", []))
                    logger.info(f"EvolutionAgent: Generated {steps_count} steps for scenario {scenario_id} "
                               f"(confidence: {steps_result.get('confidence', 0.85):.2f}, "
                               f"tokens: {steps_result.get('tokens_used', 0)})")
                    generated_test_cases.append({
                        "scenario_id": scenario_id,
                        "steps": steps_result["steps"],
                        "confidence": steps_result.get("confidence", 0.85),
                        "from_cache": False
                    })
                    total_tokens += steps_result.get("tokens_used", 0)
                    
                    # Cache the result
                    if self.cache_enabled:
                        self.steps_cache[cache_key] = {
                            "steps": steps_result["steps"],
                            "confidence": steps_result.get("confidence", 0.85),
                            "cached_at": datetime.now(timezone.utc).isoformat()
                        }

                    _emit_progress(
                        min(0.95, idx / max(1, len(scenarios))),
                        f"Generated {steps_count} steps for scenario {idx}/{len(scenarios)}",
                        scenarios_total=len(scenarios),
                        scenarios_processed=idx,
                        current_scenario_id=scenario_id,
                    )
                else:
                    logger.warning(f"EvolutionAgent: Failed to generate steps for scenario {scenario_id}")
            
            # Store test cases in database (if database session available)
            db_test_case_ids = []
            if db_session:
                logger.info(f"EvolutionAgent: Storing {len(generated_test_cases)} test cases in database...")
                try:
                    db_test_case_ids = await self._store_test_cases_in_database(
                        db_session, generated_test_cases, scenarios, 
                        risk_scores, prioritization, page_context, generation_id
                    )
                    logger.info(f"EvolutionAgent: Successfully stored {len(db_test_case_ids)} test cases in database "
                               f"(IDs: {db_test_case_ids[:5]}{'...' if len(db_test_case_ids) > 5 else ''})")
                except Exception as e:
                    logger.error(f"EvolutionAgent: Failed to store test cases in database: {e}", exc_info=True)
                    # Continue even if database storage fails
            else:
                logger.warning("EvolutionAgent: No database session available - test cases not stored in database")
            
            # Calculate overall confidence
            if generated_test_cases:
                overall_confidence = sum(t.get("confidence", 0.85) for t in generated_test_cases) / len(generated_test_cases)
            else:
                overall_confidence = 0.0
            
            # Prepare result
            cancelled = callable(cancel_check) and cancel_check()
            result = {
                "generation_id": generation_id,
                "test_count": len(generated_test_cases),
                "test_case_ids": db_test_case_ids,  # Database IDs
                "test_cases": generated_test_cases,  # Test steps data
                "confidence": round(overall_confidence, 2),
                "prompt_variant": self.current_variant,
                "cache_hits": sum(1 for t in generated_test_cases if t.get("from_cache", False)),
                "cache_misses": sum(1 for t in generated_test_cases if not t.get("from_cache", False)),
                "stored_in_database": len(db_test_case_ids) > 0,
                "cancelled": cancelled,
            }

            if cancelled:
                logger.info("EvolutionAgent: Returning partial generation result due to cancellation request")

            _emit_progress(
                1.0,
                f"Evolution stage complete ({len(generated_test_cases)}/{len(scenarios)} scenarios)",
                scenarios_total=len(scenarios),
                scenarios_processed=len(generated_test_cases),
            )
            
            logger.info(f"EvolutionAgent generated {len(generated_test_cases)} test cases "
                       f"(confidence: {overall_confidence:.2f}, tokens: {total_tokens}, "
                       f"stored: {len(db_test_case_ids)})")
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                confidence=overall_confidence,
                execution_time_seconds=time.time() - start_time,
                metadata={
                    "token_usage": total_tokens,
                    "generation_id": generation_id,
                    "test_count": len(generated_test_cases),
                    "prompt_variant": self.current_variant,
                    "database_ids": db_test_case_ids,
                    "cancelled": cancelled,
                }
            )
            
        except Exception as e:
            logger.error(f"EvolutionAgent error: {e}", exc_info=True)
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                confidence=0.0,
                execution_time_seconds=time.time() - start_time,
                metadata={"generation_id": generation_id}
            )
    
    async def _generate_test_steps_with_llm(
        self,
        scenario: Dict,
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        test_data: List[Dict],
        user_instruction: str = "",
        login_credentials: Dict = {}
    ) -> Optional[Dict]:
        """Generate test steps using Azure OpenAI GPT-4o"""
        try:
            # Build prompt using current variant
            prompt_builder = self.prompt_variants.get(self.current_variant, self._build_prompt_variant_1)
            prompt = prompt_builder(scenario, risk_scores, prioritization, page_context, test_data, user_instruction, login_credentials)
            
            # Call LLM (Azure OpenAI create is synchronous, not async)
            response = await asyncio.to_thread(
                self.llm_client.client.chat.completions.create,
                model=self.llm_client.deployment,
                messages=[
                    {"role": "system", "content": "You are an expert test automation engineer. Generate executable test steps as an array of strings."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent generation
                max_tokens=1500,
                response_format={"type": "json_object"}  # Request JSON format for structured output
            )
            
            # Extract generated steps
            generated_text = response.choices[0].message.content
            try:
                parsed_response = json.loads(generated_text)
                steps = parsed_response.get("steps", [])
                if not steps:
                    # Fallback: try to parse as array directly
                    steps = json.loads(generated_text) if isinstance(generated_text, str) else []
            except json.JSONDecodeError:
                # Fallback: extract steps from text
                steps = self._extract_steps_from_text(generated_text)
            
            # Validate and clean steps
            if not steps or not isinstance(steps, list):
                # Fallback to template-based generation
                logger.warning(f"LLM did not return valid steps array, using template fallback")
                return self._generate_test_steps_from_template(scenario, page_context)
            
            # Calculate confidence based on steps quality
            confidence = self._calculate_steps_confidence(steps, scenario)
            
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return {
                "steps": steps,
                "confidence": confidence,
                "tokens_used": tokens_used,
                "raw_response": generated_text
            }
            
        except Exception as e:
            logger.error(f"LLM steps generation failed: {e}")
            # Fallback to template-based generation
            return self._generate_test_steps_from_template(scenario, page_context)
    
    def _extract_steps_from_text(self, text: str) -> List[str]:
        """Extract test steps from text response (fallback)"""
        steps = []
        # Try to find JSON array
        json_match = re.search(r'\[(.*?)\]', text, re.DOTALL)
        if json_match:
            try:
                steps = json.loads(json_match.group(0))
            except:
                pass
        
        # If no JSON found, try to extract from numbered list
        if not steps:
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                # Match numbered list items: "1. Step", "- Step", "* Step"
                match = re.match(r'^\d+\.\s*(.+)$|^[-*]\s*(.+)$', line)
                if match:
                    step = match.group(1) or match.group(2)
                    if step:
                        steps.append(step.strip())
        
        return steps if steps else self._convert_scenario_to_steps({}, None)
    
    async def _store_test_cases_in_database(
        self,
        db_session,
        generated_test_cases: List[Dict],
        scenarios: List[Dict],
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        generation_id: str
    ) -> List[int]:
        """Store test cases in database as TestCase objects"""
        from app.models.test_case import TestCase, TestType, Priority, TestStatus
        
        db_test_case_ids = []
        
        # Priority mapping
        priority_map = {
            "critical": Priority.HIGH,
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW
        }
        
        for test_case_data in generated_test_cases:
            scenario_id = test_case_data.get("scenario_id")
            steps = test_case_data.get("steps", [])
            
            # Find corresponding scenario
            scenario = next((s for s in scenarios if s.get("scenario_id") == scenario_id), {})
            
            # Find risk score
            risk_info = next((r for r in risk_scores if r.get("scenario_id") == scenario_id), {})
            
            # Get priority
            scenario_priority = scenario.get("priority", "medium").lower()
            priority = priority_map.get(scenario_priority, Priority.MEDIUM)
            
            # Create TestCase object
            db_test_case = TestCase(
                title=scenario.get("title", f"Test: {scenario_id}"),
                description=scenario.get("given", ""),
                test_type=TestType.E2E,
                priority=priority,
                status=TestStatus.PENDING,
                steps=steps,  # Array of strings
                expected_result=scenario.get("then", ""),
                preconditions=scenario.get("given", ""),
                user_id=1,  # Default system user (can be passed from task if needed)
                test_metadata={
                    "scenario_id": scenario_id,
                    "generation_id": generation_id,
                    "rpn": risk_info.get("rpn", 0),
                    "scenario_type": scenario.get("scenario_type", "functional"),
                    "generated_by": "EvolutionAgent"
                }
            )
            
            db_session.add(db_test_case)
            db_session.flush()  # Flush to get the ID
            db_test_case_ids.append(db_test_case.id)
        
        # Commit all test cases
        db_session.commit()
        
        return db_test_case_ids
    
    def _build_prompt_variant_1(
        self,
        scenario: Dict,
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        test_data: List[Dict],
        user_instruction: str = "",
        login_credentials: Dict = {}
    ) -> str:
        """Variant 1: Detailed, explicit prompt with full context - generates test steps with goal-aware completion"""
        scenario_id = scenario.get("scenario_id", "UNKNOWN")
        title = scenario.get("title", "")
        given = scenario.get("given", "")
        when = scenario.get("when", "")
        then = scenario.get("then", "")
        priority = scenario.get("priority", "medium")
        scenario_type = scenario.get("scenario_type", "functional")
        
        # Find risk score for this scenario
        risk_info = next((r for r in risk_scores if r.get("scenario_id") == scenario_id), {})
        rpn = risk_info.get("rpn", 0)
        
        # Find prioritization info
        priority_info = next((p for p in prioritization if p.get("scenario_id") == scenario_id), {})
        composite_score = priority_info.get("composite_score", 0.5)
        
        url = page_context.get("url", "https://example.com")
        page_type = page_context.get("page_type", "unknown")
        
        # Extract goal from user instruction or scenario title for goal-aware generation
        goal = self._extract_goal_from_instruction(user_instruction, title)
        completion_criteria = self._get_completion_criteria_for_goal(goal)
        
        # Build login credentials section if provided
        login_section = ""
        if login_credentials and login_credentials.get("email") and login_credentials.get("password"):
            login_email = login_credentials.get("email", "")
            login_password = login_credentials.get("password", "")
            login_section = f"""
**LOGIN CREDENTIALS PROVIDED:**
- **Email:** {login_email}
- **Password:** {login_credentials.get("password", "")[:3]}*** (masked for security)

**CRITICAL: Login Requirements:**
1. **If the flow requires login** (e.g., purchase flow, checkout, account access), include login steps BEFORE the main flow
2. **Login steps should be:**
   - Navigate to login page (if not already on it)
   - Enter email: {login_email}
   - Enter password: {login_password}
   - Click Login/Submit button
   - Verify successful login (e.g., URL changes, user menu appears, welcome message)
3. **Place login steps BEFORE** the main flow steps (e.g., before plan selection in purchase flow)
4. **If login is required for the goal**, ensure login is completed before proceeding with the main flow

**Example for "Complete purchase flow" with login:**
- Steps should be: Navigate to login page → Login with provided credentials → Verify login success → Navigate to plan page → Select plan → Continue with purchase flow

"""
        
        # Build goal-aware section if goal is identified
        goal_section = ""
        if goal:
            goal_section = f"""
**GOAL-AWARE GENERATION:**
- **User Goal:** {goal}
- **Completion Criteria:** {completion_criteria}

**CRITICAL: Goal Completion Requirements:**
1. **DO NOT STOP** until the goal "{goal}" is TRULY achieved
2. **Multi-Page Flows:** If the goal requires multiple pages, include ALL pages:
   - For "complete purchase flow": Include plan selection → registration → payment → order confirmation
   - For "user registration": Include registration form → email verification → welcome page
   - For "checkout process": Include cart → checkout → payment → confirmation
3. **State Verification:** After each major step, verify the current state and continue if goal not achieved
4. **Final Verification:** The last step MUST verify that the goal is complete (e.g., order ID displayed, payment confirmed, registration complete)

**Example for "Complete purchase flow":**
- Steps must continue through: Plan selection → Registration → Payment entry → Payment confirmation → Order confirmation with order ID
- Final step must verify: Order ID is displayed AND payment is confirmed AND order details are shown
- DO NOT stop at "verify confirmation" if purchase is not actually complete

"""
        
        prompt = f"""Generate executable test steps for the following BDD scenario.

**Scenario Information:**
- ID: {scenario_id}
- Title: {title}
- Priority: {priority} (RPN: {rpn}, Composite Score: {composite_score:.2f})
- Type: {scenario_type}

**BDD Scenario:**
Given: {given}
When: {when}
Then: {then}

**Page Context:**
- URL: {url}
- Page Type: {page_type}
{login_section}
{goal_section}
**Requirements:**
1. Generate an array of executable test steps (as strings)
2. Each step should be a clear, actionable instruction
3. Steps should be in execution order
4. Include navigation, actions, and assertions
5. Use natural language that can be executed by a test automation engine
6. Be specific with selectors and values where applicable
7. **IMPORTANT:** Generate steps until the goal is TRULY achieved (see Goal-Aware section above if provided)

**Output Format:**
Return a JSON object with a "steps" array:
{{
  "steps": [
    "Navigate to {url}",
    "Enter email: test@example.com",
    "Enter password: password123",
    "Click Login button",
    "Verify URL contains /dashboard"
  ]
}}

**Example Steps:**
- Navigation: "Navigate to https://example.com/login"
- Input: "Enter email: user@example.com"
- Click: "Click Submit button"
- Verification: "Verify URL contains /dashboard"
- Assertion: "Verify page title contains 'Welcome'"

Generate ONLY the JSON object with the steps array."""
        
        return prompt
    
    def _extract_goal_from_instruction(self, user_instruction: str, scenario_title: str) -> str:
        """Extract the goal from user instruction or scenario title"""
        if user_instruction:
            # Check for common goal patterns
            goal_keywords = {
                "complete purchase flow": "complete purchase flow",
                "purchase flow": "complete purchase flow",
                "complete registration": "complete user registration",
                "user registration": "complete user registration",
                "checkout process": "complete checkout process",
                "checkout": "complete checkout process"
            }
            
            instruction_lower = user_instruction.lower()
            for keyword, goal in goal_keywords.items():
                if keyword in instruction_lower:
                    return goal
        
        # Fallback to scenario title if it contains goal indicators
        title_lower = scenario_title.lower()
        if "complete" in title_lower and ("purchase" in title_lower or "flow" in title_lower):
            return "complete purchase flow"
        elif "complete" in title_lower and "registration" in title_lower:
            return "complete user registration"
        elif "checkout" in title_lower:
            return "complete checkout process"
        
        return ""
    
    def _get_completion_criteria_for_goal(self, goal: str) -> str:
        """Get completion criteria description for a goal"""
        criteria_map = {
            "complete purchase flow": "Order confirmed with order ID, payment confirmed, and order details displayed",
            "complete user registration": "User registered, email verified (if required), and logged in to welcome page",
            "complete checkout process": "Order placed with order number, shipping confirmed, and payment confirmed"
        }
        
        return criteria_map.get(goal, "Goal achieved with all required actions completed and final state verified")
    
    def _build_prompt_variant_2(
        self,
        scenario: Dict,
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        test_data: List[Dict],
        user_instruction: str = "",
        login_credentials: Dict = {}
    ) -> str:
        """Variant 2: Concise, focused prompt - generates test steps"""
        title = scenario.get("title", "")
        given = scenario.get("given", "")
        when = scenario.get("when", "")
        then = scenario.get("then", "")
        url = page_context.get("url", "https://example.com")
        
        # Extract goal for goal-aware generation
        goal = self._extract_goal_from_instruction(user_instruction, title)
        goal_note = f"\n**Goal:** {goal} - Generate steps until goal is TRULY achieved." if goal else ""
        
        # Add login note if credentials provided
        login_note = ""
        if login_credentials and login_credentials.get("email") and login_credentials.get("password"):
            login_note = f"\n**Login Required:** Use email '{login_credentials.get('email')}' and password '{login_credentials.get('password', '')[:3]}***' to login BEFORE main flow steps."
        
        prompt = f"""Generate executable test steps as a JSON array:

Given: {given}
When: {when}
Then: {then}
URL: {url}{goal_note}{login_note}

Return JSON: {{"steps": ["step1", "step2", ...]}}"""
        
        return prompt
    
    def _build_prompt_variant_3(
        self,
        scenario: Dict,
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        test_data: List[Dict],
        user_instruction: str = "",
        login_credentials: Dict = {}
    ) -> str:
        """Variant 3: Pattern-based prompt with reusable patterns - generates test steps"""
        title = scenario.get("title", "")
        given = scenario.get("given", "")
        when = scenario.get("when", "")
        then = scenario.get("then", "")
        scenario_type = scenario.get("scenario_type", "functional")
        url = page_context.get("url", "https://example.com")
        
        # Include common patterns based on scenario type
        patterns = {
            "functional": "Navigation → Input → Click → Verify",
            "accessibility": "Keyboard navigation → ARIA checks → Screen reader verification",
            "security": "Input validation → XSS prevention → CSRF checks",
            "edge_case": "Boundary testing → Error handling → Edge case validation"
        }
        pattern_hint = patterns.get(scenario_type, patterns["functional"])
        
        # Extract goal for goal-aware generation
        goal = self._extract_goal_from_instruction(user_instruction, title)
        goal_note = f"\n**Goal:** {goal} - Generate steps until goal is TRULY achieved." if goal else ""
        
        # Add login note if credentials provided
        login_note = ""
        if login_credentials and login_credentials.get("email") and login_credentials.get("password"):
            login_note = f"\n**Login Required:** Use email '{login_credentials.get('email')}' and password '{login_credentials.get('password', '')[:3]}***' to login BEFORE main flow steps."
        
        prompt = f"""Generate test steps using pattern for {scenario_type} scenarios.

Scenario: {title}
Given: {given}
When: {when}
Then: {then}
URL: {url}

Pattern: {pattern_hint}{goal_note}{login_note}

Return JSON: {{"steps": ["step1", "step2", ...]}}"""
        
        return prompt
    
    def _generate_test_steps_from_template(
        self,
        scenario: Dict,
        page_context: Dict
    ) -> Optional[Dict]:
        """Generate test steps from template (fallback when LLM unavailable)"""
        # Use the same conversion logic as AnalysisAgent
        steps = self._convert_scenario_to_steps(scenario, page_context)
        
        return {
            "steps": steps,
            "confidence": 0.7,  # Moderate confidence for template-based
            "tokens_used": 0
        }
    
    def _convert_scenario_to_steps(self, scenario: Dict, page_context: Optional[Dict] = None) -> List[str]:
        """
        Convert BDD scenario (Given/When/Then) to executable test steps.
        
        Example:
        Given: "User is on login page"
        When: "User enters email and password, clicks Login"
        Then: "User is redirected to dashboard"
        
        Converts to:
        - Navigate to login page
        - Enter email: test@example.com
        - Enter password: password123
        - Click Login button
        - Verify URL contains /dashboard
        """
        steps = []
        
        # Priority: Always add navigation from page_context URL if available (most reliable)
        if page_context and page_context.get("url"):
            url = page_context["url"]
            # Only add navigation if URL is valid
            if url.startswith("http://") or url.startswith("https://"):
                nav_step = f"Navigate to {url}"
                steps.append(nav_step)
        
        # Given: Preconditions → Navigate/setup (only if no URL was added above)
        given = scenario.get("given", "")
        url_was_added = bool(page_context and page_context.get("url") and 
                            page_context["url"].startswith(("http://", "https://")))
        if given and not url_was_added:
            given_lower = given.lower()
            if "on" in given_lower and "page" in given_lower:
                # Extract page name from "User is on {page} page"
                page_match = re.search(r'on\s+([^,\s]+)\s+page', given_lower)
                if page_match:
                    page_name = page_match.group(1)
                    steps.append(f"Navigate to {page_name} page")
                else:
                    steps.append(f"Navigate to page: {given}")
            elif "navigate" in given_lower or "go to" in given_lower:
                steps.append(given)
        
        # When: Actions → Click, type, navigate
        when = scenario.get("when", "")
        if when:
            # Parse actions from "when" clause
            # Simple heuristic: split by commas, detect action verbs
            when_parts = [p.strip() for p in when.split(",")]
            
            # If only one part, try to break it down into multiple steps
            if len(when_parts) == 1:
                single_action = when_parts[0]
                part_lower = single_action.lower()
                
                # Try to extract multiple actions from a single sentence
                # Pattern: "User does X, then Y, then Z" or "User does X and Y and Z"
                if " and " in single_action or " then " in single_action:
                    # Split by "and" or "then"
                    sub_actions = re.split(r'\s+(?:and|then)\s+', single_action, flags=re.IGNORECASE)
                    for sub_action in sub_actions:
                        sub_action = sub_action.strip()
                        if sub_action:
                            # Remove "User" prefix if present
                            sub_action = re.sub(r'^User\s+', '', sub_action, flags=re.IGNORECASE)
                            steps.append(sub_action)
                # Check for multiple verbs in sequence
                elif any(word in part_lower for word in ["click", "select", "press", "enter", "type"]):
                    # Single action - add as is
                    clean_action = re.sub(r'^User\s+', '', single_action, flags=re.IGNORECASE)
                    steps.append(clean_action)
                else:
                    # Generic action
                    clean_action = re.sub(r'^User\s+', '', single_action, flags=re.IGNORECASE)
                    steps.append(clean_action)
            else:
                # Multiple comma-separated actions
                for part in when_parts:
                    part_lower = part.lower()
                    # Remove "User" prefix if present
                    clean_part = re.sub(r'^User\s+', '', part, flags=re.IGNORECASE)
                    if any(word in part_lower for word in ["enter", "type", "fill", "input"]):
                        steps.append(clean_part)  # e.g., "Enter email: test@example.com"
                    elif any(word in part_lower for word in ["click", "select", "press"]):
                        steps.append(clean_part)  # e.g., "Click Login button"
                    elif any(word in part_lower for word in ["navigate", "go to", "open"]):
                        steps.append(clean_part)  # e.g., "Navigate to dashboard"
                    elif part.strip():
                        steps.append(clean_part)  # Include other actions
        
        # Then: Assertions → Verify, check, wait
        then = scenario.get("then", "")
        if then:
            if not then.lower().startswith("verify"):
                steps.append(f"Verify: {then}")
            else:
                steps.append(then)
        
        # If no steps generated, create a basic step from title
        if not steps:
            title = scenario.get("title", "")
            if title:
                steps.append(f"Execute: {title}")
            else:
                steps.append("Execute scenario")
        
        return steps
    
    def _calculate_steps_confidence(self, steps: List[str], scenario: Dict) -> float:
        """Calculate confidence score based on test steps quality"""
        confidence = 0.7  # Base confidence
        
        # Check for required elements
        if len(steps) >= 3:  # At least 3 steps (navigation, action, verification)
            confidence += 0.1
        if any("navigate" in step.lower() for step in steps):
            confidence += 0.1
        if any("verify" in step.lower() or "check" in step.lower() for step in steps):
            confidence += 0.05
        if any("click" in step.lower() or "enter" in step.lower() or "type" in step.lower() for step in steps):
            confidence += 0.05
        
        # Check for scenario coverage
        given = scenario.get("given", "").lower()
        when = scenario.get("when", "").lower()
        then = scenario.get("then", "").lower()
        
        steps_text = " ".join(steps).lower()
        if any(word in steps_text for word in given.split()[:3] if len(word) > 3):
            confidence += 0.05
        if any(word in steps_text for word in when.split()[:3] if len(word) > 3):
            confidence += 0.05
        
        return min(0.95, confidence)
    
    
    def _generate_cache_key(self, scenario: Dict, page_context: Dict) -> str:
        """Generate cache key for scenario"""
        # Use scenario content + page context for cache key
        key_data = {
            "scenario_id": scenario.get("scenario_id"),
            "given": scenario.get("given", ""),
            "when": scenario.get("when", ""),
            "then": scenario.get("then", ""),
            "url": page_context.get("url", "")
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def learn_from_feedback(
        self,
        generation_id: str,
        execution_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Learn from execution feedback - Analyze execution results and generate recommendations.
        
        This method:
        1. Analyzes execution results (pass/fail rates, error patterns)
        2. Identifies patterns in successful vs failed tests
        3. Generates recommendations for RequirementsAgent to improve scenario generation
        4. Returns structured feedback for continuous improvement
        
        Args:
            generation_id: The generation ID from EvolutionAgent
            execution_results: Dict with execution data:
                - test_case_ids: List of test case IDs that were executed
                - execution_summary: Dict with pass/fail counts, error messages, etc.
                - failed_scenarios: List of scenario IDs that failed
                - successful_scenarios: List of scenario IDs that passed
        
        Returns:
            Dict with:
                - status: "success" or "error"
                - insights: List of insights about execution patterns
                - recommendations: List of recommendations for RequirementsAgent
                - metrics: Dict with pass_rate, fail_rate, common_errors, etc.
        """
        logger.info(f"EvolutionAgent: Learning from feedback for generation_id: {generation_id}")
        
        try:
            # Extract execution data
            test_case_ids = execution_results.get("test_case_ids", [])
            execution_summary = execution_results.get("execution_summary", {})
            failed_scenarios = execution_results.get("failed_scenarios", [])
            successful_scenarios = execution_results.get("successful_scenarios", [])
            
            # Query database for execution results if test_case_ids provided
            execution_data = []
            if test_case_ids and self.db:
                try:
                    from app.models.test_execution import TestExecution, ExecutionResult
                    from app.models.test_case import TestCase
                    
                    # Query TestExecution records for these test cases
                    executions = self.db.query(TestExecution).filter(
                        TestExecution.test_case_id.in_(test_case_ids),
                        TestExecution.status == "completed"
                    ).all()
                    
                    for exec in executions:
                        test_case = self.db.query(TestCase).filter(
                            TestCase.id == exec.test_case_id
                        ).first()
                        
                        if test_case:
                            execution_data.append({
                                "test_case_id": exec.test_case_id,
                                "scenario_id": test_case.test_metadata.get("scenario_id") if isinstance(test_case.test_metadata, dict) else None,
                                "result": exec.result.value if exec.result else None,
                                "status": exec.status.value if exec.status else None,
                                "passed_steps": exec.passed_steps or 0,
                                "failed_steps": exec.failed_steps or 0,
                                "total_steps": exec.total_steps or 0,
                                "error_message": exec.error_message,
                                "duration_seconds": exec.duration_seconds
                            })
                    
                    logger.info(f"Retrieved {len(execution_data)} execution records from database")
                except Exception as e:
                    logger.warning(f"Failed to query execution data from database: {e}")
            
            # Analyze execution results
            total_executions = len(execution_data) or len(test_case_ids)
            if total_executions == 0:
                logger.warning("No execution data available for feedback analysis")
                return {
                    "status": "no_data",
                    "generation_id": generation_id,
                    "message": "No execution results available for analysis",
                    "insights": [],
                    "recommendations": [],
                    "metrics": {}
                }
            
            # Calculate metrics
            passed = sum(1 for e in execution_data if e.get("result") == "pass") or len(successful_scenarios)
            failed = sum(1 for e in execution_data if e.get("result") == "fail") or len(failed_scenarios)
            total = total_executions
            
            pass_rate = (passed / total * 100) if total > 0 else 0
            fail_rate = (failed / total * 100) if total > 0 else 0
            
            # Collect error patterns
            error_messages = []
            for e in execution_data:
                if e.get("error_message"):
                    error_messages.append(e["error_message"])
            
            # Identify common error patterns
            common_errors = {}
            for error in error_messages:
                # Extract key error patterns (simplified)
                if "selector" in error.lower() or "element not found" in error.lower():
                    common_errors["selector_issues"] = common_errors.get("selector_issues", 0) + 1
                elif "timeout" in error.lower() or "wait" in error.lower():
                    common_errors["timeout_issues"] = common_errors.get("timeout_issues", 0) + 1
                elif "assertion" in error.lower() or "expected" in error.lower():
                    common_errors["assertion_failures"] = common_errors.get("assertion_failures", 0) + 1
            
            # Generate insights
            insights = []
            if pass_rate >= 80:
                insights.append(f"High success rate ({pass_rate:.1f}%) - Test scenarios are well-designed")
            elif pass_rate < 50:
                insights.append(f"Low success rate ({pass_rate:.1f}%) - Scenarios may need refinement")
            
            if common_errors.get("selector_issues", 0) > 0:
                insights.append(f"Selector issues detected ({common_errors['selector_issues']} cases) - Consider more robust selectors")
            
            if common_errors.get("timeout_issues", 0) > 0:
                insights.append(f"Timeout issues detected ({common_errors['timeout_issues']} cases) - Scenarios may need wait conditions")
            
            # Generate recommendations for RequirementsAgent
            recommendations = []
            if fail_rate > 30:
                recommendations.append("Focus on generating more stable scenarios with robust selectors")
                recommendations.append("Prioritize scenarios that test core functionality over edge cases")
            
            if common_errors.get("selector_issues", 0) > total * 0.2:
                recommendations.append("Generate scenarios with multiple selector strategies (ID, class, text, XPath)")
                recommendations.append("Include wait conditions for dynamic elements")
            
            if pass_rate < 50:
                recommendations.append("Review failed scenarios and adjust scenario generation to avoid similar patterns")
                recommendations.append("Focus on high-priority scenarios that are more likely to succeed")
            
            # Calculate average execution time
            avg_duration = sum(e.get("duration_seconds", 0) for e in execution_data) / len(execution_data) if execution_data else 0
            
            metrics = {
                "total_executions": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": pass_rate,
                "fail_rate": fail_rate,
                "common_errors": common_errors,
                "avg_duration_seconds": avg_duration
            }
            
            logger.info(f"Feedback analysis complete: {pass_rate:.1f}% pass rate, {len(insights)} insights, {len(recommendations)} recommendations")
            
            return {
                "status": "success",
                "generation_id": generation_id,
                "insights": insights,
                "recommendations": recommendations,
                "metrics": metrics,
                "execution_data_count": len(execution_data)
            }
            
        except Exception as e:
            logger.error(f"Error in learn_from_feedback: {e}", exc_info=True)
            return {
                "status": "error",
                "generation_id": generation_id,
                "error": str(e),
                "insights": [],
                "recommendations": [],
                "metrics": {}
            }
    
    async def calculate_performance_score(
        self,
        task_result: TaskResult,
        execution_results: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, Any]:
        """
        Calculate EvolutionAgent performance score.
        
        Dimensions:
        - Code Generation Accuracy (40%): Syntax correctness, test structure validity
        - Test Execution Success Rate (35%): How many generated tests actually pass
        - Code Quality (15%): Maintainability, readability, best practices
        - Efficiency (10%): Generation time, token usage, cost
        """
        if not task_result.success:
            return {
                "overall_score": 0.0,
                "component_scores": {},
                "grade": "F",
                "recommendations": ["Fix generation errors"]
            }
        
        result = task_result.result
        test_count = result.get("test_count", 0)
        
        # Component 1: Steps Generation Accuracy (40%)
        # Extract steps from result
        test_cases = result.get("test_cases", [])
        if test_cases:
            all_steps = []
            for tc in test_cases:
                all_steps.extend(tc.get("steps", []))
            syntax_accuracy = self._validate_steps_syntax(all_steps) if all_steps else 0.0
        else:
            syntax_accuracy = 0.0
        
        # Component 2: Test Execution Success Rate (35%)
        if execution_results:
            execution_success = self._calculate_execution_success_rate(execution_results)
        else:
            execution_success = 0.85  # Default if no execution results yet
        
        # Component 3: Steps Quality (15%)
        steps_quality = self._analyze_steps_quality(test_cases)
        
        # Component 4: Efficiency (10%)
        efficiency = self._calculate_efficiency(
            task_result.execution_time_seconds,
            task_result.metadata.get("token_usage", 0) if task_result.metadata else 0
        )
        
        # Overall score
        overall_score = (
            syntax_accuracy * 0.40 +
            execution_success * 0.35 +
            code_quality * 0.15 +
            efficiency * 0.10
        )
        
        # Grade
        if overall_score >= 0.85:
            grade = "A"
        elif overall_score >= 0.75:
            grade = "B"
        elif overall_score >= 0.65:
            grade = "C"
        elif overall_score >= 0.50:
            grade = "D"
        else:
            grade = "F"
        
        # Recommendations
        recommendations = self._generate_recommendations(
            syntax_accuracy, execution_success, code_quality, efficiency
        )
        
        return {
            "overall_score": round(overall_score, 3),
            "component_scores": {
                "syntax_accuracy": round(syntax_accuracy, 3),
                "execution_success": round(execution_success, 3),
                "steps_quality": round(steps_quality, 3),
                "efficiency": round(efficiency, 3)
            },
            "grade": grade,
            "recommendations": recommendations
        }
    
    def _validate_steps_syntax(self, steps: List[str]) -> float:
        """Validate test steps syntax (basic checks)"""
        score = 0.0
        
        # Check for minimum steps
        if len(steps) >= 2:
            score += 0.3
        
        # Check for navigation step
        if any("navigate" in step.lower() for step in steps):
            score += 0.3
        
        # Check for action steps
        if any(word in " ".join(steps).lower() for word in ["click", "enter", "type", "select"]):
            score += 0.2
        
        # Check for verification/assertion steps
        if any("verify" in step.lower() or "check" in step.lower() for step in steps):
            score += 0.2
        
        return min(1.0, score)
    
    def _calculate_execution_success_rate(self, execution_results: Dict[str, Dict]) -> float:
        """Calculate execution success rate from actual results"""
        if not execution_results:
            return 0.85  # Default
        
        total_tests = len(execution_results)
        passed_tests = sum(1 for r in execution_results.values() if r.get("status") == "passed")
        
        if total_tests == 0:
            return 0.85
        
        return passed_tests / total_tests
    
    def _analyze_steps_quality(self, test_cases: List[Dict]) -> float:
        """Analyze test steps quality (clarity, completeness)"""
        score = 0.5  # Base score
        
        if not test_cases:
            return 0.0
        
        # Check for step clarity (average step length)
        all_steps = []
        for tc in test_cases:
            all_steps.extend(tc.get("steps", []))
        
        if all_steps:
            avg_length = sum(len(step) for step in all_steps) / len(all_steps)
            if 20 <= avg_length <= 100:  # Reasonable step length
                score += 0.2
            
            # Check for specific action words (indicates clarity)
            action_words = ["click", "enter", "type", "navigate", "verify", "check", "select"]
            if any(word in " ".join(all_steps).lower() for word in action_words):
                score += 0.2
            
            # Check for completeness (has navigation, action, verification)
            has_nav = any("navigate" in step.lower() for step in all_steps)
            has_action = any(word in " ".join(all_steps).lower() for word in ["click", "enter", "type"])
            has_verify = any("verify" in step.lower() or "check" in step.lower() for step in all_steps)
            if has_nav and has_action and has_verify:
                score += 0.1
        
        return min(1.0, score)
    
    def _calculate_efficiency(self, execution_time: float, token_usage: int) -> float:
        """Calculate efficiency score (time and cost)"""
        # Normalize: faster and cheaper = better
        # Target: <5 seconds, <2000 tokens
        time_score = max(0.0, 1.0 - (execution_time / 10.0))  # 10s = 0, 0s = 1.0
        token_score = max(0.0, 1.0 - (token_usage / 3000.0))  # 3000 tokens = 0, 0 = 1.0
        
        return (time_score + token_score) / 2.0
    
    def _generate_recommendations(
        self,
        syntax_accuracy: float,
        execution_success: float,
        code_quality: float,
        efficiency: float
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if syntax_accuracy < 0.8:
            recommendations.append("Improve steps syntax validation - ensure all tests have navigation, actions, and verifications")
        
        if execution_success < 0.8:
            recommendations.append("Improve test reliability - review step clarity and execution strategies")
        
        if steps_quality < 0.7:
            recommendations.append("Enhance steps quality - improve clarity, completeness, and action specificity")
        
        if efficiency < 0.7:
            recommendations.append("Optimize generation efficiency - reduce token usage, improve caching")
        
        if not recommendations:
            recommendations.append("Performance is good - continue monitoring")
        
        return recommendations

