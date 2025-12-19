"""
Sprint 4 Simplified E2E Test
Tests the feedback API directly without requiring test execution.
"""

import requests
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


def test_create_feedback() -> int:
    """Test creating feedback entry."""
    print("\n1. Creating feedback entry...")
    
    feedback_data = {
        "execution_id": 1,  # Assuming execution ID 1 exists
        "step_index": 2,
        "failure_type": "selector_not_found",
        "error_message": "Element with selector '#submit-button' not found",
        "failed_selector": "#submit-button",
        "selector_type": "css",
        "page_url": "https://example.com/form",
        "browser_type": "chromium",
        "viewport_width": 1920,
        "viewport_height": 1080,
        "notes": "Test feedback entry for Sprint 4"
    }
    
    response = requests.post(
        f"{BASE_URL}/feedback",
        headers=get_headers(),
        json=feedback_data
    )
    
    assert response.status_code == 201, f"Failed to create feedback: {response.text}"
    feedback = response.json()
    
    print(f"✓ Created feedback entry #{feedback['id']}")
    print(f"  Execution ID: {feedback['execution_id']}")
    print(f"  Step Index: {feedback['step_index']}")
    print(f"  Failure Type: {feedback['failure_type']}")
    print(f"  Failed Selector: {feedback['failed_selector']}")
    
    return feedback['id']


def test_get_feedback(feedback_id: int):
    """Test retrieving feedback entry."""
    print(f"\n2. Retrieving feedback #{feedback_id}...")
    
    response = requests.get(
        f"{BASE_URL}/feedback/{feedback_id}",
        headers=get_headers()
    )
    
    assert response.status_code == 200, f"Failed to get feedback: {response.text}"
    feedback = response.json()
    
    print(f"✓ Retrieved feedback")
    print(f"  ID: {feedback['id']}")
    print(f"  Failure Type: {feedback['failure_type']}")
    print(f"  Has Correction: {'Yes' if feedback.get('corrected_step') else 'No'}")


def test_list_feedback():
    """Test listing feedback entries."""
    print("\n3. Listing all feedback entries...")
    
    response = requests.get(
        f"{BASE_URL}/feedback",
        headers=get_headers(),
        params={"limit": 10}
    )
    
    assert response.status_code == 200, f"Failed to list feedback: {response.text}"
    result = response.json()
    feedback_list = result.get('items', result)  # Handle both list and paginated response
    
    print(f"✓ Found {len(feedback_list)} feedback entries")
    for fb in feedback_list[:3]:  # Show first 3
        print(f"  - ID {fb['id']}: Execution {fb['execution_id']}, Step {fb['step_index']}, Type: {fb['failure_type']}")


def test_submit_correction(feedback_id: int):
    """Test submitting correction."""
    print(f"\n4. Submitting correction for feedback #{feedback_id}...")
    
    correction_data = {
        "corrected_step": {
            "action": "click",
            "selector": "button[type='submit']",
            "value": "",
            "description": "Click submit button with corrected selector"
        },
        "correction_source": "human",
        "correction_confidence": 0.9,
        "notes": "Corrected based on manual page inspection"
    }
    
    response = requests.post(
        f"{BASE_URL}/feedback/{feedback_id}/correction",
        headers=get_headers(),
        json=correction_data
    )
    
    assert response.status_code == 200, f"Failed to submit correction: {response.text}"
    updated_feedback = response.json()
    
    print(f"✓ Submitted correction")
    print(f"  Corrected Selector: {updated_feedback['corrected_step']['selector']}")
    print(f"  Correction Source: {updated_feedback['correction_source']}")
    print(f"  Correction Confidence: {updated_feedback['correction_confidence']}")
    
    # Verify correction fields
    assert updated_feedback['corrected_step'] is not None
    assert updated_feedback['correction_source'] == 'human'
    assert updated_feedback['correction_confidence'] == 0.9


def test_get_statistics():
    """Test statistics endpoint."""
    print("\n5. Getting feedback statistics...")
    
    response = requests.get(
        f"{BASE_URL}/feedback/stats/summary",
        headers=get_headers()
    )
    
    assert response.status_code == 200, f"Failed to get stats: {response.text}"
    stats = response.json()
    
    print(f"✓ Statistics:")
    print(f"  Total Feedback: {stats.get('total_feedback', 0)}")
    print(f"  Total Corrections: {stats.get('total_corrections', 0)}")
    print(f"  Correction Rate: {stats.get('correction_rate', 0):.1%}")
    print(f"  Average Confidence: {stats.get('avg_confidence', 0):.2f}")
    print(f"  Failure Types: {stats.get('failure_types', {})}")
    print(f"  Anomalies: {stats.get('anomalies', 0)}")
    
    assert stats.get('total_feedback', 0) > 0


def test_filter_by_execution():
    """Test filtering feedback by execution_id."""
    print("\n6. Testing execution ID filter...")
    
    response = requests.get(
        f"{BASE_URL}/executions/1/feedback",
        headers=get_headers()
    )
    
    assert response.status_code == 200, f"Failed to filter feedback: {response.text}"
    feedback_list = response.json()
    
    print(f"✓ Found {len(feedback_list)} feedback entries for execution #1")
    
    # Verify all entries belong to execution 1
    for fb in feedback_list:
        assert fb['execution_id'] == 1, f"Unexpected execution_id: {fb['execution_id']}"


def test_update_feedback(feedback_id: int):
    """Test updating feedback entry."""
    print(f"\n7. Updating feedback #{feedback_id}...")
    
    update_data = {
        "notes": "Updated notes - Sprint 4 test completed successfully",
        "tags": ["sprint4", "tested", "corrected"]
    }
    
    response = requests.put(
        f"{BASE_URL}/feedback/{feedback_id}",
        headers=get_headers(),
        json=update_data
    )
    
    assert response.status_code == 200, f"Failed to update feedback: {response.text}"
    updated_feedback = response.json()
    
    print(f"✓ Updated feedback")
    print(f"  New Notes: {updated_feedback['notes']}")
    print(f"  Tags: {updated_feedback.get('tags', [])}")


def test_delete_feedback(feedback_id: int):
    """Test deleting feedback entry."""
    print(f"\n8. Deleting feedback #{feedback_id}...")
    
    response = requests.delete(
        f"{BASE_URL}/feedback/{feedback_id}",
        headers=get_headers()
    )
    
    assert response.status_code == 204, f"Failed to delete feedback: {response.text}"
    
    print(f"✓ Deleted feedback #{feedback_id}")
    
    # Verify it's deleted
    response = requests.get(
        f"{BASE_URL}/feedback/{feedback_id}",
        headers=get_headers()
    )
    assert response.status_code == 404, "Feedback should be deleted"
    print(f"✓ Confirmed deletion")


def main():
    """Run all feedback API tests."""
    print("=" * 70)
    print("Sprint 4 Feedback API Test Suite")
    print("Testing all 8 feedback endpoints")
    print("=" * 70)
    
    feedback_id = None
    
    try:
        # Create feedback
        feedback_id = test_create_feedback()
        
        # Get feedback
        test_get_feedback(feedback_id)
        
        # List feedback
        test_list_feedback()
        
        # Submit correction
        test_submit_correction(feedback_id)
        
        # Get statistics
        test_get_statistics()
        
        # Filter by execution
        test_filter_by_execution()
        
        # Update feedback
        test_update_feedback(feedback_id)
        
        # Delete feedback (cleanup)
        test_delete_feedback(feedback_id)
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nAll Sprint 4 Feedback API endpoints working correctly:")
        print("  ✓ POST /feedback/ (create)")
        print("  ✓ GET /feedback/{id} (retrieve)")
        print("  ✓ GET /feedback/ (list)")
        print("  ✓ POST /feedback/{id}/correction (submit correction)")
        print("  ✓ GET /feedback/stats (statistics)")
        print("  ✓ PUT /feedback/{id} (update)")
        print("  ✓ DELETE /feedback/{id} (delete)")
        print("  ✓ Filter by execution_id")
        print("\n🎉 Sprint 4 Backend Implementation Complete!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
