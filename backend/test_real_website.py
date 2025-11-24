"""
Test real website (three.com.hk) to verify browser automation works.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """Login and get token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"[OK] Logged in successfully")
        return token
    else:
        print(f"[FAIL] Login failed: {response.status_code}")
        return None

def create_three_test(token):
    """Create a test case for three.com.hk."""
    headers = {"Authorization": f"Bearer {token}"}
    
    test_data = {
        "title": "Three.com.hk - Homepage Test",
        "description": "Verify three.com.hk homepage loads and navigation works",
        "test_type": "e2e",
        "priority": "high",
        "steps": [
            "Navigate to https://www.three.com.hk",
            "Wait for page to load",
            "Verify page title contains 'Three' or '3香港'",
            "Check if main navigation menu is visible"
        ],
        "expected_result": "Homepage loads successfully with navigation visible",
        "test_data": {
            "base_url": "https://www.three.com.hk"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/tests",
        headers=headers,
        json=test_data
    )
    
    if response.status_code == 201:
        test_id = response.json()["id"]
        print(f"[OK] Created test case: {test_id} - {test_data['title']}")
        return test_id
    else:
        print(f"[FAIL] Failed to create test: {response.status_code}")
        print(response.text)
        return None

def run_test(token, test_id):
    """Execute the test."""
    headers = {"Authorization": f"Bearer {token}"}
    
    run_data = {
        "browser": "chromium",
        "environment": "production",
        "base_url": "https://www.three.com.hk",
        "triggered_by": "manual"
    }
    
    print(f"\n[INFO] Starting execution for test {test_id}...")
    print(f"[INFO] Target: three.com.hk")
    print(f"[INFO] Browser: chromium")
    
    response = requests.post(
        f"{BASE_URL}/tests/{test_id}/run",
        headers=headers,
        json=run_data
    )
    
    if response.status_code == 201:
        execution_id = response.json()["id"]
        print(f"[OK] Execution started: ID {execution_id}")
        print(f"[INFO] Test is running in background...")
        return execution_id
    else:
        print(f"[FAIL] Failed to start execution: {response.status_code}")
        print(response.text)
        return None

def monitor_execution(token, execution_id, max_wait=60):
    """Monitor execution progress."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n[INFO] Monitoring execution {execution_id}...")
    print(f"[INFO] Max wait time: {max_wait} seconds")
    print("-" * 60)
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{BASE_URL}/executions/{execution_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            result = data.get("result")
            steps = data.get("steps", [])
            
            if status != last_status:
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] Status: {status}", end="")
                if result:
                    print(f" | Result: {result}", end="")
                if steps:
                    passed = sum(1 for s in steps if s.get("result") == "pass")
                    print(f" | Steps: {passed}/{len(steps)} passed", end="")
                print()
                last_status = status
            
            if status in ["completed", "failed"]:
                print("-" * 60)
                print(f"\n[OK] Execution {status.upper()}!")
                print(f"\nFinal Status: {status}")
                print(f"Result: {result or 'N/A'}")
                print(f"Duration: {data.get('duration_seconds', 0):.2f}s")
                print(f"Steps: {len(steps)}")
                
                if steps:
                    print(f"\n📊 Step Results:")
                    for step in steps:
                        step_num = step.get("step_number", "?")
                        step_desc = step.get("step_description", "Unknown")
                        step_result = step.get("result", "unknown")
                        icon = "✅" if step_result == "pass" else "❌" if step_result == "fail" else "⚠️"
                        print(f"  {icon} Step {step_num}: {step_desc}")
                        if step_result == "pass":
                            print(f"     Result: {step.get('actual_result', 'N/A')}")
                
                return data
        
        time.sleep(3)
    
    print(f"\n[TIMEOUT] Execution still running after {max_wait}s")
    return None

def main():
    print("=" * 60)
    print("🌐 Real Website Test - three.com.hk")
    print("=" * 60)
    
    # Step 1: Login
    print("\n[Step 1] Authentication")
    print("-" * 60)
    token = login()
    if not token:
        return 1
    
    # Step 2: Create test case
    print("\n[Step 2] Create Test Case for three.com.hk")
    print("-" * 60)
    test_id = create_three_test(token)
    if not test_id:
        return 1
    
    # Step 3: Execute test
    print("\n[Step 3] Execute Test")
    print("-" * 60)
    execution_id = run_test(token, test_id)
    if not execution_id:
        return 1
    
    # Step 4: Monitor execution
    print("\n[Step 4] Monitor Execution Progress")
    result = monitor_execution(token, execution_id, max_wait=90)
    
    if result:
        if result.get("status") == "completed" and result.get("result") == "pass":
            print("\n" + "=" * 60)
            print("🎉 TEST PASSED! Browser automation works with real website!")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("⚠️  Test completed but with issues")
            print("=" * 60)
            return 1
    else:
        print("\n" + "=" * 60)
        print("❌ Test did not complete in time")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit(main())

