"""
Sprint 4 End-to-End Test
Tests the complete feedback workflow from execution failure to correction submission.
"""

import requests
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None


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


def get_or_create_test_case() -> int:
    """Get an existing test case or use test case ID 1."""
    # First, try to get list of test cases
    response = requests.get(
        f"{BASE_URL}/tests",
        headers=get_headers(),
        params={"limit": 1}
    )
    
    if response.status_code == 200:
        tests = response.json().get("items", [])
        if tests:
            test_case_id = tests[0]["id"]
            print(f"✓ Using existing test case #{test_case_id}")
            return test_case_id
    
    # If no test cases exist, return 1 (assuming it exists)
    print(f"✓ Using test case #1 (assumed to exist)")
    return 1


def execute_test_case(test_case_id: int) -> int:
    """Execute the test case and wait for completion."""
    response = requests.post(
        f"{BASE_URL}/executions/tests/{test_case_id}/execute",
        headers=get_headers(),
        json={
            "browser": "chromium",
            "headless": True
        }
    )
    assert response.status_code == 201, f"Failed to start execution: {response.text}"
    execution_id = response.json()["id"]
    print(f"✓ Started execution #{execution_id}")
    
    # Wait for execution to complete (max 60 seconds)
    for i in range(60):
        response = requests.get(
            f"{BASE_URL}/executions/{execution_id}",
            headers=get_headers()
        )
        assert response.status_code == 200
        execution = response.json()
        
        if execution["status"] in ["completed", "failed"]:
            print(f"✓ Execution completed with status: {execution['status']}")
            print(f"  Result: {execution.get('result', 'N/A')}")
            print(f"  Failed steps: {execution['failed_steps']}")
            return execution_id
        
        time.sleep(1)
    
    raise TimeoutError("Execution did not complete within 60 seconds")


def verify_feedback_captured(execution_id: int) -> Dict[str, Any]:
    """Verify that feedback was captured for the failed execution."""
    response = requests.get(
        f"{BASE_URL}/execution-feedback/",
        headers=get_headers(),
        params={"execution_id": execution_id}
    )
    assert response.status_code == 200, f"Failed to fetch feedback: {response.text}"
    feedback_list = response.json()
    
    assert len(feedback_list) > 0, "No feedback entries found for failed execution"
    print(f"✓ Found {len(feedback_list)} feedback entries")
    
    # Verify the first feedback entry
    feedback = feedback_list[0]
    print(f"\nFeedback Details:")
    print(f"  ID: {feedback['id']}")
    print(f"  Execution ID: {feedback['execution_id']}")
    print(f"  Step Index: {feedback['step_index']}")
    print(f"  Failure Type: {feedback['failure_type']}")
    print(f"  Failed Selector: {feedback.get('failed_selector', 'N/A')}")
    print(f"  Has Screenshot: {'Yes' if feedback.get('screenshot_url') else 'No'}")
    print(f"  Has HTML Snapshot: {'Yes' if feedback.get('page_html_snapshot') else 'No'}")
    
    # Verify required fields
    assert feedback['execution_id'] == execution_id
    assert feedback['failure_type'] in ['selector_not_found', 'timeout', 'element_not_found', 'other']
    assert feedback.get('failed_selector') is not None
    
    return feedback


def submit_correction(feedback: Dict[str, Any]) -> Dict[str, Any]:
    """Submit a correction for the failed step."""
    correction_data = {
        "corrected_step": {
            "action": "click",
            "selector": "#correct-selector",
            "value": "",
            "description": "Click element with corrected selector"
        },
        "correction_source": "human",
        "correction_confidence": 0.95,
        "notes": "Corrected selector based on manual inspection of page HTML"
    }
    
    response = requests.post(
        f"{BASE_URL}/execution-feedback/{feedback['id']}/correction",
        headers=get_headers(),
        json=correction_data
    )
    assert response.status_code == 200, f"Failed to submit correction: {response.text}"
    updated_feedback = response.json()
    
    print(f"\n✓ Submitted correction")
    print(f"  Corrected Selector: {updated_feedback['corrected_step']['selector']}")
    print(f"  Correction Source: {updated_feedback['correction_source']}")
    print(f"  Correction Confidence: {updated_feedback['correction_confidence']}")
    
    # Verify correction was saved
    assert updated_feedback['corrected_step'] is not None
    assert updated_feedback['correction_source'] == 'human'
    assert updated_feedback['correction_confidence'] == 0.95
    
    return updated_feedback


def verify_statistics(execution_id: int):
    """Verify that statistics endpoint includes the new feedback."""
    response = requests.get(
        f"{BASE_URL}/execution-feedback/stats",
        headers=get_headers(),
        params={"execution_id": execution_id}
    )
    assert response.status_code == 200, f"Failed to fetch stats: {response.text}"
    stats = response.json()
    
    print(f"\nFeedback Statistics:")
    print(f"  Total Feedback: {stats['total_feedback']}")
    print(f"  Total Corrections: {stats['total_corrections']}")
    print(f"  Correction Rate: {stats['correction_rate']:.1%}")
    print(f"  Failure Types: {stats['failure_types']}")
    
    assert stats['total_feedback'] > 0
    assert stats['total_corrections'] > 0
    assert stats['correction_rate'] > 0


def cleanup(test_case_id: int):
    """Clean up test data (skipped for existing test cases)."""
    print(f"\n✓ Skipping cleanup for test case #{test_case_id} (using existing test)")


def main():
    """Run the complete end-to-end test."""
    print("=" * 70)
    print("Sprint 4 End-to-End Test")
    print("Testing: Execution → Feedback Capture → Correction Submission")
    print("=" * 70)
    
    test_case_id = None
    
    try:
        # Step 1: Get an existing test case
        print("\n1. Getting test case...")
        test_case_id = get_or_create_test_case()
        
        # Step 2: Execute test case
        print("\n2. Executing test case...")
        execution_id = execute_test_case(test_case_id)
        
        # Step 3: Verify feedback was captured
        print("\n3. Verifying feedback capture...")
        feedback = verify_feedback_captured(execution_id)
        
        # Step 4: Submit correction
        print("\n4. Submitting correction...")
        updated_feedback = submit_correction(feedback)
        
        # Step 5: Verify statistics
        print("\n5. Verifying statistics...")
        verify_statistics(execution_id)
        
        print("\n" + "=" * 70)
        print("✅ END-TO-END TEST PASSED")
        print("=" * 70)
        print("\nAll Sprint 4 features working correctly:")
        print("  ✓ Test execution with failure")
        print("  ✓ Automatic feedback capture")
        print("  ✓ Feedback retrieval via API")
        print("  ✓ Correction submission")
        print("  ✓ Statistics calculation")
        print("\nReady for frontend integration testing!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise
    finally:
        # Clean up
        if test_case_id:
            cleanup(test_case_id)


if __name__ == "__main__":
    main()
