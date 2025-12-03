"""
Advanced test for three.com.hk - 5G Broadba        "Find and click the checkbox that says 'I confirm that I have reviewed details and agree to the'",
        "Find and click the 'Subscribe Now' button to proceed to the next page",
        "Wait 3 seconds for the page to load",
        "Find the Email Address input field and type 'pmo.andrewchan+010@gmail.com'",
        "Find and click the 'Login' button to proceed to password screen",
        "Wait 3 seconds for the password field to appear",
        "Find the Password input field and type 'cA8mn49&'",
        "Find and click the 'Login' button to submit the credentials and authenticate",
        "Wait 5 seconds for authentication to complete and next page to load",tion.
Tests navigation, element identification, clicking, and form interaction.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def print_header(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)

def print_section(text):
    print(f"\n{text}")
    print("-" * 70)

print_header("🌐 Advanced Real Website Test - three.com.hk 5G Broadband")

# Step 1: Login
print_section("[Step 1] Authentication")
response = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "admin123"})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Logged in successfully")

# Step 2: Create test case for 5G Broadband page
print_section("[Step 2] Create Test Case")
test_data = {
    "title": "Three.com.hk - 5G Broadband Complete Subscription Flow",
    "description": "Complete end-to-end flow: select plan, verify details, proceed through checkout pages with full validation, login and select service date",
    "test_type": "e2e",
    "priority": "high",
    "steps": [
        "Scroll down the page slowly to see all the 5G Broadband plans with contract period options",
        "Find and click the button that says exactly '30 months' under 'Please select contract period' - make sure to click directly on the text '30 months'",
        "Verify that the '30 months' button now has a purple/colored border around it showing it is selected",
        "Find and click the 'Subscribe Now' button that appears under the selected plan",
        "Wait for the customer notice popup to appear",
        "Find and click the checkbox that says 'Don't show this again' at the bottom left of the notice",
        "Find and click the 'X' button to close the customer notice popup",
        "Verify that the popup is closed and the subscription form is visible",
        "Verify page shows: plan price $135/month, original price $198 strikethrough, FREE 6-month promotion, 5G Broadband Wi-Fi 6 Service Plan name, Infinite 5G Data, Waived $28 Admin Fee, and 30 months contract",
        "Find and click the 'Next' button to proceed to the next page",
        "Wait for the Service Plan Details section to load and verify it shows: 5G Broadband Wi-Fi 6 Service Plan, average monthly fee $135/month, waived admin fee, waived Wi-Fi 6 5G Router Rental Fee, and 30 months contract",
        "Verify the payment breakdown shows: Prepayment SIM Card Fee $100, Deposit $0, First Month Payment $0, and Total Amount Due $100",
        "Find and click the checkbox that says 'I confirm that I have reviewed details and agree to the'",
        "Find and click the 'Subscribe Now' button to proceed to the next page",
        "Wait 3 seconds for the page to load",
        "Click the 'Login' button to open the login form",
        "Wait 2 seconds for the login form to appear",
        "Find the email input field and type 'pmo.andrewchan+010@gmail.com'",
        "Click the 'Login' button to proceed to password screen",
        "Wait 2 seconds for the password field to appear",
        "Find the password input field and type 'cA8mn49&'",
        "Click the 'Login' button to submit credentials",
        "Wait 5 seconds for authentication to complete",
        "Find the service effective date field and select a date 3 days from today",
        "Click the 'Confirm' button to proceed to the next step"
    ],
    "expected_result": "Successfully complete full subscription flow including login and service date selection",
    "test_data": {
        "base_url": "https://web.three.com.hk/5gbroadband/plan-hsbc-en.html",
        "contract_period": "30 Months",
        "monthly_price": "$135",
        "original_price": "$198",
        "plan_name": "5G Broadband Wi-Fi 6 Service Plan",
        "data_plan": "Infinite 5G Data",
        "admin_fee": "Waived",
        "router_fee": "Waived",
        "free_months": "6 months",
        "sim_card_fee": "$100",
        "deposit": "$0",
        "first_month": "$0",
        "total_due": "$100",
        "email": "pmo.andrewchan+010@gmail.com",
        "password": "cA8mn49&",
        "service_date_offset": "3 days"
    }
}

response = requests.post(f"{BASE_URL}/tests", headers=headers, json=test_data)
if response.status_code != 201:
    print(f"❌ Failed to create test: {response.status_code}")
    print(response.text)
    exit(1)

test_id = response.json()["id"]
print(f"✅ Created test case: ID {test_id}")
print(f"   Title: {test_data['title']}")
print(f"   Steps: {len(test_data['steps'])} steps")

# Step 3: Execute test
print_section("[Step 3] Execute Test")
run_data = {
    "browser": "chromium",
    "environment": "production",
    "base_url": "https://web.three.com.hk/5gbroadband/plan-hsbc-en.html",
    "triggered_by": "manual"
}

print(f"🌐 Target: https://web.three.com.hk/5gbroadband/plan-hsbc-en.html")
print(f"🎯 Action: Select 30 months plan and click Subscribe Now")
print(f"🖥️  Browser: Chromium (headless)")

response = requests.post(f"{BASE_URL}/executions/tests/{test_id}/run", headers=headers, json=run_data)
if response.status_code != 201:
    print(f"❌ Failed to start execution: {response.status_code}")
    print(response.text)
    exit(1)

execution_id = response.json()["id"]
print(f"✅ Execution started: ID {execution_id}")
print(f"⏳ Test running in background...")

# Step 4: Monitor execution
print_section("[Step 4] Monitor Execution Progress")
print(f"📊 Polling every 3 seconds (max 5 minutes)...")
print()

start_time = time.time()
last_status = None
last_step_count = 0

for i in range(100):  # 100 * 3 = 300 seconds (5 minutes) max
    elapsed = int(time.time() - start_time)
    
    response = requests.get(f"{BASE_URL}/executions/{execution_id}", headers=headers)
    if response.status_code != 200:
        print(f"⚠️  Failed to get execution status: {response.status_code}")
        time.sleep(3)
        continue
    
    data = response.json()
    status = data.get("status", "unknown")
    result = data.get("result")
    steps = data.get("steps", [])
    passed_steps = data.get("passed_steps", 0)
    failed_steps = data.get("failed_steps", 0)
    total_steps = passed_steps + failed_steps
    
    # Show progress
    if status != last_status or len(steps) != last_step_count:
        print(f"[{elapsed}s] Status: {status}", end="")
        if result:
            print(f" | Result: {result}", end="")
        if total_steps > 0:
            print(f" | Progress: {passed_steps}/{total_steps} passed", end="")
        print()
        last_status = status
        last_step_count = len(steps)
    
    # Check if completed
    if status in ["completed", "failed"]:
        print()
        print("-" * 70)
        print(f"\n{'✅' if status == 'completed' else '❌'} Execution {status.upper()}!")
        print(f"\n📊 Final Results:")
        print(f"   Status: {status}")
        print(f"   Result: {result or 'N/A'}")
        print(f"   Duration: {data.get('duration_seconds', 0):.2f}s")
        print(f"   Total Steps: {len(steps)}")
        print(f"   Passed: {passed_steps}")
        print(f"   Failed: {failed_steps}")
        
        if steps:
            print(f"\n📋 Detailed Step Results:")
            for step in steps:
                step_num = step.get("step_number", "?")
                step_desc = step.get("step_description", "Unknown")
                step_result = step.get("result", "unknown")
                step_duration = step.get("duration_seconds", 0)
                
                if step_result == "pass":
                    icon = "✅"
                elif step_result == "fail":
                    icon = "❌"
                else:
                    icon = "⚠️"
                
                print(f"\n   {icon} Step {step_num}: {step_desc}")
                print(f"      Duration: {step_duration:.2f}s")
                
                if step.get("actual_result"):
                    result_text = step.get("actual_result", "")
                    if len(result_text) > 100:
                        result_text = result_text[:100] + "..."
                    print(f"      Result: {result_text}")
                
                if step.get("error_message"):
                    print(f"      ❌ Error: {step.get('error_message')}")
                
                if step.get("screenshot_path"):
                    print(f"      📸 Screenshot: {step.get('screenshot_path')}")
        
        # Final summary
        print()
        print("=" * 70)
        if status == "completed" and result == "pass":
            print("🎉 TEST PASSED! Complex interaction successful!")
            print("\n✨ Successfully:")
            print("   • Navigated to 5G broadband page")
            print("   • Identified available plans")
            print("   • Selected 30 months option")
            print("   • Clicked Subscribe Now button")
            print("   • Verified page transition")
        elif status == "completed":
            print("⚠️  Test completed with issues")
        else:
            print("❌ Test failed")
        print("=" * 70)
        
        exit(0 if status == "completed" and result == "pass" else 1)
    
    time.sleep(3)

# Timeout
print()
print("=" * 70)
print("⏱️  TIMEOUT: Test still running after 5 minutes")
print("   The test may still be executing in the background.")
print("   Check execution ID", execution_id, "for final results.")
print("=" * 70)
exit(1)

