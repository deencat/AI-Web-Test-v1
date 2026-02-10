# Goal-Aware Test Generation: Completing Flows to True Completion

## Problem Statement

**Current Issue:** The system generates test steps that appear to complete a flow, but actually stop before the goal is truly achieved.

**Example:**
- **User Requirement:** "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"
- **Generated Steps (11 steps):**
  1. Navigate to page
  2. Find and select plan
  3. Select contract term '48個月'
  4. Verify price
  5. Click '立即登記'
  6. Fill form fields
  7. Click '下一步'
  8. Verify confirmation
  9. ✅ **STOPS HERE** ❌

**Problem:** After step 8, the purchase is **NOT complete**:
- ❌ User hasn't reached payment page
- ❌ User hasn't entered payment details
- ❌ User hasn't confirmed payment
- ❌ Purchase order hasn't been created
- ❌ No order confirmation received

**Root Cause:** The system generates steps based on the BDD scenario's "Then" clause, but doesn't verify if the **actual goal** (complete purchase) has been achieved.

---

## Solution: Goal-Aware Test Generation

### Approach 1: Enhanced Prompt with Goal Completion Criteria

**Enhance EvolutionAgent prompt to include goal completion verification:**

```python
def _build_prompt_variant_1_goal_aware(
    self,
    scenario: Dict,
    risk_scores: List[Dict],
    prioritization: List[Dict],
    page_context: Dict,
    test_data: List[Dict],
    user_instruction: str = ""  # Add user instruction for goal awareness
) -> str:
    """Variant 1 with goal-aware completion detection"""
    
    # Extract goal from user instruction or scenario title
    goal = self._extract_goal(user_instruction or scenario.get("title", ""))
    
    # Determine completion criteria based on goal type
    completion_criteria = self._get_completion_criteria(goal)
    
    prompt = f"""Generate executable test steps for the following BDD scenario.

**GOAL:** {goal}
**COMPLETION CRITERIA:** {completion_criteria}

**Scenario Information:**
- Title: {scenario.get("title", "")}
- Given: {scenario.get("given", "")}
- When: {scenario.get("when", "")}
- Then: {scenario.get("then", "")}

**CRITICAL REQUIREMENTS:**
1. **Goal Completion:** The steps MUST continue until the goal "{goal}" is TRULY achieved
2. **Multi-Page Flows:** If the goal requires multiple pages (e.g., purchase flow), include ALL pages:
   - Plan selection page
   - Registration/checkout page
   - Payment page
   - Order confirmation page
3. **State Verification:** After each major step, verify the current state:
   - If on payment page → Continue to payment completion
   - If on confirmation page → Verify order details
   - If goal not achieved → Generate additional steps
4. **Complete Flow:** For "Complete purchase flow", include:
   - Plan selection ✅
   - Registration/checkout ✅
   - Payment entry ✅
   - Payment confirmation ✅
   - Order confirmation ✅
   - Order details verification ✅

**DO NOT STOP** until you verify:
- The goal state has been reached
- All required pages have been visited
- All required actions have been completed
- Final verification confirms goal achievement

**Output Format:**
{{
  "steps": ["step1", "step2", ...],
  "goal_verification": "How to verify the goal is achieved",
  "completion_state": "Expected final state (e.g., 'Order confirmed with order ID')"
}}
"""
    return prompt
```

### Approach 2: Execution-Time Goal Verification

**Add goal verification during execution:**

```python
async def _execute_with_goal_verification(
    self,
    test_steps: List[str],
    goal: str,
    page_context: Dict
) -> Dict:
    """
    Execute test steps and verify goal completion.
    If goal not achieved, generate additional steps dynamically.
    """
    execution_service = StagehandExecutionService()
    await execution_service.initialize()
    
    executed_steps = []
    current_state = None
    
    # Execute initial steps
    for step in test_steps:
        result = await execution_service._execute_step_hybrid(step, len(executed_steps) + 1)
        executed_steps.append({
            "step": step,
            "result": result,
            "success": result.get("success", False)
        })
        
        # Check current state after each step
        current_state = await self._get_current_page_state(execution_service)
        
        # Verify if goal is achieved
        goal_achieved = await self._verify_goal_achievement(
            goal=goal,
            current_state=current_state,
            page_context=page_context
        )
        
        if goal_achieved:
            logger.info(f"Goal '{goal}' achieved after {len(executed_steps)} steps")
            break
    
    # If goal not achieved, generate additional steps
    if not goal_achieved:
        logger.warning(f"Goal '{goal}' not achieved after {len(executed_steps)} steps")
        logger.info(f"Current state: {current_state}")
        
        # Generate additional steps to reach goal
        additional_steps = await self._generate_additional_steps_for_goal(
            goal=goal,
            current_state=current_state,
            page_context=page_context,
            executed_steps=executed_steps
        )
        
        # Execute additional steps
        for step in additional_steps:
            result = await execution_service._execute_step_hybrid(step, len(executed_steps) + 1)
            executed_steps.append({
                "step": step,
                "result": result,
                "success": result.get("success", False)
            })
            
            # Check goal again
            current_state = await self._get_current_page_state(execution_service)
            goal_achieved = await self._verify_goal_achievement(
                goal=goal,
                current_state=current_state,
                page_context=page_context
            )
            
            if goal_achieved:
                break
    
    return {
        "executed_steps": executed_steps,
        "goal_achieved": goal_achieved,
        "final_state": current_state,
        "total_steps": len(executed_steps)
    }
```

### Approach 3: Goal Completion Criteria Library

**Define completion criteria for common goals:**

```python
GOAL_COMPLETION_CRITERIA = {
    "complete purchase flow": {
        "required_pages": [
            "plan_selection",
            "registration/checkout",
            "payment",
            "order_confirmation"
        ],
        "required_actions": [
            "select_plan",
            "select_contract_term",
            "click_register",
            "fill_registration_form",
            "click_next",
            "enter_payment_details",
            "confirm_payment",
            "verify_order_confirmation"
        ],
        "verification_indicators": [
            "order_id_present",
            "order_confirmation_message",
            "payment_success_indicator",
            "order_details_displayed"
        ],
        "final_state": "Order confirmed with order ID and payment confirmation"
    },
    "user registration": {
        "required_pages": [
            "registration_form",
            "email_verification",
            "welcome_page"
        ],
        "required_actions": [
            "fill_registration_form",
            "submit_form",
            "verify_email",
            "complete_registration"
        ],
        "verification_indicators": [
            "welcome_message",
            "user_profile_visible",
            "registration_complete_indicator"
        ],
        "final_state": "User registered and logged in"
    },
    "checkout process": {
        "required_pages": [
            "cart",
            "checkout",
            "payment",
            "order_confirmation"
        ],
        "required_actions": [
            "review_cart",
            "proceed_to_checkout",
            "enter_shipping_details",
            "enter_payment_details",
            "confirm_order"
        ],
        "verification_indicators": [
            "order_number",
            "shipping_confirmation",
            "payment_confirmation"
        ],
        "final_state": "Order placed with order number"
    }
}

def _get_completion_criteria(self, goal: str) -> Dict:
    """Get completion criteria for a goal"""
    goal_lower = goal.lower()
    
    # Match goal to criteria
    for key, criteria in GOAL_COMPLETION_CRITERIA.items():
        if key in goal_lower:
            return criteria
    
    # Default criteria for unknown goals
    return {
        "required_pages": [],
        "required_actions": [],
        "verification_indicators": [
            "goal_achieved_indicator",
            "success_message",
            "completion_state_visible"
        ],
        "final_state": "Goal achieved"
    }
```

### Approach 4: Multi-Page Flow Detection

**Detect when flow spans multiple pages:**

```python
async def _detect_multi_page_flow(
    self,
    goal: str,
    page_context: Dict,
    ui_elements: List[Dict]
) -> Dict:
    """
    Detect if goal requires multiple pages and identify navigation points.
    """
    # Analyze UI elements for navigation indicators
    navigation_buttons = [
        elem for elem in ui_elements
        if elem.get("type") == "button" and any(
            keyword in elem.get("text", "").lower()
            for keyword in ["next", "continue", "proceed", "submit", "confirm", "下一步", "立即登記"]
        )
    ]
    
    # Check for form submission indicators
    forms = [elem for elem in ui_elements if elem.get("type") == "form"]
    
    # Determine if flow is multi-page
    is_multi_page = (
        len(navigation_buttons) > 1 or  # Multiple navigation buttons
        len(forms) > 0 or  # Forms indicate multi-step process
        "flow" in goal.lower() or  # Goal mentions "flow"
        "complete" in goal.lower()  # Goal requires completion
    )
    
    return {
        "is_multi_page": is_multi_page,
        "navigation_points": navigation_buttons,
        "estimated_pages": self._estimate_page_count(goal, navigation_buttons),
        "flow_type": self._classify_flow_type(goal)
    }
```

### Approach 5: Dynamic Step Generation Based on Current State

**Generate additional steps based on current page state:**

```python
async def _generate_additional_steps_for_goal(
    self,
    goal: str,
    current_state: Dict,
    page_context: Dict,
    executed_steps: List[Dict]
) -> List[str]:
    """
    Generate additional steps to reach goal based on current state.
    """
    current_url = current_state.get("url", "")
    current_page_type = current_state.get("page_type", "unknown")
    available_elements = current_state.get("elements", [])
    
    # Build prompt for LLM to generate next steps
    prompt = f"""The goal "{goal}" has not been achieved yet.

**Current State:**
- URL: {current_url}
- Page Type: {current_page_type}
- Available Elements: {len(available_elements)} elements

**Executed Steps So Far:**
{chr(10).join(f"{i+1}. {step['step']}" for i, step in enumerate(executed_steps[-5:]))}

**Goal:** {goal}

**Task:** Generate the next steps needed to achieve this goal from the current state.

**Requirements:**
1. Analyze the current page state
2. Identify what actions are needed to progress toward the goal
3. Generate specific, executable steps
4. Continue until goal is achieved

**Output Format:**
{{
  "next_steps": ["step1", "step2", ...],
  "expected_outcome": "What should happen after these steps",
  "goal_verification": "How to verify goal is achieved after these steps"
}}
"""
    
    # Call LLM to generate next steps
    response = self.llm_client.client.chat.completions.create(
        model=self.llm_client.deployment,
        messages=[
            {"role": "system", "content": "You are an expert test automation engineer. Generate next steps to achieve a goal."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1000,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return result.get("next_steps", [])
```

### Approach 6: Goal State Verification

**Verify if goal has been achieved:**

```python
async def _verify_goal_achievement(
    self,
    goal: str,
    current_state: Dict,
    page_context: Dict
) -> bool:
    """
    Verify if the goal has been achieved based on current state.
    """
    current_url = current_state.get("url", "")
    page_content = current_state.get("content", "")
    page_title = current_state.get("title", "")
    
    # Get completion criteria for goal
    criteria = self._get_completion_criteria(goal)
    
    # Check verification indicators
    verification_indicators = criteria.get("verification_indicators", [])
    
    # Check if any verification indicator is present
    for indicator in verification_indicators:
        if indicator == "order_id_present":
            # Check for order ID pattern
            if re.search(r"order[_\s]?id[:\s]?\d+", page_content, re.IGNORECASE):
                return True
        elif indicator == "order_confirmation_message":
            # Check for confirmation message
            confirmation_keywords = ["confirmed", "success", "complete", "thank you", "訂單確認"]
            if any(keyword in page_content.lower() for keyword in confirmation_keywords):
                return True
        elif indicator == "payment_success_indicator":
            # Check for payment success
            payment_keywords = ["payment successful", "paid", "payment confirmed", "付款成功"]
            if any(keyword in page_content.lower() for keyword in payment_keywords):
                return True
        elif indicator == "order_details_displayed":
            # Check for order details
            detail_keywords = ["order details", "order summary", "訂單詳情"]
            if any(keyword in page_content.lower() for keyword in detail_keywords):
                return True
    
    # Check URL patterns
    if "order" in goal.lower() or "purchase" in goal.lower():
        # Check if URL contains order/confirmation indicators
        if any(pattern in current_url.lower() for pattern in ["order", "confirm", "success", "complete"]):
            return True
    
    return False
```

---

## Implementation Plan

### Phase 1: Enhanced Prompt (Immediate)

**File:** `backend/agents/evolution_agent.py`

1. Add `user_instruction` parameter to `_build_prompt_variant_1()`
2. Extract goal from user instruction
3. Add goal completion criteria to prompt
4. Include multi-page flow instructions

**Expected Impact:**
- ✅ LLM generates more complete flows
- ✅ Includes all required pages
- ✅ Verifies goal achievement

### Phase 2: Goal Completion Criteria Library

**File:** `backend/agents/goal_completion.py` (new)

1. Create `GOAL_COMPLETION_CRITERIA` dictionary
2. Implement `_get_completion_criteria()` method
3. Add common goals (purchase, registration, checkout)

**Expected Impact:**
- ✅ Standardized completion criteria
- ✅ Reusable across scenarios
- ✅ Consistent goal verification

### Phase 3: Execution-Time Goal Verification

**File:** `backend/agents/analysis_agent.py`

1. Add `_verify_goal_achievement()` method
2. Add `_generate_additional_steps_for_goal()` method
3. Integrate into `_execute_scenario_real_time()`

**Expected Impact:**
- ✅ Real-time goal verification
- ✅ Dynamic step generation
- ✅ True completion detection

### Phase 4: Multi-Page Flow Detection

**File:** `backend/agents/requirements_agent.py`

1. Add `_detect_multi_page_flow()` method
2. Include flow information in scenario metadata
3. Pass to EvolutionAgent for enhanced generation

**Expected Impact:**
- ✅ Better multi-page flow handling
- ✅ Accurate page count estimation
- ✅ Proper navigation detection

---

## Example: Enhanced Purchase Flow

### Before (Current - Incomplete)

```
1. Navigate to page
2. Find and select plan '5G寬頻數據無限任用'
3. Select contract term '48個月'
4. Verify price
5. Click '立即登記'
6. Fill form fields
7. Click '下一步'
8. Verify confirmation
✅ STOPS HERE ❌
```

### After (Goal-Aware - Complete)

```
1. Navigate to page
2. Find and select plan '5G寬頻數據無限任用'
3. Select contract term '48個月'
4. Verify price
5. Click '立即登記'
6. Fill registration form (name, email, phone)
7. Click '下一步'
8. Verify navigation to next page
9. Fill additional details if required
10. Click 'Continue' or 'Proceed to Payment'
11. Verify navigation to payment page
12. Enter payment details (card number, expiry, CVV)
13. Click 'Confirm Payment' or 'Pay Now'
14. Verify payment processing
15. Verify navigation to order confirmation page
16. Verify order ID is displayed
17. Verify order details (plan, contract term, price)
18. Verify payment confirmation message
19. Verify order confirmation number
✅ GOAL ACHIEVED ✅
```

---

## Industry Best Practices

### 1. **Goal-Oriented Testing**
- **Principle:** Tests should verify goal achievement, not just step completion
- **Your System:** ✅ Enhanced with goal verification
- **Reference:** BDD (Behavior-Driven Development), Acceptance Testing

### 2. **State-Based Verification**
- **Principle:** Verify application state, not just actions
- **Your System:** ✅ State verification after each major step
- **Reference:** State Machine Testing, Model-Based Testing

### 3. **Dynamic Test Generation**
- **Principle:** Generate additional steps based on current state
- **Your System:** ✅ Dynamic step generation when goal not achieved
- **Reference:** Adaptive Testing, Self-Healing Tests

### 4. **Multi-Page Flow Handling**
- **Principle:** Handle flows that span multiple pages
- **Your System:** ✅ Multi-page flow detection and handling
- **Reference:** End-to-End Testing, User Journey Testing

### 5. **Completion Criteria**
- **Principle:** Define clear completion criteria for goals
- **Your System:** ✅ Goal completion criteria library
- **Reference:** Acceptance Criteria, Definition of Done

---

## Testing the Enhancement

### Test Case 1: Purchase Flow Completion

**Input:**
```
Goal: "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"
```

**Expected Output:**
- Steps include all pages (selection → registration → payment → confirmation)
- Final step verifies order confirmation
- Goal verification confirms purchase is complete

### Test Case 2: Registration Flow Completion

**Input:**
```
Goal: "Complete user registration"
```

**Expected Output:**
- Steps include registration form → email verification → welcome page
- Final step verifies user is logged in
- Goal verification confirms registration is complete

### Test Case 3: Checkout Flow Completion

**Input:**
```
Goal: "Complete checkout process"
```

**Expected Output:**
- Steps include cart → checkout → payment → confirmation
- Final step verifies order number
- Goal verification confirms checkout is complete

---

## Conclusion

**Problem:** System generates incomplete flows that stop before goal achievement.

**Solution:** Goal-aware test generation with:
1. ✅ Enhanced prompts with goal completion criteria
2. ✅ Execution-time goal verification
3. ✅ Dynamic step generation
4. ✅ Multi-page flow detection
5. ✅ State-based verification

**Result:** System generates complete flows that truly achieve the goal! 🎯

