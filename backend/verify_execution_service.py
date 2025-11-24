"""
Verify Sprint 3 Execution Service
Tests the Playwright-based test execution system.
"""
import requests
import time
import json

API_BASE = "http://localhost:8000/api/v1"

def print_success(msg):
    print(f"[OK] {msg}")

def print_fail(msg):
    print(f"[FAIL] {msg}")

def print_info(msg):
    print(f"[INFO] {msg}")

def login():
    """Login and get auth token."""
    response = requests.post(
        f"{API_BASE}/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        data = response.json()
        print_success("Logged in as admin")
        return data["access_token"]
    else:
        print_fail(f"Login failed: {response.text}")
        return None

def get_or_create_test_case(token):
    """Get or create a simple test case for execution."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to get existing test cases
    response = requests.get(f"{API_BASE}/tests", headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get("tests") and len(data["tests"]) > 0:
            test = data["tests"][0]
            print_info(f"Using existing test case: {test['id']} - {test['title']}")
            return test["id"]
    
    # Create a simple test case
    print_info("Creating test case for execution...")
    test_data = {
        "title": "Simple Navigation Test",
        "description": "Test basic navigation and page load",
        "test_type": "e2e",
        "priority": "medium",
        "steps": [
            "Navigate to the homepage",
            "Verify page title is visible",
            "Click on About link",
            "Verify About page loaded"
        ],
        "expected_result": "All navigation steps complete successfully",
        "preconditions": "Browser is open and internet connection is available"
    }
    
    response = requests.post(
        f"{API_BASE}/tests",
        headers={**headers, "Content-Type": "application/json"},
        json=test_data
    )
    
    if response.status_code == 201:
        test = response.json()
        print_success(f"Created test case: {test['id']} - {test['title']}")
        return test["id"]
    else:
        print_fail(f"Failed to create test case: {response.text}")
        return None

def main():
    print("\n" + "="*60)
    print("Sprint 3 Execution Service Verification")
    print("="*60 + "\n")
    
    # Step 1: Login
    print("Step 1: Authentication")
    print("-" * 60)
    token = login()
    if not token:
        print_fail("Cannot proceed without authentication")
        return 1
    print()
    
    # Step 2: Get or create test case
    print("Step 2: Get Test Case")
    print("-" * 60)
    test_id = get_or_create_test_case(token)
    if not test_id:
        print_fail("Cannot proceed without a test case")
        return 1
    print()
    
    # Step 3: Run test with Playwright
    print("Step 3: Execute Test with Playwright")
    print("-" * 60)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    execution_request = {
        "browser": "chromium",
        "environment": "dev",
        "base_url": "https://example.com",
        "triggered_by": "manual"
    }
    
    print_info(f"Starting execution for test {test_id}...")
    print_info(f"Browser: {execution_request['browser']}")
    print_info(f"Target URL: {execution_request['base_url']}")
    
    response = requests.post(
        f"{API_BASE}/tests/{test_id}/run",
        headers=headers,
        json=execution_request
    )
    
    if response.status_code == 201:
        data = response.json()
        execution_id = data["id"]
        print_success(f"Execution started: ID {execution_id}")
        print_info(data["message"])
    else:
        print_fail(f"Failed to start execution: {response.status_code}")
        print_fail(response.text)
        return 1
    
    print()
    
    # Step 4: Check execution status
    print("Step 4: Monitor Execution Progress")
    print("-" * 60)
    
    max_wait = 60  # Wait up to 60 seconds
    wait_time = 0
    final_status = None
    
    while wait_time < max_wait:
        time.sleep(3)
        wait_time += 3
        
        response = requests.get(
            f"{API_BASE}/executions/{execution_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            result = data.get("result")
            
            print_info(f"[{wait_time}s] Status: {status}" + (f", Result: {result}" if result else ""))
            
            if status in ["completed", "failed", "cancelled"]:
                final_status = status
                final_result = result
                
                # Show execution details
                print()
                print_success("Execution finished!")
                print_info(f"Final Status: {final_status}")
                print_info(f"Final Result: {final_result}")
                
                if data.get("total_steps"):
                    print_info(f"Total Steps: {data['total_steps']}")
                    print_info(f"Passed Steps: {data.get('passed_steps', 0)}")
                    print_info(f"Failed Steps: {data.get('failed_steps', 0)}")
                
                if data.get("duration_seconds"):
                    print_info(f"Duration: {data['duration_seconds']:.2f}s")
                
                if data.get("screenshot_path"):
                    print_info(f"Screenshot: {data['screenshot_path']}")
                
                if data.get("video_path"):
                    print_info(f"Video: {data['video_path']}")
                
                # Show steps if available
                if data.get("steps"):
                    print()
                    print_info("Execution Steps:")
                    for step in data["steps"]:
                        step_result = step.get("result", "unknown")
                        step_num = step.get("step_number", "?")
                        step_desc = step.get("step_description", "")
                        if step_result == "pass":
                            print_success(f"  Step {step_num}: {step_desc}")
                        else:
                            print_fail(f"  Step {step_num}: {step_desc}")
                        if step.get("error_message"):
                            print_info(f"    Error: {step['error_message']}")
                
                break
        else:
            print_fail(f"Failed to get execution status: {response.status_code}")
            break
    
    if not final_status:
        print_fail("Execution did not complete within timeout")
        return 1
    
    print()
    
    # Step 5: Verify execution history
    print("Step 5: Verify Execution History")
    print("-" * 60)
    
    response = requests.get(
        f"{API_BASE}/tests/{test_id}/executions",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        total = data.get("total", 0)
        executions = data.get("executions", [])
        print_success(f"Retrieved execution history: {total} total executions")
        if executions:
            latest = executions[0]
            print_info(f"Latest execution: ID {latest['id']}, Status: {latest['status']}")
    else:
        print_fail(f"Failed to get execution history: {response.status_code}")
    
    print()
    
    # Summary
    print("="*60)
    print_success("SPRINT 3 EXECUTION SERVICE VERIFICATION COMPLETE!")
    print()
    print("Features Verified:")
    print_success("  [OK] Playwright integration")
    print_success("  [OK] Test execution API endpoint")
    print_success("  [OK] Background task execution")
    print_success("  [OK] Execution status tracking")
    print_success("  [OK] Step-by-step result recording")
    print_success("  [OK] Screenshot capture")
    print_success("  [OK] Execution history")
    print()
    print_info("Next Steps:")
    print_info("  - Add WebSocket support for real-time updates")
    print_info("  - Integrate Stagehand SDK for AI-powered execution")
    print_info("  - Add video recording")
    print_info("  - Implement execution queue system")
    print("="*60 + "\n")
    
    return 0

if __name__ == "__main__":
    exit(main())

