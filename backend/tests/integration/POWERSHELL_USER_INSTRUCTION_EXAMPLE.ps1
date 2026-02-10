# PowerShell Example: How to Set USER_INSTRUCTION and Run Test
# 
# Copy and paste these commands into your PowerShell terminal

# Method 1: Set variable, then run test (two separate commands)
$env:USER_INSTRUCTION = "Test purchase flow for '5G寬頻數據無限任用' plan"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s

# Method 2: One line (separate commands with semicolon)
$env:USER_INSTRUCTION = "Test purchase flow for '5G寬頻數據無限任用' plan"; python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s

# Method 3: Different instruction examples
$env:USER_INSTRUCTION = "Test user login flow"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s

$env:USER_INSTRUCTION = "Test clicking the 立即登記 button"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s

# To clear the variable (run test without instruction):
$env:USER_INSTRUCTION = ""
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s

# Or remove it entirely:
Remove-Item Env:\USER_INSTRUCTION
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s

