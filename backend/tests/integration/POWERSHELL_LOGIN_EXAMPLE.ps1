# PowerShell Example: Running Test with Login Credentials and User Instruction
# 
# This script demonstrates how to pass login credentials and user instruction
# when running the 4-agent E2E test.

# Set login credentials
$env:LOGIN_EMAIL = "pmo.andrewchan-010@gmail.com"
$env:LOGIN_PASSWORD = "cA8mn49"

# Set user instruction (optional)
$env:USER_INSTRUCTION = "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"

# Run the test
Write-Host "Running test with login credentials..." -ForegroundColor Green
Write-Host "Email: $env:LOGIN_EMAIL" -ForegroundColor Yellow
Write-Host "Password: *** (masked)" -ForegroundColor Yellow
Write-Host "User Instruction: $env:USER_INSTRUCTION" -ForegroundColor Yellow
Write-Host ""

python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py::TestFourAgentE2EReal::test_complete_4_agent_workflow_real -v -s

# Clean up (optional - uncomment to clear credentials after test)
# Remove-Item Env:\LOGIN_EMAIL
# Remove-Item Env:\LOGIN_PASSWORD
# Remove-Item Env:\USER_INSTRUCTION

