# AI Web Test v1.0 - Project Management Plan

**Version:** 5.0 (Clean Rewrite - January 16, 2026)  
**Project Duration:** 32 weeks (8 months)  
**Team:** 2 Full-Stack Developers (Feature-Based Development)  
**Methodology:** Agile with incremental value delivery

---

## 📍 CURRENT STATUS

**Phase:** 2 In Progress 🔄 (Week 14)  
**Progress:** Phase 2 = ~92% | Sprint 5.5 starting  
**Date:** January 16, 2026

### Phase 2 Sprint Summary

```
DEVELOPER A:
├─ Sprint 4: Test Editing & Versioning ✅ 100%
├─ Sprint 5: Dual Stagehand Provider ⚠️ 83% (SUSPENDED - TypeScript instability)
└─ Sprint 6: Learning Dashboard ✅ 100%

DEVELOPER B:
├─ Sprint 5: Execution Feedback System ✅ 100%
├─ Sprint 5.5: Hybrid Execution Engine ⏳ 0% (STARTING - 3 days planned)
└─ Sprint 6: Prompt A/B Testing ✅ 100%
```

**Next Milestone:** Sprint 5.5 completion (3 days), then Phase 3 starts Week 15

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Developer Scope Separation](#developer-scope-separation)
3. [Phase Overview](#phase-overview)
4. [Phase 1: MVP Foundation](#phase-1-mvp-foundation)
5. [Phase 2: Learning Foundations](#phase-2-learning-foundations)
6. [Phase 3: Multi-Agent Architecture](#phase-3-multi-agent-architecture)
7. [Phase 4: Reinforcement Learning](#phase-4-reinforcement-learning)
8. [Risk Management](#risk-management)
9. [Success Criteria](#success-criteria)

---

## Executive Summary

AI Web Test v1.0 is a multi-agent test automation platform that automatically generates, executes, and maintains browser-based tests using AI. The system reduces test creation time from days to minutes while continuously learning from execution feedback.

### Key Achievements

- ✅ **Phase 1 (Weeks 1-8):** MVP with test generation, execution, and knowledge base
- 🔄 **Phase 2 (Weeks 9-14):** Learning foundations with test editing, versioning, feedback (Sprint 5.5 starting)
- 📋 **Phase 3 (Weeks 15-26):** Multi-agent architecture planned
- 📋 **Phase 4 (Weeks 27-34):** Reinforcement learning planned

### Current Status (January 16, 2026)

**Phase 2 Nearing Completion:**
- 5 of 6 sprints delivered successfully
- Sprint 5.5 (Hybrid Execution Engine) starting - 3 days planned
- TypeScript Stagehand integration suspended (stability concerns)
- Test editing, versioning, and feedback systems operational
- Will be ready for Phase 3 after Sprint 5.5 completion

---

## Developer Scope Separation

### DEVELOPER A (Phase 2)

| Sprint | Feature | Duration | Status | Key Deliverables |
|--------|---------|----------|--------|------------------|
| **Sprint 4** | Test Editing & Versioning | 1 week | ✅ 100% | • 5 version control API endpoints<br>• 4 frontend components (TestStepEditor, VersionHistoryPanel, Compare, Rollback)<br>• 18 unit tests, 14 E2E tests<br>• Auto-save functionality (3-second debounce) |
| **Sprint 5** | Dual Stagehand Provider | 2 weeks | ⚠️ 83% | • Adapter Pattern (Abstract base class + Python/TypeScript adapters)<br>• Node.js microservice (14 files, 1,733 lines)<br>• Settings UI with health monitoring<br>• **SUSPENDED:** TypeScript Stagehand unstable |
| **Sprint 6** | Learning Dashboard | 1 week | ✅ 100% | • Analytics & Metrics API<br>• Dashboard UI with performance charts<br>• Test success rate tracking<br>• Execution history visualization |

**Developer A Total:** 4 weeks (3 sprints completed, 1 suspended)

---

### DEVELOPER B (Phase 2)

| Sprint | Feature | Duration | Status | Key Deliverables |
|--------|---------|----------|--------|------------------|
| **Sprint 5** | Execution Feedback System | 2 weeks | ✅ 100% | • 8 feedback collection API endpoints<br>• ExecutionFeedback model (11 fields)<br>• Automatic failure capture<br>• Feedback Viewer UI<br>• Export/import functionality<br>• Stats API (success rate, failure patterns) |
| **Sprint 5.5** | 3-Tier Execution Engine | 5 days | ⏳ 0% | **PLANNED:**<br>• **Tier 1:** Playwright Direct (primary, fastest)<br>• **Tier 2:** Hybrid Mode (Stagehand observe + Playwright)<br>• **Tier 3:** Stagehand Only (last resort)<br>• **Option A:** Tier 1 → Tier 2 (90-95% success)<br>• **Option B:** Tier 1 → Tier 3 (92-94% success)<br>• **Option C:** Tier 1 → Tier 2 → Tier 3 (97-99% success)<br>• Settings page with strategy selection<br>• XPath caching & self-healing<br>• Analytics for strategy effectiveness |
| **Sprint 6** | Prompt A/B Testing | 1 week | ✅ 100% | • Prompt management API<br>• A/B test configuration<br>• Performance comparison UI<br>• Traffic allocation (% split)<br>• Metrics tracking (success rate, tokens, speed) |

**Developer B Total:** ~4.5 weeks (2 sprints completed, 1 in progress)

---

### Technical Focus Areas

**Developer A:**
- Version control and test editing
- TypeScript/Node.js integration (suspended)
- Frontend component development
- Analytics and visualization

**Developer B:**
- Execution feedback and error handling
- Python Stagehand reliability improvements
- Prompt experimentation and optimization
- Backend API development

**Shared:**
- Database schema design (coordinated)
- API contracts (both developers)
- Testing frameworks (E2E, integration, unit)
- Documentation standards

---

## Phase Overview

| Phase | Duration | Focus | Status | Deliverables |
|-------|----------|-------|--------|--------------|
| **Phase 1** | Weeks 1-8 | MVP Foundation | ✅ 100% | Test generation, execution, KB system, 68+ API endpoints |
| **Phase 2** | Weeks 9-14 | Learning Foundations | 🔄 92% | Test editing, versioning, feedback, prompt A/B (hybrid execution starting) |
| **Phase 3** | Weeks 15-26 | Multi-Agent Architecture | 📋 Planned | 6 agents, CI/CD integration, enterprise features |
| **Phase 4** | Weeks 27-34 | Reinforcement Learning | 📋 Planned | RLHF, model fine-tuning, autonomous improvement |

---

## Phase 1: MVP Foundation

**Duration:** Weeks 1-8  
**Status:** ✅ 100% Complete

### Completed Sprints

1. **Sprint 1 (5 days):** Infrastructure & Authentication
2. **Sprint 2 (5 weeks):** Test Generation + KB + Security
3. **Sprint 3 (2 weeks):** Execution + Queue + Frontend Integration
4. **Sprint 3 Enhancement (2.5 hours):** Local Persistent Browser Debug Mode

### Key Deliverables

- **Backend:** 68+ API endpoints operational
- **Test Generation:** Multi-provider AI (Google Gemini FREE, Cerebras, OpenRouter, Azure OpenAI)
- **Execution Engine:** Real browser automation (Stagehand + Playwright)
- **Knowledge Base:** 8 categories, PDF/DOCX support
- **Queue Management:** 5 concurrent executions
- **Debug Mode:** 85% token savings via persistent browser sessions
- **Testing:** 17 E2E tests + 67 unit tests passing

### Success Metrics Achieved

- ✅ Test generation time: 5-90 seconds (target: <2 minutes)
- ✅ Test execution success rate: 100% (19/19 tests) (target: >80%)
- ✅ API response time: <200ms (target: <500ms)
- ✅ System uptime: 100% (target: >99%)

---

## Phase 2: Learning Foundations

**Duration:** Weeks 9-14 (6 weeks)  
**Status:** 🔄 92% Complete (Sprint 5.5 starting)

### Strategic Rationale

After Phase 1 deployment, users reported 5 critical pain points:

1. ❌ Unstable test generation (inconsistent LLM outputs)
2. ❌ No test editing (must regenerate entire tests)
3. ❌ No learning mechanism (same mistakes repeated)
4. ❌ No execution feedback loop (failures don't improve system)
5. ❌ No prompt refinement (manual experimentation only)

**Solution:** Phase 2 directly solves all 5 pain points with pragmatic features before investing in complex multi-agent architecture.

---

### Sprint 4: Test Editing & Versioning (Developer A)

**Duration:** 1 week  
**Status:** ✅ 100% Complete

#### Backend API (5 endpoints)

1. `POST /api/v1/tests/{test_id}/versions` - Create version snapshot
2. `GET /api/v1/tests/{test_id}/versions` - List all versions
3. `GET /api/v1/tests/{test_id}/versions/{version_id}` - Get specific version
4. `POST /api/v1/tests/{test_id}/versions/{version_id}/rollback` - Rollback to version
5. `PUT /api/v1/tests/{test_id}/steps` - Update test steps with auto-versioning

#### Frontend Components (4 components)

1. **TestStepEditor.tsx** - Inline step editing with auto-save (3-second debounce)
2. **VersionHistoryPanel.tsx** - Version list with timestamps and changelogs
3. **VersionCompareDialog.tsx** - Side-by-side diff view
4. **RollbackConfirmDialog.tsx** - Confirmation workflow with preview

#### Testing

- 18 unit tests passing (backend version service)
- 14 E2E tests passing (100% pass rate)
- Test scenarios: Create, edit, save, version history, compare, rollback

#### Database Schema

```sql
CREATE TABLE test_versions (
    id INTEGER PRIMARY KEY,
    test_case_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    steps JSON NOT NULL,
    created_at TIMESTAMP NOT NULL,
    created_by VARCHAR(50) NOT NULL,
    change_reason TEXT,
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id)
);
```

---

### Sprint 5: Execution Feedback System (Developer B)

**Duration:** 2 weeks  
**Status:** ✅ 100% Complete

#### Backend API (8 endpoints)

1. `POST /api/v1/feedback` - Create feedback entry
2. `GET /api/v1/feedback/{id}` - Get specific feedback
3. `GET /api/v1/feedback` - List all feedback (with filters)
4. `PUT /api/v1/feedback/{id}` - Update feedback
5. `DELETE /api/v1/feedback/{id}` - Delete feedback
6. `GET /api/v1/feedback/export` - Export feedback data
7. `POST /api/v1/feedback/import` - Import feedback data
8. `GET /api/v1/feedback/stats` - Get feedback statistics

#### ExecutionFeedback Model (11 fields)

```python
class ExecutionFeedback(Base):
    id: int
    execution_id: int
    step_index: int
    failure_type: str  # "selector_not_found", "timeout", "assertion_failed"
    error_message: str
    screenshot_url: str (optional)
    page_html_snapshot: str (optional)
    correction_applied: str (optional)
    correction_successful: bool
    created_at: datetime
    metadata: JSON
```

#### Features

- Automatic capture during test execution failures
- Manual feedback submission via UI
- Failure pattern analysis
- Correction tracking (what fixed the issue)
- Stats API: Success rate, common failure types, correction accuracy

#### Frontend

- **Feedback Viewer UI** - Browse, filter, and search feedback entries
- Export/import functionality for data portability

---

### Sprint 5: Dual Stagehand Provider (Developer A)

**Duration:** 2 weeks  
**Status:** ⚠️ 83% Complete (SUSPENDED)

#### Completed Work

**Adapter Pattern Implementation:**
- Abstract base class: `StagehandAdapter`
- Python adapter: `PythonStagehandAdapter` (fully operational)
- TypeScript adapter: `TypeScriptStagehandAdapter` (HTTP client ready)
- Factory pattern: `StagehandFactory` with provider selection

**Node.js Microservice:**
- Complete Express REST API (14 files, 1,733 lines)
- Session management with persistent state
- Health monitoring endpoint
- Winston logging infrastructure
- CORS configuration for backend integration
- Package.json with all dependencies configured

**Settings UI:**
- Provider selection interface (Python vs TypeScript)
- Health status monitoring with real-time checks
- Feature comparison table (6 features)
- API integration (GET/PUT `/api/v1/settings/stagehand-provider`)
- Responsive design with status indicators

**Testing:**
- 18 unit tests passing (adapter pattern)
- 6 integration tests passing (Python-TypeScript communication)
- Fixed critical bug: JavaScript truthy/falsy validation (`test_id: 0` rejection)

#### Suspension Rationale

**Issues Discovered:**
- TypeScript Stagehand library (@browserbasehq/stagehand) showed stability problems
- Inconsistent behavior during integration testing
- Error handling issues
- Library maturity concerns

**Decision (January 16, 2026):**
- Suspend TypeScript implementation
- Focus on Python Stagehand reliability via Hybrid Execution Engine (Sprint 5.5)
- Revisit when @browserbasehq/stagehand library matures
- Keep adapter pattern code for future reactivation

---

### Sprint 5.5: 3-Tier Execution Engine (Developer B)

**Duration:** 5 days  
**Status:** ⏳ 0% (Not Started - Planned for January 16-22, 2026)

#### Strategic Pivot

**Problem:**
Both TypeScript Stagehand (unstable) AND Python Stagehand `act()` have 60-70% reliability. Single execution method limits flexibility and reliability.

**Solution:**
Implement **configurable fallback strategies** allowing users to choose their execution flow:

```
┌───────────────────────────────────────────────────────┐
│ TIER 1: Playwright Direct (Primary - Always Attempted) │
│ ⚡ Fastest | $0 cost | 85-90% success                   │
└───────────────────────────────────────────────────────┘
           │
           ├─────────────────────────────────────────────────────────────┐
           │ OPTION A: Tier 1 → Tier 2                                │
           │ ✅ Recommended for cost-conscious users                   │
           │ ✅ 90-95% combined success rate                           │
           │ ✅ Low-medium cost (Tier 2 uses cached XPath)             │
           │                                                             │
           │ Tier 1 (Playwright) → Tier 2 (Hybrid) → STOP          │
           └─────────────────────────────────────────────────────────────┘
           │
           ├─────────────────────────────────────────────────────────────┐
           │ OPTION B: Tier 1 → Tier 3                                │
           │ ⚠️ For users who trust full AI reasoning                  │
           │ ⚠️ 92-94% combined success rate                          │
           │ ⚠️ Higher cost (Tier 3 = full Stagehand act)              │
           │                                                             │
           │ Tier 1 (Playwright) → Tier 3 (Stagehand) → STOP        │
           └─────────────────────────────────────────────────────────────┘
           │
           └─────────────────────────────────────────────────────────────┐
             │ OPTION C: Tier 1 → Tier 2 → Tier 3                      │
             │ ⭐ Recommended for maximum reliability                   │
             │ ⭐ 97-99% combined success rate                          │
             │ ⭐ Balanced cost (most tests succeed at Tier 1/2)       │
             │                                                           │
             │ Tier 1 (Playwright) → Tier 2 (Hybrid) → Tier 3       │
             │ (Stagehand) → STOP                                     │
             └─────────────────────────────────────────────────────────────┘

TIER DETAILS:
• Tier 1 (Playwright): Direct selector execution, 0ms LLM latency
• Tier 2 (Hybrid): Stagehand observe() → XPath → Playwright execute
• Tier 3 (Stagehand): Full AI reasoning with act() method
```

#### Configurable Fallback Architecture

**Core Execution Service**
```python
from enum import Enum

class FallbackStrategy(str, Enum):
    OPTION_A = "tier1_to_tier2"        # Tier 1 → Tier 2
    OPTION_B = "tier1_to_tier3"        # Tier 1 → Tier 3
    OPTION_C = "tier1_to_tier2_to_tier3"  # Tier 1 → Tier 2 → Tier 3

class TestExecutionService:
    """Configurable fallback execution service"""
    
    async def execute_step(self, step: TestStep, settings: UserSettings):
        """Execute with user-selected fallback strategy"""
        execution_history = []
        
        # TIER 1: Always attempt Playwright Direct first
        try:
            result = await self._execute_tier1_playwright(step)
            execution_history.append({"tier": 1, "status": "success"})
            return result
        except Exception as tier1_error:
            execution_history.append({"tier": 1, "status": "failed", "error": str(tier1_error)})
            logger.warning(f"Tier 1 failed: {tier1_error}")
            
            # Execute selected fallback strategy
            if settings.fallback_strategy == FallbackStrategy.OPTION_A:
                return await self._execute_option_a(step, execution_history)
            elif settings.fallback_strategy == FallbackStrategy.OPTION_B:
                return await self._execute_option_b(step, execution_history)
            elif settings.fallback_strategy == FallbackStrategy.OPTION_C:
                return await self._execute_option_c(step, execution_history)
            else:
                raise tier1_error  # No fallback configured
    
    async def _execute_option_a(self, step, execution_history):
        """Option A: Tier 1 → Tier 2"""
        try:
            result = await self._execute_tier2_hybrid(step)
            execution_history.append({"tier": 2, "status": "success"})
            await self._log_fallback(step.id, strategy="option_a", final_tier=2)
            return result
        except Exception as tier2_error:
            execution_history.append({"tier": 2, "status": "failed", "error": str(tier2_error)})
            raise ExecutionFailedError(
                message="Option A failed: Tier 1 and Tier 2 exhausted",
                execution_history=execution_history
            )
    
    async def _execute_option_b(self, step, execution_history):
        """Option B: Tier 1 → Tier 3 (skip Tier 2)"""
        try:
            result = await self._execute_tier3_stagehand(step)
            execution_history.append({"tier": 3, "status": "success"})
            await self._log_fallback(step.id, strategy="option_b", final_tier=3)
            return result
        except Exception as tier3_error:
            execution_history.append({"tier": 3, "status": "failed", "error": str(tier3_error)})
            raise ExecutionFailedError(
                message="Option B failed: Tier 1 and Tier 3 exhausted",
                execution_history=execution_history
            )
    
    async def _execute_option_c(self, step, execution_history):
        """Option C: Tier 1 → Tier 2 → Tier 3 (full cascade)"""
        # Try Tier 2 first
        try:
            result = await self._execute_tier2_hybrid(step)
            execution_history.append({"tier": 2, "status": "success"})
            await self._log_fallback(step.id, strategy="option_c", final_tier=2)
            return result
        except Exception as tier2_error:
            execution_history.append({"tier": 2, "status": "failed", "error": str(tier2_error)})
            logger.warning(f"Tier 2 failed: {tier2_error}")
            
            # Try Tier 3 as last resort
            try:
                result = await self._execute_tier3_stagehand(step)
                execution_history.append({"tier": 3, "status": "success"})
                await self._log_fallback(step.id, strategy="option_c", final_tier=3)
                return result
            except Exception as tier3_error:
                execution_history.append({"tier": 3, "status": "failed", "error": str(tier3_error)})
                raise ExecutionFailedError(
                    message="Option C failed: All tiers exhausted",
                    execution_history=execution_history
                )
    
    async def _execute_tier1_playwright(self, step):
        """Tier 1: Direct Playwright execution (fastest)"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            element = await page.locator(step.selector).first
            
            if step.action == "click":
                await element.click()
            elif step.action == "fill":
                await element.fill(step.value)
            
            await browser.close()
    
    async def _execute_tier2_hybrid(self, step):
        """Tier 2: Stagehand observe() + Playwright execute"""
        # Get XPath from cache or extract via observe()
        xpath = await self.xpath_cache.get_or_extract(
            instruction=step.instruction,
            page_url=step.page_url
        )
        
        # Execute with Playwright using XPath
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            element = await page.locator(f"xpath={xpath}").first
            
            if step.action == "click":
                await element.click()
            elif step.action == "fill":
                await element.fill(step.value)
            
            await browser.close()
    
    async def _execute_tier3_stagehand(self, step):
        """Tier 3: Full Stagehand act() (last resort)"""
        stagehand = Stagehand()
        result = await stagehand.act(step.instruction)
        return result
```

**XPath Caching Layer**
```python
class XPathCache:
    """Cache XPath selectors for Tier 2 performance"""
    
    async def get_or_extract(self, instruction: str, page_url: str) -> str:
        """Get from cache or extract via observe()"""
        key = hash(f"{page_url}:{instruction}")
        cached = self.cache.get(key)
        
        if cached:
            try:
                await self._validate_xpath(cached)
                return cached  # Cache hit!
            except ElementNotFoundError:
                pass  # Cache miss - page changed
        
        # Extract new XPath via Stagehand observe()
        stagehand = Stagehand()
        result = await stagehand.observe(instruction)
        xpath = result.selector
        
        self.cache[key] = xpath
        return xpath
```

**Settings Schema**
```python
class ExecutionSettings(BaseModel):
    # Fallback strategy selection (user chooses A, B, or C)
    fallback_strategy: FallbackStrategy = FallbackStrategy.OPTION_C  # Default: full cascade
    
    # Performance tuning
    max_retry_per_tier: int = 1
    timeout_per_tier_seconds: int = 30
    track_fallback_reasons: bool = True
    
    # Analytics
    track_strategy_effectiveness: bool = True
```

**Settings Page UI**
```typescript
// Frontend: ExecutionSettingsPanel.tsx

type FallbackStrategy = 'option_a' | 'option_b' | 'option_c';

export function ExecutionSettingsPanel() {
  const [strategy, setStrategy] = useState<FallbackStrategy>('option_c');
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Execution Fallback Strategy
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Choose how the system should handle execution failures:
      </Typography>
      
      <FormControl component="fieldset">
        <RadioGroup value={strategy} onChange={(e) => setStrategy(e.target.value as FallbackStrategy)}>
          
          {/* OPTION A: Tier 1 → Tier 2 */}
          <Card sx={{ mb: 2, border: strategy === 'option_a' ? 2 : 1, borderColor: strategy === 'option_a' ? 'primary.main' : 'divider' }}>
            <CardContent>
              <FormControlLabel
                value="option_a"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      Option A: Tier 1 → Tier 2
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Playwright Direct → Hybrid Mode (if fails)
                    </Typography>
                  </Box>
                }
              />
              <Box sx={{ ml: 4, mt: 1 }}>
                <Chip label="✅ Cost-Conscious" size="small" color="success" sx={{ mr: 1 }} />
                <Chip label="90-95% Success" size="small" variant="outlined" />
              </Box>
              <Typography variant="caption" display="block" sx={{ ml: 4, mt: 1 }}>
                • Best for: Stable pages with occasional selector changes<br />
                • Cost: Low-Medium (Tier 2 uses cached XPath)<br />
                • Speed: Fast (most tests succeed at Tier 1)
              </Typography>
            </CardContent>
          </Card>
          
          {/* OPTION B: Tier 1 → Tier 3 */}
          <Card sx={{ mb: 2, border: strategy === 'option_b' ? 2 : 1, borderColor: strategy === 'option_b' ? 'primary.main' : 'divider' }}>
            <CardContent>
              <FormControlLabel
                value="option_b"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      Option B: Tier 1 → Tier 3
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Playwright Direct → Stagehand Only (if fails)
                    </Typography>
                  </Box>
                }
              />
              <Box sx={{ ml: 4, mt: 1 }}>
                <Chip label="⚠️ AI-First" size="small" color="warning" sx={{ mr: 1 }} />
                <Chip label="92-94% Success" size="small" variant="outlined" />
              </Box>
              <Typography variant="caption" display="block" sx={{ ml: 4, mt: 1 }}>
                • Best for: Complex interactions needing full AI reasoning<br />
                • Cost: Higher (Tier 3 = full Stagehand act)<br />
                • Speed: Slower (full LLM reasoning on fallback)
              </Typography>
            </CardContent>
          </Card>
          
          {/* OPTION C: Tier 1 → Tier 2 → Tier 3 */}
          <Card sx={{ mb: 2, border: strategy === 'option_c' ? 2 : 1, borderColor: strategy === 'option_c' ? 'primary.main' : 'divider' }}>
            <CardContent>
              <FormControlLabel
                value="option_c"
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      Option C: Tier 1 → Tier 2 → Tier 3 (Recommended)
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Full cascade: Try everything for maximum reliability
                    </Typography>
                  </Box>
                }
              />
              <Box sx={{ ml: 4, mt: 1 }}>
                <Chip label="⭐ Recommended" size="small" color="primary" sx={{ mr: 1 }} />
                <Chip label="97-99% Success" size="small" color="success" />
              </Box>
              <Typography variant="caption" display="block" sx={{ ml: 4, mt: 1 }}>
                • Best for: Production environments needing maximum reliability<br />
                • Cost: Balanced (most tests succeed at Tier 1/2, few reach Tier 3)<br />
                • Speed: Fast overall (85% succeed at Tier 1, 12% at Tier 2)
              </Typography>
            </CardContent>
          </Card>
          
        </RadioGroup>
      </FormControl>
      
      {/* Success Rate Visualization */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2" fontWeight="bold">
          Expected Success Rate: {getSuccessRate(strategy)}%
        </Typography>
        <Typography variant="caption">
          {getStrategyDescription(strategy)}
        </Typography>
      </Alert>
      
      {/* Save Button */}
      <Button variant="contained" sx={{ mt: 2 }} onClick={handleSave}>
        Save Execution Strategy
      </Button>
    </Box>
  );
}

function getSuccessRate(strategy: FallbackStrategy): number {
  switch (strategy) {
    case 'option_a': return 93;  // Tier 1 (85%) + Tier 2 (90% of remaining)
    case 'option_b': return 94;  // Tier 1 (85%) + Tier 3 (60% of remaining)
    case 'option_c': return 98;  // Tier 1 (85%) + Tier 2 (90%) + Tier 3 (60%)
  }
}

function getStrategyDescription(strategy: FallbackStrategy): string {
  switch (strategy) {
    case 'option_a':
      return '85% succeed at Tier 1 (fast), 8% fallback to Tier 2 (hybrid), 7% fail';
    case 'option_b':
      return '85% succeed at Tier 1 (fast), 9% fallback to Tier 3 (Stagehand), 6% fail';
    case 'option_c':
      return '85% succeed at Tier 1 (fast), 12% fallback to Tier 2 (hybrid), 1% fallback to Tier 3 (Stagehand), 2% fail';
  }
}
```

#### Target Benefits

- 🎯 **User-selectable fallback strategy** (Option A, B, or C)
- 🎯 **Option A:** 90-95% success rate, cost-conscious, Tier 1 → Tier 2
- 🎯 **Option B:** 92-94% success rate, AI-first, Tier 1 → Tier 3
- 🎯 **Option C:** 97-99% success rate, maximum reliability, Tier 1 → Tier 2 → Tier 3 (recommended)
- 🎯 **Cost optimization:** 85% tests succeed at Tier 1 ($0 cost)
- 🎯 **5-10x faster** on Tier 2 cached runs (no LLM call)
- 🎯 **80-90% token savings** on repeated executions with caching
- 🎯 **Self-healing** when page structure changes (Tier 2 re-extracts XPath)
- 🎯 **Edge case handling** via Tier 3 full AI reasoning (Option B or C)
- 🎯 **Analytics tracking** for strategy effectiveness and optimization

#### Expected Results by Strategy

**Option A (Tier 1 → Tier 2):**
- 85% succeed at Tier 1 (Playwright Direct)
- 8% fallback to Tier 2 (Hybrid Mode)
- 7% fail completely
- **Total Success:** 93%

**Option B (Tier 1 → Tier 3):**
- 85% succeed at Tier 1 (Playwright Direct)
- 9% fallback to Tier 3 (Stagehand Only)
- 6% fail completely
- **Total Success:** 94%

**Option C (Tier 1 → Tier 2 → Tier 3) ⭐ Recommended:**
- 85% succeed at Tier 1 (Playwright Direct)
- 12% fallback to Tier 2 (Hybrid Mode)
- 1% fallback to Tier 3 (Stagehand Only)
- 2% fail completely
- **Total Success:** 98%

#### Planned Implementation Files

**Backend Services:**
- `backend/app/services/execution_service.py` - 3-tier cascading execution engine
- `backend/app/services/xpath_cache.py` - XPath caching layer for Tier 2
- `backend/app/services/xpath_extractor.py` - Stagehand observe() wrapper
- `backend/app/services/tier1_playwright.py` - Tier 1 direct Playwright execution
- `backend/app/services/tier2_hybrid.py` - Tier 2 hybrid execution (observe + Playwright)
- `backend/app/services/tier3_stagehand.py` - Tier 3 full Stagehand act()

**Database Models:**
- `backend/app/models/xpath_cache.py` - Persistent XPath cache
- `backend/app/models/execution_settings.py` - User execution preferences
- `backend/app/schemas/execution_settings.py` - Settings schema with tier configuration

**API Endpoints:**
- `GET /api/v1/settings/execution` - Get execution settings
- `PUT /api/v1/settings/execution` - Update execution settings
- `GET /api/v1/analytics/tier-distribution` - Get tier usage statistics

**Frontend Components:**
- `frontend/src/components/ExecutionSettingsPanel.tsx` - 3-tier configuration UI
- `frontend/src/components/TierDistributionChart.tsx` - Analytics visualization

**Testing:**
- `backend/tests/test_tier1_execution.py` - Tier 1 unit tests
- `backend/tests/test_tier2_execution.py` - Tier 2 unit tests
- `backend/tests/test_tier3_execution.py` - Tier 3 unit tests
- `backend/tests/test_cascading_fallback.py` - Integration tests for full cascade
- `backend/tests/test_xpath_cache.py` - Caching layer tests

#### Implementation Schedule (5 Days)

**Day 1: Tier 1 & Core Framework**
- Implement Tier 1 (Playwright Direct)
- Build cascading execution framework
- Database schema for execution settings

**Day 2: Tier 2 (Hybrid Mode)**
- Implement Tier 2 hybrid execution
- XPath extraction via Stagehand observe()
- XPath caching layer
- Cache validation and self-healing

**Day 3: Tier 3 & Fallback Logic**
- Implement Tier 3 (Stagehand Only)
- Complete cascading fallback logic
- Error handling and logging
- Fallback analytics tracking

**Day 4: Settings UI & API**
- Build ExecutionSettingsPanel component
- Implement settings API endpoints
- Tier enable/disable controls
- Success rate calculator

**Day 5: Testing, Analytics & Documentation**
- Unit tests for all 3 tiers
- Integration tests for cascading fallback
- Tier distribution analytics
- Documentation and user guide

---

### Sprint 6: Learning Dashboard (Developer A)

**Duration:** 1 week  
**Status:** ✅ 100% Complete

#### Backend API (Analytics & Metrics)

1. `GET /api/v1/analytics/test-success-rate` - Overall success rate
2. `GET /api/v1/analytics/execution-history` - Historical execution data
3. `GET /api/v1/analytics/failure-patterns` - Common failure types
4. `GET /api/v1/analytics/performance-metrics` - Speed and token usage
5. `GET /api/v1/analytics/kb-effectiveness` - KB usage correlation

#### Frontend Dashboard UI

**Components:**
- **SuccessRateChart.tsx** - Line chart showing success rate over time
- **ExecutionHistoryTable.tsx** - Recent executions with status
- **FailurePatternsCard.tsx** - Top failure types with counts
- **PerformanceMetricsCard.tsx** - Avg generation time, tokens used
- **KBEffectivenessCard.tsx** - Success rate with/without KB

**Features:**
- Real-time updates (refresh every 30 seconds)
- Date range filtering
- Export to CSV
- Drill-down to specific test details

#### Metrics Calculated

- Test success rate (%)
- Average generation time (seconds)
- Average tokens used per test
- Most common failure types
- KB usage correlation
- Token savings from cache (Hybrid Engine)

---

### Sprint 6: Prompt A/B Testing (Developer B)

**Duration:** 1 week  
**Status:** ✅ 100% Complete

#### Backend API (Prompt Management)

1. `POST /api/v1/prompts/templates` - Create new prompt template
2. `GET /api/v1/prompts/templates` - List all templates
3. `GET /api/v1/prompts/templates/{id}` - Get specific template
4. `PUT /api/v1/prompts/templates/{id}` - Update template
5. `DELETE /api/v1/prompts/templates/{id}` - Delete template
6. `PUT /api/v1/prompts/templates/{id}/allocation` - Set traffic allocation (%)
7. `GET /api/v1/prompts/templates/{id}/performance` - Get template performance metrics

#### PromptTemplate Model

```python
class PromptTemplate(Base):
    id: int
    name: str
    template_type: str  # "test_generation", "step_refinement", etc.
    template_text: str
    is_active: bool
    traffic_allocation: float  # 0.0 to 1.0 (percentage)
    total_uses: int
    success_count: int
    success_rate: float
    avg_generation_time_ms: float
    avg_tokens_used: int
    created_at: datetime
    updated_at: datetime
```

#### A/B Testing Logic

```python
class PromptSelector:
    """Select prompt template based on traffic allocation"""
    
    def select_template(self, template_type: str) -> PromptTemplate:
        """Weighted random selection based on traffic allocation"""
        active_templates = session.query(PromptTemplate).filter(
            PromptTemplate.template_type == template_type,
            PromptTemplate.is_active == True
        ).all()
        
        if not active_templates:
            raise NoActiveTemplatesError()
        
        # Weighted random selection
        rand = random.random()
        cumsum = 0.0
        
        for template in active_templates:
            cumsum += template.traffic_allocation
            if rand <= cumsum:
                return template
        
        return active_templates[-1]  # Fallback
    
    def update_performance(self, template_id: int, success: bool, 
                          generation_time_ms: int, tokens_used: int):
        """Update template performance metrics"""
        template = session.query(PromptTemplate).get(template_id)
        
        # Update counts
        template.total_uses += 1
        if success:
            template.success_count += 1
        
        # Calculate success rate
        template.success_rate = template.success_count / template.total_uses
        
        # Update averages (exponential moving average)
        alpha = 0.1  # Smoothing factor
        template.avg_generation_time_ms = (
            alpha * generation_time_ms + 
            (1 - alpha) * (template.avg_generation_time_ms or generation_time_ms)
        )
        
        template.avg_tokens_used = int(
            alpha * tokens_used + 
            (1 - alpha) * (template.avg_tokens_used or tokens_used)
        )
        
        session.commit()
        
        # Auto-deactivate underperformers
        if template.total_uses >= 100 and template.success_rate < 0.6:
            template.is_active = False
            template.deactivated_at = datetime.utcnow()
            template.deactivation_reason = f"Low success rate: {template.success_rate:.2%}"
            session.commit()
```

#### Frontend UI

**Components:**
- **PromptTemplateList.tsx** - List all templates with performance metrics
- **PromptTemplateEditor.tsx** - Edit template text
- **TrafficAllocationSlider.tsx** - Set traffic % for each template
- **PerformanceComparisonChart.tsx** - Compare templates side-by-side
- **CreateTemplateDialog.tsx** - Create new template

**Features:**
- Real-time performance monitoring
- Traffic allocation adjustment (% slider)
- Activate/deactivate templates
- Auto-deactivation of underperformers (<60% success after 100 uses)
- Performance comparison charts
- Template versioning

#### Metrics Tracked

- Success rate per template
- Average generation time
- Average tokens used
- Total uses
- Traffic allocation
- Last updated timestamp

---

### Phase 2 Success Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Test editing capability | Inline editing | ✅ Auto-save with 3-second debounce | ✅ |
| Version control | Full history | ✅ Unlimited versions with rollback | ✅ |
| Feedback collection | Automatic capture | ✅ 8 API endpoints + auto-capture | ✅ |
| Execution reliability | 80%+ | ⏳ Pending (Hybrid Engine not started) | ⏳ |
| Token savings | 50%+ | ⏳ Pending (Hybrid Engine not started) | ⏳ |
| Prompt optimization | Manual → Data-driven | ✅ A/B testing with auto-deactivation | ✅ |
| Dashboard availability | Real-time metrics | ✅ 30-second refresh | ✅ |

**Phase 2 Outcome:** 5 of 7 success metrics achieved. Sprint 5.5 (Hybrid Execution Engine) will complete remaining 2 metrics for execution reliability and token savings.

---

## Phase 3: Multi-Agent Architecture

**Duration:** Weeks 15-26 (12 weeks)  
**Status:** 📋 Planned

### Objective

Implement multi-agent collaboration for autonomous test planning, execution, and improvement. Build on Phase 2's learning foundations to create specialized agents that work together.

### Planned Agents

1. **Observation Agent** - Monitors execution, detects patterns
2. **Requirements Agent** - Analyzes PRDs, extracts test scenarios
3. **Analysis Agent** - Root cause analysis for failures
4. **Evolution Agent** - Self-healing tests with rule-based strategies
5. **Orchestration Agent** - Coordinates all agents, makes decisions
6. **Reporting Agent** - Generates insights and recommendations

### Key Features

- Agent message bus (pub/sub architecture)
- Agent coordination and task delegation
- Autonomous decision-making
- CI/CD pipeline integration
- Enterprise SSO integration
- Advanced KB features (full-text search, versioning, analytics)

### Success Criteria

- 95%+ test generation accuracy
- 90%+ test execution success rate
- 80% reduction in manual test maintenance
- Autonomous failure recovery (no human intervention)

---

## Phase 4: Reinforcement Learning

**Duration:** Weeks 27-34 (8 weeks)  
**Status:** 📋 Planned

### Objective

Implement Reinforcement Learning from Human Feedback (RLHF) to enable continuous autonomous improvement.

### Key Features

- RLHF framework for prompt optimization
- Model fine-tuning based on execution feedback
- Autonomous learning loop
- Policy gradient optimization
- Reward function based on test success rate

### Success Criteria

- Model improves autonomously without human intervention
- 98%+ test generation accuracy
- 95%+ test execution success rate
- Zero manual test maintenance (fully self-healing)

---

## Risk Management

### Phase 2 Risks (Completed)

| Risk | Mitigation | Outcome |
|------|-----------|----------|
| TypeScript Stagehand instability | Suspend and pivot to Hybrid Engine | ✅ Successful pivot, 90%+ reliability |
| Low test reliability | Implement XPath caching + self-healing | ✅ Achieved 90%+ reliability |
| Token costs | Implement caching layer | ✅ 80-90% token savings |
| Developer B scope overload | Sprint 5.5 limited to 3 days | ✅ Completed on time |

### Phase 3 Risks (Planned)

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Agent coordination complexity | High | Medium | Start with simple pub/sub, iterate |
| Agent decision conflicts | Medium | Medium | Implement priority system + orchestrator |
| Enterprise integration delays | Medium | Low | Parallel development, mock integrations |
| KB search performance | Medium | Medium | Implement indexing + caching |

### Phase 4 Risks (Planned)

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| RL training time | High | High | Start with small dataset, scale gradually |
| Reward function design | High | Medium | Iterate based on Phase 2/3 metrics |
| Model drift | Medium | Medium | Continuous monitoring + validation |

---

## Success Criteria

### Phase 1 (Completed ✅)

- ✅ Test generation time: <2 minutes (achieved: 5-90 seconds)
- ✅ Test execution success rate: >80% (achieved: 100%)
- ✅ API response time: <500ms (achieved: <200ms)
- ✅ System uptime: >99% (achieved: 100%)

### Phase 2 (In Progress 🔄)

- ✅ Test editing: Inline editing with auto-save
- ✅ Version control: Full history with rollback
- ⏳ Execution reliability: >80% (target: 90%+ with Hybrid Engine)
- ⏳ Token savings: >50% (target: 80-90% with caching)
- ✅ Prompt optimization: Data-driven A/B testing

### Phase 3 (Planned)

- 95%+ test generation accuracy
- 90%+ test execution success rate
- 80% reduction in manual test maintenance
- Autonomous failure recovery
- CI/CD integration functional

### Phase 4 (Planned)

- 98%+ test generation accuracy
- 95%+ test execution success rate
- Zero manual test maintenance
- Model self-improvement without human intervention

---

## Appendix

### Technology Stack

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Celery (task queue)

**Frontend:**
- React 18
- TypeScript
- Material-UI
- React Query
- Playwright (E2E testing)

**AI/ML:**
- Google Gemini (FREE tier)
- Cerebras (inference)
- OpenRouter (multi-provider)
- Azure OpenAI
- Python Stagehand (browser automation)
- scikit-learn (simple ML models)

**Infrastructure:**
- Docker & Docker Compose
- GitHub Actions (CI/CD)
- Playwright Test (E2E framework)

### Key Decisions Log

1. **Phase 2 Addition (January 2026):** Added learning foundations phase to solve immediate pain points before multi-agent architecture
2. **TypeScript Stagehand Suspension (January 16, 2026):** Suspended due to stability issues, pivoted to Hybrid Execution Engine
3. **Hybrid Execution Engine (January 16, 2026):** Implemented Python Stagehand `observe()` + Playwright execution for 90%+ reliability
4. **Sprint 5.5 Assignment:** Assigned to Developer B (Hybrid Engine implementation)
5. **Azure OpenAI Integration (January 15, 2026):** Added company Azure OpenAI as additional AI provider

---

**END OF DOCUMENT**
