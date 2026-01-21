"""
RequirementsAgent - Extracts test requirements from UI observations
Follows BDD, ISTQB, WCAG 2.1, OWASP security standards
"""
from agents.base_agent import BaseAgent, AgentCapability, TaskContext, TaskResult
from typing import Dict, List, Tuple, Optional
import time
import re
import json
import logging
from enum import Enum

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
        
        try:
            # Extract input data
            ui_elements = task.payload.get("ui_elements", [])
            page_structure = task.payload.get("page_structure", {})
            page_context = task.payload.get("page_context", {})
            
            logger.info(f"RequirementsAgent processing {len(ui_elements)} UI elements for {page_structure.get('url', 'unknown')}")
            
            # Stage 1: Group elements by page/component (Page Object Model)
            element_groups = self._group_elements_by_page(ui_elements, page_structure)
            logger.debug(f"Grouped elements into {len(element_groups)} sections")
            
            # Stage 2: Map user journeys (multi-step flows)
            user_journeys = self._map_user_journeys(element_groups, page_context)
            logger.debug(f"Mapped {len(user_journeys)} user journeys")
            
            # Stage 3: Generate functional test scenarios
            functional_scenarios = await self._generate_functional_scenarios(
                user_journeys, element_groups, page_context
            )
            logger.debug(f"Generated {len(functional_scenarios)} functional scenarios")
            
            # Stage 4: Generate accessibility scenarios (WCAG 2.1)
            accessibility_scenarios = self._generate_accessibility_scenarios(ui_elements)
            logger.debug(f"Generated {len(accessibility_scenarios)} accessibility scenarios")
            
            # Stage 5: Generate security scenarios (OWASP)
            security_scenarios = self._generate_security_scenarios(ui_elements, page_context)
            logger.debug(f"Generated {len(security_scenarios)} security scenarios")
            
            # Stage 6: Generate edge case scenarios
            edge_case_scenarios = self._generate_edge_case_scenarios(ui_elements)
            logger.debug(f"Generated {len(edge_case_scenarios)} edge case scenarios")
            
            # Combine all scenarios
            all_scenarios = (
                functional_scenarios + 
                accessibility_scenarios + 
                security_scenarios + 
                edge_case_scenarios
            )
            
            # Stage 7: Extract test data
            test_data = self._extract_test_data(ui_elements)
            logger.debug(f"Extracted {len(test_data)} test data fields")
            
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
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                confidence=result["quality_indicators"]["confidence"],
                execution_time_seconds=time.time() - start_time,
                token_usage=self._estimate_token_usage(ui_elements, all_scenarios)
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
    
    async def _generate_functional_scenarios(self, user_journeys: List[Dict],
                                             element_groups: Dict,
                                             page_context: Dict) -> List[Scenario]:
        """Generate functional test scenarios using patterns"""
        scenarios = []
        
        # Pattern-based scenario generation
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
    
    def _estimate_token_usage(self, ui_elements: List[Dict], 
                              scenarios: List[Scenario]) -> int:
        """Estimate token usage for LLM calls (if used)"""
        # Rough estimation: 1 token ??4 characters
        input_chars = len(json.dumps(ui_elements))
        output_chars = sum(len(s.given) + len(s.when) + len(s.then) for s in scenarios)
        return int((input_chars + output_chars) / 4)
