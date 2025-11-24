"""
Advanced test for three.com.hk - 5G Broadband plan selection.
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
    "title": "Three.com.hk - 5G Broadband Plan Selection",
    "description": "Navigate to 5G broadband page, identify plans, select 30 months option, and click Subscribe Now",
    "test_type": "e2e",
    "priority": "high",
    "steps": [
        "Navigate to https://www.three.com.hk/website/appmanager/three/home?_nfpb=true&_pageLabel=P200470391315433531600",
        "Wait for 5G broadband page to load completely",
        "Identify and list available broadband plans on the page",
        "Find and verify the 30 months option box exists",
        "Click on the 30 months option box to select it",
        "Wait for the option to be selected (visual feedback)",
        "Find the 'Subscribe Now' button",
        "Click the 'Subscribe Now' button",
        "Verify navigation to the next page (subscription page)"
    ],
    "expected_result": "Successfully navigate to 5G broadband page, select 30 months plan, click Subscribe Now, and reach subscription page",
    "test_data": {
        "base_url": "https://www.three.com.hk/website/appmanager/three/home?_nfpb=true&_pageLabel=P200470391315433531600",
        "plan_option": "30 months",
        "action": "Subscribe Now"
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
    "base_url": "https://www.three.com.hk/website/appmanager/three/home?_nfpb=true&_pageLabel=P200470391315433531600",
    "triggered_by": "manual"
}

print(f"🌐 Target: three.com.hk 5G Broadband Page")
print(f"🎯 Action: Select 30 months plan and click Subscribe Now")
print(f"🖥️  Browser: Chromium (headless)")

response = requests.post(f"{BASE_URL}/tests/{test_id}/run", headers=headers, json=run_data)
if response.status_code != 201:
    print(f"❌ Failed to start execution: {response.status_code}")
    print(response.text)
    exit(1)

execution_id = response.json()["id"]
print(f"✅ Execution started: ID {execution_id}")
print(f"⏳ Test running in background...")

# Step 4: Monitor execution
print_section("[Step 4] Monitor Execution Progress")
print(f"📊 Polling every 3 seconds (max 2 minutes)...")
print()

start_time = time.time()
last_status = None
last_step_count = 0

for i in range(40):  # 40 * 3 = 120 seconds max
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
print("⏱️  TIMEOUT: Test still running after 2 minutes")
print("   The test may still be executing in the background.")
print("   Check execution ID", execution_id, "for final results.")
print("=" * 70)
exit(1)

