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
            
            for scenario in scenarios:
                scenario_id = scenario.get("scenario_id", "UNKNOWN")
                
                # Check cache first (if enabled)
                cache_key = self._generate_cache_key(scenario, page_context)
                if self.cache_enabled and cache_key in self.steps_cache:
                    logger.info(f"Cache hit for scenario {scenario_id}")
                    cached_result = self.steps_cache[cache_key]
                    generated_test_cases.append({
                        "scenario_id": scenario_id,
                        "steps": cached_result["steps"],
                        "confidence": cached_result["confidence"],
                        "from_cache": True
                    })
                    continue
                
                # Generate test steps using LLM or template
                if self.use_llm and self.llm_client:
                    steps_result = await self._generate_test_steps_with_llm(
                        scenario, risk_scores, prioritization, page_context, test_data
                    )
                else:
                    steps_result = self._generate_test_steps_from_template(
                        scenario, page_context
                    )
                
                if steps_result:
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
            
            # Store test cases in database (if database session available)
            db_test_case_ids = []
            if db_session:
                try:
                    db_test_case_ids = await self._store_test_cases_in_database(
                        db_session, generated_test_cases, scenarios, 
                        risk_scores, prioritization, page_context, generation_id
                    )
                    logger.info(f"Stored {len(db_test_case_ids)} test cases in database")
                except Exception as e:
                    logger.error(f"Failed to store test cases in database: {e}", exc_info=True)
                    # Continue even if database storage fails
            else:
                logger.warning("No database session available - test cases not stored in database")
            
            # Calculate overall confidence
            if generated_test_cases:
                overall_confidence = sum(t.get("confidence", 0.85) for t in generated_test_cases) / len(generated_test_cases)
            else:
                overall_confidence = 0.0
            
            # Prepare result
            result = {
                "generation_id": generation_id,
                "test_count": len(generated_test_cases),
                "test_case_ids": db_test_case_ids,  # Database IDs
                "test_cases": generated_test_cases,  # Test steps data
                "confidence": round(overall_confidence, 2),
                "prompt_variant": self.current_variant,
                "cache_hits": sum(1 for t in generated_test_cases if t.get("from_cache", False)),
                "cache_misses": sum(1 for t in generated_test_cases if not t.get("from_cache", False)),
                "stored_in_database": len(db_test_case_ids) > 0
            }
            
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
                    "database_ids": db_test_case_ids
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
        test_data: List[Dict]
    ) -> Optional[Dict]:
        """Generate test steps using Azure OpenAI GPT-4o"""
        try:
            # Build prompt using current variant
            prompt_builder = self.prompt_variants.get(self.current_variant, self._build_prompt_variant_1)
            prompt = prompt_builder(scenario, risk_scores, prioritization, page_context, test_data)
            
            # Call LLM (Azure OpenAI create is synchronous, not async)
            response = self.llm_client.client.chat.completions.create(
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
        test_data: List[Dict]
    ) -> str:
        """Variant 1: Detailed, explicit prompt with full context - generates test steps"""
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

**Requirements:**
1. Generate an array of executable test steps (as strings)
2. Each step should be a clear, actionable instruction
3. Steps should be in execution order
4. Include navigation, actions, and assertions
5. Use natural language that can be executed by a test automation engine
6. Be specific with selectors and values where applicable

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
    
    def _build_prompt_variant_2(
        self,
        scenario: Dict,
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        test_data: List[Dict]
    ) -> str:
        """Variant 2: Concise, focused prompt - generates test steps"""
        title = scenario.get("title", "")
        given = scenario.get("given", "")
        when = scenario.get("when", "")
        then = scenario.get("then", "")
        url = page_context.get("url", "https://example.com")
        
        prompt = f"""Generate executable test steps as a JSON array:

Given: {given}
When: {when}
Then: {then}
URL: {url}

Return JSON: {{"steps": ["step1", "step2", ...]}}"""
        
        return prompt
    
    def _build_prompt_variant_3(
        self,
        scenario: Dict,
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        test_data: List[Dict]
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
        
        prompt = f"""Generate test steps using pattern for {scenario_type} scenarios.

Scenario: {title}
Given: {given}
When: {when}
Then: {then}
URL: {url}

Pattern: {pattern_hint}

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
        Learn from execution feedback (for future enhancement - Sprint 9).
        
        This method will be implemented in Sprint 9 to:
        1. Analyze execution results (pass/fail rates)
        2. Identify patterns in successful vs failed tests
        3. Update prompt templates based on feedback
        4. Store patterns for reuse
        """
        logger.info(f"Feedback learning not yet implemented (Sprint 9) - generation_id: {generation_id}")
        return {
            "status": "not_implemented",
            "generation_id": generation_id,
            "message": "Feedback learning will be implemented in Sprint 9"
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

