# ObservationAgent Flow Crawling Analysis & Solution

**Date:** February 11, 2026  
**Issue:** ObservationAgent only crawls the targeted URL but doesn't follow user flows (e.g., purchase process)  
**Requirement Example:** "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"

---

## 🔍 Current Problem Analysis

### Current Behavior

From code analysis (`backend/agents/observation_agent.py`):

1. **`_crawl_pages` Method (Line 457-531):**
   - Crawls pages based on `max_depth` parameter
   - Follows links **randomly** (first 10 links per page, line 522)
   - No understanding of user instructions or business flows
   - No intelligent navigation based on flow requirements

2. **Test Log Evidence (`test_four_agent_e2e_20260210_150734.log`):**
   ```
   Line 67: max_depth=1
   Line 68: Crawled: https://web.three.com.hk/5gbroadband/plan-monthly.html (depth 0, 38 links)
   Line 69: ObservationAgent: Found 1 page(s) to analyze
   ```
   - Only 1 page crawled despite user instruction requiring multi-page flow
   - User instruction: "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"
   - This requires: Product page → Plan selection → Configuration → Checkout → Confirmation

3. **Missing Capabilities:**
   - ❌ No user instruction parsing
   - ❌ No flow understanding (purchase, login, registration, etc.)
   - ❌ No intelligent link selection (follows random links)
   - ❌ No state management across pages
   - ❌ No form interaction to progress through flows

---

## 🏭 Industrial Best Practices

### 1. **LLM-Guided Navigation** (Industry Standard)

**Examples:**
- **BrowserGPT / AutoGPT:** Use LLM to understand user intent and navigate accordingly
- **LangChain Browser Tools:** LLM decides which links/buttons to click based on goal
- **Playwright Codegen with AI:** AI understands flow requirements and generates navigation steps

**Best Practice:**
```python
# LLM analyzes user instruction and determines flow steps
user_instruction = "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"

# LLM identifies flow:
flow_steps = [
    "1. Find and click on '5G寬頻數據無限任用' plan",
    "2. Select contract term '48個月'",
    "3. Click 'Continue' or 'Add to Cart'",
    "4. Navigate to checkout page",
    "5. Complete purchase form",
    "6. Verify confirmation page"
]
```

### 2. **Intent-Based Link Selection** (Not Random)

**Current (Bad):**
```python
# Line 522: Random link selection
for link in filtered_links[:10]:  # Just takes first 10 links
    if link not in visited:
        to_visit.append((link, depth + 1))
```

**Best Practice:**
```python
# Intelligent link selection based on user intent
relevant_links = await llm.select_relevant_links(
    links=filtered_links,
    user_instruction=user_instruction,
    current_page_context=page_content
)
```

### 3. **Flow-Aware Crawling** (Stateful Navigation)

**Best Practice:**
- Maintain **session state** across pages
- Track **flow progress** (which step are we on?)
- **Form interaction** to progress (not just link following)
- **Button clicks** to advance flow (e.g., "Add to Cart", "Continue")

**Example Flow State:**
```python
flow_state = {
    "current_step": "plan_selection",
    "completed_steps": ["landing_page"],
    "target_plan": "5G寬頻數據無限任用",
    "target_term": "48個月",
    "next_action": "click_plan_button"
}
```

### 4. **Multi-Modal Understanding** (Text + Visual)

**Best Practice:**
- **Text Analysis:** Page content, button labels, form fields
- **Visual Analysis:** Screenshots to understand page structure
- **LLM Vision:** Use GPT-4 Vision or similar to understand page context

**Example:**
```python
# Analyze page with LLM Vision
page_analysis = await llm.analyze_page(
    screenshot=page_screenshot,
    html=page_html,
    user_instruction=user_instruction,
    current_step=flow_state["current_step"]
)

# LLM returns: "Found '5G寬頻數據無限任用' plan button. Click it to proceed."
```

### 5. **Progressive Flow Execution** (Step-by-Step)

**Best Practice:**
- Don't crawl all pages upfront
- **Execute flow step-by-step** based on user instruction
- **Extract elements** from each page as you progress
- **Verify progress** at each step (did we reach the right page?)

**Example:**
```python
# Step 1: Navigate to product page
await page.goto(start_url)
elements_step1 = await extract_elements(page)

# Step 2: Find and click target plan (based on user instruction)
plan_button = await find_element_by_text(page, "5G寬頻數據無限任用")
await plan_button.click()
await page.wait_for_navigation()
elements_step2 = await extract_elements(page)

# Step 3: Select contract term
term_select = await find_element_by_text(page, "48個月")
await term_select.click()
elements_step3 = await extract_elements(page)

# Continue until flow complete...
```

---

## 💡 Recommended Solution Architecture

### Solution 1: LLM-Guided Flow Navigation (Recommended)

**Architecture:**
```
User Instruction → LLM Flow Parser → Flow Steps → Intelligent Navigation → Element Extraction
```

**Implementation:**

1. **Flow Parser (New Method):**
   ```python
   async def _parse_user_flow(
       self,
       user_instruction: str,
       start_url: str
   ) -> List[FlowStep]:
       """
       Use LLM to parse user instruction into flow steps.
       
       Example:
       Input: "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"
       Output: [
           FlowStep(step=1, action="find_plan", target="5G寬頻數據無限任用", page_type="product"),
           FlowStep(step=2, action="select_term", target="48個月", page_type="configuration"),
           FlowStep(step=3, action="proceed_to_checkout", page_type="checkout"),
           FlowStep(step=4, action="complete_purchase", page_type="confirmation")
       ]
       """
   ```

2. **Intelligent Navigation (Enhanced `_crawl_pages`):**
   ```python
   async def _crawl_flow(
       self,
       page: Page,
       start_url: str,
       flow_steps: List[FlowStep],
       user_instruction: str
   ) -> List[PageInfo]:
       """
       Navigate through flow steps intelligently.
       """
       pages = []
       current_url = start_url
       
       for step in flow_steps:
           # Navigate to current step
           await page.goto(current_url)
           
           # Use LLM to find next action element
           next_action = await self._llm_find_next_action(
               page=page,
               step=step,
               user_instruction=user_instruction
           )
           
           # Execute action (click button, fill form, etc.)
           await self._execute_action(page, next_action)
           
           # Wait for navigation
           await page.wait_for_navigation()
           current_url = page.url
           
           # Extract elements from this step
           page_info = await self._extract_page_info(page, current_url)
           pages.append(page_info)
       
       return pages
   ```

3. **LLM Action Finder:**
   ```python
   async def _llm_find_next_action(
       self,
       page: Page,
       step: FlowStep,
       user_instruction: str
   ) -> Dict[str, Any]:
       """
       Use LLM to find the element to interact with for this step.
       
       Returns: {
           "type": "button",
           "selector": "#plan-5g-unlimited",
           "action": "click",
           "text": "5G寬頻數據無限任用"
       }
       """
       html = await page.content()
       screenshot = await page.screenshot()
       
       prompt = f"""
       User wants to: {user_instruction}
       Current step: {step.action} - {step.target}
       
       Find the element on this page that matches the step requirement.
       Return JSON with selector and action.
       """
       
       result = await self.llm_client.analyze_and_find_element(
           html=html,
           screenshot=screenshot,
           prompt=prompt
       )
       
       return result
   ```

### Solution 2: Hybrid Approach (Fallback)

**If LLM is unavailable or too slow:**

1. **Pattern-Based Flow Detection:**
   - Use keyword matching for common flows (purchase, login, registration)
   - Pre-defined flow templates

2. **Smart Link Filtering:**
   - Filter links by relevance to user instruction
   - Use text matching (e.g., links containing "checkout", "cart", "purchase")

3. **Form Interaction:**
   - Detect forms on page
   - Fill forms based on user instruction
   - Submit to progress flow

---

## 🛠️ Implementation Plan

### Phase 1: Add User Instruction Support (2-3 days)

**Changes to `ObservationAgent.execute_task`:**
```python
async def execute_task(self, task: TaskContext) -> TaskResult:
    url = task.payload.get("url")
    user_instruction = task.payload.get("user_instruction")  # NEW
    max_depth = task.payload.get("max_depth", self.max_depth)
    
    # NEW: Parse flow if user instruction provided
    if user_instruction:
        flow_steps = await self._parse_user_flow(user_instruction, url)
        pages = await self._crawl_flow(page, url, flow_steps, user_instruction)
    else:
        # Fallback to existing random crawling
        pages = await self._crawl_pages(page, url, max_depth)
```

### Phase 2: Implement Flow Parser (3-4 days)

**New Method: `_parse_user_flow`**
- Use LLM to parse user instruction
- Identify flow type (purchase, login, registration, etc.)
- Generate flow steps
- Return structured flow steps

### Phase 3: Implement Intelligent Navigation (4-5 days)

**Enhanced Method: `_crawl_flow`**
- Navigate step-by-step through flow
- Use LLM to find next action element
- Execute actions (click, fill, submit)
- Extract elements from each step
- Track flow progress

### Phase 4: Add LLM Action Finder (3-4 days)

**New Method: `_llm_find_next_action`**
- Analyze page HTML + screenshot
- Use LLM Vision to understand page context
- Find element matching flow step requirement
- Return selector and action

### Phase 5: Testing & Refinement (2-3 days)

- Test with real purchase flows
- Test with login flows
- Test with registration flows
- Handle edge cases (modals, dynamic content, etc.)

**Total Estimated Time:** 14-19 days

---

## 📊 Comparison: Current vs. Recommended

| Aspect | Current | Recommended |
|--------|---------|-------------|
| **Navigation** | Random link following | LLM-guided flow navigation |
| **User Instruction** | Ignored | Parsed and used for navigation |
| **Flow Understanding** | None | Flow steps identified and executed |
| **Element Selection** | All links | Relevant elements only |
| **State Management** | None | Flow state tracked |
| **Form Interaction** | None | Forms filled and submitted |
| **Multi-Page Flows** | ❌ Not supported | ✅ Fully supported |

---

## 🎯 Success Criteria

### For Purchase Flow Example:

**Input:**
```
URL: https://web.three.com.hk/5gbroadband/plan-monthly.html
User Instruction: "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"
```

**Expected Output:**
```python
{
    "pages_crawled": 4,  # Product → Plan Selection → Configuration → Checkout
    "flow_completed": True,
    "pages": [
        {
            "url": "https://web.three.com.hk/5gbroadband/plan-monthly.html",
            "step": "product_selection",
            "elements": [...]
        },
        {
            "url": "https://web.three.com.hk/5gbroadband/configure",
            "step": "plan_configuration",
            "elements": [...]
        },
        {
            "url": "https://web.three.com.hk/checkout",
            "step": "checkout",
            "elements": [...]
        },
        {
            "url": "https://web.three.com.hk/confirmation",
            "step": "confirmation",
            "elements": [...]
        }
    ],
    "flow_steps_completed": [
        "Found '5G寬頻數據無限任用' plan",
        "Selected '48個月' contract term",
        "Proceeded to checkout",
        "Reached confirmation page"
    ]
}
```

---

## 🔗 References

### Industrial Examples:
1. **BrowserGPT:** LLM-guided browser automation
2. **LangChain Browser Tools:** Intelligent web navigation
3. **Playwright Codegen:** AI-powered test generation
4. **AutoGPT:** Goal-oriented web navigation

### Technical Patterns:
1. **State Machine Pattern:** For flow state management
2. **Strategy Pattern:** For different flow types (purchase, login, etc.)
3. **LLM Function Calling:** For structured action selection
4. **Vision Models:** For page understanding (GPT-4 Vision, Claude Vision)

---

## ✅ Next Steps

1. **Review this analysis** with team
2. **Decide on approach:** LLM-guided (recommended) vs. Hybrid
3. **Create detailed implementation plan** for selected approach
4. **Implement Phase 1** (User Instruction Support)
5. **Test with real purchase flow** example
6. **Iterate and refine** based on results

---

**Status:** ✅ **ANALYSIS COMPLETE**  
**Recommendation:** Implement LLM-Guided Flow Navigation (Solution 1)  
**Estimated Effort:** 14-19 days  
**Priority:** HIGH (Blocks multi-page flow testing)

