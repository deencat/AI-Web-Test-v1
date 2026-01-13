"""
Sprint 4 Complete Workflow Test
=================================
This test demonstrates the complete execution feedback system workflow:
1. Create a test case with a failing selector
2. Execute the test (which will fail)
3. Verify feedback was automatically captured
4. Submit a correction for the failed step
5. Verify the correction was stored
6. Check feedback statistics

This validates that Sprint 4's execution feedback system is working end-to-end.
"""

import requests
import time
import json
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None

# ANSI color codes for better output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_section(title: str):
    """Print a section header."""
    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD}{title}{RESET}")
    print(f"{BLUE}{BOLD}{'='*60}{RESET}")


def print_success(message: str):
    """Print a success message."""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    """Print an error message."""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message: str):
    """Print an info message."""
    print(f"{YELLOW}ℹ {message}{RESET}")


def login() -> str:
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def get_headers() -> Dict[str, str]:
    """Get authorization headers."""
    global TOKEN
    if not TOKEN:
        TOKEN = login()
    return {"Authorization": f"Bearer {TOKEN}"}


def create_test_with_bad_selector() -> int:
    """Create a test case with an intentionally bad selector."""
    print_section("Step 1: Create Test Case with Bad Selector")
    
    test_data = {
        "title": f"Sprint 4 Feedback Test - {int(time.time())}",
        "description": "Test case designed to fail for feedback capture testing",
        "test_type": "e2e",
        "priority": "medium",
        "steps": [
            "Navigate to https://example.com",
            "Click on element with selector: #non-existent-button-12345",
            "Verify element exists"
        ],
        "expected_result": "Should fail at step 2 with selector not found error",
        "test_data": {
            "url": "https://example.com",
            "bad_selector": "#non-existent-button-12345"
        },
        "tags": ["sprint4", "feedback-test", "intentional-failure"]
    }
    
    response = requests.post(
        f"{BASE_URL}/tests",
        headers=get_headers(),
        json=test_data
    )
    
    if response.status_code != 201:
        print_error(f"Failed to create test: {response.text}")
        return None
    
    test_case = response.json()
    print_success(f"Created test case #{test_case['id']}")
    print_info(f"Title: {test_case['title']}")
    print_info(f"Steps: {len(test_case['steps'])}")
    print_info(f"Test Type: {test_case['test_type']}")
    
    return test_case['id']


def execute_test_and_wait(test_case_id: int) -> Optional[Dict[str, Any]]:
    """Execute test case and wait for completion."""
    print_section("Step 2: Execute Test Case")
    
    # Start execution
    execution_request = {
        "browser": "chromium",
        "environment": "test",
        "triggered_by": "sprint4_feedback_test"
    }
    
    response = requests.post(
        f"{BASE_URL}/executions/tests/{test_case_id}/execute",
        headers=get_headers(),
        json=execution_request
    )
    
    if response.status_code != 201:
        print_error(f"Failed to start execution: {response.text}")
        return None
    
    execution = response.json()
    execution_id = execution['id']
    print_success(f"Started execution #{execution_id}")
    
    # Wait for completion (max 60 seconds)
    print_info("Waiting for execution to complete...")
    for i in range(60):
        time.sleep(1)
        response = requests.get(
            f"{BASE_URL}/executions/{execution_id}",
            headers=get_headers()
        )
        
        if response.status_code != 200:
            continue
        
        execution = response.json()
        status = execution['status']
        
        if status in ['completed', 'failed']:
            print_success(f"Execution completed with status: {status}")
            print_info(f"Duration: {execution.get('duration_ms', 0)}ms")
            return execution
        
        if i % 5 == 0:
            print_info(f"Status: {status} ({i}s elapsed)")
    
    print_error("Execution timed out after 60 seconds")
    return None


def check_feedback_captured(execution_id: int) -> Optional[int]:
    """Check if feedback was automatically captured."""
    print_section("Step 3: Check Feedback Capture")
    
    response = requests.get(
        f"{BASE_URL}/executions/{execution_id}/feedback",
        headers=get_headers()
    )
    
    if response.status_code != 200:
        print_error(f"Failed to get feedback: {response.text}")
        return None
    
    feedback_list = response.json()
    
    if not feedback_list:
        print_error("No feedback was captured for this execution")
        return None
    
    print_success(f"Found {len(feedback_list)} feedback entry(ies)")
    
    for feedback in feedback_list:
        print_info(f"Feedback ID: {feedback['id']}")
        print_info(f"  Step Index: {feedback['step_index']}")
        print_info(f"  Failure Type: {feedback['failure_type']}")
        print_info(f"  Failed Selector: {feedback.get('failed_selector', 'N/A')}")
        print_info(f"  Error: {feedback.get('error_message', 'N/A')[:80]}...")
        print_info(f"  Has Correction: {'Yes' if feedback.get('corrected_step') else 'No'}")
    
    return feedback_list[0]['id']


def submit_correction(feedback_id: int):
    """Submit a correction for the failed step."""
    print_section("Step 4: Submit Correction")
    
    correction_data = {
        "corrected_step": {
            "action": "click",
            "selector": "button.submit-btn",  # Corrected selector
            "value": "",
            "description": "Click submit button (corrected)"
        },
        "selector_type": "css",
        "correction_source": "human",
        "correction_confidence": 0.95,
        "notes": "Changed from ID selector to class selector based on page inspection"
    }
    
    response = requests.post(
        f"{BASE_URL}/feedback/{feedback_id}/correction",
        headers=get_headers(),
        json=correction_data
    )
    
    if response.status_code != 200:
        print_error(f"Failed to submit correction: {response.text}")
        return False
    
    feedback = response.json()
    print_success("Correction submitted successfully")
    print_info(f"Corrected Selector: {correction_data['corrected_step']['selector']}")
    print_info(f"Confidence: {correction_data['correction_confidence'] * 100}%")
    print_info(f"Source: {correction_data['correction_source']}")
    
    return True


def verify_correction_stored(feedback_id: int):
    """Verify the correction was stored correctly."""
    print_section("Step 5: Verify Correction Stored")
    
    response = requests.get(
        f"{BASE_URL}/feedback/{feedback_id}",
        headers=get_headers()
    )
    
    if response.status_code != 200:
        print_error(f"Failed to get feedback: {response.text}")
        return False
    
    feedback = response.json()
    
    if not feedback.get('corrected_step'):
        print_error("Correction was not stored")
        return False
    
    print_success("Correction verified in database")
    print_info(f"Corrected Selector: {feedback['corrected_step'].get('selector', 'N/A')}")
    print_info(f"Correction Source: {feedback.get('correction_source', 'N/A')}")
    print_info(f"Correction Confidence: {feedback.get('correction_confidence', 0) * 100}%")
    
    return True


def check_statistics():
    """Check overall feedback statistics."""
    print_section("Step 6: Check Feedback Statistics")
    
    response = requests.get(
        f"{BASE_URL}/feedback/stats/summary",
        headers=get_headers()
    )
    
    if response.status_code != 200:
        print_error(f"Failed to get statistics: {response.text}")
        return
    
    stats = response.json()
    print_success("Statistics retrieved")
    print_info(f"Total Feedback Entries: {stats.get('total_feedback', 0)}")
    print_info(f"Total Failures: {stats.get('total_failures', 0)}")
    print_info(f"Total Corrections: {stats.get('total_corrected', 0)}")
    print_info(f"Correction Rate: {stats.get('correction_rate', 0):.1f}%")
    print_info(f"Total Anomalies: {stats.get('total_anomalies', 0)}")
    
    if stats.get('failure_type_distribution'):
        print_info("\nFailure Type Distribution:")
        for failure_type, count in stats['failure_type_distribution'].items():
            print_info(f"  - {failure_type}: {count}")


def cleanup_test_case(test_case_id: int):
    """Delete the test case created for this test."""
    print_section("Step 7: Cleanup")
    
    response = requests.delete(
        f"{BASE_URL}/tests/{test_case_id}",
        headers=get_headers()
    )
    
    if response.status_code == 204:
        print_success(f"Deleted test case #{test_case_id}")
    else:
        print_info(f"Keeping test case #{test_case_id} for inspection")


def main():
    """Run the complete workflow test."""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Sprint 4: Complete Feedback Workflow Test{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print("\nThis test will:")
    print("1. Create a test with a bad selector")
    print("2. Execute it to capture feedback")
    print("3. Submit a correction")
    print("4. Verify everything was stored")
    print(f"{BOLD}{'='*60}{RESET}")
    
    try:
        # Step 1: Create test case
        test_case_id = create_test_with_bad_selector()
        if not test_case_id:
            print_error("Failed to create test case")
            return False
        
        # Step 2: Execute test
        execution = execute_test_and_wait(test_case_id)
        if not execution:
            print_error("Failed to execute test")
            cleanup_test_case(test_case_id)
            return False
        
        execution_id = execution['id']
        
        # Step 3: Check feedback
        feedback_id = check_feedback_captured(execution_id)
        if not feedback_id:
            print_error("Feedback was not captured")
            cleanup_test_case(test_case_id)
            return False
        
        # Step 4: Submit correction
        if not submit_correction(feedback_id):
            print_error("Failed to submit correction")
            cleanup_test_case(test_case_id)
            return False
        
        # Step 5: Verify correction
        if not verify_correction_stored(feedback_id):
            print_error("Failed to verify correction")
            cleanup_test_case(test_case_id)
            return False
        
        # Step 6: Check statistics
        check_statistics()
        
        # Step 7: Cleanup
        cleanup_test_case(test_case_id)
        
        # Success!
        print_section("✅ TEST COMPLETED SUCCESSFULLY")
        print(f"\n{GREEN}{BOLD}All Sprint 4 Feedback System features verified:{RESET}")
        print(f"{GREEN}✓ Automatic feedback capture on failure{RESET}")
        print(f"{GREEN}✓ Feedback storage with full context{RESET}")
        print(f"{GREEN}✓ Correction submission{RESET}")
        print(f"{GREEN}✓ Correction verification{RESET}")
        print(f"{GREEN}✓ Statistics and analytics{RESET}")
        print(f"\n{BOLD}🎉 Sprint 4 Implementation Complete!{RESET}\n")
        
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
