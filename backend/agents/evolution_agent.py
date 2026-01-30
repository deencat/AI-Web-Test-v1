"""
EvolutionAgent - Test Code Generator
Converts BDD scenarios (Given/When/Then) into executable Playwright test code

Industry Standards:
- BDD (Behavior-Driven Development): Gherkin syntax
- Playwright best practices: Page Object Model, explicit waits, assertions
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
    Generates executable Playwright test code from BDD scenarios.
    
    Input: BDD scenarios (Given/When/Then) from RequirementsAgent/AnalysisAgent
    Output: Executable Playwright test files (.spec.ts)
    
    Process:
    1. Receives BDD scenarios with risk scores and prioritization
    2. Converts each scenario to Playwright test code using LLM
    3. Generates test file with proper imports, setup, and assertions
    4. Returns generated code with metadata (generation_id, confidence, etc.)
    """
    
    def __init__(self, agent_id: str, agent_type: str, priority: int, 
                 message_queue, config: Optional[Dict] = None):
        """Initialize EvolutionAgent with optional LLM and caching support"""
        super().__init__(agent_id, agent_type, priority, message_queue, config)
        
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
        
        # Caching for code generation (30% cost reduction)
        self.cache_enabled = config.get("cache_enabled", True) if config else True
        self.code_cache: Dict[str, Dict] = {}  # In-memory cache (can be replaced with Redis)
        
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
                description="Converts BDD scenarios to Playwright test code"
            ),
            AgentCapability(
                "code_generation", 
                "1.0.0", 
                confidence_threshold=0.75,
                description="Generates executable test code from test requirements"
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
        """Generate Playwright test code from BDD scenarios"""
        start_time = time.time()
        generation_id = str(uuid.uuid4())
        
        try:
            # Extract input data
            scenarios = task.payload.get("scenarios", [])
            risk_scores = task.payload.get("risk_scores", [])
            prioritization = task.payload.get("final_prioritization", [])
            page_context = task.payload.get("page_context", {})
            test_data = task.payload.get("test_data", [])
            
            logger.info(f"EvolutionAgent processing {len(scenarios)} scenarios (generation_id: {generation_id})")
            
            if not scenarios:
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error="No scenarios provided in payload",
                    confidence=0.0,
                    execution_time_seconds=time.time() - start_time
                )
            
            # Generate test code for each scenario
            generated_tests = []
            total_tokens = 0
            
            for scenario in scenarios:
                scenario_id = scenario.get("scenario_id", "UNKNOWN")
                
                # Check cache first (if enabled)
                cache_key = self._generate_cache_key(scenario, page_context)
                if self.cache_enabled and cache_key in self.code_cache:
                    logger.info(f"Cache hit for scenario {scenario_id}")
                    cached_result = self.code_cache[cache_key]
                    generated_tests.append({
                        "scenario_id": scenario_id,
                        "test_code": cached_result["test_code"],
                        "confidence": cached_result["confidence"],
                        "from_cache": True
                    })
                    continue
                
                # Generate test code using LLM or template
                if self.use_llm and self.llm_client:
                    test_code_result = await self._generate_test_code_with_llm(
                        scenario, risk_scores, prioritization, page_context, test_data
                    )
                else:
                    test_code_result = self._generate_test_code_from_template(
                        scenario, page_context
                    )
                
                if test_code_result:
                    generated_tests.append({
                        "scenario_id": scenario_id,
                        "test_code": test_code_result["code"],
                        "confidence": test_code_result.get("confidence", 0.85),
                        "from_cache": False
                    })
                    total_tokens += test_code_result.get("tokens_used", 0)
                    
                    # Cache the result
                    if self.cache_enabled:
                        self.code_cache[cache_key] = {
                            "test_code": test_code_result["code"],
                            "confidence": test_code_result.get("confidence", 0.85),
                            "cached_at": datetime.now(timezone.utc).isoformat()
                        }
            
            # Combine all tests into a single test file
            test_file_content = self._combine_tests_to_file(
                generated_tests, page_context
            )
            
            # Calculate overall confidence
            if generated_tests:
                overall_confidence = sum(t.get("confidence", 0.85) for t in generated_tests) / len(generated_tests)
            else:
                overall_confidence = 0.0
            
            # Generate filename and save to disk
            test_filename = self._generate_test_filename(page_context)
            test_file_path = self._save_test_file(test_filename, test_file_content)
            
            # Prepare result
            result = {
                "generation_id": generation_id,
                "test_file": test_filename,
                "test_file_path": str(test_file_path) if test_file_path else None,
                "code": test_file_content,
                "test_count": len(generated_tests),
                "scenarios": generated_tests,
                "confidence": round(overall_confidence, 2),
                "prompt_variant": self.current_variant,
                "cache_hits": sum(1 for t in generated_tests if t.get("from_cache", False)),
                "cache_misses": sum(1 for t in generated_tests if not t.get("from_cache", False))
            }
            
            logger.info(f"EvolutionAgent generated {len(generated_tests)} tests "
                       f"(confidence: {overall_confidence:.2f}, tokens: {total_tokens})")
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                confidence=overall_confidence,
                execution_time_seconds=time.time() - start_time,
                metadata={
                    "token_usage": total_tokens,
                    "generation_id": generation_id,
                    "test_count": len(generated_tests),
                    "prompt_variant": self.current_variant
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
    
    async def _generate_test_code_with_llm(
        self,
        scenario: Dict,
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        test_data: List[Dict]
    ) -> Optional[Dict]:
        """Generate test code using Azure OpenAI GPT-4o"""
        try:
            # Build prompt using current variant
            prompt_builder = self.prompt_variants.get(self.current_variant, self._build_prompt_variant_1)
            prompt = prompt_builder(scenario, risk_scores, prioritization, page_context, test_data)
            
            # Call LLM (Azure OpenAI create is synchronous, not async)
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.deployment,
                messages=[
                    {"role": "system", "content": "You are an expert Playwright test automation engineer. Generate high-quality, maintainable test code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent code generation
                max_tokens=2500,
                response_format={"type": "text"}  # We'll parse the code from text response
            )
            
            # Extract generated code
            generated_text = response.choices[0].message.content
            test_code = self._extract_code_from_response(generated_text)
            
            # Calculate confidence based on code quality
            confidence = self._calculate_code_confidence(test_code, scenario)
            
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return {
                "code": test_code,
                "confidence": confidence,
                "tokens_used": tokens_used,
                "raw_response": generated_text
            }
            
        except Exception as e:
            logger.error(f"LLM code generation failed: {e}")
            # Fallback to template-based generation
            return self._generate_test_code_from_template(scenario, page_context)
    
    def _build_prompt_variant_1(
        self,
        scenario: Dict,
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        test_data: List[Dict]
    ) -> str:
        """Variant 1: Detailed, explicit prompt with full context"""
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
        
        prompt = f"""Generate a Playwright test for the following BDD scenario.

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
1. Generate a complete, executable Playwright test
2. Use TypeScript/JavaScript syntax
3. Include proper imports: `import {{ test, expect }} from '@playwright/test';`
4. Use explicit waits and proper selectors
5. Add meaningful assertions
6. Follow Playwright best practices (page object model if applicable)
7. Include error handling where appropriate
8. Add comments explaining each step

**Test Code Template:**
```typescript
import {{ test, expect }} from '@playwright/test';

test('{title}', async ({{ page }}) => {{
  // Given: {given}
  // ... navigation and setup code ...
  
  // When: {when}
  // ... action code ...
  
  // Then: {then}
  // ... assertion code ...
}});
```

Generate ONLY the test code, no explanations or markdown formatting."""
        
        return prompt
    
    def _build_prompt_variant_2(
        self,
        scenario: Dict,
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        test_data: List[Dict]
    ) -> str:
        """Variant 2: Concise, focused prompt"""
        title = scenario.get("title", "")
        given = scenario.get("given", "")
        when = scenario.get("when", "")
        then = scenario.get("then", "")
        url = page_context.get("url", "https://example.com")
        
        prompt = f"""Generate a Playwright test:

Given: {given}
When: {when}
Then: {then}

URL: {url}

Generate executable Playwright TypeScript code with imports, navigation, actions, and assertions."""
        
        return prompt
    
    def _build_prompt_variant_3(
        self,
        scenario: Dict,
        risk_scores: List[Dict],
        prioritization: List[Dict],
        page_context: Dict,
        test_data: List[Dict]
    ) -> str:
        """Variant 3: Pattern-based prompt with reusable patterns"""
        title = scenario.get("title", "")
        given = scenario.get("given", "")
        when = scenario.get("when", "")
        then = scenario.get("then", "")
        scenario_type = scenario.get("scenario_type", "functional")
        url = page_context.get("url", "https://example.com")
        
        # Include common patterns based on scenario type
        patterns = {
            "functional": "Use page.goto(), page.fill(), page.click(), expect()",
            "accessibility": "Focus on keyboard navigation, ARIA labels, screen reader support",
            "security": "Test input validation, XSS prevention, CSRF protection",
            "edge_case": "Test boundary conditions, error handling, edge cases"
        }
        pattern_hint = patterns.get(scenario_type, patterns["functional"])
        
        prompt = f"""Generate a Playwright test using common patterns for {scenario_type} scenarios.

Scenario: {title}
Given: {given}
When: {when}
Then: {then}
URL: {url}

Pattern: {pattern_hint}

Generate complete, executable Playwright TypeScript code."""
        
        return prompt
    
    def _generate_test_code_from_template(
        self,
        scenario: Dict,
        page_context: Dict
    ) -> Optional[Dict]:
        """Generate test code from template (fallback when LLM unavailable)"""
        title = scenario.get("title", "Test Scenario")
        given = scenario.get("given", "")
        when = scenario.get("when", "")
        then = scenario.get("then", "")
        url = page_context.get("url", "https://example.com")
        
        # Simple template-based generation
        test_code = f"""import {{ test, expect }} from '@playwright/test';

test('{title}', async ({{ page }}) => {{
  // Given: {given}
  await page.goto('{url}');
  
  // When: {when}
  // TODO: Implement actions based on scenario
  
  // Then: {then}
  // TODO: Add assertions
}});
"""
        
        return {
            "code": test_code,
            "confidence": 0.6,  # Lower confidence for template-based
            "tokens_used": 0
        }
    
    def _extract_code_from_response(self, response_text: str) -> str:
        """Extract code block from LLM response"""
        # Try to find code blocks (```typescript or ```javascript)
        code_block_pattern = r'```(?:typescript|javascript|ts|js)?\n(.*?)```'
        matches = re.findall(code_block_pattern, response_text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code block, try to find import statement (likely start of code)
        if 'import' in response_text:
            lines = response_text.split('\n')
            start_idx = next((i for i, line in enumerate(lines) if 'import' in line), 0)
            code = '\n'.join(lines[start_idx:])
            # Remove any markdown formatting
            code = re.sub(r'^```.*?\n', '', code, flags=re.MULTILINE)
            code = re.sub(r'\n```.*?$', '', code, flags=re.MULTILINE)
            return code.strip()
        
        # Fallback: return as-is
        return response_text.strip()
    
    def _calculate_code_confidence(self, code: str, scenario: Dict) -> float:
        """Calculate confidence score based on code quality"""
        confidence = 0.7  # Base confidence
        
        # Check for required elements
        if 'import' in code and '@playwright/test' in code:
            confidence += 0.1
        if 'test(' in code or 'test(' in code:
            confidence += 0.1
        if 'expect(' in code or 'assert' in code.lower():
            confidence += 0.05
        if 'await' in code:
            confidence += 0.05
        
        # Check for scenario coverage
        given = scenario.get("given", "").lower()
        when = scenario.get("when", "").lower()
        then = scenario.get("then", "").lower()
        
        code_lower = code.lower()
        if any(word in code_lower for word in given.split()[:3] if len(word) > 3):
            confidence += 0.05
        if any(word in code_lower for word in when.split()[:3] if len(word) > 3):
            confidence += 0.05
        
        return min(0.95, confidence)
    
    def _combine_tests_to_file(
        self,
        generated_tests: List[Dict],
        page_context: Dict
    ) -> str:
        """Combine multiple test scenarios into a single test file"""
        url = page_context.get("url", "https://example.com")
        
        file_content = f"""import {{ test, expect }} from '@playwright/test';

// Generated test file
// URL: {url}
// Generated at: {datetime.now(timezone.utc).isoformat()}
// Test count: {len(generated_tests)}

"""
        
        for test_data in generated_tests:
            scenario_id = test_data.get("scenario_id", "UNKNOWN")
            test_code = test_data.get("test_code", "")
            from_cache = test_data.get("from_cache", False)
            
            file_content += f"""
// Scenario: {scenario_id} {'(from cache)' if from_cache else ''}
{test_code}

"""
        
        return file_content
    
    def _generate_test_filename(self, page_context: Dict) -> str:
        """Generate appropriate test filename"""
        url = page_context.get("url", "example.com")
        # Extract domain or page name
        if "://" in url:
            domain = url.split("://")[1].split("/")[0]
            # Clean domain name
            domain = domain.replace(".", "_").replace("-", "_")
        else:
            domain = "test"
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"{domain}_tests_{timestamp}.spec.ts"
    
    def _save_test_file(self, filename: str, content: str) -> Optional[Path]:
        """Save generated test file to disk"""
        try:
            import os
            
            # Determine output directory from config or use default
            output_dir = self.config.get("test_output_dir") if self.config else None
            if not output_dir:
                # Default: backend/artifacts/generated_tests/
                backend_path = Path(__file__).parent.parent
                output_dir = backend_path / "artifacts" / "generated_tests"
            else:
                output_dir = Path(output_dir)
            
            # Ensure directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path = output_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved generated test file to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.warning(f"Failed to save test file to disk: {e}")
            return None
    
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
        test_code = result.get("code", "")
        test_count = result.get("test_count", 0)
        
        # Component 1: Code Generation Accuracy (40%)
        syntax_accuracy = self._validate_code_syntax(test_code)
        
        # Component 2: Test Execution Success Rate (35%)
        if execution_results:
            execution_success = self._calculate_execution_success_rate(execution_results)
        else:
            execution_success = 0.85  # Default if no execution results yet
        
        # Component 3: Code Quality (15%)
        code_quality = self._analyze_code_quality(test_code)
        
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
                "code_quality": round(code_quality, 3),
                "efficiency": round(efficiency, 3)
            },
            "grade": grade,
            "recommendations": recommendations
        }
    
    def _validate_code_syntax(self, code: str) -> float:
        """Validate code syntax (basic checks)"""
        score = 0.0
        
        # Check for required imports
        if 'import' in code and '@playwright/test' in code:
            score += 0.3
        
        # Check for test structure
        if 'test(' in code or 'test(' in code:
            score += 0.3
        
        # Check for async/await
        if 'async' in code and 'await' in code:
            score += 0.2
        
        # Check for assertions
        if 'expect(' in code:
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
    
    def _analyze_code_quality(self, code: str) -> float:
        """Analyze code quality (maintainability, readability)"""
        score = 0.5  # Base score
        
        # Check for comments
        if '//' in code or '/*' in code:
            score += 0.2
        
        # Check for proper formatting (indentation, structure)
        lines = code.split('\n')
        if len(lines) > 5:  # Reasonable test length
            score += 0.2
        
        # Check for error handling
        if 'try' in code or 'catch' in code or 'error' in code.lower():
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
            recommendations.append("Improve code syntax validation - ensure all tests have proper imports and structure")
        
        if execution_success < 0.8:
            recommendations.append("Improve test reliability - review selectors and wait strategies")
        
        if code_quality < 0.7:
            recommendations.append("Enhance code quality - add comments, improve readability, follow best practices")
        
        if efficiency < 0.7:
            recommendations.append("Optimize generation efficiency - reduce token usage, improve caching")
        
        if not recommendations:
            recommendations.append("Performance is good - continue monitoring")
        
        return recommendations

