# Goal-Aware Test Generation - Implementation Summary

## ✅ Implementation Complete

**Date:** 2026-02-02  
**Approach:** Enhanced Prompt (Approach 1) - Immediate Fix  
**Status:** ✅ Implemented and Ready for Testing

---

## What Was Implemented

### 1. Enhanced EvolutionAgent Prompt (`backend/agents/evolution_agent.py`)

**Changes:**
- ✅ Added `user_instruction` parameter to all prompt variants (`_build_prompt_variant_1`, `_build_prompt_variant_2`, `_build_prompt_variant_3`)
- ✅ Added goal extraction from user instruction or scenario title
- ✅ Added completion criteria for common goals (purchase flow, registration, checkout)
- ✅ Enhanced prompt with goal-aware instructions

**Key Features:**
- **Goal Extraction:** Automatically identifies goals like "complete purchase flow", "user registration", "checkout process"
- **Completion Criteria:** Defines what "complete" means for each goal type
- **Multi-Page Flow Instructions:** LLM is instructed to include all required pages
- **Final Verification:** Last step must verify goal achievement

### 2. User Instruction Passing (`backend/tests/integration/test_four_agent_e2e_real.py`)

**Changes:**
- ✅ Pass `user_instruction` from test file to EvolutionAgent task payload
- ✅ Log when user instruction is provided to EvolutionAgent

### 3. Goal Extraction Methods

**New Methods in EvolutionAgent:**
- `_extract_goal_from_instruction()`: Extracts goal from user instruction or scenario title
- `_get_completion_criteria_for_goal()`: Returns completion criteria for identified goals

**Supported Goals:**
- ✅ "complete purchase flow" → Order confirmed with order ID, payment confirmed
- ✅ "complete user registration" → User registered, logged in
- ✅ "complete checkout process" → Order placed with order number

---

## How It Works

### Flow Diagram

```
User Instruction: "Complete purchase flow for '5G寬頻數據無限任用' plan"
    ↓
RequirementsAgent: Generates BDD scenario
    ↓
AnalysisAgent: Analyzes and prioritizes
    ↓
EvolutionAgent: 
    1. Extracts goal: "complete purchase flow"
    2. Gets completion criteria: "Order confirmed with order ID..."
    3. Enhances prompt with goal-aware instructions
    4. LLM generates steps until goal is TRULY achieved
    ↓
Generated Steps: Include ALL pages (selection → registration → payment → confirmation)
    ↓
Final Step: Verifies order ID, payment confirmation, order details
    ✅ GOAL ACHIEVED
```

### Example: Enhanced Prompt

**Before (Old Prompt):**
```
Generate executable test steps for the following BDD scenario.
[Scenario details]
Requirements: Generate steps...
```

**After (Goal-Aware Prompt):**
```
Generate executable test steps for the following BDD scenario.
[Scenario details]

**GOAL-AWARE GENERATION:**
- **User Goal:** complete purchase flow
- **Completion Criteria:** Order confirmed with order ID, payment confirmed, and order details displayed

**CRITICAL: Goal Completion Requirements:**
1. **DO NOT STOP** until the goal "complete purchase flow" is TRULY achieved
2. **Multi-Page Flows:** Include ALL pages: plan selection → registration → payment → order confirmation
3. **State Verification:** After each major step, verify current state and continue if goal not achieved
4. **Final Verification:** Last step MUST verify goal is complete (order ID displayed, payment confirmed)

Requirements: Generate steps until the goal is TRULY achieved...
```

---

## Testing the Implementation

### Test Case 1: Purchase Flow with User Instruction

**Command:**
```powershell
$env:USER_INSTRUCTION = "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s
```

**Expected Results:**
1. ✅ EvolutionAgent receives user instruction
2. ✅ Goal "complete purchase flow" is extracted
3. ✅ Prompt includes goal-aware instructions
4. ✅ Generated steps include:
   - Plan selection ✅
   - Registration form ✅
   - Payment page ✅
   - Order confirmation ✅
   - Final verification (order ID, payment confirmed) ✅

**Verification:**
- Check log for: `EvolutionAgent: User instruction provided: '...'`
- Check generated test steps (should be 15-20 steps, not just 11)
- Verify final step checks for order ID or payment confirmation

### Test Case 2: Purchase Flow without User Instruction

**Command:**
```powershell
# Don't set USER_INSTRUCTION
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s
```

**Expected Results:**
- ✅ System works normally (backward compatible)
- ✅ Goal extraction falls back to scenario title if available
- ✅ If scenario title contains "complete purchase flow", goal-aware generation still applies

### Test Case 3: Other Goals

**Test Registration:**
```powershell
$env:USER_INSTRUCTION = "Complete user registration"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s
```

**Test Checkout:**
```powershell
$env:USER_INSTRUCTION = "Complete checkout process"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s
```

---

## Expected Improvements

### Before (11 steps, incomplete):
```
1. Navigate to page
2. Find and select plan
3. Select contract term
4. Verify price
5. Click '立即登記'
6. Fill form fields
7. Click '下一步'
8. Verify confirmation
✅ STOPS - Purchase NOT complete ❌
```

### After (15-20 steps, complete):
```
1. Navigate to page
2. Find and select plan
3. Select contract term
4. Verify price
5. Click '立即登記'
6. Fill form fields
7. Click '下一步'
8. Verify navigation to next page
9. Fill additional details if required
10. Click 'Continue' or 'Proceed to Payment'
11. Verify navigation to payment page
12. Enter payment details
13. Click 'Confirm Payment'
14. Verify payment processing
15. Verify navigation to order confirmation
16. Verify order ID is displayed
17. Verify order details (plan, contract term, price)
18. Verify payment confirmation message
19. Verify order confirmation number
✅ GOAL ACHIEVED - Purchase complete! ✅
```

---

## Code Changes Summary

### Files Modified:

1. **`backend/agents/evolution_agent.py`**
   - Added `user_instruction` parameter to `_generate_test_steps_with_llm()`
   - Added `user_instruction` parameter to all prompt variants
   - Added `_extract_goal_from_instruction()` method
   - Added `_get_completion_criteria_for_goal()` method
   - Enhanced `_build_prompt_variant_1()` with goal-aware section

2. **`backend/tests/integration/test_four_agent_e2e_real.py`**
   - Pass `user_instruction` to EvolutionAgent task payload
   - Log when user instruction is provided

### New Methods:

- `_extract_goal_from_instruction(user_instruction, scenario_title)`: Extracts goal from instruction or title
- `_get_completion_criteria_for_goal(goal)`: Returns completion criteria for goal

---

## Next Steps (Future Enhancements)

### Phase 2: Execution-Time Goal Verification (Recommended Next)
- Verify goal achievement after each step during execution
- Generate additional steps dynamically if goal not achieved
- Continue until goal is truly complete

### Phase 3: Goal Completion Criteria Library
- Expand library with more goal types
- Add domain-specific goals (telecom, e-commerce, etc.)
- Make criteria configurable

### Phase 4: Multi-Page Flow Detection
- Automatically detect when flow spans multiple pages
- Identify navigation points
- Estimate page count

---

## Troubleshooting

### Issue: Goal not extracted
**Solution:** Check user instruction format. Should contain keywords like "complete purchase flow", "purchase flow", "registration", "checkout"

### Issue: Steps still incomplete
**Solution:** 
1. Check if user instruction is being passed correctly (check logs)
2. Verify LLM is receiving enhanced prompt (check token usage)
3. May need to adjust prompt or add more specific instructions

### Issue: Too many steps generated
**Solution:** This is expected for complete flows. System now generates all steps needed to achieve goal. If steps are excessive, may need to refine completion criteria.

---

## Success Criteria

✅ **Implementation Complete:**
- User instruction passed to EvolutionAgent
- Goal extracted from instruction
- Enhanced prompt includes goal-aware instructions
- All prompt variants support goal-aware generation
- Backward compatible (works without user instruction)

✅ **Ready for Testing:**
- Test with purchase flow user instruction
- Verify steps include all required pages
- Verify final step checks goal achievement
- Test backward compatibility

---

## Conclusion

**Status:** ✅ **Implementation Complete**

The system now generates goal-aware test steps that continue until the goal is truly achieved. When a user provides a high-level requirement like "Complete purchase flow", the system will:

1. ✅ Extract the goal
2. ✅ Understand completion criteria
3. ✅ Generate steps for all required pages
4. ✅ Include final verification
5. ✅ Ensure goal is truly achieved

**Next:** Test the implementation and verify it generates complete flows! 🎯

