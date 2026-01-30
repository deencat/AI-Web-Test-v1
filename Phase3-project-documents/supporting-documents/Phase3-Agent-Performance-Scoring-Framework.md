# Phase 3: Agent Performance Scoring Framework

**Purpose:** Comprehensive performance scoring system for all Phase 3 agents  
**Scope:** Metrics, scoring formulas, validation methods, and industry best practices  
**Status:** 📋 Design Document - Ready for Implementation  
**Last Updated:** January 29, 2026

> **📖 When to Use This Document:**
> - **Understanding Agent Quality:** How each agent measures its own performance
> - **Implementing Metrics:** Code examples for scoring calculations
> - **Validating Results:** Methods to verify agent accuracy
> - **Industry Standards:** ISTQB, IEEE 29119, ISO/IEC 25010 compliance

---

## 📋 Table of Contents

1. [Overview & Industry Standards](#1-overview--industry-standards)
2. [ObservationAgent Performance Scoring](#2-observationagent-performance-scoring)
3. [RequirementsAgent Performance Scoring](#3-requirementsagent-performance-scoring)
4. [AnalysisAgent Performance Scoring](#4-analysisagent-performance-scoring)
5. [Cross-Agent Validation](#5-cross-agent-validation)
6. [Implementation Roadmap](#6-implementation-roadmap)

---

## 1. Overview & Industry Standards

### 1.1 Industry Standards Reference

**ISTQB (International Software Testing Qualifications Board):**
- **Test Coverage Metrics:** Statement, branch, path, condition coverage
- **Test Quality Attributes:** Correctness, completeness, traceability, maintainability
- **Risk-Based Testing:** Risk priority, severity, probability assessment

**IEEE 29119 (Software Testing Standard):**
- **Test Design Quality:** Test case effectiveness, test data quality
- **Test Execution Quality:** Pass/fail accuracy, defect detection rate
- **Test Process Quality:** Coverage metrics, traceability matrices

**ISO/IEC 25010 (Software Quality Model):**
- **Functional Suitability:** Functional completeness, correctness, appropriateness
- **Reliability:** Fault tolerance, recoverability, maturity
- **Usability:** Operability, user error protection, accessibility

**W3C Web Standards:**
- **Selector Accuracy:** CSS selector specificity, XPath reliability
- **Accessibility:** WCAG 2.1 compliance (A, AA, AAA levels)
- **DOM Stability:** Element identification robustness

### 1.2 Scoring Framework Principles

1. **Multi-Dimensional Scoring:** Each agent scored on multiple axes (accuracy, completeness, efficiency)
2. **Ground Truth Validation:** Compare agent outputs against known correct results
3. **Continuous Improvement:** Track scores over time to measure agent learning
4. **Industry Alignment:** Metrics align with ISTQB, IEEE 29119, ISO/IEC 25010 standards
5. **Actionable Insights:** Scores provide clear guidance for improvement

### 1.3 Scoring Scale

**Overall Agent Score:** `0.0 - 1.0` (0.0 = poor, 1.0 = excellent)

**Component Scores:**
- **Accuracy:** `0.0 - 1.0` (How correct are the outputs?)
- **Completeness:** `0.0 - 1.0` (How much did we capture?)
- **Efficiency:** `0.0 - 1.0` (How fast/resource-efficient?)
- **Reliability:** `0.0 - 1.0` (How consistent across different inputs?)

**Weighted Formula:**
```
Overall Score = (Accuracy × 0.40) + (Completeness × 0.30) + (Efficiency × 0.20) + (Reliability × 0.10)
```

---

## 2. ObservationAgent Performance Scoring

### 2.1 Scoring Dimensions

#### **Dimension 1: Selector/XPath Accuracy** (Weight: 0.35)

**What it measures:** How accurately can we re-identify elements using the generated selectors?

**Scoring Method:**
```python
def score_selector_accuracy(observed_elements: List[Dict], page: Page) -> float:
    """
    Validate selectors by re-querying the page.
    
    Returns: Accuracy score 0.0-1.0
    """
    total_elements = len(observed_elements)
    if total_elements == 0:
        return 0.0
    
    valid_selectors = 0
    for element in observed_elements:
        selector = element.get("selector", "")
        xpath = element.get("xpath", "")
        
        # Try CSS selector first
        if selector:
            try:
                found = await page.query_selector(selector)
                if found and await self._elements_match(found, element):
                    valid_selectors += 1
                    continue
            except:
                pass
        
        # Fallback to XPath
        if xpath:
            try:
                found = await page.query_selector(f"xpath={xpath}")
                if found and await self._elements_match(found, element):
                    valid_selectors += 1
                    continue
            except:
                pass
    
    return valid_selectors / total_elements
```

**Industry Benchmark:**
- **Excellent (≥0.95):** 95%+ selectors are valid and unique
- **Good (0.85-0.94):** 85-94% selectors are valid
- **Acceptable (0.75-0.84):** 75-84% selectors are valid
- **Poor (<0.75):** Less than 75% selectors are valid

#### **Dimension 2: Element Detection Completeness** (Weight: 0.30)

**What it measures:** How many interactive elements did we find vs. total available?

**Scoring Method:**
```python
def score_detection_completeness(observed_elements: List[Dict], page: Page) -> float:
    """
    Compare observed elements against ground truth (manual count or LLM validation).
    
    Returns: Completeness score 0.0-1.0
    """
    # Ground truth: Count all interactive elements manually or via comprehensive scan
    ground_truth_count = await self._count_all_interactive_elements(page)
    
    # Observed count (filter for interactive elements only)
    observed_count = len([
        e for e in observed_elements 
        if e.get("type") in ["button", "input", "link", "select", "textarea"]
    ])
    
    # Completeness = min(observed / ground_truth, 1.0)
    # Cap at 1.0 to avoid penalizing over-detection (false positives are handled separately)
    completeness = min(observed_count / ground_truth_count, 1.0) if ground_truth_count > 0 else 0.0
    
    # Bonus for LLM enhancement finding missed elements
    llm_enhanced = len([e for e in observed_elements if e.get("source") == "llm"])
    if llm_enhanced > 0:
        completeness = min(completeness + 0.05, 1.0)  # Small bonus
    
    return completeness
```

**Industry Benchmark:**
- **Excellent (≥0.90):** 90%+ of interactive elements detected
- **Good (0.80-0.89):** 80-89% detected
- **Acceptable (0.70-0.79):** 70-79% detected
- **Poor (<0.70):** Less than 70% detected

#### **Dimension 3: Element Classification Accuracy** (Weight: 0.20)

**What it measures:** Are elements correctly classified (button vs. link vs. input)?

**Scoring Method:**
```python
def score_classification_accuracy(observed_elements: List[Dict], page: Page) -> float:
    """
    Validate element type classification by checking actual DOM element.
    
    Returns: Classification accuracy 0.0-1.0
    """
    total_elements = len(observed_elements)
    if total_elements == 0:
        return 0.0
    
    correct_classifications = 0
    for element in observed_elements:
        selector = element.get("selector", "")
        observed_type = element.get("type", "")
        
        try:
            dom_element = await page.query_selector(selector)
            if not dom_element:
                continue
            
            # Determine actual type from DOM
            tag_name = await dom_element.evaluate("el => el.tagName.toLowerCase()")
            actual_type = self._infer_element_type(tag_name, dom_element)
            
            # Check if classification matches
            if self._types_match(observed_type, actual_type):
                correct_classifications += 1
        except:
            continue
    
    return correct_classifications / total_elements if total_elements > 0 else 0.0

def _infer_element_type(self, tag_name: str, element) -> str:
    """Infer element type from DOM tag and attributes."""
    if tag_name == "button" or (tag_name == "input" and await element.get_attribute("type") in ["button", "submit"]):
        return "button"
    elif tag_name == "input":
        return "input"
    elif tag_name == "a":
        return "link"
    elif tag_name == "select":
        return "select"
    elif tag_name == "textarea":
        return "textarea"
    return "unknown"
```

**Industry Benchmark:**
- **Excellent (≥0.95):** 95%+ correct classifications
- **Good (0.90-0.94):** 90-94% correct
- **Acceptable (0.85-0.89):** 85-89% correct
- **Poor (<0.85):** Less than 85% correct

#### **Dimension 4: LLM Enhancement Effectiveness** (Weight: 0.15)

**What it measures:** How much value did LLM add beyond Playwright detection?

**Scoring Method:**
```python
def score_llm_enhancement(observed_elements: List[Dict], llm_analysis: Dict) -> float:
    """
    Measure LLM's contribution to element detection.
    
    Returns: Enhancement effectiveness 0.0-1.0
    """
    playwright_elements = len([e for e in observed_elements if e.get("source") != "llm"])
    llm_elements = len([e for e in observed_elements if e.get("source") == "llm"])
    
    if playwright_elements == 0:
        return 0.0  # No baseline to enhance
    
    # Effectiveness = (LLM elements found) / (Total elements) × (LLM elements validity)
    llm_validity = self._validate_llm_elements(llm_elements, observed_elements)
    enhancement_ratio = llm_elements / (playwright_elements + llm_elements)
    
    # Score = enhancement_ratio × validity
    # Bonus if LLM found critical elements (buttons, forms) that Playwright missed
    critical_llm_elements = len([
        e for e in observed_elements 
        if e.get("source") == "llm" and e.get("type") in ["button", "form"]
    ])
    critical_bonus = min(critical_llm_elements * 0.05, 0.15)  # Max 15% bonus
    
    return min(enhancement_ratio * llm_validity + critical_bonus, 1.0)
```

**Industry Benchmark:**
- **Excellent (≥0.20):** LLM found 20%+ additional valid elements
- **Good (0.10-0.19):** 10-19% additional elements
- **Acceptable (0.05-0.09):** 5-9% additional elements
- **Poor (<0.05):** Minimal LLM contribution

### 2.2 Overall ObservationAgent Score

```python
def calculate_observation_agent_score(
    selector_accuracy: float,
    detection_completeness: float,
    classification_accuracy: float,
    llm_enhancement: float
) -> Dict[str, Any]:
    """
    Calculate weighted overall score for ObservationAgent.
    
    Returns: {
        "overall_score": 0.0-1.0,
        "component_scores": {...},
        "grade": "A" | "B" | "C" | "D" | "F",
        "recommendations": [...]
    }
    """
    overall = (
        selector_accuracy * 0.35 +
        detection_completeness * 0.30 +
        classification_accuracy * 0.20 +
        llm_enhancement * 0.15
    )
    
    # Grade assignment
    if overall >= 0.90:
        grade = "A"
    elif overall >= 0.80:
        grade = "B"
    elif overall >= 0.70:
        grade = "C"
    elif overall >= 0.60:
        grade = "D"
    else:
        grade = "F"
    
    # Generate recommendations
    recommendations = []
    if selector_accuracy < 0.85:
        recommendations.append("Improve selector generation: Use more stable attributes (data-testid, aria-label)")
    if detection_completeness < 0.80:
        recommendations.append("Increase element detection: Enable deeper DOM traversal or LLM enhancement")
    if classification_accuracy < 0.90:
        recommendations.append("Fix element classification: Validate against actual DOM tag names")
    if llm_enhancement < 0.10 and self.use_llm:
        recommendations.append("Enhance LLM prompts: Focus on finding hidden or dynamic elements")
    
    return {
        "overall_score": overall,
        "component_scores": {
            "selector_accuracy": selector_accuracy,
            "detection_completeness": detection_completeness,
            "classification_accuracy": classification_accuracy,
            "llm_enhancement": llm_enhancement
        },
        "grade": grade,
        "recommendations": recommendations
    }
```

### 2.3 Implementation in ObservationAgent

**Add to `observation_agent.py`:**

```python
async def calculate_performance_score(self, task_result: TaskResult) -> Dict[str, Any]:
    """
    Calculate performance score for this observation task.
    Called after execute_task() completes.
    """
    result = task_result.result
    ui_elements = result.get("ui_elements", [])
    pages = result.get("pages", [])
    llm_analysis = result.get("llm_analysis", {})
    
    # Re-open browser to validate selectors (if not in stub mode)
    if PLAYWRIGHT_AVAILABLE and pages:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to first page
            first_url = pages[0].get("url") if isinstance(pages[0], dict) else pages[0].url
            await page.goto(first_url, timeout=30000)
            
            # Calculate component scores
            selector_accuracy = await self._score_selector_accuracy(ui_elements, page)
            detection_completeness = await self._score_detection_completeness(ui_elements, page)
            classification_accuracy = await self._score_classification_accuracy(ui_elements, page)
            llm_enhancement = self._score_llm_enhancement(ui_elements, llm_analysis)
            
            await browser.close()
            
            # Calculate overall score
            performance = self._calculate_observation_agent_score(
                selector_accuracy,
                detection_completeness,
                classification_accuracy,
                llm_enhancement
            )
            
            # Add to result metadata
            result["performance_score"] = performance
            
            return performance
    else:
        # Stub mode: Return placeholder
        return {
            "overall_score": 0.0,
            "component_scores": {},
            "grade": "N/A",
            "note": "Performance scoring requires Playwright (stub mode)"
        }
```

---

## 3. RequirementsAgent Performance Scoring

### 3.1 Scoring Dimensions

#### **Dimension 1: Test Scenario Correctness** (Weight: 0.40)

**What it measures:** Are the generated BDD scenarios syntactically correct and logically sound?

**Scoring Method:**
```python
def score_scenario_correctness(scenarios: List[Scenario]) -> float:
    """
    Validate BDD scenario format and logic.
    
    Returns: Correctness score 0.0-1.0
    """
    if not scenarios:
        return 0.0
    
    total_scenarios = len(scenarios)
    valid_scenarios = 0
    
    for scenario in scenarios:
        # Check 1: BDD format (Given/When/Then present)
        has_given = bool(scenario.given and scenario.given.strip())
        has_when = bool(scenario.when and scenario.when.strip())
        has_then = bool(scenario.then and scenario.then.strip())
        
        if not (has_given and has_when and has_then):
            continue  # Invalid BDD format
        
        # Check 2: Logical coherence (Given sets context, When performs action, Then verifies)
        if self._is_logically_coherent(scenario):
            valid_scenarios += 1
    
    return valid_scenarios / total_scenarios

def _is_logically_coherent(self, scenario: Scenario) -> bool:
    """Check if scenario follows logical flow: Given (context) → When (action) → Then (verification)."""
    given_lower = scenario.given.lower()
    when_lower = scenario.when.lower()
    then_lower = scenario.then.lower()
    
    # Given should contain context keywords
    context_keywords = ["user", "page", "on", "is", "has", "logged in", "navigated"]
    has_context = any(kw in given_lower for kw in context_keywords)
    
    # When should contain action keywords
    action_keywords = ["click", "enter", "type", "select", "submit", "navigate", "fill"]
    has_action = any(kw in when_lower for kw in action_keywords)
    
    # Then should contain verification keywords
    verification_keywords = ["verify", "should", "expect", "see", "display", "show", "appear"]
    has_verification = any(kw in then_lower for kw in verification_keywords)
    
    return has_context and has_action and has_verification
```

**Industry Benchmark:**
- **Excellent (≥0.95):** 95%+ scenarios are valid BDD format
- **Good (0.90-0.94):** 90-94% valid
- **Acceptable (0.85-0.89):** 85-89% valid
- **Poor (<0.85):** Less than 85% valid

#### **Dimension 2: Test Scenario Execution Success Rate** (Weight: 0.35)

**What it measures:** How many generated scenarios actually execute successfully?

**Scoring Method:**
```python
def score_execution_success_rate(
    scenarios: List[Scenario],
    execution_results: Dict[str, Dict]  # scenario_id -> {success: bool, error: str}
) -> float:
    """
    Measure how many scenarios execute successfully.
    
    Returns: Success rate 0.0-1.0
    """
    if not scenarios or not execution_results:
        return 0.0
    
    total_scenarios = len(scenarios)
    successful_executions = 0
    
    for scenario in scenarios:
        result = execution_results.get(scenario.scenario_id, {})
        if result.get("success", False):
            successful_executions += 1
    
    return successful_executions / total_scenarios
```

**Industry Benchmark:**
- **Excellent (≥0.90):** 90%+ scenarios execute successfully
- **Good (0.80-0.89):** 80-89% execute successfully
- **Acceptable (0.70-0.79):** 70-79% execute successfully
- **Poor (<0.70):** Less than 70% execute successfully

#### **Dimension 3: Test Coverage Completeness** (Weight: 0.15)

**What it measures:** Do scenarios cover all critical UI elements and user journeys?

**Scoring Method:**
```python
def score_coverage_completeness(
    scenarios: List[Scenario],
    ui_elements: List[Dict],
    user_journeys: List[List[str]]
) -> float:
    """
    Measure how well scenarios cover UI elements and user journeys.
    
    Returns: Coverage score 0.0-1.0
    """
    # Coverage 1: UI element coverage
    critical_elements = [
        e for e in ui_elements 
        if e.get("type") in ["button", "form", "input"] and e.get("required", False)
    ]
    
    covered_elements = set()
    for scenario in scenarios:
        # Extract element references from scenario
        scenario_elements = self._extract_element_references(scenario)
        covered_elements.update(scenario_elements)
    
    element_coverage = len(covered_elements) / len(critical_elements) if critical_elements else 0.0
    
    # Coverage 2: User journey coverage
    covered_journeys = 0
    for journey in user_journeys:
        if self._journey_covered_by_scenarios(journey, scenarios):
            covered_journeys += 1
    
    journey_coverage = covered_journeys / len(user_journeys) if user_journeys else 0.0
    
    # Weighted average
    return (element_coverage * 0.6) + (journey_coverage * 0.4)
```

**Industry Benchmark:**
- **Excellent (≥0.85):** 85%+ coverage of critical elements/journeys
- **Good (0.75-0.84):** 75-84% coverage
- **Acceptable (0.65-0.74):** 65-74% coverage
- **Poor (<0.65):** Less than 65% coverage

#### **Dimension 4: Scenario Quality (Relevance & Completeness)** (Weight: 0.10)

**What it measures:** Are scenarios relevant to the application and complete (not missing steps)?

**Scoring Method:**
```python
def score_scenario_quality(scenarios: List[Scenario], ui_elements: List[Dict]) -> float:
    """
    Measure scenario relevance and completeness.
    
    Returns: Quality score 0.0-1.0
    """
    if not scenarios:
        return 0.0
    
    total_score = 0.0
    for scenario in scenarios:
        # Relevance: Does scenario reference actual UI elements?
        scenario_elements = self._extract_element_references(scenario)
        element_exists = any(
            self._element_matches(e, ui_elements) 
            for e in scenario_elements
        )
        relevance_score = 1.0 if element_exists else 0.5
        
        # Completeness: Does scenario have sufficient detail?
        given_words = len(scenario.given.split()) if scenario.given else 0
        when_words = len(scenario.when.split()) if scenario.when else 0
        then_words = len(scenario.then.split()) if scenario.then else 0
        
        # Minimum thresholds: Given (5 words), When (3 words), Then (3 words)
        completeness_score = 1.0 if (
            given_words >= 5 and when_words >= 3 and then_words >= 3
        ) else 0.7
        
        total_score += (relevance_score * 0.6) + (completeness_score * 0.4)
    
    return total_score / len(scenarios)
```

**Industry Benchmark:**
- **Excellent (≥0.90):** 90%+ scenarios are relevant and complete
- **Good (0.80-0.89):** 80-89% relevant and complete
- **Acceptable (0.70-0.79):** 70-79% relevant and complete
- **Poor (<0.70):** Less than 70% relevant and complete

### 3.2 Overall RequirementsAgent Score

```python
def calculate_requirements_agent_score(
    scenario_correctness: float,
    execution_success_rate: float,
    coverage_completeness: float,
    scenario_quality: float
) -> Dict[str, Any]:
    """
    Calculate weighted overall score for RequirementsAgent.
    """
    overall = (
        scenario_correctness * 0.40 +
        execution_success_rate * 0.35 +
        coverage_completeness * 0.15 +
        scenario_quality * 0.10
    )
    
    # Grade assignment
    grade = "A" if overall >= 0.90 else "B" if overall >= 0.80 else "C" if overall >= 0.70 else "D" if overall >= 0.60 else "F"
    
    recommendations = []
    if scenario_correctness < 0.90:
        recommendations.append("Improve BDD format validation: Ensure all scenarios have Given/When/Then")
    if execution_success_rate < 0.80:
        recommendations.append("Fix scenario executability: Validate selectors and element references before generation")
    if coverage_completeness < 0.75:
        recommendations.append("Increase coverage: Generate scenarios for all critical UI elements and user journeys")
    if scenario_quality < 0.80:
        recommendations.append("Enhance scenario quality: Add more detail and ensure element references are valid")
    
    return {
        "overall_score": overall,
        "component_scores": {
            "scenario_correctness": scenario_correctness,
            "execution_success_rate": execution_success_rate,
            "coverage_completeness": coverage_completeness,
            "scenario_quality": scenario_quality
        },
        "grade": grade,
        "recommendations": recommendations
    }
```

### 3.3 Implementation in RequirementsAgent

**Add to `requirements_agent.py`:**

```python
async def calculate_performance_score(
    self,
    task_result: TaskResult,
    execution_results: Optional[Dict[str, Dict]] = None
) -> Dict[str, Any]:
    """
    Calculate performance score for this requirements extraction task.
    Requires execution results from AnalysisAgent for success rate calculation.
    """
    result = task_result.result
    scenarios = [self._dict_to_scenario(s) for s in result.get("scenarios", [])]
    ui_elements = task_result.result.get("ui_elements", [])  # From ObservationAgent
    user_journeys = result.get("user_journeys", [])
    
    # Calculate component scores
    scenario_correctness = self._score_scenario_correctness(scenarios)
    execution_success_rate = self._score_execution_success_rate(scenarios, execution_results or {})
    coverage_completeness = self._score_coverage_completeness(scenarios, ui_elements, user_journeys)
    scenario_quality = self._score_scenario_quality(scenarios, ui_elements)
    
    # Calculate overall score
    performance = self._calculate_requirements_agent_score(
        scenario_correctness,
        execution_success_rate,
        coverage_completeness,
        scenario_quality
    )
    
    # Add to result metadata
    result["performance_score"] = performance
    
    return performance
```

---

## 4. AnalysisAgent Performance Scoring

### 4.1 Scoring Dimensions

#### **Dimension 1: Risk Score Accuracy** (Weight: 0.30)

**What it measures:** How accurately did we predict which scenarios would fail?

**Scoring Method:**
```python
def score_risk_accuracy(
    predicted_risks: Dict[str, RiskScore],  # scenario_id -> RiskScore
    actual_failures: Dict[str, bool]  # scenario_id -> failed (True) or passed (False)
) -> float:
    """
    Compare predicted risk scores against actual test failures.
    
    Returns: Risk prediction accuracy 0.0-1.0
    """
    if not predicted_risks or not actual_failures:
        return 0.0
    
    # Convert risk scores to binary predictions (high risk = likely to fail)
    # High risk = RPN >= 50 (HIGH priority)
    high_risk_scenarios = {
        sid for sid, rs in predicted_risks.items()
        if rs.to_priority() == RiskPriority.HIGH
    }
    
    # Actual failures
    failed_scenarios = {sid for sid, failed in actual_failures.items() if failed}
    
    # Calculate precision and recall
    true_positives = len(high_risk_scenarios & failed_scenarios)
    false_positives = len(high_risk_scenarios - failed_scenarios)
    false_negatives = len(failed_scenarios - high_risk_scenarios)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    
    # F1 score (harmonic mean of precision and recall)
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return f1_score
```

**Industry Benchmark:**
- **Excellent (≥0.80):** F1 score ≥ 0.80 (high precision and recall)
- **Good (0.70-0.79):** F1 score 0.70-0.79
- **Acceptable (0.60-0.69):** F1 score 0.60-0.69
- **Poor (<0.60):** F1 score < 0.60

#### **Dimension 2: ROI Prediction Accuracy** (Weight: 0.25)

**What it measures:** How accurately did we predict the ROI of testing each scenario?

**Scoring Method:**
```python
def score_roi_accuracy(
    predicted_roi: Dict[str, float],  # scenario_id -> predicted ROI
    actual_roi: Dict[str, float]  # scenario_id -> actual ROI (from execution results)
) -> float:
    """
    Compare predicted ROI against actual ROI.
    
    Actual ROI = (Bugs found × Bug severity value) / (Execution time × Cost per hour)
    """
    if not predicted_roi or not actual_roi:
        return 0.0
    
    # Calculate correlation coefficient (Pearson's r)
    scenario_ids = set(predicted_roi.keys()) & set(actual_roi.keys())
    if len(scenario_ids) < 2:
        return 0.0
    
    predicted_values = [predicted_roi[sid] for sid in scenario_ids]
    actual_values = [actual_roi[sid] for sid in scenario_ids]
    
    # Pearson correlation
    correlation = self._pearson_correlation(predicted_values, actual_values)
    
    # Convert correlation (-1 to 1) to accuracy score (0 to 1)
    # Strong positive correlation (r > 0.7) = high accuracy
    accuracy_score = max(0.0, correlation)  # Only positive correlations count
    
    return accuracy_score

def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    n = len(x)
    if n == 0:
        return 0.0
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))
    
    if denominator_x == 0 or denominator_y == 0:
        return 0.0
    
    return numerator / ((denominator_x * denominator_y) ** 0.5)
```

**Industry Benchmark:**
- **Excellent (≥0.70):** Correlation ≥ 0.70 (strong positive correlation)
- **Good (0.60-0.69):** Correlation 0.60-0.69
- **Acceptable (0.50-0.59):** Correlation 0.50-0.59
- **Poor (<0.50):** Correlation < 0.50

#### **Dimension 3: Execution Time Prediction Accuracy** (Weight: 0.20)

**What it measures:** How accurately did we predict test execution times?

**Scoring Method:**
```python
def score_execution_time_accuracy(
    predicted_times: Dict[str, float],  # scenario_id -> predicted seconds
    actual_times: Dict[str, float]  # scenario_id -> actual seconds
) -> float:
    """
    Compare predicted execution times against actual times.
    
    Returns: Time prediction accuracy 0.0-1.0 (using Mean Absolute Percentage Error)
    """
    if not predicted_times or not actual_times:
        return 0.0
    
    scenario_ids = set(predicted_times.keys()) & set(actual_times.keys())
    if not scenario_ids:
        return 0.0
    
    # Calculate MAPE (Mean Absolute Percentage Error)
    errors = []
    for sid in scenario_ids:
        predicted = predicted_times[sid]
        actual = actual_times[sid]
        
        if actual > 0:
            error = abs(predicted - actual) / actual
            errors.append(error)
    
    if not errors:
        return 0.0
    
    mape = sum(errors) / len(errors)
    
    # Convert MAPE to accuracy score (lower MAPE = higher accuracy)
    # MAPE < 0.20 (20% error) = excellent, MAPE < 0.40 = good, etc.
    if mape < 0.20:
        accuracy = 1.0
    elif mape < 0.40:
        accuracy = 0.8
    elif mape < 0.60:
        accuracy = 0.6
    elif mape < 0.80:
        accuracy = 0.4
    else:
        accuracy = 0.2
    
    return accuracy
```

**Industry Benchmark:**
- **Excellent (MAPE < 0.20):** Within 20% of actual time
- **Good (MAPE 0.20-0.39):** Within 20-39% of actual time
- **Acceptable (MAPE 0.40-0.59):** Within 40-59% of actual time
- **Poor (MAPE ≥ 0.60):** More than 60% error

#### **Dimension 4: Prioritization Effectiveness** (Weight: 0.25)

**What it measures:** Did prioritizing high-risk scenarios first lead to finding bugs faster?

**Scoring Method:**
```python
def score_prioritization_effectiveness(
    prioritization_order: List[str],  # scenario_id in priority order
    actual_failures: Dict[str, bool],  # scenario_id -> failed
    execution_times: Dict[str, float]  # scenario_id -> execution time
) -> float:
    """
    Measure if high-priority scenarios found bugs earlier (faster time-to-bug-discovery).
    
    Returns: Prioritization effectiveness 0.0-1.0
    """
    if not prioritization_order or not actual_failures:
        return 0.0
    
    # Calculate cumulative time to first bug discovery
    cumulative_time = 0.0
    bugs_found_at_positions = []
    
    for idx, scenario_id in enumerate(prioritization_order):
        cumulative_time += execution_times.get(scenario_id, 0.0)
        
        if actual_failures.get(scenario_id, False):
            bugs_found_at_positions.append((idx, cumulative_time))
    
    if not bugs_found_at_positions:
        return 0.5  # No bugs found, neutral score
    
    # Ideal: Bugs found in first 30% of scenarios
    # Good: Bugs found in first 50% of scenarios
    # Poor: Bugs found in last 50% of scenarios
    
    first_bug_position = bugs_found_at_positions[0][0]
    total_scenarios = len(prioritization_order)
    position_ratio = first_bug_position / total_scenarios if total_scenarios > 0 else 1.0
    
    if position_ratio <= 0.30:
        effectiveness = 1.0
    elif position_ratio <= 0.50:
        effectiveness = 0.8
    elif position_ratio <= 0.70:
        effectiveness = 0.6
    else:
        effectiveness = 0.4
    
    return effectiveness
```

**Industry Benchmark:**
- **Excellent (≥0.90):** First bugs found in top 30% of prioritized scenarios
- **Good (0.80-0.89):** First bugs found in top 30-50%
- **Acceptable (0.70-0.79):** First bugs found in top 50-70%
- **Poor (<0.70):** First bugs found in bottom 30%

### 4.2 Overall AnalysisAgent Score

```python
def calculate_analysis_agent_score(
    risk_accuracy: float,
    roi_accuracy: float,
    execution_time_accuracy: float,
    prioritization_effectiveness: float
) -> Dict[str, Any]:
    """
    Calculate weighted overall score for AnalysisAgent.
    """
    overall = (
        risk_accuracy * 0.30 +
        roi_accuracy * 0.25 +
        execution_time_accuracy * 0.20 +
        prioritization_effectiveness * 0.25
    )
    
    grade = "A" if overall >= 0.85 else "B" if overall >= 0.75 else "C" if overall >= 0.65 else "D" if overall >= 0.55 else "F"
    
    recommendations = []
    if risk_accuracy < 0.70:
        recommendations.append("Improve risk prediction: Enhance FMEA scoring with more historical data")
    if roi_accuracy < 0.60:
        recommendations.append("Refine ROI calculation: Better estimate bug severity values and execution costs")
    if execution_time_accuracy < 0.60:
        recommendations.append("Improve time estimation: Use historical execution data for more accurate predictions")
    if prioritization_effectiveness < 0.75:
        recommendations.append("Enhance prioritization: Adjust risk weights to better align with actual bug discovery")
    
    return {
        "overall_score": overall,
        "component_scores": {
            "risk_accuracy": risk_accuracy,
            "roi_accuracy": roi_accuracy,
            "execution_time_accuracy": execution_time_accuracy,
            "prioritization_effectiveness": prioritization_effectiveness
        },
        "grade": grade,
        "recommendations": recommendations
    }
```

### 4.3 Implementation in AnalysisAgent

**Add to `analysis_agent.py`:**

```python
async def calculate_performance_score(
    self,
    task_result: TaskResult,
    execution_results: Dict[str, Dict]  # scenario_id -> {success: bool, execution_time: float, bugs_found: int}
) -> Dict[str, Any]:
    """
    Calculate performance score for this analysis task.
    Requires execution results to compare predictions against actual outcomes.
    """
    result = task_result.result
    risk_scores = {rs["scenario_id"]: self._dict_to_risk_score(rs) for rs in result.get("risk_scores", [])}
    roi_scores = {rs["scenario_id"]: rs.get("roi", 0.0) for rs in result.get("roi_scores", [])}
    execution_times = result.get("execution_times", {})
    final_prioritization = result.get("final_prioritization", [])
    
    # Extract actual results from execution
    actual_failures = {
        sid: not exec_result.get("success", True)
        for sid, exec_result in execution_results.items()
    }
    actual_times = {
        sid: exec_result.get("execution_time", 0.0)
        for sid, exec_result in execution_results.items()
    }
    actual_roi = {
        sid: self._calculate_actual_roi(exec_result)
        for sid, exec_result in execution_results.items()
    }
    
    # Calculate component scores
    risk_accuracy = self._score_risk_accuracy(risk_scores, actual_failures)
    roi_accuracy = self._score_roi_accuracy(roi_scores, actual_roi)
    execution_time_accuracy = self._score_execution_time_accuracy(execution_times, actual_times)
    prioritization_effectiveness = self._score_prioritization_effectiveness(
        final_prioritization, actual_failures, actual_times
    )
    
    # Calculate overall score
    performance = self._calculate_analysis_agent_score(
        risk_accuracy,
        roi_accuracy,
        execution_time_accuracy,
        prioritization_effectiveness
    )
    
    # Add to result metadata
    result["performance_score"] = performance
    
    return performance
```

---

## 5. Cross-Agent Validation

### 5.1 End-to-End Workflow Scoring

**Overall System Score:**
```python
def calculate_system_score(
    observation_score: float,
    requirements_score: float,
    analysis_score: float
) -> Dict[str, Any]:
    """
    Calculate overall system performance across all agents.
    """
    # Weighted by agent criticality in the pipeline
    system_score = (
        observation_score * 0.30 +  # Foundation: Good observation = good foundation
        requirements_score * 0.40 +  # Core: Requirements drive everything
        analysis_score * 0.30        # Optimization: Analysis improves efficiency
    )
    
    return {
        "system_score": system_score,
        "agent_scores": {
            "observation": observation_score,
            "requirements": requirements_score,
            "analysis": analysis_score
        },
        "grade": "A" if system_score >= 0.85 else "B" if system_score >= 0.75 else "C" if system_score >= 0.65 else "D" if system_score >= 0.55 else "F"
    }
```

### 5.2 Continuous Improvement Tracking

**Store scores in database for trend analysis:**
```python
# In database schema (add to Phase 2 test_executions or new table)
CREATE TABLE agent_performance_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type TEXT NOT NULL,  -- 'observation', 'requirements', 'analysis'
    task_id TEXT NOT NULL,
    overall_score REAL,
    component_scores JSON,
    grade TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);
```

---

## 6. Implementation Roadmap

### Phase 1: ObservationAgent Scoring (Week 1)
- [ ] Implement `score_selector_accuracy()`
- [ ] Implement `score_detection_completeness()`
- [ ] Implement `score_classification_accuracy()`
- [ ] Implement `score_llm_enhancement()`
- [ ] Add `calculate_performance_score()` to ObservationAgent
- [ ] Unit tests for scoring methods

### Phase 2: RequirementsAgent Scoring (Week 2)
- [ ] Implement `score_scenario_correctness()`
- [ ] Implement `score_execution_success_rate()` (requires AnalysisAgent integration)
- [ ] Implement `score_coverage_completeness()`
- [ ] Implement `score_scenario_quality()`
- [ ] Add `calculate_performance_score()` to RequirementsAgent
- [ ] Unit tests for scoring methods

### Phase 3: AnalysisAgent Scoring (Week 3)
- [ ] Implement `score_risk_accuracy()`
- [ ] Implement `score_roi_accuracy()`
- [ ] Implement `score_execution_time_accuracy()`
- [ ] Implement `score_prioritization_effectiveness()`
- [ ] Add `calculate_performance_score()` to AnalysisAgent
- [ ] Unit tests for scoring methods

### Phase 4: Integration & Reporting (Week 4)
- [ ] Add database schema for storing performance scores
- [ ] Create performance dashboard/reporting endpoint
- [ ] Integrate scoring into E2E workflow
- [ ] Add trend analysis (score improvement over time)
- [ ] Documentation and examples

---

## 7. Example Usage

### 7.1 Calculating ObservationAgent Score

```python
# After ObservationAgent.execute_task() completes
observation_result = await observation_agent.execute_task(task)
performance = await observation_agent.calculate_performance_score(observation_result)

print(f"ObservationAgent Score: {performance['overall_score']:.2f} (Grade: {performance['grade']})")
print(f"  - Selector Accuracy: {performance['component_scores']['selector_accuracy']:.2f}")
print(f"  - Detection Completeness: {performance['component_scores']['detection_completeness']:.2f}")
print(f"  - Classification Accuracy: {performance['component_scores']['classification_accuracy']:.2f}")
print(f"  - LLM Enhancement: {performance['component_scores']['llm_enhancement']:.2f}")
```

### 7.2 Calculating RequirementsAgent Score

```python
# After RequirementsAgent.execute_task() completes
requirements_result = await requirements_agent.execute_task(task)

# After AnalysisAgent executes scenarios
analysis_result = await analysis_agent.execute_task(analysis_task)
execution_results = analysis_result.result.get("execution_success", {})

# Calculate RequirementsAgent performance
performance = await requirements_agent.calculate_performance_score(
    requirements_result,
    execution_results
)

print(f"RequirementsAgent Score: {performance['overall_score']:.2f} (Grade: {performance['grade']})")
print(f"  - Scenario Correctness: {performance['component_scores']['scenario_correctness']:.2f}")
print(f"  - Execution Success Rate: {performance['component_scores']['execution_success_rate']:.2f}")
```

### 7.3 Calculating AnalysisAgent Score

```python
# After AnalysisAgent.execute_task() completes
analysis_result = await analysis_agent.execute_task(task)

# Get actual execution results (from Phase 2 test_executions or real-time execution)
execution_results = {
    "scenario-1": {"success": True, "execution_time": 12.5, "bugs_found": 0},
    "scenario-2": {"success": False, "execution_time": 8.3, "bugs_found": 1},
    # ...
}

# Calculate AnalysisAgent performance
performance = await analysis_agent.calculate_performance_score(
    analysis_result,
    execution_results
)

print(f"AnalysisAgent Score: {performance['overall_score']:.2f} (Grade: {performance['grade']})")
print(f"  - Risk Accuracy: {performance['component_scores']['risk_accuracy']:.2f}")
print(f"  - ROI Accuracy: {performance['component_scores']['roi_accuracy']:.2f}")
print(f"  - Time Prediction Accuracy: {performance['component_scores']['execution_time_accuracy']:.2f}")
print(f"  - Prioritization Effectiveness: {performance['component_scores']['prioritization_effectiveness']:.2f}")
```

---

## 8. References

- **ISTQB Foundation Level Syllabus:** Test coverage metrics, test quality attributes
- **IEEE 29119-1:** Software Testing Standard - Concepts and Definitions
- **ISO/IEC 25010:** Systems and software Quality Requirements and Evaluation (SQuaRE) - System and software quality models
- **WCAG 2.1:** Web Content Accessibility Guidelines
- **OWASP Top 10:** Application Security Risks

---

**Document Status:** 📋 Design Complete - Ready for Implementation  
**Next Steps:** Begin Phase 1 implementation (ObservationAgent scoring)

