# TypeScript Stagehand Test - Three.com.hk 5G Broadband Flow

This standalone test validates the TypeScript `@browserbasehq/stagehand` implementation with a real-world complex subscription flow.

## Purpose

- **Validate TypeScript Stagehand** works with complex multi-step workflows
- **Prototype for Phase 4** - Understand how to build the Node.js microservice
- **Compare with Python** - Validate both implementations handle the same scenario

## Test Scenario

Tests the Three.com.hk 5G Broadband subscription flow (18 steps):
1. Navigate to plan page
2. Scroll to contract period options
3. Select 30 months contract
4. Verify pricing ($135/month discounted from $198)
5. Verify plan details (5G Broadband Wi-Fi 6, Infinite Data)
6. Click Subscribe Now
7-11. Verify "Your Selection" page details
12. Proceed to service plan details
13. Verify payment breakdown ($100)
14. Confirm reviewed details
15. Proceed to login
16. Complete login
17. Select service effective date (3 days from today)
18. Confirm subscription

## Setup

1. **Install Dependencies**:
   ```bash
   cd stagehand-typescript-test
   npm install
   ```

2. **Configure Environment**:
   ```bash
   # Copy example and add your API key
   cp .env.example .env
   
   # Edit .env and add:
   OPENAI_API_KEY=your_key_here
   ```

3. **Run Test**:
   ```bash
   npm test
   ```

## Expected Output

```
╔════════════════════════════════════════════════════════════════════╗
║         TypeScript Stagehand - Three.com.hk 5G Broadband Test     ║
╚════════════════════════════════════════════════════════════════════╝

ℹ️  Initializing TypeScript Stagehand...
✅ Stagehand initialized successfully

======================================================================
  Step 1: Navigate to 5G Broadband plan page
======================================================================
✅ Navigated to: https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc

[... 18 steps ...]

╔════════════════════════════════════════════════════════════════════╗
║                         TEST SUMMARY                               ║
╚════════════════════════════════════════════════════════════════════╝
✅ Test completed successfully in X.XX seconds
ℹ️  TypeScript Stagehand successfully handled complex multi-step flow
ℹ️  All 18 steps executed
ℹ️  Ready for Phase 4 Node.js microservice implementation
```

## Configuration

**Environment Variables** (`.env`):
- `OPENAI_API_KEY` - OpenAI API key (required)
- `ANTHROPIC_API_KEY` - Anthropic API key (optional)
- `MODEL_NAME` - AI model to use (default: `gpt-4o-mini`)
- `TEMPERATURE` - Model temperature (default: `0.7`)
- `MAX_TOKENS` - Max tokens per request (default: `4096`)
- `HEADLESS` - Run browser headless (default: `true`)

## Next Steps

After successful test:
1. Use learnings to build Phase 4 Node.js microservice
2. Implement HTTP API matching TypeScript adapter protocol
3. Integrate with existing Python backend
4. Enable users to switch between Python/TypeScript providers

## Comparison with Python

This test uses the same test case that can be run with Python Stagehand via our adapter pattern. Both implementations should produce similar results, validating our dual-provider approach.
