# ObservationAgent Quick Fix - Flow Crawling

**Date:** February 11, 2026  
**Priority:** HIGH  
**Issue:** ObservationAgent doesn't follow user flows (e.g., purchase process)

---

## 🚨 Immediate Issue

**Current Behavior:**
- ObservationAgent only crawls the starting URL
- Follows links randomly (first 10 links per page)
- Doesn't understand user instructions
- Can't navigate through multi-page flows (e.g., purchase process)

**User Requirement Example:**
```
"Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"
```

**Expected Flow:**
1. Product page → Find "5G寬頻數據無限任用" plan
2. Plan selection → Select "48個月" contract term
3. Configuration → Fill form, click "Continue"
4. Checkout → Complete purchase
5. Confirmation → Verify success

**Current Result:**
- Only 1 page crawled (product page)
- No navigation through flow steps
- Missing elements from checkout, confirmation pages

---

## 💡 Quick Fix Options

### Option 1: Pass User Instruction to ObservationAgent (Immediate - 1 day)

**Problem:** User instruction is passed to RequirementsAgent but NOT to ObservationAgent.

**Fix:**
```python
# In OrchestrationService or test:
observation_task = TaskContext(
    task_id=f"{workflow_id}-obs-1",
    task_type="web_crawling",
    payload={
        "url": request["url"],
        "max_depth": request.get("max_depth", 2),
        "user_instruction": request.get("user_instruction"),  # ADD THIS
        "auth": request.get("login_credentials")
    }
)
```

**Then in ObservationAgent.execute_task:**
```python
user_instruction = task.payload.get("user_instruction")
if user_instruction:
    # Use instruction to guide crawling
    logger.info(f"ObservationAgent: User instruction: {user_instruction}")
```

**Impact:** Low effort, enables future flow navigation work

---

### Option 2: Smart Link Filtering (Quick Win - 2-3 days)

**Enhance `_crawl_pages` to filter links by relevance:**

```python
async def _crawl_pages(
    self,
    page: Page,
    start_url: str,
    max_depth: int,
    user_instruction: Optional[str] = None  # ADD
) -> List[PageInfo]:
    # ... existing code ...
    
    # Extract links
    links = await page.eval_on_selector_all("a[href]", "...")
    
    # NEW: Filter links by user instruction relevance
    if user_instruction:
        relevant_links = self._filter_relevant_links(links, user_instruction)
    else:
        relevant_links = links[:10]  # Fallback to existing behavior
    
    # Add relevant links to visit queue
    for link in relevant_links:
        if link not in visited:
            to_visit.append((link, depth + 1))

def _filter_relevant_links(
    self,
    links: List[str],
    user_instruction: str
) -> List[str]:
    """
    Filter links relevant to user instruction using keyword matching.
    
    Example:
    Instruction: "purchase flow" → Prioritize links with "checkout", "cart", "buy"
    Instruction: "login" → Prioritize links with "login", "signin"
    """
    keywords = self._extract_keywords(user_instruction)
    relevant = []
    
    for link in links:
        link_lower = link.lower()
        # Check if link text or URL contains keywords
        if any(keyword in link_lower for keyword in keywords):
            relevant.append(link)
    
    return relevant[:10]  # Limit to 10 most relevant
```

**Impact:** Medium effort, improves link selection but still not flow-aware

---

### Option 3: LLM-Guided Flow Navigation (Full Solution - 14-19 days)

**See:** `OBSERVATION_AGENT_FLOW_CRAWLING_ANALYSIS.md` for complete solution

**Summary:**
- Use LLM to parse user instruction into flow steps
- Navigate step-by-step through flow
- Use LLM Vision to find next action element
- Execute actions (click, fill, submit)
- Extract elements from each step

**Impact:** High effort, full solution for flow-aware crawling

---

## 🎯 Recommended Approach

### Phase 1: Quick Fixes (This Week)
1. ✅ **Option 1:** Pass user instruction to ObservationAgent (1 day)
2. ✅ **Option 2:** Smart link filtering (2-3 days)

### Phase 2: Full Solution (Next Sprint)
3. ✅ **Option 3:** LLM-guided flow navigation (14-19 days)

---

## 📝 Implementation Checklist

### Immediate (Option 1):
- [ ] Update `ObservationAgent.execute_task` to accept `user_instruction`
- [ ] Update test to pass `user_instruction` to ObservationAgent
- [ ] Log user instruction in ObservationAgent
- [ ] Test with purchase flow example

### Short-term (Option 2):
- [ ] Add `_filter_relevant_links` method
- [ ] Add `_extract_keywords` method
- [ ] Update `_crawl_pages` to use filtered links
- [ ] Test with various user instructions

### Long-term (Option 3):
- [ ] Implement flow parser
- [ ] Implement intelligent navigation
- [ ] Implement LLM action finder
- [ ] Comprehensive testing

---

## 🔍 Testing

**Test Case:**
```python
task = TaskContext(
    task_id="test-flow",
    task_type="web_crawling",
    payload={
        "url": "https://web.three.com.hk/5gbroadband/plan-monthly.html",
        "user_instruction": "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term",
        "max_depth": 3
    }
)

result = await observation_agent.execute_task(task)

# Verify:
assert result.result["pages_crawled"] >= 3  # Should crawl multiple pages
assert any("checkout" in p["url"] for p in result.result["pages"])  # Should reach checkout
assert any("confirmation" in p["url"] for p in result.result["pages"])  # Should reach confirmation
```

---

## 📚 References

- **Full Analysis:** `OBSERVATION_AGENT_FLOW_CRAWLING_ANALYSIS.md`
- **Current Code:** `backend/agents/observation_agent.py` (Line 230-531)
- **Test Log:** `backend/logs/test_four_agent_e2e_20260210_150734.log`

---

**Status:** ✅ **QUICK FIX OPTIONS IDENTIFIED**  
**Next Action:** Implement Option 1 (pass user instruction) - 1 day effort

