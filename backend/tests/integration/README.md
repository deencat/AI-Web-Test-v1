# Integration Tests Documentation

## Active Documentation

### User Guides (Keep These)
- **[E2E_REAL_RUN_GUIDE.md](./E2E_REAL_RUN_GUIDE.md)** - How to run the 4-agent E2E real test (env vars, Gmail/OTP, run script)
- **[USER_INSTRUCTION_USAGE.md](./USER_INSTRUCTION_USAGE.md)** - How to use user instruction support
- **[LOGIN_CREDENTIALS_USAGE.md](./LOGIN_CREDENTIALS_USAGE.md)** - How to pass login credentials
- **[HOW_TO_VIEW_TEST_STEPS.md](./HOW_TO_VIEW_TEST_STEPS.md)** - How to view generated test steps

### Technical Documentation (Keep These)
- **[GOAL_AWARE_TEST_GENERATION.md](./GOAL_AWARE_TEST_GENERATION.md)** - Complete solution for goal-aware test generation
- **[GOAL_AWARE_IMPLEMENTATION_SUMMARY.md](./GOAL_AWARE_IMPLEMENTATION_SUMMARY.md)** - Implementation summary for goal-aware features
- **[AUTONOMOUS_TEST_GENERATION_ANALYSIS.md](./AUTONOMOUS_TEST_GENERATION_ANALYSIS.md)** - Analysis of autonomous test generation capabilities
- **[EVOLUTION_AGENT_TEST_GENERATION_EXPLANATION.md](./EVOLUTION_AGENT_TEST_GENERATION_EXPLANATION.md)** - How EvolutionAgent generates test steps

### Example Scripts (Keep These)
- **[POWERSHELL_USER_INSTRUCTION_EXAMPLE.ps1](./POWERSHELL_USER_INSTRUCTION_EXAMPLE.ps1)** - PowerShell example for user instructions
- **[POWERSHELL_LOGIN_EXAMPLE.ps1](./POWERSHELL_LOGIN_EXAMPLE.ps1)** - PowerShell example for login credentials
- **[view_test_steps.py](./view_test_steps.py)** - Python script to view test steps from database

## Test Files

- **test_four_agent_e2e_real.py** - Main 4-agent E2E test with real execution
- **test_three_agent_workflow.py** - 3-agent workflow test
- **test_four_agent_workflow.py** - 4-agent workflow test
- **test_three_hk_real_page.py** - Three HK specific test
- **test_user_instruction_support.py** - User instruction support test

## Quick Start

### Run Test with User Instruction
```powershell
$env:USER_INSTRUCTION = "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

### Run 4-Agent E2E Real Test
See **[E2E_REAL_RUN_GUIDE.md](./E2E_REAL_RUN_GUIDE.md)** for required env vars (Azure OpenAI, optional Gmail/OTP) and Gmail "+" alias behaviour.

```powershell
# From backend with venv active (set AZURE_OPENAI_* first)
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s
# Or use helper script:
.\scripts\run_e2e_real.ps1
```

### Run Test with Login Credentials
```powershell
$env:LOGIN_EMAIL = "your-email@example.com"
$env:LOGIN_PASSWORD = "your-password"
$env:USER_INSTRUCTION = "Complete purchase flow for '5G寬頻數據無限任用' plan"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

## Documentation Status

All active documentation is up-to-date and reflects the current implementation. Outdated debug/analysis documents have been removed.

