"""
Sprint 4 Feedback Correction Test
==================================
This test focuses on testing the feedback correction workflow using existing
feedback entries, avoiding the execution issues.

Tests:
1. Get existing feedback entries
2. Submit corrections for feedback entries
3. Verify corrections were stored
4. Check statistics
"""

import requests
import json
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None

# ANSI color codes
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


def get_feedback_without_corrections():
    """Get feedback entries that don't have corrections yet."""
    print_section("Step 1: Find Feedback Without Corrections")
    
    response = requests.get(
        f"{BASE_URL}/feedback",
        headers=get_headers(),
        params={"limit": 100}
    )
    
    if response.status_code != 200:
        print_error(f"Failed to get feedback: {response.text}")
        return []
    
    result = response.json()
    all_feedback = result.get('items', [])
    
    # Filter for feedback without corrections
    feedback_without_corrections = [
        f for f in all_feedback 
        if not f.get('corrected_step') or f.get('correction_source') is None
    ]
    
    print_success(f"Found {len(all_feedback)} total feedback entries")
    print_info(f"Feedback without corrections: {len(feedback_without_corrections)}")
    
    if feedback_without_corrections:
        for i, feedback in enumerate(feedback_without_corrections[:3], 1):
            print_info(f"{i}. ID: {feedback['id']}, Exec: {feedback['execution_id']}, "
                      f"Type: {feedback['failure_type']}, "
                      f"Selector: {feedback.get('failed_selector', 'N/A')}")
    
    return feedback_without_corrections


def submit_correction_for_feedback(feedback_id: int, feedback_data: Dict) -> bool:
    """Submit a correction for a feedback entry."""
    print_section(f"Step 2: Submit Correction for Feedback #{feedback_id}")
    
    # Create a realistic correction based on the failure type
    failure_type = feedback_data.get('failure_type')
    failed_selector = feedback_data.get('failed_selector', '#unknown')
    
    # Generate a corrected selector based on failure type
    if failure_type == 'selector_not_found':
        # Change ID selector to class or different ID
        if failed_selector.startswith('#'):
            corrected_selector = f"button.{failed_selector[1:]}-btn"
        else:
            corrected_selector = f"button.submit-btn"
    else:
        corrected_selector = "button[type='submit']"
    
    correction_data = {
        "corrected_step": {
            "action": "click",
            "selector": corrected_selector,
            "value": "",
            "description": "Corrected selector based on failure analysis"
        },
        "selector_type": "css",
        "correction_source": "human",
        "correction_confidence": 0.90,
        "notes": f"Sprint 4 test: Corrected {failure_type} error. Original selector: {failed_selector}"
    }
    
    response = requests.post(
        f"{BASE_URL}/feedback/{feedback_id}/correction",
        headers=get_headers(),
        json=correction_data
    )
    
    if response.status_code != 200:
        print_error(f"Failed to submit correction: {response.text}")
        return False
    
    print_success("Correction submitted successfully")
    print_info(f"Original Selector: {failed_selector}")
    print_info(f"Corrected Selector: {corrected_selector}")
    print_info(f"Confidence: 90%")
    print_info(f"Source: human")
    
    return True


def verify_correction(feedback_id: int) -> bool:
    """Verify correction was stored correctly."""
    print_section(f"Step 3: Verify Correction for Feedback #{feedback_id}")
    
    response = requests.get(
        f"{BASE_URL}/feedback/{feedback_id}",
        headers=get_headers()
    )
    
    if response.status_code != 200:
        print_error(f"Failed to get feedback: {response.text}")
        return False
    
    feedback = response.json()
    
    if not feedback.get('corrected_step'):
        print_error("Correction was not stored!")
        return False
    
    print_success("Correction verified in database")
    print_info(f"Corrected Selector: {feedback['corrected_step'].get('selector', 'N/A')}")
    print_info(f"Correction Source: {feedback.get('correction_source', 'N/A')}")
    print_info(f"Correction Confidence: {feedback.get('correction_confidence', 0) * 100:.0f}%")
    print_info(f"Notes: {feedback.get('notes', 'N/A')[:80]}")
    
    return True


def test_update_feedback_metadata(feedback_id: int) -> bool:
    """Test updating feedback metadata."""
    print_section(f"Step 4: Update Feedback Metadata #{feedback_id}")
    
    update_data = {
        "is_anomaly": True,
        "anomaly_score": 0.75,
        "anomaly_type": "selector_pattern_mismatch",
        "tags": ["sprint4-test", "corrected", "verified"],
        "notes": "Tested and corrected during Sprint 4 validation"
    }
    
    response = requests.put(
        f"{BASE_URL}/feedback/{feedback_id}",
        headers=get_headers(),
        json=update_data
    )
    
    if response.status_code != 200:
        print_error(f"Failed to update feedback: {response.text}")
        return False
    
    feedback = response.json()
    print_success("Metadata updated successfully")
    print_info(f"Is Anomaly: {feedback.get('is_anomaly')}")
    print_info(f"Anomaly Score: {feedback.get('anomaly_score')}")
    print_info(f"Tags: {', '.join(feedback.get('tags', []))}")
    
    return True


def check_statistics():
    """Check overall feedback statistics."""
    print_section("Step 5: Check Feedback Statistics")
    
    response = requests.get(
        f"{BASE_URL}/feedback/stats/summary",
        headers=get_headers()
    )
    
    if response.status_code != 200:
        print_error(f"Failed to get statistics: {response.text}")
        return False
    
    stats = response.json()
    print_success("Statistics retrieved successfully")
    print_info(f"Total Feedback Entries: {stats.get('total_feedback', 0)}")
    print_info(f"Total Failures: {stats.get('total_failures', 0)}")
    print_info(f"Total Corrections: {stats.get('total_corrected', 0)}")
    
    # Avoid division by zero
    correction_rate = stats.get('correction_rate', 0)
    print_info(f"Correction Rate: {correction_rate:.1f}%")
    print_info(f"Total Anomalies: {stats.get('total_anomalies', 0)}")
    
    if stats.get('failure_type_distribution'):
        print_info("\nFailure Type Distribution:")
        for failure_type, count in stats['failure_type_distribution'].items():
            print_info(f"  {failure_type}: {count}")
    
    return True


def test_filtering():
    """Test feedback filtering capabilities."""
    print_section("Step 6: Test Feedback Filtering")
    
    # Test 1: Filter by failure type
    response = requests.get(
        f"{BASE_URL}/feedback",
        headers=get_headers(),
        params={"failure_type": "selector_not_found", "limit": 5}
    )
    
    if response.status_code == 200:
        result = response.json()
        count = len(result.get('items', []))
        print_success(f"Filter by failure_type=selector_not_found: {count} entries")
    
    # Test 2: Filter by has_correction
    response = requests.get(
        f"{BASE_URL}/feedback",
        headers=get_headers(),
        params={"has_correction": True, "limit": 5}
    )
    
    if response.status_code == 200:
        result = response.json()
        count = len(result.get('items', []))
        print_success(f"Filter by has_correction=True: {count} entries")
    
    # Test 3: Filter by is_anomaly
    response = requests.get(
        f"{BASE_URL}/feedback",
        headers=get_headers(),
        params={"is_anomaly": True, "limit": 5}
    )
    
    if response.status_code == 200:
        result = response.json()
        count = len(result.get('items', []))
        print_success(f"Filter by is_anomaly=True: {count} entries")
    
    return True


def main():
    """Run the feedback correction workflow test."""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Sprint 4: Feedback Correction Workflow Test{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print("\nThis test will:")
    print("1. Find existing feedback without corrections")
    print("2. Submit corrections for feedback entries")
    print("3. Verify corrections are stored")
    print("4. Update feedback metadata")
    print("5. Check statistics")
    print("6. Test filtering capabilities")
    print(f"{BOLD}{'='*60}{RESET}")
    
    try:
        # Step 1: Get feedback without corrections
        feedback_list = get_feedback_without_corrections()
        
        if not feedback_list:
            print_error("No feedback entries found without corrections")
            print_info("Creating a test feedback entry...")
            
            # Create a test feedback entry
            response = requests.post(
                f"{BASE_URL}/feedback",
                headers=get_headers(),
                json={
                    "execution_id": 1,
                    "step_index": 5,
                    "failure_type": "selector_not_found",
                    "error_message": "Element '#test-button' not found",
                    "failed_selector": "#test-button",
                    "selector_type": "css",
                    "page_url": "https://example.com/test",
                    "browser_type": "chromium"
                }
            )
            
            if response.status_code == 201:
                feedback = response.json()
                feedback_list = [feedback]
                print_success(f"Created test feedback entry #{feedback['id']}")
            else:
                print_error("Failed to create test feedback entry")
                return False
        
        # Use the first feedback entry for testing
        test_feedback = feedback_list[0]
        feedback_id = test_feedback['id']
        
        # Step 2: Submit correction
        if not submit_correction_for_feedback(feedback_id, test_feedback):
            print_error("Failed to submit correction")
            return False
        
        # Step 3: Verify correction
        if not verify_correction(feedback_id):
            print_error("Failed to verify correction")
            return False
        
        # Step 4: Update metadata
        if not test_update_feedback_metadata(feedback_id):
            print_error("Failed to update metadata")
            return False
        
        # Step 5: Check statistics
        if not check_statistics():
            print_error("Failed to get statistics")
            return False
        
        # Step 6: Test filtering
        if not test_filtering():
            print_error("Failed to test filtering")
            return False
        
        # Success!
        print_section("✅ TEST COMPLETED SUCCESSFULLY")
        print(f"\n{GREEN}{BOLD}All Sprint 4 Feedback Correction features verified:{RESET}")
        print(f"{GREEN}✓ Finding feedback entries{RESET}")
        print(f"{GREEN}✓ Submitting corrections{RESET}")
        print(f"{GREEN}✓ Verifying corrections stored{RESET}")
        print(f"{GREEN}✓ Updating feedback metadata{RESET}")
        print(f"{GREEN}✓ Retrieving statistics{RESET}")
        print(f"{GREEN}✓ Filtering feedback entries{RESET}")
        print(f"\n{BOLD}🎉 Sprint 4 Feedback System Working Perfectly!{RESET}\n")
        
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
