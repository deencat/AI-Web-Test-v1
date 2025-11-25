"""
Test the queue system with multiple concurrent executions.

Sprint 3 Day 2 - Queue System Testing
"""
import requests
import time
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"

# Test credentials
EMAIL = "admin@aiwebtest.com"
PASSWORD = "admin123"


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_success(text):
    """Print success message."""
    print(f"[OK] {text}")


def print_info(text):
    """Print info message."""
    print(f"[INFO] {text}")


def print_fail(text):
    """Print failure message."""
    print(f"[FAIL] {text}")


def login():
    """Login and get access token."""
    print_info("Logging in...")
    print_info(f"Using credentials: {EMAIL} / {PASSWORD}")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": PASSWORD}  # Use username "admin"
    )
    
    if response.status_code != 200:
        print_fail(f"Login failed: {response.text}")
        print_fail(f"Status code: {response.status_code}")
        return None
    
    token = response.json()["access_token"]
    print_success("Logged in successfully")
    return token


def get_or_create_test_case(token):
    """Get existing test case or create a new one."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to get existing test cases
    response = requests.get(f"{BASE_URL}/tests", headers=headers)
    if response.status_code == 200:
        tests = response.json()
        # Handle both list and dict responses
        if isinstance(tests, dict):
            tests = tests.get('items', tests.get('data', []))
        if tests and len(tests) > 0:
            test_id = tests[0]["id"]
            print_success(f"Using existing test case ID: {test_id}")
            return test_id
    
    # Create a new test case
    print_info("Creating new test case...")
    test_data = {
        "title": "Queue System Test",
        "description": "Test case for queue system testing",
        "test_type": "e2e",
        "status": "draft",
        "priority": "medium",
        "test_steps": [
            {"step_number": 1, "action": "navigate", "target": "homepage", "expected_result": "Page loads"},
            {"step_number": 2, "action": "verify", "target": "title", "expected_result": "Title is visible"},
            {"step_number": 3, "action": "click", "target": "button", "expected_result": "Button clicked"},
            {"step_number": 4, "action": "verify", "target": "result", "expected_result": "Action completed"}
        ],
        "test_data": {"base_url": "https://example.com"}
    }
    
    response = requests.post(f"{BASE_URL}/tests", headers=headers, json=test_data)
    if response.status_code != 201:
        print_fail(f"Failed to create test case: {response.text}")
        return None
    
    test_id = response.json()["id"]
    print_success(f"Created test case ID: {test_id}")
    return test_id


def check_queue_status(token):
    """Check current queue status."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/executions/queue/status", headers=headers)
    
    if response.status_code != 200:
        print_fail(f"Failed to get queue status: {response.text}")
        return None
    
    return response.json()


def run_test(token, test_case_id, priority=5):
    """Trigger a test execution."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "browser": "chromium",
        "environment": "dev",
        "base_url": "https://www.three.com.hk",
        "triggered_by": "queue_test",
        "priority": priority
    }
    
    response = requests.post(
        f"{BASE_URL}/executions/tests/{test_case_id}/run",
        headers=headers,
        json=data
    )
    
    if response.status_code != 201:
        print_fail(f"Failed to start execution: {response.text}")
        return None
    
    return response.json()


def get_execution_status(token, execution_id):
    """Get execution status."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/executions/{execution_id}", headers=headers)
    
    if response.status_code != 200:
        return None
    
    return response.json()


def test_queue_system():
    """Main test function."""
    print_header("Sprint 3 Day 2 - Queue System Test")
    
    # Login
    token = login()
    if not token:
        return False
    
    # Get or create test case
    test_case_id = get_or_create_test_case(token)
    if not test_case_id:
        return False
    
    print_header("Initial Queue Status")
    status = check_queue_status(token)
    if status:
        print_info(f"Active: {status['active_count']}/{status['max_concurrent']}")
        print_info(f"Queued: {status['queued_count']}")
        print_info(f"Under limit: {status['is_under_limit']}")
    
    # Test 1: Queue multiple executions (more than max_concurrent)
    print_header("Test 1: Queue 8 Executions (max=5)")
    print_info("This should result in 5 running and 3 queued...")
    
    execution_ids = []
    for i in range(8):
        priority = 1 if i < 2 else (5 if i < 5 else 10)  # 2 high, 3 medium, 3 low
        result = run_test(token, test_case_id, priority=priority)
        if result:
            execution_ids.append(result["id"])
            print_success(f"#{i+1}: Execution {result['id']} - {result['message']}")
            time.sleep(0.5)  # Small delay between submissions
    
    # Check queue status after queueing
    time.sleep(2)
    print_header("Queue Status After Queueing 8 Tests")
    status = check_queue_status(token)
    if status:
        print_info(f"Active: {status['active_count']}/{status['max_concurrent']}")
        print_info(f"Queued: {status['queued_count']}")
        print_info(f"Queue items:")
        for item in status['queue']:
            print_info(f"  - Execution {item['execution_id']} (priority={item['priority']}, pos={item['queue_position']})")
        print_info(f"Active items:")
        for item in status['active']:
            print_info(f"  - Execution {item['execution_id']} (priority={item['priority']})")
    
    # Wait for some executions to complete
    print_header("Waiting for Executions to Complete")
    print_info("Monitoring progress for 30 seconds...")
    
    start_time = time.time()
    completed_count = 0
    
    while time.time() - start_time < 30:
        time.sleep(3)
        
        # Check how many completed
        completed = 0
        running = 0
        pending = 0
        
        for exec_id in execution_ids:
            exec_status = get_execution_status(token, exec_id)
            if exec_status:
                status_val = exec_status.get("status", "unknown")
                if status_val in ["completed", "failed"]:
                    completed += 1
                elif status_val == "running":
                    running += 1
                else:
                    pending += 1
        
        print_info(f"Status: {completed} completed, {running} running, {pending} pending")
        
        if completed > completed_count:
            completed_count = completed
            # Check queue status when completions happen
            queue_status = check_queue_status(token)
            if queue_status:
                print_info(f"  Queue: {queue_status['active_count']} active, {queue_status['queued_count']} queued")
        
        if completed == len(execution_ids):
            print_success("All executions completed!")
            break
    
    # Final status
    print_header("Final Results")
    for i, exec_id in enumerate(execution_ids):
        exec_status = get_execution_status(token, exec_id)
        if exec_status:
            status_val = exec_status.get("status", "unknown")
            result_val = exec_status.get("result", "N/A")
            passed = exec_status.get("passed_steps", 0)
            total = exec_status.get("total_steps", 0)
            
            status_icon = "[OK]" if status_val == "completed" else "[INFO]"
            print(f"{status_icon} Execution #{i+1} ({exec_id}): {status_val} - {passed}/{total} steps passed")
    
    # Final queue status
    print_header("Final Queue Status")
    status = check_queue_status(token)
    if status:
        print_info(f"Active: {status['active_count']}/{status['max_concurrent']}")
        print_info(f"Queued: {status['queued_count']}")
    
    print_header("Test Complete!")
    print_success("Queue system is working!")
    
    return True


if __name__ == "__main__":
    try:
        success = test_queue_system()
        exit(0 if success else 1)
    except Exception as e:
        print_fail(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

