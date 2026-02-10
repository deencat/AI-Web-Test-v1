# How to Pass Login Credentials for Test Execution

## Overview

When testing flows that require authentication (like purchase flows, account access, etc.), you can provide login credentials via environment variables. The system will automatically include login steps in the generated test steps.

## Usage

### Method 1: Environment Variables (Recommended)

Set both `LOGIN_EMAIL` and `LOGIN_PASSWORD` environment variables before running the test:

**PowerShell:**
```powershell
# Set login credentials
$env:LOGIN_EMAIL = "pmo.andrewchan-010@gmail.com"
$env:LOGIN_PASSWORD = "cA8mn49"

# Set user instruction (optional)
$env:USER_INSTRUCTION = "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"

# Run test
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

**PowerShell (One Line):**
```powershell
$env:LOGIN_EMAIL = "pmo.andrewchan-010@gmail.com"; $env:LOGIN_PASSWORD = "cA8mn49"; $env:USER_INSTRUCTION = "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"; python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

**Bash/Linux:**
```bash
export LOGIN_EMAIL="pmo.andrewchan-010@gmail.com"
export LOGIN_PASSWORD="cA8mn49"
export USER_INSTRUCTION="Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"
python -u -m pytest tests/integration/test_four_agent_e2e_real.py -v -s
```

**Windows CMD:**
```cmd
set LOGIN_EMAIL=pmo.andrewchan-010@gmail.com
set LOGIN_PASSWORD=cA8mn49
set USER_INSTRUCTION=Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term
python -u -m pytest tests\integration\test_four_agent_e2e_real.py -v -s
```

### Method 2: Using .env File (For Security)

For better security, you can store credentials in a `.env` file:

**Create `.env` file in `backend/` directory:**
```env
LOGIN_EMAIL=pmo.andrewchan-010@gmail.com
LOGIN_PASSWORD=cA8mn49
USER_INSTRUCTION=Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term
```

**Note:** Make sure `.env` is in `.gitignore` to avoid committing credentials!

The test file already loads environment variables from `.env` using `load_dotenv()`, so credentials will be automatically loaded.

## How It Works

### 1. Credentials Passed to EvolutionAgent

When you set `LOGIN_EMAIL` and `LOGIN_PASSWORD`, they are:
- Extracted from environment variables
- Passed to EvolutionAgent in the task payload
- Used to enhance the LLM prompt with login instructions

### 2. Login Steps Generated

The LLM will automatically:
- **Detect if login is required** for the flow (e.g., purchase flow)
- **Generate login steps BEFORE** the main flow steps
- **Use the provided credentials** in the login steps
- **Verify login success** before proceeding

### 3. Example Generated Steps

**Without Login Credentials:**
```
1. Navigate to plan page
2. Select plan '5G寬頻數據無限任用'
3. Select contract term '48個月'
4. Click '立即登記'
...
```

**With Login Credentials:**
```
1. Navigate to login page
2. Enter email: pmo.andrewchan-010@gmail.com
3. Enter password: cA8mn49
4. Click Login button
5. Verify successful login (e.g., URL changes, user menu appears)
6. Navigate to plan page
7. Select plan '5G寬頻數據無限任用'
8. Select contract term '48個月'
9. Click '立即登記'
...
```

## Expected Output

When you run the test with login credentials, you'll see:

```
[INFO] Login credentials provided: email='pmo.andrewc...'
        Test steps will include login before purchase flow

Step 4: Generating test steps with EvolutionAgent...
        EvolutionAgent: Login credentials provided (email: pmo.andrewc...)
```

## Security Best Practices

### ✅ DO:
- Use environment variables for credentials
- Store credentials in `.env` file (and add to `.gitignore`)
- Use different credentials for test vs production
- Mask passwords in logs (system does this automatically)

### ❌ DON'T:
- Hardcode credentials in test files
- Commit credentials to version control
- Use production credentials for testing
- Share credentials in logs or documentation

## Troubleshooting

### Issue: Login steps not generated

**Possible causes:**
1. Credentials not set correctly
   - **Solution:** Verify both `LOGIN_EMAIL` and `LOGIN_PASSWORD` are set
   - **Check:** Run `echo $env:LOGIN_EMAIL` in PowerShell to verify

2. LLM didn't detect login requirement
   - **Solution:** Make login requirement explicit in user instruction:
     ```powershell
     $env:USER_INSTRUCTION = "Complete purchase flow for '5G寬頻數據無限任用' plan (requires login)"
     ```

3. Flow doesn't actually require login
   - **Solution:** Check if the website actually requires login for the flow
   - If login is optional, the system may not include it

### Issue: Login steps in wrong order

**Solution:** The system should place login steps before the main flow. If not, the LLM prompt includes explicit instructions to do so. If issues persist, check the generated steps in the log file.

### Issue: Wrong login page URL

**Solution:** The system uses the page context from ObservationAgent. If the login page URL is different, you may need to:
1. Navigate to the login page first in your user instruction
2. Or provide the login page URL in the user instruction

## Examples

### Example 1: Purchase Flow with Login

```powershell
$env:LOGIN_EMAIL = "pmo.andrewchan-010@gmail.com"
$env:LOGIN_PASSWORD = "cA8mn49"
$env:USER_INSTRUCTION = "Complete purchase flow for '5G寬頻數據無限任用' plan with 48個月 contract term"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

**Generated Steps Will Include:**
- Login steps (using provided credentials)
- Plan selection
- Contract term selection
- Registration form
- Payment
- Order confirmation

### Example 2: Account Access Flow

```powershell
$env:LOGIN_EMAIL = "pmo.andrewchan-010@gmail.com"
$env:LOGIN_PASSWORD = "cA8mn49"
$env:USER_INSTRUCTION = "Test account dashboard access"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

**Generated Steps Will Include:**
- Login steps
- Navigation to dashboard
- Verification of dashboard elements

### Example 3: Without Login (Anonymous Flow)

```powershell
# Don't set LOGIN_EMAIL or LOGIN_PASSWORD
$env:USER_INSTRUCTION = "Test plan browsing without login"
python -u -m pytest .\tests\integration\test_four_agent_e2e_real.py -v -s
```

**Generated Steps Will:**
- Skip login steps
- Start directly with the main flow

## Verification

To verify login steps were generated:

1. **Check the log file:**
   ```bash
   grep -A 30 "Test case 1 steps" backend/logs/test_four_agent_e2e_*.log
   ```

2. **Look for login steps:**
   - "Navigate to login page"
   - "Enter email: ..."
   - "Enter password: ..."
   - "Click Login button"
   - "Verify successful login"

3. **Check database:**
   - Query test cases and check if steps include login

## Notes

- **Password Masking:** Passwords are automatically masked in logs (only first 3 characters shown)
- **Both Required:** Both `LOGIN_EMAIL` and `LOGIN_PASSWORD` must be set for login steps to be generated
- **Optional:** If credentials are not provided, the system works normally without login steps
- **Flow Detection:** The system automatically detects if login is needed based on the flow type (purchase, account access, etc.)

