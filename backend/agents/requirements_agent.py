"""
RequirementsAgent - Extracts test requirements from UI observations
Follows BDD, ISTQB, WCAG 2.1, OWASP security standards
"""
from agents.base_agent import BaseAgent, AgentCapability, TaskContext, TaskResult
from typing import Dict, List, Tuple, Optional, Any
import asyncio
import time
import re
import json
import logging
from enum import Enum
from llm.azure_client import AzureClient, get_azure_client

logger = logging.getLogger(__name__)


class ScenarioPriority(Enum):
    """Test scenario priority levels (ISTQB standard)"""
    CRITICAL = "critical"  # Core functionality, blocking issues
    HIGH = "high"          # Important features, major user flows
    MEDIUM = "medium"      # Secondary features, edge cases
    LOW = "low"            # Nice-to-have, cosmetic issues


class ScenarioType(Enum):
    """Test scenario categories (ISO 29119 standard)"""
    FUNCTIONAL = "functional"         # Feature behavior
    ACCESSIBILITY = "accessibility"   # WCAG 2.1 compliance
    SECURITY = "security"             # OWASP security tests
    PERFORMANCE = "performance"       # Load, response time
    USABILITY = "usability"          # UX, navigation
    EDGE_CASE = "edge_case"          # Boundary, error handling


class Scenario:
    """BDD-style test scenario (Gherkin format)"""
    def __init__(self, scenario_id: str, title: str, 
                 given: str, when: str, then: str,
                 priority: ScenarioPriority,
                 scenario_type: ScenarioType,
                 test_data: List[Dict] = None,
                 tags: List[str] = None):
        self.scenario_id = scenario_id
        self.title = title
        self.given = given  # Preconditions
        self.when = when    # Actions
        self.then = then    # Expected results
        self.priority = priority
        self.scenario_type = scenario_type
        self.test_data = test_data or []
        self.tags = tags or []
        self.confidence = 0.0


class RequirementsAgent(BaseAgent):
    """
    Extracts test requirements from UI observations.
    
    Industry Standards:
    - BDD (Gherkin syntax)
    - ISTQB test design techniques
    - WCAG 2.1 accessibility
    - OWASP Top 10 security
    - Page Object Model organization
    """
    
    def __init__(self, agent_id: str, agent_type: str, priority: int, 
                 message_queue, config: Optional[Dict] = None):
        """Initialize RequirementsAgent with optional LLM support"""
        super().__init__(agent_id, agent_type, priority, message_queue, config)
        
        # Initialize LLM client if enabled
        self.use_llm = config.get("use_llm", False) if config else False
        self.llm_client = None
        if self.use_llm:
            self.llm_client = get_azure_client()
            if self.llm_client.enabled:
                logger.info("RequirementsAgent initialized with LLM enhancement (Azure OpenAI)")
            else:
                logger.warning("LLM requested but not available, falling back to pattern-based generation")
                self.use_llm = False
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability("requirement_extraction", "1.0.0", confidence_threshold=0.7),
            AgentCapability("scenario_generation", "1.0.0", confidence_threshold=0.8),
            AgentCapability("test_data_extraction", "1.0.0", confidence_threshold=0.75)
        ]
    
    async def can_handle(self, task: TaskContext) -> Tuple[bool, float]:
        """Check if agent can handle task"""
        if task.task_type in ["requirement_extraction", "scenario_generation"]:
            # Check if input has required UI elements
            ui_elements = task.payload.get("ui_elements", [])
            if len(ui_elements) > 0:
                confidence = min(0.95, 0.7 + (len(ui_elements) / 100) * 0.25)
                return True, confidence
            return True, 0.7
        return False, 0.0
    
    async def execute_task(self, task: TaskContext) -> TaskResult:
        """Extract requirements from UI observations"""
        start_time = time.time()

        progress_callback = task.payload.get("progress_callback")
        cancel_check = task.payload.get("cancel_check")

        def _emit_progress(progress: float, message: str, **extra: Any):
            if not callable(progress_callback):
                return
            payload: Dict[str, Any] = {"progress": max(0.0, min(1.0, float(progress))), "message": message}
            payload.update(extra)
            try:
                progress_callback(payload)
            except Exception as emit_error:
                logger.debug(f"RequirementsAgent: progress_callback failed: {emit_error}")

        def _is_cancelled() -> bool:
            if not callable(cancel_check):
                return False
            try:
                return bool(cancel_check())
            except Exception as cancel_error:
                logger.debug(f"RequirementsAgent: cancel_check failed: {cancel_error}")
                return False

        def _cancelled_result() -> TaskResult:
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result={"scenarios": [], "test_data": [], "coverage_metrics": {}},
                confidence=0.0,
                execution_time_seconds=time.time() - start_time,
                metadata={"cancelled": True},
            )
        
        try:
            # Extract input data
            ui_elements = task.payload.get("ui_elements", [])
            page_structure = task.payload.get("page_structure", {})
            page_context = task.payload.get("page_context", {})
            user_instruction = task.payload.get("user_instruction", "")  # NEW: User's specific test requirement
            test_requirement = task.payload.get("test_requirement", "")  # Alternative field name
            scenario_types_filter = task.payload.get("scenario_types") or []
            max_scenarios = task.payload.get("max_scenarios")
            focus_goal_only = bool(task.payload.get("focus_goal_only"))

            if isinstance(scenario_types_filter, list):
                scenario_types_filter = {s.lower() for s in scenario_types_filter}
            else:
                scenario_types_filter = set()
            
            # Use test_requirement if user_instruction is empty
            if not user_instruction and test_requirement:
                user_instruction = test_requirement
            
            if user_instruction:
                logger.info(f"RequirementsAgent: User instruction provided: '{user_instruction}'")
                logger.info(f"RequirementsAgent: Will prioritize scenarios matching user intent")
            
            logger.info(f"RequirementsAgent: Processing {len(ui_elements)} UI elements for {page_structure.get('url', 'unknown')}")
            if scenario_types_filter:
                logger.info(f"RequirementsAgent: scenario_types filter applied: {sorted(scenario_types_filter)}")
            if max_scenarios:
                logger.info(f"RequirementsAgent: max_scenarios={max_scenarios}")
            if focus_goal_only and user_instruction:
                logger.info("RequirementsAgent: focus_goal_only enabled (goal-focused mode)")

            _emit_progress(0.05, "Grouping UI elements", ui_elements=len(ui_elements))
            if _is_cancelled():
                logger.info("RequirementsAgent: Cancelled before Stage 1")
                return _cancelled_result()
            
            # Stage 1: Group elements by page/component (Page Object Model)
            logger.debug("RequirementsAgent: Stage 1 - Grouping elements by page/component...")
            element_groups = self._group_elements_by_page(ui_elements, page_structure)
            logger.info(f"RequirementsAgent: Grouped elements into {len(element_groups)} sections")

            _emit_progress(0.18, "Mapping user journeys", groups=len(element_groups))
            if _is_cancelled():
                logger.info("RequirementsAgent: Cancelled after Stage 1")
                return _cancelled_result()
            
            # Stage 2: Map user journeys (multi-step flows)
            logger.debug("RequirementsAgent: Stage 2 - Mapping user journeys...")
            user_journeys = self._map_user_journeys(element_groups, page_context)
            logger.info(f"RequirementsAgent: Mapped {len(user_journeys)} user journeys")

            _emit_progress(0.32, "Generating functional scenarios", user_journeys=len(user_journeys))
            if _is_cancelled():
                logger.info("RequirementsAgent: Cancelled after Stage 2")
                return _cancelled_result()
            
            # Stage 3: Generate functional test scenarios
            logger.debug("RequirementsAgent: Stage 3 - Generating functional test scenarios...")
            execution_feedback = task.payload.get("execution_feedback", {})
            if execution_feedback:
                logger.info("RequirementsAgent: Using execution feedback to improve scenario generation")

            flow_steps = task.payload.get("flow_steps", [])
            pages = task.payload.get("pages", [])
            navigation_flow = task.payload.get("navigation_flow") or {}
            if flow_steps:
                logger.info(f"RequirementsAgent: Using observed flow from crawl ({len(flow_steps)} steps) for end-to-end scenario")

            include_functional = not scenario_types_filter or "functional" in scenario_types_filter
            include_accessibility = not scenario_types_filter or "accessibility" in scenario_types_filter
            include_security = not scenario_types_filter or "security" in scenario_types_filter
            include_edge = not scenario_types_filter or "edge_case" in scenario_types_filter

            functional_scenarios: List[Scenario] = []
            if include_functional:
                functional_scenarios = await self._generate_functional_scenarios(
                    user_journeys, element_groups, page_context, page_structure, user_instruction, execution_feedback,
                    flow_steps=flow_steps, pages=pages, navigation_flow=navigation_flow
                )
                logger.info(f"RequirementsAgent: Generated {len(functional_scenarios)} functional scenarios")
            else:
                logger.info("RequirementsAgent: Functional scenarios disabled by scenario_types filter")

            _emit_progress(0.48, "Generating accessibility scenarios", scenarios_generated=len(functional_scenarios))
            if _is_cancelled():
                logger.info("RequirementsAgent: Cancelled after Stage 3")
                return _cancelled_result()
            
            # Stage 4: Generate accessibility scenarios (WCAG 2.1)
            accessibility_scenarios: List[Scenario] = []
            if include_accessibility:
                logger.debug("RequirementsAgent: Stage 4 - Generating accessibility scenarios...")
                accessibility_scenarios = self._generate_accessibility_scenarios(ui_elements)
                logger.info(f"RequirementsAgent: Generated {len(accessibility_scenarios)} accessibility scenarios")
            else:
                logger.info("RequirementsAgent: Accessibility scenarios disabled by scenario_types filter")

            _emit_progress(0.60, "Generating security scenarios", scenarios_generated=(len(functional_scenarios) + len(accessibility_scenarios)))
            if _is_cancelled():
                logger.info("RequirementsAgent: Cancelled after Stage 4")
                return _cancelled_result()
            
            # Stage 5: Generate security scenarios (OWASP)
            security_scenarios: List[Scenario] = []
            if include_security:
                logger.debug("RequirementsAgent: Stage 5 - Generating security scenarios...")
                security_scenarios = self._generate_security_scenarios(ui_elements, page_context)
                logger.info(f"RequirementsAgent: Generated {len(security_scenarios)} security scenarios")
            else:
                logger.info("RequirementsAgent: Security scenarios disabled by scenario_types filter")

            _emit_progress(0.72, "Generating edge-case scenarios", scenarios_generated=(len(functional_scenarios) + len(accessibility_scenarios) + len(security_scenarios)))
            if _is_cancelled():
                logger.info("RequirementsAgent: Cancelled after Stage 5")
                return _cancelled_result()
            
            # Stage 6: Generate edge case scenarios
            edge_case_scenarios: List[Scenario] = []
            if include_edge:
                logger.debug("RequirementsAgent: Stage 6 - Generating edge case scenarios...")
                edge_case_scenarios = self._generate_edge_case_scenarios(ui_elements)
                logger.info(f"RequirementsAgent: Generated {len(edge_case_scenarios)} edge case scenarios")
            else:
                logger.info("RequirementsAgent: Edge case scenarios disabled by scenario_types filter")
            
            # Combine all scenarios
            all_scenarios = (
                functional_scenarios +
                accessibility_scenarios +
                security_scenarios +
                edge_case_scenarios
            )
            
            # Deduplicate scenario_ids: LLM may assign IDs like REQ-A-xxx, REQ-S-xxx
            # that conflict with template-generated accessibility/security/edge scenarios.
            # Re-number any duplicates to ensure uniqueness.
            seen_ids = set()
            for scenario in all_scenarios:
                if scenario.scenario_id in seen_ids:
                    # Generate a new unique ID based on type
                    type_prefix = {
                        ScenarioType.FUNCTIONAL: "F",
                        ScenarioType.ACCESSIBILITY: "A",
                        ScenarioType.SECURITY: "S",
                        ScenarioType.EDGE_CASE: "E",
                        ScenarioType.USABILITY: "U",
                        ScenarioType.PERFORMANCE: "P",
                    }.get(scenario.scenario_type, "X")
                    counter = 1
                    while f"REQ-{type_prefix}-{counter:03d}" in seen_ids:
                        counter += 1
                    old_id = scenario.scenario_id
                    scenario.scenario_id = f"REQ-{type_prefix}-{counter:03d}"
                    logger.debug(f"RequirementsAgent: Renumbered duplicate scenario_id {old_id} -> {scenario.scenario_id}")
                seen_ids.add(scenario.scenario_id)

            _emit_progress(0.84, "Extracting test data", scenarios_total=len(all_scenarios))
            if _is_cancelled():
                logger.info("RequirementsAgent: Cancelled after Stage 6")
                return _cancelled_result()
            
            # Optional goal-focused reordering and limiting
            if all_scenarios:
                # First, sort by priority (critical/high first)
                priority_order = {
                    ScenarioPriority.CRITICAL: 0,
                    ScenarioPriority.HIGH: 1,
                    ScenarioPriority.MEDIUM: 2,
                    ScenarioPriority.LOW: 3,
                }

                def _base_order(s: Scenario) -> int:
                    return priority_order.get(s.priority, 2)

                if focus_goal_only and user_instruction:
                    scored = [
                        (self._score_scenario_relevance(s, user_instruction), s)
                        for s in all_scenarios
                    ]
                    # Filter out very low relevance, but keep a fallback if everything is low.
                    filtered = [s for score, s in scored if score >= 0.15]
                    if not filtered:
                        filtered = [s for _, s in scored]

                    # Rebuild scores for filtered scenarios
                    scored_filtered = [
                        (self._score_scenario_relevance(s, user_instruction), s)
                        for s in filtered
                    ]

                    def _sort_key(item: Tuple[float, Scenario]) -> Tuple[float, int]:
                        score, scen = item
                        return (-score, _base_order(scen))

                    scored_filtered.sort(key=_sort_key)
                    all_scenarios = [s for score, s in scored_filtered]
                else:
                    all_scenarios.sort(key=_base_order)

                # Apply max_scenarios limit if provided
                if isinstance(max_scenarios, int) and max_scenarios > 0:
                    all_scenarios = all_scenarios[:max_scenarios]
                    logger.info(f"RequirementsAgent: Trimmed scenarios to max_scenarios={max_scenarios}")

            # Stage 7: Extract test data
            test_data = self._extract_test_data(ui_elements)
            logger.debug(f"Extracted {len(test_data)} test data fields")

            _emit_progress(0.92, "Calculating coverage metrics", test_data_fields=len(test_data))
            if _is_cancelled():
                logger.info("RequirementsAgent: Cancelled after Stage 7")
                return _cancelled_result()
            
            # Stage 8: Calculate coverage metrics
            coverage_metrics = self._calculate_coverage(ui_elements, all_scenarios)
            
            # Prepare output
            result = {
                "scenarios": [self._scenario_to_dict(s) for s in all_scenarios],
                "test_data": test_data,
                "coverage_metrics": coverage_metrics,
                "element_groups": {k: len(v) for k, v in element_groups.items()},
                "user_journeys": user_journeys,
                "quality_indicators": {
                    "completeness": coverage_metrics["ui_coverage_percent"],
                    "confidence": self._calculate_confidence(all_scenarios),
                    "scenario_count": len(all_scenarios),
                    "priority_distribution": self._get_priority_distribution(all_scenarios)
                }
            }
            
            logger.info(f"RequirementsAgent completed: {len(all_scenarios)} scenarios, "
                       f"{coverage_metrics['ui_coverage_percent']:.1f}% coverage, "
                       f"confidence={result['quality_indicators']['confidence']:.2f}")

            _emit_progress(1.0, "Requirements extraction complete", scenarios_total=len(all_scenarios))
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                confidence=result["quality_indicators"]["confidence"],
                execution_time_seconds=time.time() - start_time,
                metadata={"token_usage": self._estimate_token_usage(ui_elements, all_scenarios)}
            )
            
        except Exception as e:
            logger.error(f"RequirementsAgent failed: {e}", exc_info=True)
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                confidence=0.0,
                execution_time_seconds=time.time() - start_time
            )
    
    def _group_elements_by_page(self, ui_elements: List[Dict], 
                                 page_structure: Dict) -> Dict[str, List[Dict]]:
        """Group UI elements by page/component (Page Object Model)"""
        groups = {}
        url = page_structure.get("url", "unknown")
        
        # Group by element type and location
        for element in ui_elements:
            # Extract page section from selector
            selector = element.get("selector", "")
            section = self._extract_section_from_selector(selector)
            
            group_key = f"{section}"
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(element)
        
        return groups
    
    def _extract_section_from_selector(self, selector: str) -> str:
        """Extract page section from CSS selector"""
        # Common section identifiers
        sections = ["header", "nav", "main", "footer", "sidebar", "form", "modal"]
        selector_lower = selector.lower()
        
        for section in sections:
            if section in selector_lower:
                return section
        
        # Extract ID or class that suggests section
        if "#" in selector:
            return selector.split("#")[1].split(" ")[0].split(".")[0]
        if "." in selector:
            return selector.split(".")[1].split(" ")[0].split("#")[0]
        
        return "main"
    
    def _map_user_journeys(self, element_groups: Dict, 
                           page_context: Dict) -> List[Dict]:
        """Map multi-step user journeys (industry best practice)"""
        journeys = []
        page_type = page_context.get("page_type", "unknown")
        
        # Common user journey patterns
        if page_type == "login":
            journeys.append({
                "journey_name": "User Login Flow",
                "steps": ["Navigate to login page", "Enter credentials", 
                          "Click submit", "Verify dashboard redirect"],
                "priority": ScenarioPriority.CRITICAL
            })
        elif page_type == "registration":
            journeys.append({
                "journey_name": "User Registration Flow",
                "steps": ["Fill registration form", "Accept terms", 
                          "Submit", "Verify email confirmation"],
                "priority": ScenarioPriority.CRITICAL
            })
        elif page_type in ["checkout", "pricing"]:
            journeys.append({
                "journey_name": "Purchase Flow",
                "steps": ["Select plan", "Enter payment info", 
                          "Confirm order", "Verify confirmation"],
                "priority": ScenarioPriority.CRITICAL
            })
        else:
            # Generic navigation journey
            journeys.append({
                "journey_name": "Page Navigation",
                "steps": ["Load page", "Interact with elements", 
                          "Verify content", "Navigate away"],
                "priority": ScenarioPriority.HIGH
            })
        
        return journeys

    def _score_scenario_relevance(self, scenario: "Scenario", user_instruction: str) -> float:
        """Heuristic relevance score between scenario text and user instruction (0.0–1.0)."""
        if not user_instruction:
            return 0.5

        import re

        def _tokenize(text: str) -> List[str]:
            tokens = re.split(r"[^a-zA-Z0-9\u4e00-\u9fff]+", text.lower())
            return [t for t in tokens if t]

        user_tokens = set(_tokenize(user_instruction))
        if not user_tokens:
            return 0.5

        scenario_text = " ".join([
            scenario.title or "",
            scenario.given or "",
            scenario.when or "",
            scenario.then or "",
        ])
        scenario_tokens = set(_tokenize(scenario_text))
        if not scenario_tokens:
            return 0.0

        overlap = user_tokens & scenario_tokens
        score = len(overlap) / len(user_tokens)
        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))
    
    async def _generate_functional_scenarios(self, user_journeys: List[Dict],
                                             element_groups: Dict,
                                             page_context: Dict,
                                             page_structure: Dict,
                                             user_instruction: str = "",
                                             execution_feedback: Dict = {},
                                             flow_steps: Optional[List[Dict]] = None,
                                             pages: Optional[List[Dict]] = None,
                                             navigation_flow: Optional[Dict] = None) -> List[Scenario]:
        """Generate functional test scenarios using LLM or patterns.
        
        When flow_steps/pages from ObservationAgent (browser-use crawl) are provided,
        the LLM is instructed to generate at least one end-to-end scenario that follows
        the observed flow to the user's goal (e.g. complete subscription to success page).
        """
        scenarios = []
        flow_steps = flow_steps or []
        pages = pages or []
        navigation_flow = navigation_flow or {}
        
        # Try LLM-based generation first if enabled
        if self.use_llm and self.llm_client:
            logger.info("Using LLM for high-quality scenario generation")
            # Reconstruct ui_elements from element_groups
            ui_elements = []
            for group_elements in element_groups.values():
                ui_elements.extend(group_elements)
            
            llm_scenarios = await self._generate_scenarios_with_llm(
                ui_elements, page_structure, page_context, user_instruction, execution_feedback,
                flow_steps=flow_steps, pages=pages, navigation_flow=navigation_flow
            )
            
            if llm_scenarios:
                scenarios.extend(llm_scenarios)
                logger.info(f"LLM generated {len(llm_scenarios)} scenarios with avg confidence "
                           f"{sum(s.confidence for s in llm_scenarios)/len(llm_scenarios):.2f}")
                return scenarios  # Return LLM scenarios if successful
            else:
                logger.warning("LLM scenario generation failed, falling back to patterns")
        
        # Fallback: Pattern-based scenario generation
        logger.info("Using pattern-based scenario generation")
        pattern_scenarios = self._generate_scenarios_from_patterns(
            user_journeys, element_groups
        )
        scenarios.extend(pattern_scenarios)
        
        # Generate scenarios for interactive elements
        for section, elements in element_groups.items():
            buttons = [e for e in elements if e.get("type") == "button"]
            links = [e for e in elements if e.get("type") == "link"]
            
            # Button scenarios
            for idx, button in enumerate(buttons[:3]):  # Limit to first 3
                scenario = Scenario(
                    scenario_id=f"REQ-F-{len(scenarios)+1:03d}",
                    title=f"Click {button.get('text', 'button')} in {section}",
                    given=f"User is on the page and {section} section is visible",
                    when=f"User clicks {button.get('text', 'button')} button",
                    then=f"System performs expected action for {button.get('text', 'button')}",
                    priority=ScenarioPriority.HIGH,
                    scenario_type=ScenarioType.FUNCTIONAL,
                    tags=["button-interaction", section]
                )
                scenario.confidence = 0.80
                scenarios.append(scenario)
            
            # Link scenarios
            for idx, link in enumerate(links[:2]):  # Limit to first 2
                scenario = Scenario(
                    scenario_id=f"REQ-F-{len(scenarios)+1:03d}",
                    title=f"Navigate via {link.get('text', 'link')} in {section}",
                    given=f"User is on the page",
                    when=f"User clicks {link.get('text', 'link')} link",
                    then=f"User is navigated to the linked page",
                    priority=ScenarioPriority.MEDIUM,
                    scenario_type=ScenarioType.FUNCTIONAL,
                    tags=["navigation", section]
                )
                scenario.confidence = 0.75
                scenarios.append(scenario)
        
        return scenarios
    
    def _generate_scenarios_from_patterns(self, user_journeys: List[Dict],
                                          element_groups: Dict) -> List[Scenario]:
        """Pattern-based scenario generation (deterministic fallback)"""
        scenarios = []
        
        for journey in user_journeys:
            # Generate scenario from journey template
            scenario = Scenario(
                scenario_id=f"REQ-P-{len(scenarios)+1:03d}",
                title=journey["journey_name"],
                given=f"User is on the starting page",
                when=f"User completes: {', '.join(journey['steps'])}",
                then=f"Journey completes successfully",
                priority=journey["priority"],
                scenario_type=ScenarioType.FUNCTIONAL,
                tags=["pattern-based", "journey"]
            )
            scenario.confidence = 0.70  # Lower confidence for pattern-based
            scenarios.append(scenario)
        
        return scenarios
    
    def _generate_accessibility_scenarios(self, ui_elements: List[Dict]) -> List[Scenario]:
        """Generate WCAG 2.1 accessibility test scenarios"""
        scenarios = []
        
        # A11y checks (WCAG 2.1 Level AA)
        accessibility_checks = [
            {
                "id": "REQ-A-001",
                "title": "Keyboard Navigation - All Interactive Elements Accessible",
                "given": "User navigates using keyboard only",
                "when": "User presses Tab to cycle through interactive elements",
                "then": "All buttons, links, and form fields are reachable and have visible focus indicators",
                "priority": ScenarioPriority.HIGH
            },
            {
                "id": "REQ-A-002",
                "title": "Screen Reader - Semantic HTML and ARIA Labels",
                "given": "User uses screen reader (NVDA/JAWS)",
                "when": "User navigates the page",
                "then": "All elements have proper ARIA labels and semantic HTML",
                "priority": ScenarioPriority.HIGH
            },
            {
                "id": "REQ-A-003",
                "title": "Color Contrast - WCAG AA Compliance",
                "given": "User has low vision",
                "when": "User views the page",
                "then": "All text has minimum 4.5:1 contrast ratio (3:1 for large text)",
                "priority": ScenarioPriority.MEDIUM
            },
            {
                "id": "REQ-A-004",
                "title": "Text Resize - Content Readable at 200% Zoom",
                "given": "User zooms browser to 200%",
                "when": "User reads content",
                "then": "All content is readable without horizontal scrolling",
                "priority": ScenarioPriority.MEDIUM
            }
        ]
        
        for check in accessibility_checks:
            scenario = Scenario(
                scenario_id=check["id"],
                title=check["title"],
                given=check["given"],
                when=check["when"],
                then=check["then"],
                priority=check["priority"],
                scenario_type=ScenarioType.ACCESSIBILITY,
                tags=["wcag-2.1", "a11y", "compliance"]
            )
            scenario.confidence = 0.90  # High confidence for standard checks
            scenarios.append(scenario)
        
        return scenarios
    
    def _generate_security_scenarios(self, ui_elements: List[Dict], 
                                     page_context: Dict) -> List[Scenario]:
        """Generate OWASP Top 10 security test scenarios"""
        scenarios = []
        
        # Check for forms (common attack vectors)
        has_forms = any(el.get("type") == "form" for el in ui_elements)
        has_inputs = any(el.get("type") == "input" for el in ui_elements)
        
        if has_forms or has_inputs:
            security_checks = [
                {
                    "id": "REQ-S-001",
                    "title": "XSS Prevention - Script Injection in Form Fields",
                    "given": "User has form access",
                    "when": "User enters <script>alert('XSS')</script> in input fields",
                    "then": "Input is sanitized, script does not execute, error message shown",
                    "priority": ScenarioPriority.CRITICAL
                },
                {
                    "id": "REQ-S-002",
                    "title": "SQL Injection Prevention - Malicious SQL in Inputs",
                    "given": "User has form access",
                    "when": "User enters ' OR '1'='1 in input fields",
                    "then": "Input is parameterized, SQL injection blocked",
                    "priority": ScenarioPriority.CRITICAL
                },
                {
                    "id": "REQ-S-003",
                    "title": "CSRF Protection - Token Validation on Form Submit",
                    "given": "User submits form",
                    "when": "Request is sent without CSRF token",
                    "then": "Request is rejected with 403 error",
                    "priority": ScenarioPriority.HIGH
                },
                {
                    "id": "REQ-S-004",
                    "title": "Input Validation - Max Length and Type Enforcement",
                    "given": "User has form access",
                    "when": "User enters 10,000 character string or invalid types",
                    "then": "Input is rejected with validation error",
                    "priority": ScenarioPriority.HIGH
                }
            ]
            
            for check in security_checks:
                scenario = Scenario(
                    scenario_id=check["id"],
                    title=check["title"],
                    given=check["given"],
                    when=check["when"],
                    then=check["then"],
                    priority=check["priority"],
                    scenario_type=ScenarioType.SECURITY,
                    tags=["owasp", "security", "pentest"]
                )
                scenario.confidence = 0.85
                scenarios.append(scenario)
        
        return scenarios
    
    def _generate_edge_case_scenarios(self, ui_elements: List[Dict]) -> List[Scenario]:
        """Generate edge case test scenarios (boundary value analysis)"""
        scenarios = []
        
        # Find input fields for boundary testing
        input_elements = [el for el in ui_elements if el.get("type") == "input"]
        
        for idx, input_el in enumerate(input_elements[:5]):  # Limit to first 5
            field_name = input_el.get("name", input_el.get("id", f"field_{idx}"))
            input_type = input_el.get("input_type", "text")
            
            if input_type in ["text", "email", "tel", "password"]:
                scenario = Scenario(
                    scenario_id=f"REQ-E-{idx+1:03d}",
                    title=f"Edge Case - Empty {field_name} Field",
                    given=f"User is filling form",
                    when=f"User submits form with empty {field_name} field",
                    then=f"Validation error shown if field is required, or form submits if optional",
                    priority=ScenarioPriority.MEDIUM,
                    scenario_type=ScenarioType.EDGE_CASE,
                    tags=["boundary", "validation", "negative-test"]
                )
                scenario.confidence = 0.75
                scenarios.append(scenario)
        
        return scenarios
    
    def _extract_test_data(self, ui_elements: List[Dict]) -> List[Dict]:
        """Extract test data patterns from forms and inputs"""
        test_data = []
        
        for element in ui_elements:
            if element.get("type") in ["input", "select", "textarea"]:
                field_data = {
                    "field_name": element.get("name", element.get("id", "unknown")),
                    "field_type": element.get("input_type", element.get("type", "text")),
                    "required": element.get("required", False),
                    "placeholder": element.get("placeholder", ""),
                    "validation": self._extract_validation_rules(element),
                    "example_values": self._generate_example_values(element)
                }
                test_data.append(field_data)
        
        return test_data
    
    def _extract_validation_rules(self, element: Dict) -> Dict:
        """Extract validation rules from element attributes"""
        rules = {}
        
        if element.get("required"):
            rules["required"] = True
        if "maxlength" in element:
            rules["max_length"] = element["maxlength"]
        if "minlength" in element:
            rules["min_length"] = element["minlength"]
        if "pattern" in element:
            rules["pattern"] = element["pattern"]
        
        input_type = element.get("input_type", "text")
        if input_type == "email":
            rules["format"] = "email"
        elif input_type == "tel":
            rules["format"] = "phone"
        elif input_type == "url":
            rules["format"] = "url"
        
        return rules
    
    def _generate_example_values(self, element: Dict) -> List[str]:
        """Generate example test data values"""
        input_type = element.get("input_type", element.get("type", "text"))
        examples = []
        
        if input_type == "email":
            examples = ["test@example.com", "user+tag@domain.co.uk", "invalid.email"]
        elif input_type == "tel":
            examples = ["+1-555-123-4567", "555-1234", "invalid"]
        elif input_type == "url":
            examples = ["https://example.com", "http://test.org", "invalid-url"]
        elif input_type == "number":
            examples = ["0", "42", "-1", "9999", "abc"]
        elif input_type == "password":
            examples = ["ValidPass123!", "weak", ""]
        else:
            examples = ["valid text", "", "   ", "very long text " * 10]
        
        return examples
    
    def _calculate_coverage(self, ui_elements: List[Dict], 
                           scenarios: List[Scenario]) -> Dict:
        """Calculate test coverage metrics"""
        total_elements = len(ui_elements)
        interactive_elements = len([el for el in ui_elements 
                                     if el.get("type") in ["button", "link", "input", "select"]])
        
        # Count elements covered by scenarios
        covered_elements = set()
        for scenario in scenarios:
            # Simple heuristic: if scenario mentions element type, it's covered
            for element in ui_elements:
                element_text = element.get("text", "").lower()
                element_id = element.get("id", "").lower()
                element_name = element.get("name", "").lower()
                
                scenario_text = f"{scenario.title} {scenario.when} {scenario.then}".lower()
                
                if (element_text and element_text in scenario_text) or \
                   (element_id and element_id in scenario_text) or \
                   (element_name and element_name in scenario_text):
                    covered_elements.add(element.get("selector", ""))
        
        coverage_percent = (len(covered_elements) / interactive_elements * 100) if interactive_elements > 0 else 0
        
        return {
            "total_elements": total_elements,
            "interactive_elements": interactive_elements,
            "covered_elements": len(covered_elements),
            "ui_coverage_percent": round(coverage_percent, 2),
            "scenario_count": len(scenarios),
            "scenarios_by_type": {
                "functional": len([s for s in scenarios if s.scenario_type == ScenarioType.FUNCTIONAL]),
                "accessibility": len([s for s in scenarios if s.scenario_type == ScenarioType.ACCESSIBILITY]),
                "security": len([s for s in scenarios if s.scenario_type == ScenarioType.SECURITY]),
                "edge_case": len([s for s in scenarios if s.scenario_type == ScenarioType.EDGE_CASE])
            }
        }
    
    def _calculate_confidence(self, scenarios: List[Scenario]) -> float:
        """Calculate overall confidence score"""
        if not scenarios:
            return 0.0
        
        total_confidence = sum(s.confidence for s in scenarios)
        return round(total_confidence / len(scenarios), 2)
    
    def _get_priority_distribution(self, scenarios: List[Scenario]) -> Dict:
        """Get distribution of scenarios by priority"""
        distribution = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for scenario in scenarios:
            distribution[scenario.priority.value] += 1
        
        return distribution
    
    def _scenario_to_dict(self, scenario: Scenario) -> Dict:
        """Convert Scenario to dictionary"""
        return {
            "scenario_id": scenario.scenario_id,
            "title": scenario.title,
            "given": scenario.given,
            "when": scenario.when,
            "then": scenario.then,
            "priority": scenario.priority.value,
            "scenario_type": scenario.scenario_type.value,
            "test_data": scenario.test_data,
            "tags": scenario.tags,
            "confidence": scenario.confidence
        }
    
    async def _generate_scenarios_with_llm(self, ui_elements: List[Dict], 
                                           page_structure: Dict,
                                           page_context: Dict,
                                           user_instruction: str = "",
                                           execution_feedback: Dict = {},
                                           flow_steps: Optional[List[Dict]] = None,
                                           pages: Optional[List[Dict]] = None,
                                           navigation_flow: Optional[Dict] = None) -> List[Scenario]:
        """Generate high-quality test scenarios using LLM.
        
        When flow_steps from ObservationAgent crawl are provided, the prompt instructs
        the LLM to generate at least one complete end-to-end scenario following that flow.
        """
        if not self.llm_client or not self.llm_client.enabled:
            logger.warning("LLM not available, falling back to pattern-based generation")
            return []
        
        flow_steps = flow_steps or []
        pages = pages or []
        navigation_flow = navigation_flow or {}
        
        try:
            # Build prompt for LLM
            prompt = self._build_scenario_generation_prompt(
                ui_elements, page_structure, page_context, user_instruction, execution_feedback,
                flow_steps=flow_steps, pages=pages, navigation_flow=navigation_flow
            )
            
            # Call Azure OpenAI
            response = await asyncio.to_thread(
                self.llm_client.client.chat.completions.create,
                model=self.llm_client.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert test analyst specializing in BDD (Behavior-Driven Development) test scenarios.
Generate comprehensive test scenarios following these standards:
- BDD (Gherkin): Given/When/Then format
- ISTQB: Equivalence partitioning, boundary value analysis
- WCAG 2.1: Accessibility testing (keyboard, screen readers, contrast)
- OWASP Top 10: Security testing (XSS, SQL injection, CSRF)

Always respond with valid JSON containing high-quality test scenarios."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,  # Balance creativity with consistency
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            scenarios = []
            
            # Convert LLM output to Scenario objects
            for idx, scenario_data in enumerate(result.get("scenarios", [])[:15]):  # Limit to 15
                # Check if this scenario matches user instruction (for logging and priority)
                matches_user_requirement = False
                if user_instruction:
                    title_lower = scenario_data.get("title", "").lower()
                    when_lower = scenario_data.get("when", "").lower()
                    given_lower = scenario_data.get("given", "").lower()
                    then_lower = scenario_data.get("then", "").lower()
                    
                    # Enhanced matching logic for user instructions
                    matches_user_requirement = self._is_scenario_matching_instruction(
                        scenario_data, user_instruction, title_lower, when_lower, given_lower, then_lower
                    )
                    
                    # Debug logging to understand matching
                    if user_instruction:
                        logger.debug(f"Matching scenario '{scenario_data.get('title')}' against instruction: '{user_instruction}'")
                        logger.debug(f"  Title: {title_lower[:100]}")
                        logger.debug(f"  When: {when_lower[:100]}")
                        logger.debug(f"  Match result: {matches_user_requirement}")
                    
                    if matches_user_requirement:
                        logger.info(f"Scenario '{scenario_data.get('title')}' matches user requirement: '{user_instruction}'")
                        # Ensure high/critical priority for matching scenarios
                        current_priority = scenario_data.get("priority", "medium").lower()
                        if current_priority in ["medium", "low"]:
                            scenario_data["priority"] = "high"
                        # If already high, consider making it critical for very strong matches
                        elif current_priority == "high" and self._is_strong_match(scenario_data, user_instruction):
                            scenario_data["priority"] = "critical"
                
                tags = scenario_data.get("tags", [])
                if matches_user_requirement:
                    tags.append("user-requirement")
                    # Log the match with details
                    logger.info(f"  -> Matched keywords/phrases found in scenario")
                
                scenario = Scenario(
                    scenario_id=scenario_data.get("scenario_id", f"REQ-LLM-{idx+1:03d}"),
                    title=scenario_data.get("title", "Untitled Scenario"),
                    given=scenario_data.get("given", ""),
                    when=scenario_data.get("when", ""),
                    then=scenario_data.get("then", ""),
                    priority=self._map_priority(scenario_data.get("priority", "medium")),
                    scenario_type=self._map_scenario_type(scenario_data.get("scenario_type", "functional")),
                    tags=tags
                )
                scenario.confidence = scenario_data.get("confidence", 0.90)
                scenarios.append(scenario)
            
            # Log summary of matching scenarios
            if user_instruction:
                matching_count = sum(1 for s in scenarios if "user-requirement" in s.tags)
                # Always log the summary - use INFO level to ensure visibility
                logger.info(f"RequirementsAgent: {matching_count}/{len(scenarios)} scenarios match user instruction: '{user_instruction}'")
                if matching_count == 0:
                    logger.warning(f"RequirementsAgent: No scenarios matched user instruction. This may indicate:")
                    logger.warning(f"  - The instruction doesn't match available UI elements")
                    logger.warning(f"  - The LLM didn't generate matching scenarios")
                    logger.warning(f"  - Consider using more specific keywords or checking the generated scenarios")
                else:
                    # Log which scenarios matched
                    matching_scenarios = [s for s in scenarios if "user-requirement" in s.tags]
                    logger.info(f"RequirementsAgent: Matching scenarios:")
                    for ms in matching_scenarios[:5]:  # Show first 5
                        logger.info(f"  - {ms.scenario_id}: {ms.title} (Priority: {ms.priority.value})")
            
            logger.info(f"LLM generated {len(scenarios)} high-quality scenarios")
            return scenarios
            
        except Exception as e:
            logger.error(f"Error generating scenarios with LLM: {e}")
            return []
    
    def _build_scenario_generation_prompt(self, ui_elements: List[Dict], 
                                          page_structure: Dict,
                                          page_context: Dict,
                                          user_instruction: str = "",
                                          execution_feedback: Dict = {},
                                          flow_steps: Optional[List[Dict]] = None,
                                          pages: Optional[List[Dict]] = None,
                                          navigation_flow: Optional[Dict] = None) -> str:
        """Build prompt for LLM scenario generation.
        
        When flow_steps from ObservationAgent (browser-use) are provided, adds a section
        so the LLM generates at least one end-to-end scenario following the observed flow.
        """
        flow_steps = flow_steps or []
        pages = pages or []
        navigation_flow = navigation_flow or {}
        
        # Summarize UI elements
        element_summary = self._summarize_elements(ui_elements)
        
        url = page_structure.get("url", "unknown")
        page_type = page_context.get("page_type", "unknown")
        framework = page_context.get("framework", "unknown")
        
        # Build user instruction section if provided
        user_instruction_section = ""
        if user_instruction:
            user_instruction_section = f"""
**USER REQUIREMENT (HIGH PRIORITY):**
The user wants to test: "{user_instruction}"

**CRITICAL INSTRUCTIONS:**
1. **MUST generate at least one scenario that specifically matches this user requirement**
2. **PRIORITIZE scenarios matching the user's intent** - assign "critical" or "high" priority
3. **Use semantic matching** to find UI elements related to the user's requirement
   - Example: If user says "Test purchase flow for '5G寬頻數據無限任用' plan"
   - Find elements containing "5G寬頻數據無限任用" or related text
   - Generate scenario: "Click on plan '5G寬頻數據無限任用', Select contract term, Verify price, Click subscribe button"
4. **Include specific details** from the user requirement in the scenario
5. **Mark matching scenarios** with tags like ["user-requirement", "priority-test"]
6. **For login flows:** Describe in-page email/password login only (click Login → enter email → enter password → click Login). Do NOT describe Gmail, OAuth, or new-tab login unless the user explicitly asks for OTP or email verification.
"""
        
        # Build observed crawl flow section when ObservationAgent passed flow_steps (browser-use)
        observed_flow_section = ""
        if flow_steps:
            goal_reached = page_context.get("goal_reached", False)
            steps_list = "\n".join(
                f"  {s.get('order', i+1)}. [{s.get('action', '')}] {s.get('target', '')} (page: {s.get('page_title', '') or s.get('page_url', '')[:50]})"
                for i, s in enumerate(flow_steps[:80])  # Cap at 80 steps
            )
            observed_flow_section = f"""
**OBSERVED CRAWL FLOW (FROM BROWSER-USE – USE THIS FOR END-TO-END SCENARIO):**
The ObservationAgent crawled the application and recorded the following flow. The user's goal is: "{user_instruction or 'complete the flow to success'}". Goal was reached: {goal_reached}.

**Steps observed in order (follow this exact sequence for one complete scenario):**
{steps_list}

**CRITICAL:** Generate **at least one scenario** that describes this **full end-to-end flow** from start to finish:
- **Given:** User is on the start page (or logged in if the flow includes login).
- **When:** List ALL the key actions in order (navigate, click Login, input email, click Login, input password, click Login, select plan, click Next, acknowledge T&C, click Subscribe, confirm as many times as shown, upload document if in flow, fill HKID/personal details, fill payment, sign, checkout, pay) so that the test case can be executed by the 3-tier execution engine as one complete flow.
- **Then:** User sees the success/subscription confirmation page (or the stated goal).

**Login in the scenario:** Use only in-page email/password login (click Login → enter email → click Login → enter password → click Login). Do NOT include Gmail, OAuth, "Sign in with Google", or new-tab login unless the user instruction explicitly requires OTP or email verification.

This scenario MUST be "critical" priority and tagged ["user-requirement", "end-to-end", "priority-test"]. Do not truncate the flow: include all confirmations, document upload, payment, and final pay step if they appear in the observed flow above.
"""
        
        # Build execution feedback section if provided
        feedback_section = ""
        if execution_feedback and execution_feedback.get("status") == "success":
            insights = execution_feedback.get("insights", [])
            recommendations = execution_feedback.get("recommendations", [])
            metrics = execution_feedback.get("metrics", {})
            
            if insights or recommendations:
                feedback_section = f"""
**EXECUTION FEEDBACK (Learn from Previous Test Runs):**
Previous test executions showed:
- Pass Rate: {metrics.get('pass_rate', 0):.1f}% ({metrics.get('passed', 0)}/{metrics.get('total_executions', 0)})
- Fail Rate: {metrics.get('fail_rate', 0):.1f}%

**Key Insights:**
{chr(10).join(f"- {insight}" for insight in insights) if insights else "- No specific insights available"}

**Recommendations for Better Scenarios:**
{chr(10).join(f"- {rec}" for rec in recommendations) if recommendations else "- Continue generating scenarios as before"}

**IMPORTANT:** Use these insights to generate more stable and reliable scenarios. Focus on patterns that led to successful tests and avoid patterns that caused failures.
"""
        
        prompt = f"""Generate comprehensive BDD test scenarios for this web page.

**Page Information:**
- URL: {url}
- Page Type: {page_type}
- Framework: {framework}
- UI Elements: {len(ui_elements)} total

**UI Elements Summary:**
{element_summary}
{user_instruction_section}
{observed_flow_section}
{feedback_section}
**Requirements:**
1. Generate 10-15 high-quality test scenarios
2. **IF "OBSERVED CRAWL FLOW" is present above:** Generate ONE scenario that is the complete end-to-end flow (all steps from start to success page) with "critical" priority. Then generate additional scenarios for other coverage.
3. **IF user requirement is provided above:** Generate at least one scenario that specifically matches it with "critical" priority
4. Cover multiple scenario types:
   - Functional: Core features and user workflows
   - Accessibility: WCAG 2.1 (keyboard navigation, screen readers, ARIA labels)
   - Security: OWASP Top 10 (input validation, XSS, CSRF)
   - Edge Cases: Boundary values, error handling
5. Follow BDD Given/When/Then format
6. **IMPORTANT**: The "when" clause should include MULTIPLE comma-separated actions for complex scenarios
   - Example: "Click on plan 'Plan A', Select contract term '12 months', Verify price shows '$100', Click button 'Subscribe'"
   - Simple scenarios can have single actions, but complex workflows should have 3-5 actions
7. Assign priorities: critical, high, medium, low
   - **Scenarios matching user requirement should be "critical" or "high"**
8. Include confidence scores (0.0-1.0)

**Required JSON Response Format:**
{{
  "scenarios": [
    {{
      "scenario_id": "REQ-F-001",
      "title": "Short descriptive title",
      "given": "Preconditions (user state, page state)",
      "when": "User action or multiple comma-separated actions (e.g., 'Click button A, Enter text in field B, Click submit')",
      "then": "Expected outcome or system behavior",
      "priority": "critical|high|medium|low",
      "scenario_type": "functional|accessibility|security|edge_case",
      "tags": ["tag1", "tag2"],
      "confidence": 0.90
    }}
  ]
}}

Focus on **realistic user scenarios** and **important test coverage**. Be specific and actionable. For functional scenarios, include multiple steps in the "when" clause to create comprehensive test flows.

{f"**REMINDER:** The user specifically wants to test: '{user_instruction}'. Ensure at least one scenario directly addresses this requirement with high priority." if user_instruction else ""}"""
        
        return prompt
    
    def _summarize_elements(self, ui_elements: List[Dict]) -> str:
        """Summarize UI elements for LLM prompt"""
        element_counts = {}
        for elem in ui_elements:
            elem_type = elem.get("type", "unknown")
            element_counts[elem_type] = element_counts.get(elem_type, 0) + 1
        
        summary_lines = [f"- {count} {elem_type}(s)" 
                         for elem_type, count in sorted(element_counts.items())]
        
        # Add sample elements
        sample_elements = []
        for elem in ui_elements[:10]:
            elem_type = elem.get("type", "unknown")
            text = elem.get("text", "")[:50]
            if text:
                sample_elements.append(f"  • [{elem_type}] {text}")
        
        summary = "\n".join(summary_lines)
        if sample_elements:
            summary += "\n\nSample Elements:\n" + "\n".join(sample_elements)
        
        return summary
    
    def _map_priority(self, priority_str: str) -> ScenarioPriority:
        """Map string priority to enum"""
        mapping = {
            "critical": ScenarioPriority.CRITICAL,
            "high": ScenarioPriority.HIGH,
            "medium": ScenarioPriority.MEDIUM,
            "low": ScenarioPriority.LOW
        }
        return mapping.get(priority_str.lower(), ScenarioPriority.MEDIUM)
    
    def _map_scenario_type(self, type_str: str) -> ScenarioType:
        """Map string scenario type to enum"""
        mapping = {
            "functional": ScenarioType.FUNCTIONAL,
            "accessibility": ScenarioType.ACCESSIBILITY,
            "security": ScenarioType.SECURITY,
            "edge_case": ScenarioType.EDGE_CASE,
            "performance": ScenarioType.PERFORMANCE,
            "usability": ScenarioType.USABILITY
        }
        return mapping.get(type_str.lower(), ScenarioType.FUNCTIONAL)
    
    def _is_scenario_matching_instruction(self, scenario_data: Dict, user_instruction: str,
                                         title_lower: str, when_lower: str, 
                                         given_lower: str, then_lower: str) -> bool:
        """
        Enhanced matching logic for user instructions.
        Handles:
        - Chinese text matching
        - Semantic keywords (purchase/register/subscribe)
        - Plan name matching
        - Multiple matching strategies
        """
        if not user_instruction:
            return False
        
        instruction_lower = user_instruction.lower()
        
        # Strategy 1: Direct text matching (including Chinese characters)
        # Check if key phrases from instruction appear in scenario
        key_phrases = [
            "5g寬頻數據無限任用",  # The specific plan name
            "5g寬頻",  # 5G broadband
            "寬頻",  # broadband
            "數據無限",  # unlimited data
            "purchase",  # purchase flow
            "subscribe",  # subscription
            "register",  # registration
            "立即登記",  # register button (common in purchase flow)
        ]
        
        # Check all scenario fields for matches
        scenario_text = f"{title_lower} {when_lower} {given_lower} {then_lower}"
        
        # Count matches for key phrases
        phrase_matches = sum(1 for phrase in key_phrases if phrase in scenario_text)
        
        # Strategy 2: Extract meaningful keywords (skip common words)
        common_words = {"test", "for", "the", "a", "an", "is", "are", "to", "of", "in", "on", "at", "by", "with"}
        instruction_keywords = [
            word.strip("'\".,!?;:()[]{}") 
            for word in instruction_lower.split() 
            if word.strip("'\".,!?;:()[]{}") not in common_words and len(word.strip("'\".,!?;:()[]{}")) > 2
        ]
        
        # Also extract Chinese text (non-ASCII characters)
        chinese_text = ""
        for char in user_instruction:
            if ord(char) > 127:  # Non-ASCII (likely Chinese)
                chinese_text += char
        
        # Add Chinese text as a keyword if present
        if chinese_text:
            instruction_keywords.append(chinese_text.lower())
        
        # Count keyword matches
        keyword_matches = sum(1 for keyword in instruction_keywords if keyword in scenario_text)
        
        # Strategy 3: Semantic matching for purchase/registration flows
        purchase_keywords = ["purchase", "buy", "subscribe", "register", "sign up", "order", "checkout", "立即登記"]
        has_purchase_intent = any(keyword in instruction_lower for keyword in purchase_keywords)
        has_purchase_scenario = any(keyword in scenario_text for keyword in purchase_keywords)
        
        # Strategy 4: Plan name matching (specific product names)
        # Extract quoted text (often product names)
        import re
        quoted_texts = re.findall(r"'([^']+)'", user_instruction)
        plan_name_matches = sum(1 for quoted in quoted_texts if quoted.lower() in scenario_text)
        
        # Decision logic: Match if any strong indicator
        # Strong match: Plan name found OR (phrase match + keyword match) OR (purchase intent + purchase scenario)
        strong_match = (
            plan_name_matches > 0 or  # Plan name found
            (phrase_matches >= 2) or  # Multiple key phrases
            (phrase_matches >= 1 and keyword_matches >= 2) or  # Phrase + keywords
            (has_purchase_intent and has_purchase_scenario and keyword_matches >= 1)  # Purchase flow match
        )
        
        # Medium match: Some keywords or phrases
        medium_match = (
            keyword_matches >= 2 or  # Multiple keywords
            phrase_matches >= 1  # At least one key phrase
        )
        
        return strong_match or medium_match
    
    def _is_strong_match(self, scenario_data: Dict, user_instruction: str) -> bool:
        """
        Check if scenario is a strong match (should be critical priority).
        Strong matches include:
        - Exact plan name match
        - Multiple key phrases
        - Purchase flow with specific plan
        """
        title_lower = scenario_data.get("title", "").lower()
        when_lower = scenario_data.get("when", "").lower()
        scenario_text = f"{title_lower} {when_lower}"
        
        # Extract plan name from instruction
        import re
        quoted_texts = re.findall(r"'([^']+)'", user_instruction.lower())
        
        # Strong match criteria
        has_plan_name = any(quoted in scenario_text for quoted in quoted_texts)
        has_purchase_flow = any(keyword in scenario_text for keyword in ["purchase", "subscribe", "register", "立即登記"])
        
        return has_plan_name and has_purchase_flow
    
    def _estimate_token_usage(self, ui_elements: List[Dict], 
                              scenarios: List[Scenario]) -> int:
        """Estimate token usage for LLM calls (if used)"""
        # Rough estimation: 1 token ??4 characters
        input_chars = len(json.dumps(ui_elements))
        output_chars = sum(len(s.given) + len(s.when) + len(s.then) for s in scenarios)
        return int((input_chars + output_chars) / 4)
