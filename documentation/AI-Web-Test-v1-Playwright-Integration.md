# AI-Web-Test v1 - Playwright Test Agents Integration

## Document Information
- **Version**: 1.0
- **Last Updated**: 2025-01-31
- **Status**: Architecture Specification
- **Related Documents**: 
  - [PRD](../AI-Web-Test-v1-PRD.md)
  - [SRS](../AI-Web-Test-v1-SRS.md)
  - [Playwright Test Agents](https://playwright.dev/docs/test-agents)

---

## Executive Summary

This document defines the integration of **Playwright Test Agents** capabilities into the AI-Web-Test v1 platform, enhancing the existing 6-agent architecture with production-ready Playwright-specific expertise for test planning, generation, and self-healing.

### Key Integration Capabilities

| Component | Technology | Purpose | Impact |
|-----------|-----------|---------|--------|
| **Markdown Test Specifications** | Playwright Planner Pattern | Human-readable test plans in `specs/` | +100% traceability |
| **Seed Test Pattern** | Playwright Convention | Environment setup for all tests | -50% code duplication |
| **Healer-Enhanced Self-Healing** | Playwright Healer Logic | Replay → Inspect → Patch workflow | 95% → 98%+ success rate |
| **Web-Based Interactive Planning** | Planner Pattern (Web UI) | Live app exploration via dashboard | +40% planning accuracy |
| **Playwright Generation Optimization** | Generator Best Practices | Optimized Playwright test patterns | +30% test quality |

### Why Playwright Test Agents?

**Playwright Test Agents** is Microsoft's **production-ready, officially supported** system of three specialized agents (Planner, Generator, Healer) designed specifically for Playwright test automation. Released in 2025, it represents industry best practices for AI-powered testing.

**Key Advantages:**
- ✅ **Battle-tested**: Used by enterprise teams in production
- ✅ **Playwright-optimized**: Built by the Playwright team at Microsoft
- ✅ **Non-intrusive**: Complements our architecture, doesn't replace it
- ✅ **Free**: No additional licensing costs
- ✅ **Well-documented**: Comprehensive docs and examples

### Integration Timeline
- **Total Effort**: 13 days
- **Phase 1** (Days 1-3): Markdown specs + Seed test pattern
- **Phase 2** (Days 4-8): Healer-enhanced self-healing (high priority)
- **Phase 3** (Days 9-13): Web-based interactive planning + optimization

---

## Table of Contents
1. [Architecture Integration Overview](#architecture-integration-overview)
2. [Markdown Test Specifications](#markdown-test-specifications)
3. [Seed Test Pattern](#seed-test-pattern)
4. [Healer-Enhanced Self-Healing](#healer-enhanced-self-healing)
5. [Web-Based Interactive Planning](#web-based-interactive-planning)
6. [Playwright Generation Optimization](#playwright-generation-optimization)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Summary & Integration](#summary--integration)

---

## Architecture Integration Overview

### Hybrid Agent Architecture

We integrate Playwright agent **patterns and logic** into our existing 6-agent system as **sub-capabilities**, not as replacement agents:

```
BEFORE (Current 6-Agent System):
┌─────────────────────────────────────────────────────────┐
│ Requirements Agent → Generation Agent → Execution Agent │
│        ↓                    ↓                 ↓          │
│   Observation Agent ← → Analysis Agent ← → Evolution    │
└─────────────────────────────────────────────────────────┘

AFTER (Enhanced with Playwright Patterns):
┌──────────────────────────────────────────────────────────────┐
│ Requirements Agent (ENHANCED)                                │
│   ├─ PRD/User Story Analysis (existing)                     │
│   └─ 🎭 Planner Logic (NEW)                                 │
│       • Live app exploration via web dashboard              │
│       • Markdown spec generation in specs/                  │
│       • Seed test identification                            │
│                                                              │
│ Generation Agent (ENHANCED)                                  │
│   ├─ Multi-framework generation (existing)                  │
│   └─ 🎭 Playwright Generator Optimization (NEW)             │
│       • Playwright-specific best practices                  │
│       • Live selector verification during generation        │
│       • Assertion catalog integration                       │
│       • Generation hints for better locators                │
│                                                              │
│ Execution Agent (ENHANCED)                                   │
│   └─ Seed test execution pattern (NEW)                      │
│                                                              │
│ Observation Agent (existing - no changes)                   │
│                                                              │
│ Analysis Agent (existing - no changes)                      │
│                                                              │
│ Evolution Agent (ENHANCED) 🔥                                │
│   ├─ RL-based continuous learning (existing)               │
│   └─ 🎭 Healer Logic (NEW - HIGH PRIORITY)                  │
│       • Replay failing tests to understand breakage         │
│       • Inspect current UI for alternative selectors        │
│       • Generate patches (locator/wait/data fixes)          │
│       • Re-run test until pass or guardrail limit           │
│       • Target: 98%+ self-healing (up from 95%)             │
└──────────────────────────────────────────────────────────────┘
```

### Integration Principles

1. **Non-Intrusive**: Playwright patterns enhance, don't replace existing agents
2. **Best of Both Worlds**: Our orchestration + Playwright's Playwright expertise
3. **Gradual Adoption**: Add capabilities incrementally
4. **Standalone Tool**: All integrated via web dashboard, no IDE dependency
5. **Production-Ready**: Leverage Microsoft's battle-tested patterns

---

## Markdown Test Specifications

### Overview

Adopt Playwright's **Markdown specification format** as an intermediate layer between requirements and executable tests.

### Current Workflow Problem

```
❌ BEFORE:
PRD/Requirements → Requirements Agent → JSON Scenarios → Generation Agent → Tests

Problems:
- JSON scenarios not human-readable
- No easy review by QA team or stakeholders
- Difficult to version control (binary-like JSON diffs)
- No clear separation between planning and execution
- Hard to maintain documentation-to-test traceability
```

### Enhanced Workflow with Markdown Specs

```
✅ AFTER:
PRD/Requirements → Requirements Agent → specs/*.md → Generation Agent → tests/*.spec.ts
                                            ↓
                                  (Human-readable, Git-friendly, Reviewable)
```

### Markdown Spec Format

```markdown
# Three HK Customer Login - Test Plan

**Last Updated**: 2025-01-31
**Owner**: QA Team
**Related PRD**: PRD-2025-001

---

## Application Overview

The Three Hong Kong customer portal provides secure login functionality for
postpaid and prepaid customers. Key features include:
- Multi-language support (English, Traditional Chinese)
- Multi-factor authentication (SMS OTP)
- Account lockout after 3 failed attempts
- Session timeout after 15 minutes of inactivity

**Test Environment**: https://www.three.com.hk/login
**Target Browsers**: Chrome 120+, Edge 120+, Firefox 121+

---

## Test Scenarios

### 1. Happy Path Login

**Seed**: `tests/three-hk/seed.spec.ts`
**Priority**: High
**Estimated Duration**: 2 minutes

#### 1.1 Valid Credentials Login

**Steps:**
1. Navigate to https://www.three.com.hk/login
2. Click on "Postpaid Login" tab
3. Enter valid phone number: `+852 9123 4567`
4. Enter valid password: `Test@1234`
5. Click "Login" button
6. Enter OTP from SMS (simulated in test)
7. Click "Verify" button

**Expected Results:**
- Dashboard loads within 3 seconds
- URL changes to `/dashboard`
- User name "John Doe" displayed in header
- Account balance visible (format: HK$ XX,XXX.XX)
- "Welcome back" notification appears
- Session cookie `three_session` is set with 15-min expiry

**Edge Cases:**
- Browser auto-fill credentials
- Password visible toggle works correctly
- "Remember me" checkbox persists username

#### 1.2 Remember Me Functionality

**Steps:**
1. Follow steps 1-4 from 1.1
2. Check "Remember me" checkbox
3. Complete login (steps 5-7 from 1.1)
4. Close browser
5. Reopen browser and navigate to login page

**Expected Results:**
- Username field pre-filled with `+852 9123 4567`
- Password field empty (security best practice)
- Checkbox "Remember me" remains checked

---

### 2. Error Handling

**Seed**: `tests/three-hk/seed.spec.ts`
**Priority**: High

#### 2.1 Invalid Password

**Steps:**
1. Navigate to login page
2. Enter valid phone number: `+852 9123 4567`
3. Enter invalid password: `WrongPass123`
4. Click "Login" button

**Expected Results:**
- Error message displayed: "Invalid phone number or password"
- Error message color: Red (#DC3545)
- Input fields retain values
- Login button remains enabled (allow retry)
- No navigation occurs (stay on login page)
- Alert icon visible next to error message

#### 2.2 Account Lockout After 3 Failed Attempts

**Steps:**
1. Attempt invalid login 3 times (repeat 2.1 three times)
2. On 4th attempt, enter valid credentials

**Expected Results:**
- After 3rd failed attempt: "Account temporarily locked. Try again in 30 minutes."
- Account locked in database: `locked_until` timestamp set
- 4th attempt with valid credentials: Still shows lockout message
- After 30 minutes: Login succeeds with valid credentials

---

### 3. Security Tests

**Seed**: `tests/three-hk/seed.spec.ts`
**Priority**: Medium

#### 3.1 SQL Injection Prevention

**Steps:**
1. Enter in phone number field: `' OR '1'='1' --`
2. Enter in password field: `' OR '1'='1' --`
3. Click "Login" button

**Expected Results:**
- Login fails with "Invalid phone number or password"
- No SQL error exposed to user
- Input sanitized in backend logs
- WAF blocks request (if ModSecurity enabled)

#### 3.2 XSS Prevention

**Steps:**
1. Enter in username field: `<script>alert('XSS')</script>`
2. Attempt login

**Expected Results:**
- Script tag rendered as text (HTML-escaped)
- No JavaScript execution
- Input sanitized: `&lt;script&gt;alert('XSS')&lt;/script&gt;`

---

## Data Requirements

**Test Users:**
- Valid user: `+852 9123 4567` / `Test@1234`
- Locked user: `+852 9123 4568` / `Test@1234` (pre-locked in test DB)
- Invalid user: `+852 9999 9999` / `invalid`

**Test Database:**
- PostgreSQL `three_hk_test` database
- Pre-populated with 100 test customers
- Reset via `npm run test:db:reset` before each test run

**External Dependencies:**
- SMS OTP service: Mocked in test environment
- Payment gateway: Stubbed (no real transactions)

---

## Success Criteria

- All test cases pass on Chrome, Edge, Firefox
- No console errors during test execution
- Page load time < 3 seconds (95th percentile)
- No accessibility violations (WCAG 2.1 AA)

---

## Notes

- This spec generated by Requirements Agent on 2025-01-31
- Based on PRD-2025-001 "Customer Login Improvements"
- Reviewed by QA Lead: Jane Smith
- Approved for implementation: 2025-01-31
```

### Benefits of Markdown Specs

1. **Human-Readable** ✅
   - QA team can review specs before test generation
   - Stakeholders understand test coverage without technical knowledge
   - Easy to share with product managers and business users

2. **Version-Controlled** ✅
   - Git-friendly Markdown format
   - Meaningful diffs in PRs (not binary JSON)
   - Clear history of test plan evolution

3. **Traceability** ✅
   - Direct link from requirement → spec → test code
   - Comments in generated tests reference spec: `// spec: specs/customer-login.md`
   - Audit trail for compliance

4. **Collaborative** ✅
   - Non-developers can contribute to test planning
   - Comments and discussions in PR reviews
   - Easier onboarding for new team members

5. **Maintainable** ✅
   - Update spec → regenerate tests
   - Clear documentation of expected behavior
   - Reduces "why does this test exist?" questions

### Directory Structure

```
repo/
  specs/                          # Human-readable test plans
    three-hk/
      customer-login.md           # Login flow specs
      billing-payment.md          # Billing specs
      service-activation.md       # Service activation specs
    internal-crm/
      lead-management.md          # CRM lead specs
      customer-search.md          # Search specs
  tests/                          # Generated Playwright tests
    three-hk/
      seed.spec.ts                # Environment setup
      customer-login/
        valid-credentials.spec.ts
        invalid-password.spec.ts
        account-lockout.spec.ts
      billing-payment/
        ...
    internal-crm/
      seed.spec.ts
      lead-management/
        ...
  playwright.config.ts
```

### Requirements Agent Enhancement

**New Output Format:**

```typescript
// app/agents/requirements_agent.py

class RequirementsAgent(BaseAgent):
    async def process(self, input_data: Dict) -> Dict:
        """
        Analyze requirements and generate Markdown test specifications.
        
        Enhanced to output Markdown specs in specs/ directory.
        """
        # Existing PRD analysis logic...
        scenarios = await self._analyze_requirements(input_data)
        
        # NEW: Generate Markdown spec
        spec_path = await self._generate_markdown_spec(
            scenarios=scenarios,
            project=input_data["project"],
            prd_reference=input_data.get("prd_id"),
        )
        
        return {
            "scenarios": scenarios,
            "spec_path": spec_path,  # NEW: Path to generated Markdown spec
            "confidence": self._calculate_confidence(scenarios),
        }
    
    async def _generate_markdown_spec(
        self, 
        scenarios: List[Dict], 
        project: str,
        prd_reference: str
    ) -> str:
        """Generate Playwright-style Markdown test specification."""
        
        # Use LLM to structure scenarios into Markdown format
        prompt = f"""
        Convert these test scenarios into a Playwright-style Markdown specification.
        
        Scenarios: {json.dumps(scenarios, indent=2)}
        Project: {project}
        PRD Reference: {prd_reference}
        
        Format according to Playwright Test Agents specification standard:
        - Clear Application Overview section
        - Test Scenarios with numbered subsections
        - Steps and Expected Results for each scenario
        - Data Requirements section
        - Success Criteria section
        
        Include seed test references where appropriate.
        """
        
        markdown_content = await self.llm.generate(prompt)
        
        # Save to specs/ directory
        spec_filename = f"{project.lower().replace(' ', '-')}.md"
        spec_path = f"specs/{spec_filename}"
        
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Generated Markdown spec: {spec_path}")
        
        return spec_path
```

### Generation Agent Enhancement

**New Input Format:**

```typescript
// app/agents/generation_agent.py

class GenerationAgent(BaseAgent):
    async def process(self, input_data: Dict) -> Dict:
        """
        Generate executable tests from Markdown specifications.
        
        Enhanced to read from Markdown specs instead of JSON.
        """
        spec_path = input_data.get("spec_path")
        
        if spec_path:
            # NEW: Parse Markdown spec
            test_scenarios = await self._parse_markdown_spec(spec_path)
        else:
            # Fallback: Legacy JSON scenarios
            test_scenarios = input_data["scenarios"]
        
        # Generate Playwright tests
        tests = await self._generate_playwright_tests(test_scenarios)
        
        # Add spec reference to generated tests
        for test in tests:
            test["spec_reference"] = spec_path  # NEW: Traceability
        
        return {
            "tests": tests,
            "spec_path": spec_path,
        }
    
    async def _parse_markdown_spec(self, spec_path: str) -> List[Dict]:
        """Parse Playwright Markdown spec into structured test scenarios."""
        
        with open(spec_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Use LLM to extract structured scenarios from Markdown
        prompt = f"""
        Parse this Playwright test specification and extract structured test scenarios.
        
        Markdown Spec:
        {markdown_content}
        
        Output JSON format:
        {{
          "application_overview": "...",
          "scenarios": [
            {{
              "id": "1.1",
              "title": "Valid Credentials Login",
              "seed_test": "tests/three-hk/seed.spec.ts",
              "priority": "high",
              "steps": ["...", "..."],
              "expected_results": ["...", "..."],
              "edge_cases": ["..."]
            }}
          ],
          "data_requirements": {{}},
          "success_criteria": ["..."]
        }}
        """
        
        structured_data = await self.llm.generate(prompt, output_format="json")
        
        return structured_data["scenarios"]
```

---

## Seed Test Pattern

### Overview

Implement Playwright's **seed test pattern** to eliminate repetitive environment setup code across all tests.

### Current Problem

```typescript
// ❌ BEFORE: Every test repeats setup code

// tests/customer-login.spec.ts
test('valid login', async ({ page }) => {
  // Repetitive setup
  await page.goto('https://www.three.com.hk');
  await page.getByRole('button', { name: 'Accept Cookies' }).click();
  await page.getByRole('button', { name: 'Login' }).click();
  
  // Actual test
  await page.fill('[name="phone"]', '+852 9123 4567');
  // ...
});

// tests/billing.spec.ts
test('view bill', async ({ page }) => {
  // Same repetitive setup!
  await page.goto('https://www.three.com.hk');
  await page.getByRole('button', { name: 'Accept Cookies' }).click();
  await page.getByRole('button', { name: 'Login' }).click();
  
  // Actual test
  await page.getByRole('link', { name: 'Billing' }).click();
  // ...
});
```

**Problems:**
- ❌ 50-100 lines of duplicated setup code across 100+ tests
- ❌ Changes to setup require updating every test
- ❌ Slower test execution (repeat navigation/auth every time)
- ❌ Harder to maintain

### Enhanced with Seed Test Pattern

```typescript
// ✅ AFTER: One seed test, referenced everywhere

// tests/three-hk/seed.spec.ts
import { test, expect } from './fixtures';

test('seed', async ({ page, context }) => {
  /**
   * Seed test for Three HK customer portal tests.
   * 
   * This test sets up the environment for all Three HK tests:
   * 1. Navigates to the portal
   * 2. Handles cookie consent
   * 3. Performs authentication
   * 4. Verifies dashboard loaded
   * 
   * All other tests in tests/three-hk/ build on this setup.
   */
  
  // Navigate and handle cookies
  await page.goto('https://www.three.com.hk');
  await page.getByRole('button', { name: 'Accept Cookies' }).click();
  
  // Authenticate
  await page.getByRole('button', { name: 'Login' }).click();
  await page.fill('[name="phone"]', '+852 9123 4567');
  await page.fill('[name="password"]', process.env.TEST_PASSWORD);
  await page.getByRole('button', { name: 'Submit' }).click();
  
  // Verify authenticated state
  await expect(page).toHaveURL(/.*dashboard/);
  await expect(page.getByText('Welcome back')).toBeVisible();
  
  // Save authenticated state for other tests
  await context.storageState({ path: 'tests/three-hk/.auth/user.json' });
});

// tests/three-hk/customer-login/valid-credentials.spec.ts
/**
 * Customer Login Tests
 * 
 * Seed: tests/three-hk/seed.spec.ts
 * Spec: specs/three-hk/customer-login.md
 */

test.use({ storageState: 'tests/three-hk/.auth/user.json' });

test('valid credentials login', async ({ page }) => {
  // No setup needed - seed test already did it!
  
  // Directly test the scenario
  await page.getByRole('link', { name: 'Account' }).click();
  await expect(page.getByText('Account Details')).toBeVisible();
  
  // Test steps...
});

test('invalid password error', async ({ page }) => {
  // No setup needed!
  
  // Logout first (since seed authenticated us)
  await page.getByRole('button', { name: 'Logout' }).click();
  
  // Test invalid login
  await page.fill('[name="phone"]', '+852 9123 4567');
  await page.fill('[name="password"]', 'WrongPassword123');
  await page.getByRole('button', { name: 'Submit' }).click();
  
  // Verify error
  await expect(page.getByText('Invalid phone number or password')).toBeVisible();
});
```

### Benefits

1. **Massive Code Reduction** ✅
   - Eliminate 50-100 lines of duplicated setup per test
   - 100 tests × 50 lines = 5,000 lines saved!
   - Faster to write new tests

2. **Easier Maintenance** ✅
   - Change setup once in seed test
   - All tests inherit the change automatically
   - No risk of inconsistent setup

3. **Faster Execution** ✅
   - Reuse authenticated state via `storageState`
   - Skip navigation/auth for most tests
   - 30-50% faster test suite execution

4. **Better Test Focus** ✅
   - Tests focus on what they're actually testing
   - Less boilerplate, more clarity
   - Easier to understand test intent

### Seed Test Implementation

```typescript
// app/agents/execution_agent.py

class ExecutionAgent(BaseAgent):
    async def execute(self, tests: List[Dict]) -> Dict:
        """
        Execute tests with seed test pattern support.
        
        Enhanced to run seed tests before dependent tests.
        """
        # NEW: Identify seed tests
        seed_tests = [t for t in tests if t.get("is_seed_test")]
        regular_tests = [t for t in tests if not t.get("is_seed_test")]
        
        results = []
        
        # Step 1: Run seed tests first
        for seed_test in seed_tests:
            logger.info(f"Running seed test: {seed_test['name']}")
            seed_result = await self._execute_single_test(seed_test)
            results.append(seed_result)
            
            if seed_result["status"] == "fail":
                logger.error(f"Seed test failed: {seed_test['name']}")
                # Don't run dependent tests if seed failed
                project = seed_test.get("project")
                dependent_tests = [t for t in regular_tests if t.get("project") == project]
                
                for test in dependent_tests:
                    results.append({
                        "test_id": test["id"],
                        "status": "skip",
                        "reason": f"Seed test {seed_test['name']} failed",
                    })
                
                # Remove dependent tests from regular_tests
                regular_tests = [t for t in regular_tests if t not in dependent_tests]
        
        # Step 2: Run regular tests (can use seed test state)
        for test in regular_tests:
            result = await self._execute_single_test(test)
            results.append(result)
        
        return {
            "total_tests": len(tests),
            "results": results,
            "seed_tests_run": len(seed_tests),
        }
```

### Seed Test Directory Structure

```
tests/
  three-hk/
    seed.spec.ts              # Main seed test
    .auth/
      user.json               # Authenticated state (gitignored)
    fixtures.ts               # Custom fixtures
    customer-login/
      valid-credentials.spec.ts
      invalid-password.spec.ts
    billing/
      view-bill.spec.ts
      pay-bill.spec.ts
  
  internal-crm/
    seed.spec.ts              # Different seed for internal CRM
    .auth/
      admin.json              # Admin user state
    fixtures.ts
    lead-management/
      create-lead.spec.ts
```

---

## Healer-Enhanced Self-Healing

### Overview 🔥 **HIGH PRIORITY**

Integrate Playwright Healer's **replay → inspect → patch** workflow into the Evolution Agent to dramatically improve self-healing success rates from 95% → 98%+.

### Current Self-Healing Limitations

```python
# ❌ CURRENT Evolution Agent (95% success rate):

class EvolutionAgent(BaseAgent):
    async def heal_test(self, test_id: str, failure_data: Dict) -> Dict:
        """Current self-healing approach - limited success."""
        
        # Analyze failure
        error_message = failure_data["error"]
        
        # Simple pattern matching
        if "not found" in error_message.lower():
            # Try to find alternative selector
            old_selector = self._extract_selector(failure_data)
            new_selector = await self._find_similar_element(old_selector)
            
            # Update test
            await self._update_test_selector(test_id, old_selector, new_selector)
            
            return {"status": "healed", "confidence": 0.7}
        
        return {"status": "unable_to_heal"}
```

**Problems:**
- ❌ Only handles simple "element not found" cases
- ❌ No verification that fix actually works
- ❌ Limited understanding of why test broke
- ❌ 5% of tests still require manual intervention

### Enhanced with Healer Logic

```python
# ✅ ENHANCED Evolution Agent with Healer Logic (98%+ success rate):

class EvolutionAgent(BaseAgent):
    async def heal_test(
        self, 
        test_id: str, 
        failure_data: Dict
    ) -> Dict:
        """
        Healer-enhanced self-healing with replay → inspect → patch workflow.
        
        Based on Playwright Healer agent pattern.
        """
        logger.info(f"Starting Healer workflow for test: {test_id}")
        
        # Phase 1: REPLAY - Understand the failure
        replay_result = await self._replay_failing_steps(
            test_id=test_id,
            failure_data=failure_data,
        )
        
        if not replay_result["reproduced"]:
            # Flaky test - couldn't reproduce
            return {
                "status": "flaky",
                "action": "mark_for_review",
                "reason": "Failure could not be reproduced",
            }
        
        # Phase 2: INSPECT - Analyze current UI state
        inspection = await self._inspect_current_ui(
            test_id=test_id,
            failing_step=replay_result["failing_step"],
            expected_element=replay_result["expected_element"],
        )
        
        # Phase 3: PATCH - Generate fixes based on inspection
        patches = await self._generate_patches(
            test_id=test_id,
            failure_type=replay_result["failure_type"],
            inspection_data=inspection,
        )
        
        # Phase 4: VERIFY - Test each patch until one works
        for patch in patches:
            logger.info(f"Trying patch: {patch['description']}")
            
            # Apply patch
            await self._apply_patch(test_id, patch)
            
            # Re-run test
            rerun_result = await self._rerun_test(test_id)
            
            if rerun_result["status"] == "pass":
                # Success! This patch worked
                logger.info(f"✅ Healer success: {patch['description']}")
                
                return {
                    "status": "healed",
                    "patch_applied": patch,
                    "confidence": patch["confidence"],
                    "verification": "passed",
                }
            else:
                # This patch didn't work, revert and try next
                await self._revert_patch(test_id, patch)
        
        # Phase 5: ESCALATE - Couldn't heal automatically
        logger.warning(f"Healer unable to fix test: {test_id}")
        
        # Skip test and create detailed report for human review
        await self._skip_test_with_report(
            test_id=test_id,
            reason="functionality_broken",
            diagnosis=inspection,
            attempted_patches=patches,
        )
        
        return {
            "status": "unable_to_heal",
            "action": "skipped",
            "reason": "Exhausted all patch options - functionality may be broken",
            "human_review_required": True,
        }
    
    async def _replay_failing_steps(
        self, 
        test_id: str, 
        failure_data: Dict
    ) -> Dict:
        """
        Phase 1: Replay the test to understand exactly where and why it fails.
        
        This is critical - we need to reproduce the failure to understand it.
        """
        test = await self.db.get_test(test_id)
        
        # Execute test step-by-step, stopping at failure
        browser = await self.playwright.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        failing_step = None
        failure_type = None
        expected_element = None
        
        try:
            for i, step in enumerate(test["steps"]):
                logger.debug(f"Replaying step {i+1}: {step['action']}")
                
                try:
                    await self._execute_step(page, step)
                except Exception as e:
                    # Found the failing step!
                    failing_step = i
                    failure_type = self._classify_failure(e)
                    expected_element = step.get("selector")
                    break
        finally:
            await browser.close()
        
        if failing_step is not None:
            logger.info(f"Reproduced failure at step {failing_step}: {failure_type}")
            
            return {
                "reproduced": True,
                "failing_step": failing_step,
                "failure_type": failure_type,
                "expected_element": expected_element,
            }
        else:
            return {"reproduced": False}
    
    def _classify_failure(self, exception: Exception) -> str:
        """Classify the type of failure for targeted patching."""
        error_msg = str(exception).lower()
        
        if "not found" in error_msg or "not visible" in error_msg:
            return "element_not_found"
        elif "timeout" in error_msg:
            return "timeout"
        elif "detached" in error_msg:
            return "element_detached"
        elif "cannot click" in error_msg:
            return "click_intercepted"
        elif "navigation" in error_msg:
            return "navigation_failed"
        else:
            return "unknown"
    
    async def _inspect_current_ui(
        self,
        test_id: str,
        failing_step: int,
        expected_element: str,
    ) -> Dict:
        """
        Phase 2: Inspect the current UI state to find alternatives.
        
        This is where Healer shines - it looks at the ACTUAL page,
        not just the old selector.
        """
        test = await self.db.get_test(test_id)
        
        # Navigate to the page where failure occurred
        browser = await self.playwright.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Execute steps up to (but not including) failing step
            for step in test["steps"][:failing_step]:
                await self._execute_step(page, step)
            
            # Now inspect the page state
            inspection = {
                "page_url": page.url,
                "page_title": await page.title(),
                "visible_elements": await self._get_visible_elements(page),
                "similar_elements": await self._find_similar_elements(
                    page, 
                    expected_element
                ),
                "dom_snapshot": await page.content(),
            }
            
            return inspection
            
        finally:
            await browser.close()
    
    async def _find_similar_elements(
        self, 
        page, 
        expected_selector: str
    ) -> List[Dict]:
        """Find elements similar to the expected one."""
        
        # Extract intent from old selector
        intent = await self._extract_selector_intent(expected_selector)
        # e.g., "button with text 'Login'" or "input with name 'email'"
        
        # Find all matching elements
        candidates = []
        
        # Try various strategies
        strategies = [
            self._find_by_text,
            self._find_by_role,
            self._find_by_label,
            self._find_by_placeholder,
            self._find_by_test_id,
        ]
        
        for strategy in strategies:
            matches = await strategy(page, intent)
            candidates.extend(matches)
        
        # Score candidates by similarity
        scored_candidates = [
            {
                "selector": c["selector"],
                "similarity_score": self._calculate_similarity(
                    expected_selector, 
                    c["selector"]
                ),
                "strategy": c["strategy"],
            }
            for c in candidates
        ]
        
        # Sort by score
        scored_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return scored_candidates[:5]  # Top 5 candidates
    
    async def _generate_patches(
        self,
        test_id: str,
        failure_type: str,
        inspection_data: Dict,
    ) -> List[Dict]:
        """
        Phase 3: Generate patches based on failure type and inspection.
        
        Returns list of patches in priority order.
        """
        patches = []
        
        if failure_type == "element_not_found":
            # Patch 1: Try similar elements (highest confidence)
            for candidate in inspection_data["similar_elements"]:
                if candidate["similarity_score"] > 0.7:
                    patches.append({
                        "type": "selector_update",
                        "description": f"Update selector to: {candidate['selector']}",
                        "old_selector": inspection_data["expected_element"],
                        "new_selector": candidate["selector"],
                        "confidence": candidate["similarity_score"],
                        "reason": f"Found similar element via {candidate['strategy']}",
                    })
            
            # Patch 2: Add wait before action (medium confidence)
            patches.append({
                "type": "add_wait",
                "description": "Add explicit wait for element",
                "wait_duration": 5000,  # 5 seconds
                "confidence": 0.6,
                "reason": "Element may need more time to appear",
            })
        
        elif failure_type == "timeout":
            # Patch 1: Increase timeout
            patches.append({
                "type": "increase_timeout",
                "description": "Increase timeout from 30s to 60s",
                "new_timeout": 60000,
                "confidence": 0.8,
                "reason": "Page may be slow to load",
            })
            
            # Patch 2: Add network idle wait
            patches.append({
                "type": "add_wait",
                "description": "Wait for network idle",
                "wait_type": "networkidle",
                "confidence": 0.7,
                "reason": "Page may have pending network requests",
            })
        
        elif failure_type == "click_intercepted":
            # Patch 1: Scroll into view
            patches.append({
                "type": "scroll_into_view",
                "description": "Scroll element into view before clicking",
                "confidence": 0.85,
                "reason": "Element may be outside viewport",
            })
            
            # Patch 2: Force click
            patches.append({
                "type": "force_click",
                "description": "Use force: true for click action",
                "confidence": 0.7,
                "reason": "Another element may be overlaying target",
            })
        
        elif failure_type == "element_detached":
            # Patch 1: Re-query element
            patches.append({
                "type": "requery_element",
                "description": "Re-query element before each action",
                "confidence": 0.8,
                "reason": "DOM may be re-rendering",
            })
        
        return patches
    
    async def _apply_patch(self, test_id: str, patch: Dict) -> None:
        """Apply a patch to the test code."""
        test = await self.db.get_test(test_id)
        
        if patch["type"] == "selector_update":
            # Update selector in test code
            test_code = test["code"]
            updated_code = test_code.replace(
                patch["old_selector"],
                patch["new_selector"]
            )
            await self.db.update_test(test_id, {"code": updated_code})
        
        elif patch["type"] == "add_wait":
            # Insert wait statement before failing step
            # (implementation details...)
            pass
        
        # ... handle other patch types
    
    async def _rerun_test(self, test_id: str) -> Dict:
        """Re-run test after applying patch."""
        test = await self.db.get_test(test_id)
        
        # Execute test
        result = await self.execution_agent.execute_single_test(test)
        
        return result
    
    async def _skip_test_with_report(
        self,
        test_id: str,
        reason: str,
        diagnosis: Dict,
        attempted_patches: List[Dict],
    ) -> None:
        """
        Skip test and create detailed report for human review.
        
        This is important - if Healer can't fix it, the functionality
        may actually be broken, not just the test.
        """
        report = {
            "test_id": test_id,
            "status": "skipped",
            "reason": reason,
            "diagnosis": diagnosis,
            "attempted_patches": [
                {
                    "description": p["description"],
                    "reason": p["reason"],
                    "result": "failed",
                }
                for p in attempted_patches
            ],
            "recommendation": (
                "Manual review required. Healer attempted multiple fixes but none worked. "
                "This suggests the application functionality may have changed or broken."
            ),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Save report
        await self.db.create_healer_report(report)
        
        # Mark test as skipped
        await self.db.update_test(test_id, {"status": "skipped"})
        
        # Send alert to QA team
        await self.notification_service.send_alert(
            channel="slack",
            message=f"🚨 Healer unable to fix test: {test_id}. Manual review required.",
            details=report,
        )
```

### Healer Workflow Diagram

```
Test Failure Detected
         ↓
    ┌────────────────────┐
    │  PHASE 1: REPLAY  │
    │  ────────────────  │
    │  • Execute test    │
    │    step-by-step    │
    │  • Reproduce       │
    │    failure         │
    │  • Identify        │
    │    failing step    │
    └────────────────────┘
         ↓
    Failure Reproduced?
         ↓ Yes
    ┌────────────────────┐
    │  PHASE 2: INSPECT │
    │  ────────────────  │
    │  • Navigate to     │
    │    failing point   │
    │  • Inspect current │
    │    UI state        │
    │  • Find similar    │
    │    elements        │
    │  • Analyze DOM     │
    └────────────────────┘
         ↓
    ┌────────────────────┐
    │  PHASE 3: PATCH   │
    │  ────────────────  │
    │  • Generate patch  │
    │    candidates      │
    │  • Score by        │
    │    confidence      │
    │  • Sort by         │
    │    priority        │
    └────────────────────┘
         ↓
    ┌────────────────────┐
    │  PHASE 4: VERIFY  │
    │  ────────────────  │
    │  For each patch:   │
    │  • Apply patch     │
    │  • Re-run test     │
    │  • Check result    │
    │  • If pass: ✅     │
    │  • If fail: Revert │
    └────────────────────┘
         ↓
    Patch Worked?
    ┌─────┴──────┐
    ↓ Yes        ↓ No
┌────────┐  ┌────────────┐
│ SUCCESS│  │ PHASE 5:   │
│ HEALED │  │ ESCALATE   │
│   ✅   │  │ ──────────  │
└────────┘  │ • Skip test │
            │ • Create    │
            │   report    │
            │ • Alert QA  │
            │   team      │
            └────────────┘
```

### Success Metrics

**Current Evolution Agent (RL-based):**
- Success rate: 95%
- Average repair time: 30 seconds
- Manual intervention: 5% of failures

**Enhanced with Healer Logic:**
- Success rate: **98%+** (target)
- Average repair time: 45 seconds (slightly longer due to thorough workflow)
- Manual intervention: **< 2%** of failures

**ROI:**
- 100 test failures per week
- Current: 5 require manual fix (2 hours each) = 10 hours/week
- Enhanced: 2 require manual fix = 4 hours/week
- **Savings: 6 hours/week = 24 hours/month = $12,000/year** (at $500/hour)

---

## Web-Based Interactive Planning

### Overview

Implement a **web-based interactive planning** feature in the dashboard, inspired by Playwright Planner, allowing QA engineers to explore the application and create test plans interactively.

**Note**: This is NOT IDE-integrated (as per user requirement). All functionality is accessed via the web dashboard.

### Current Planning Workflow

```
❌ CURRENT:
QA Engineer writes requirements → Upload to platform → Requirements Agent analyzes

Problems:
- No visual feedback during planning
- Can't explore the app while planning
- Hard to discover edge cases
- Time-consuming back-and-forth
```

### Enhanced Interactive Planning Workflow

```
✅ ENHANCED (Web Dashboard):
QA Engineer opens Interactive Planner → Embedded browser shows target app
→ Click elements to explore → Agent observes and generates scenarios
→ Real-time Markdown spec generation → Review and refine
→ Approve for test generation
```

### UI Design

```
┌───────────────────────────────────────────────────────────────┐
│  AI Web Test - Interactive Test Planner            [User ▼]  │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────┬──────────────────────────────────┐  │
│  │ PLANNER CONTROLS    │  GENERATED SPEC (Live Preview)   │  │
│  ├─────────────────────┼──────────────────────────────────┤  │
│  │                     │ # Three HK Login - Test Plan     │  │
│  │ Target URL:         │                                  │  │
│  │ ┌─────────────────┐ │ ## Test Scenarios                │  │
│  │ │ three.com.hk    │ │                                  │  │
│  │ └─────────────────┘ │ ### 1. User observed clicking:   │  │
│  │                     │ - Login button                   │  │
│  │ Project:            │ - Username field                 │  │
│  │ [Three HK Portal ▼] │ - Password field                 │  │
│  │                     │                                  │  │
│  │ [Start Exploration] │ **Steps Detected:**              │  │
│  │ [Pause]  [Stop]     │ 1. Navigate to login page        │  │
│  │                     │ 2. Enter credentials             │  │
│  │ Recording:          │ 3. Click login button            │  │
│  │ ●  2 min 34 sec     │                                  │  │
│  │                     │ **Edge Cases Identified:**       │  │
│  │ Interactions: 12    │ - Invalid password               │  │
│  │ Scenarios: 3        │ - Empty fields                   │  │
│  │                     │ - Remember me checkbox           │  │
│  │ [Add Note]          │                                  │  │
│  │ [Mark Scenario]     │ [Copy Markdown]  [Edit]  [Save] │  │
│  └─────────────────────┴──────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              EMBEDDED BROWSER (Target App)             │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │    ┌────────────────────────────────────────┐          │  │
│  │    │  Three Hong Kong Portal                │          │  │
│  │    │  ─────────────────────────────────────  │          │  │
│  │    │                                         │          │  │
│  │    │  Username: [________________]           │          │  │
│  │    │            ^ (Click detected)           │          │  │
│  │    │                                         │          │  │
│  │    │  Password: [________________]           │          │  │
│  │    │                                         │          │  │
│  │    │  [  Login  ]  ← (Click detected)        │          │  │
│  │    │                                         │          │  │
│  │    └────────────────────────────────────────┘          │  │
│  │                                                          │  │
│  │  Elements highlighted when hovered (AI detects intent)  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  [Cancel]  [Generate Tests from Spec] →                      │
└───────────────────────────────────────────────────────────────┘
```

### Implementation

```python
# app/api/routes/interactive_planner.py

from fastapi import APIRouter, WebSocket
from playwright.async_api import async_playwright

router = APIRouter()

@router.websocket("/ws/planner/{session_id}")
async def interactive_planner(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for interactive test planning.
    
    User interacts with embedded browser, agent observes and generates spec.
    """
    await websocket.accept()
    
    # Initialize Playwright browser
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track user interactions
        interactions = []
        scenarios = []
        
        # Listen for page events
        page.on("click", lambda: handle_click(page, interactions))
        page.on("input", lambda: handle_input(page, interactions))
        page.on("navigation", lambda: handle_navigation(page, interactions))
        
        try:
            while True:
                # Receive command from frontend
                data = await websocket.receive_json()
                command = data["command"]
                
                if command == "navigate":
                    url = data["url"]
                    await page.goto(url)
                    await websocket.send_json({
                        "type": "navigation",
                        "url": page.url,
                        "title": await page.title(),
                    })
                
                elif command == "get_interactions":
                    # Send current interactions to frontend
                    await websocket.send_json({
                        "type": "interactions",
                        "data": interactions,
                    })
                
                elif command == "generate_spec":
                    # Generate Markdown spec from interactions
                    spec = await generate_markdown_spec_from_interactions(
                        interactions=interactions,
                        url=page.url,
                        project=data["project"],
                    )
                    
                    await websocket.send_json({
                        "type": "spec_generated",
                        "spec": spec,
                    })
                
                elif command == "stop":
                    break
        
        finally:
            await browser.close()
            await websocket.close()

async def handle_click(page, interactions):
    """Record click interaction."""
    # Get element details
    element = page.locator(":hover")
    
    interaction = {
        "type": "click",
        "selector": await element.get_attribute("data-testid") or await generate_selector(element),
        "text": await element.text_content(),
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    interactions.append(interaction)

async def generate_markdown_spec_from_interactions(
    interactions: List[Dict],
    url: str,
    project: str,
) -> str:
    """
    Use Requirements Agent to convert interactions into Markdown spec.
    """
    # Group interactions into scenarios
    scenarios = group_interactions_into_scenarios(interactions)
    
    # Use LLM to generate Markdown
    prompt = f"""
    Generate a Playwright-style Markdown test specification from these user interactions.
    
    URL: {url}
    Project: {project}
    
    Interactions:
    {json.dumps(interactions, indent=2)}
    
    Grouped Scenarios:
    {json.dumps(scenarios, indent=2)}
    
    Generate comprehensive Markdown spec with:
    - Application Overview
    - Test Scenarios (from observed interactions)
    - Steps and Expected Results
    - Edge cases inferred from interactions
    - Data Requirements
    """
    
    markdown_spec = await llm.generate(prompt)
    
    return markdown_spec
```

### Frontend Implementation

```typescript
// frontend/src/components/InteractivePlanner.tsx

import React, { useState, useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';

export const InteractivePlanner: React.FC = () => {
  const [targetUrl, setTargetUrl] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [generatedSpec, setGeneratedSpec] = useState('');
  const [interactions, setInteractions] = useState([]);
  
  const ws = useWebSocket('/ws/planner/session-123');
  
  useEffect(() => {
    ws.on('spec_generated', (data) => {
      setGeneratedSpec(data.spec);
    });
    
    ws.on('interactions', (data) => {
      setInteractions(data.data);
    });
  }, []);
  
  const startExploration = () => {
    setIsRecording(true);
    ws.send({ command: 'navigate', url: targetUrl });
  };
  
  const generateSpec = () => {
    ws.send({ command: 'generate_spec', project: 'Three HK Portal' });
  };
  
  return (
    <div className="interactive-planner">
      <div className="controls-panel">
        <input
          value={targetUrl}
          onChange={(e) => setTargetUrl(e.target.value)}
          placeholder="Enter target URL..."
        />
        <button onClick={startExploration}>Start Exploration</button>
        <button onClick={generateSpec}>Generate Spec</button>
        
        <div className="stats">
          <p>Recording: {isRecording ? '●' : '○'}</p>
          <p>Interactions: {interactions.length}</p>
        </div>
      </div>
      
      <div className="spec-preview">
        <h3>Generated Spec (Live Preview)</h3>
        <pre>{generatedSpec}</pre>
      </div>
      
      <div className="embedded-browser">
        <iframe
          src={`/planner-browser/${targetUrl}`}
          title="Target Application"
        />
      </div>
    </div>
  );
};
```

### Benefits

1. **Visual Exploration** ✅
   - See the app while planning tests
   - Click and interact naturally
   - Agent observes and learns

2. **Real-Time Spec Generation** ✅
   - Markdown spec generates as you explore
   - Instant feedback on test scenarios
   - Easy to refine before generation

3. **Better Edge Case Discovery** ✅
   - Explore different paths visually
   - Agent suggests edge cases based on observations
   - More comprehensive test coverage

4. **Faster Planning** ✅
   - 50% faster than writing requirements manually
   - More accurate (based on actual app state)
   - Fun and engaging for QA engineers!

---

## Playwright Generation Optimization

### Overview

Enhance the Generation Agent with Playwright-specific best practices from the Playwright Generator agent.

### Key Optimizations

#### 1. **Generation Hints** (Better Locators)

```typescript
// ✅ Playwright Generator uses "generation hints" for better selectors

// BEFORE (Generic):
await page.click('#login-button');

// AFTER (Playwright-optimized with hints):
await page.getByRole('button', { name: 'Login' }).click();

// Why better?
// - More resilient (survives ID changes)
// - Accessible (role-based)
// - Human-readable (name describes intent)
```

**Implementation:**

```python
# app/agents/generation_agent.py

class GenerationAgent(BaseAgent):
    async def generate_playwright_test(self, scenario: Dict) -> str:
        """Generate Playwright test with generation hints."""
        
        prompt = f"""
        Generate Playwright test with these GENERATION HINTS:
        
        1. Prefer getByRole() over CSS selectors:
           ✅ page.getByRole('button', {{ name: 'Login' }})
           ❌ page.click('#login-btn')
        
        2. Use getByLabel() for form inputs:
           ✅ page.getByLabel('Email address').fill('test@example.com')
           ❌ page.fill('[name="email"]', 'test@example.com')
        
        3. Use getByText() for visible text:
           ✅ page.getByText('Welcome back').isVisible()
           ❌ page.locator('div.welcome').isVisible()
        
        4. Use getByTestId() only as last resort:
           ✅ page.getByTestId('login-form')  // If nothing else works
        
        5. Chain locators for specificity:
           ✅ page.getByRole('dialog').getByRole('button', {{ name: 'Close' }})
        
        Scenario:
        {json.dumps(scenario, indent=2)}
        
        Generate test following these hints.
        """
        
        test_code = await self.llm.generate(prompt)
        
        return test_code
```

#### 2. **Assertion Catalog** (Comprehensive Validation)

```typescript
// ✅ Playwright Generator uses comprehensive assertion catalog

// BEFORE (Minimal):
await expect(page.locator('.username')).toBeVisible();

// AFTER (Comprehensive):
await expect(page.getByRole('heading', { name: 'Account' })).toBeVisible();
await expect(page.getByText('John Doe')).toHaveText('John Doe');
await expect(page).toHaveURL(/.*dashboard/);
await expect(page).toHaveTitle(/Dashboard/);
await expect(page.getByRole('button', { name: 'Logout' })).toBeEnabled();
await expect(page.getByRole('link', { name: 'Billing' })).toHaveAttribute('href', '/billing');
```

**Assertion Catalog:**

```python
# app/agents/generation_agent.py

PLAYWRIGHT_ASSERTION_CATALOG = {
    "visibility": [
        "await expect({locator}).toBeVisible()",
        "await expect({locator}).toBeHidden()",
    ],
    "text": [
        "await expect({locator}).toHaveText('{text}')",
        "await expect({locator}).toContainText('{text}')",
    ],
    "state": [
        "await expect({locator}).toBeEnabled()",
        "await expect({locator}).toBeDisabled()",
        "await expect({locator}).toBeChecked()",
        "await expect({locator}).toBeFocused()",
    ],
    "attributes": [
        "await expect({locator}).toHaveAttribute('{name}', '{value}')",
        "await expect({locator}).toHaveClass(/{pattern}/)",
    ],
    "page": [
        "await expect(page).toHaveURL(/{pattern}/)",
        "await expect(page).toHaveTitle(/{pattern}/)",
    ],
    "count": [
        "await expect({locator}).toHaveCount({number})",
    ],
    "value": [
        "await expect({locator}).toHaveValue('{value}')",
    ],
}

class GenerationAgent(BaseAgent):
    async def generate_assertions(self, expected_results: List[str]) -> List[str]:
        """Generate comprehensive assertions using catalog."""
        
        assertions = []
        
        for result in expected_results:
            # Use LLM to match result to assertion type
            assertion_type = await self._classify_expected_result(result)
            
            # Get appropriate assertion from catalog
            assertion_template = PLAYWRIGHT_ASSERTION_CATALOG[assertion_type][0]
            
            # Fill in template
            assertion = await self._fill_assertion_template(
                template=assertion_template,
                result=result,
            )
            
            assertions.append(assertion)
        
        return assertions
```

#### 3. **Live Selector Verification** (During Generation)

```python
# app/agents/generation_agent.py

class GenerationAgent(BaseAgent):
    async def generate_test_with_verification(
        self, 
        scenario: Dict
    ) -> Dict:
        """
        Generate test and verify selectors LIVE during generation.
        
        This prevents generating tests with invalid selectors.
        """
        # Generate initial test
        test_code = await self.generate_playwright_test(scenario)
        
        # Extract selectors from generated code
        selectors = self._extract_selectors(test_code)
        
        # Verify each selector on live page
        browser = await self.playwright.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(scenario["url"])
            
            for selector in selectors:
                try:
                    # Try to find element
                    element = page.locator(selector["locator"])
                    await element.wait_for(timeout=5000)
                    
                    selector["valid"] = True
                    
                except Exception:
                    # Selector doesn't work, find alternative
                    logger.warning(f"Invalid selector: {selector['locator']}")
                    
                    alternative = await self._find_alternative_selector(
                        page, 
                        selector
                    )
                    
                    if alternative:
                        selector["locator"] = alternative
                        selector["valid"] = True
                    else:
                        selector["valid"] = False
            
        finally:
            await browser.close()
        
        # Regenerate test with corrected selectors
        if any(not s["valid"] for s in selectors):
            test_code = await self._regenerate_test_with_corrected_selectors(
                test_code, 
                selectors
            )
        
        return {
            "code": test_code,
            "selectors_verified": True,
            "corrections_made": len([s for s in selectors if not s["valid"]]),
        }
```

---

## Implementation Roadmap

### Phase 1: Markdown Specs + Seed Tests (Days 1-3)

**Day 1: Markdown Spec Infrastructure**
- [ ] Create `specs/` directory structure
- [ ] Update Requirements Agent to output Markdown specs
- [ ] Implement Markdown parser for Generation Agent
- [ ] Add spec_path to database schema

**Day 2: Seed Test Pattern**
- [ ] Create seed test templates
- [ ] Implement seed test execution logic in Execution Agent
- [ ] Add `.auth/` directory support for storage state
- [ ] Update test generator to use seed tests

**Day 3: Testing & Documentation**
- [ ] Write unit tests for Markdown generation/parsing
- [ ] Write integration tests for seed test workflow
- [ ] Update developer documentation
- [ ] Create example specs and seed tests

**Deliverables**: `specs/` directory with Markdown specs, `tests/*/seed.spec.ts` files, updated Requirements and Generation agents (300 lines), tests (200 lines)

### Phase 2: Healer-Enhanced Self-Healing (Days 4-8) 🔥

**Day 4: Healer Infrastructure**
- [ ] Implement replay logic in Evolution Agent
- [ ] Add failure classification system
- [ ] Create HealeReport database schema

**Day 5: UI Inspection**
- [ ] Implement current UI inspection
- [ ] Add similar element finder
- [ ] Implement selector intent extraction

**Day 6: Patch Generation**
- [ ] Implement patch generator for each failure type
- [ ] Add patch scoring system
- [ ] Create patch verification logic

**Day 7: Integration & Testing**
- [ ] Integrate Healer workflow into Evolution Agent
- [ ] Add Healer metrics to dashboard
- [ ] Write chaos tests for Healer workflow

**Day 8: Documentation & Refinement**
- [ ] Create Healer runbook for QA team
- [ ] Document patch types and confidence scores
- [ ] Tune patch generation prompts

**Deliverables**: Evolution Agent with Healer logic (800 lines), Healer dashboard (200 lines), tests (400 lines), runbook (50 lines)

### Phase 3: Interactive Planning + Optimization (Days 9-13)

**Day 9: Interactive Planner Backend**
- [ ] Implement WebSocket endpoint for planner
- [ ] Add Playwright browser embedding
- [ ] Create interaction tracking system

**Day 10: Interactive Planner Frontend**
- [ ] Build Interactive Planner UI component
- [ ] Add embedded browser iframe
- [ ] Implement real-time spec preview

**Day 11: Playwright Generator Optimization**
- [ ] Integrate generation hints into Generation Agent
- [ ] Add assertion catalog
- [ ] Implement live selector verification

**Day 12: Testing**
- [ ] Write E2E tests for Interactive Planner
- [ ] Test Playwright generation optimizations
- [ ] Performance testing for WebSocket communication

**Day 13: Documentation**
- [ ] Create Interactive Planner user guide
- [ ] Document Playwright best practices
- [ ] Update architecture diagrams

**Deliverables**: Interactive Planner (600 lines backend, 400 lines frontend), optimized Generation Agent (500 lines), tests (300 lines), documentation (100 lines)

---

## Cost Analysis

### Infrastructure Costs (Monthly)
| Component | Cost | Notes |
|-----------|------|-------|
| **Playwright Browser Sessions** | $0 | Free (open-source) |
| **Additional LLM Calls** | $50-150 | Markdown spec generation, Healer patches |
| **Storage for Specs** | $5 | S3/MinIO for Markdown specs |
| **WebSocket Infrastructure** | $0 | Existing backend infrastructure |
| **Total** | **$55-155/month** | Minimal additional cost |

### ROI Analysis

**Without Playwright Integration**:
- Test maintenance: 10 hours/week × $500/hour = $5,000/week
- Manual test planning: 5 hours/week × $500/hour = $2,500/week
- Broken test triage: 5 hours/week × $500/hour = $2,500/week
- **Total monthly cost**: $40,000/month in QA engineer time

**With Playwright Integration**:
- Test maintenance: 3 hours/week (70% reduction from 98% self-healing)
- Manual test planning: 2 hours/week (60% reduction from interactive planner)
- Broken test triage: 1 hour/week (80% reduction from Healer diagnosis)
- **Total monthly cost**: $9,600/month + $155 infrastructure

**Savings**:
- **Monthly savings**: $30,245
- **Annual savings**: $362,940
- **ROI**: **234,406% annually!**

**Conclusion**: Playwright integration is **essentially free** (minimal infrastructure cost) with **massive ROI** from improved self-healing and planning efficiency.

---

## Summary & Integration

### Key Achievements

✅ **Markdown Test Specifications**: Human-readable, Git-friendly test plans in `specs/`  
✅ **Seed Test Pattern**: Eliminate 50%+ code duplication across tests  
✅ **Healer-Enhanced Self-Healing**: 95% → 98%+ success rate with replay → inspect → patch  
✅ **Web-Based Interactive Planning**: Live app exploration via dashboard (no IDE)  
✅ **Playwright Generation Optimization**: Better locators, comprehensive assertions, live verification  

### Integration with Existing Components

| Component | Integration Point |
|-----------|------------------|
| **Requirements Agent** | Outputs Markdown specs to `specs/`, uses interactive planner data |
| **Generation Agent** | Reads Markdown specs, uses Playwright best practices, live verification |
| **Execution Agent** | Runs seed tests first, uses storage state for efficiency |
| **Evolution Agent** | Enhanced with Healer logic: replay → inspect → patch → verify |
| **Dashboard** | Adds Interactive Planner component, Healer metrics, spec preview |
| **Database** | Stores spec paths, seed test references, Healer reports |

### Production Readiness

- ✅ **Battle-tested patterns** from Microsoft Playwright team
- ✅ **Non-intrusive** enhancement to existing architecture
- ✅ **Gradual adoption** possible (phase by phase)
- ✅ **Minimal infrastructure cost** ($55-155/month)
- ✅ **Massive ROI** ($362,940/year savings)

### Next Steps

1. **Review** this Playwright Integration architecture document
2. **Update PRD** with new FRs (FR-76, FR-77, FR-78, FR-79)
3. **Update SRS** with Playwright integration stack
4. **Begin Phase 1** implementation (Markdown specs + Seed tests)

---

**End of Playwright Test Agents Integration Architecture Document**

This integration enhances the AI-Web-Test v1 platform with production-ready Playwright-specific capabilities while maintaining the existing 6-agent architecture and ensuring standalone web dashboard operation (no IDE dependency).

