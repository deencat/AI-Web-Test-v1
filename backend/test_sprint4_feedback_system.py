#!/usr/bin/env python3
"""
Test Execution Feedback System - Sprint 4
Tests feedback collection, correction workflow, and API endpoints.
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000/api/v1"
AUTH_TOKEN = None

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_success(text):
    """Print success message."""
    print(f"✅ {text}")

def print_fail(text):
    """Print failure message."""
    print(f"❌ {text}")

def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")

def login():
    """Login and get auth token."""
    global AUTH_TOKEN
    
    print_header("Step 1: Authentication")
    
    # Try to login (uses form data, not JSON)
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    if response.status_code == 200:
        AUTH_TOKEN = response.json()["access_token"]
        print_success("Logged in successfully")
        return True
    else:
        print_fail(f"Login failed: {response.status_code}")
        return False

def get_headers():
    """Get headers with auth token."""
    return {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

def test_create_feedback():
    """Test creating execution feedback."""
    print_header("Step 2: Create Execution Feedback")
    
    # First, create a test execution
    response = requests.get(
        f"{BASE_URL}/executions",
        headers=get_headers(),
        params={"limit": 1}
    )
    
    if response.status_code != 200 or not response.json()["items"]:
        print_fail("No executions found. Run a test first.")
        return None
    
    execution_id = response.json()["items"][0]["id"]
    print_info(f"Using execution ID: {execution_id}")
    
    # Create feedback entry
    feedback_data = {
        "execution_id": execution_id,
        "step_index": 2,
        "failure_type": "selector_not_found",
        "error_message": "Element with selector '#login-button' not found",
        "screenshot_url": "/screenshots/test_failure.png",
        "page_url": "https://example.com/login",
        "browser_type": "chromium",
        "failed_selector": "#login-button",
        "selector_type": "css",
        "step_duration_ms": 5000,
        "notes": "Login button selector changed in recent update"
    }
    
    response = requests.post(
        f"{BASE_URL}/feedback",
        headers=get_headers(),
        json=feedback_data
    )
    
    if response.status_code == 201:
        feedback = response.json()
        print_success(f"Created feedback entry (ID: {feedback['id']})")
        print_info(f"  Failure Type: {feedback['failure_type']}")
        print_info(f"  Failed Selector: {feedback['failed_selector']}")
        return feedback['id']
    else:
        print_fail(f"Failed to create feedback: {response.status_code}")
        print_fail(response.text)
        return None

def test_get_feedback(feedback_id):
    """Test retrieving feedback by ID."""
    print_header("Step 3: Get Feedback by ID")
    
    response = requests.get(
        f"{BASE_URL}/feedback/{feedback_id}",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        feedback = response.json()
        print_success(f"Retrieved feedback ID: {feedback['id']}")
        print_info(f"  Execution ID: {feedback['execution_id']}")
        print_info(f"  Step Index: {feedback['step_index']}")
        print_info(f"  Failure Type: {feedback['failure_type']}")
        print_info(f"  Has Correction: {'Yes' if feedback['corrected_step'] else 'No'}")
        return True
    else:
        print_fail(f"Failed to get feedback: {response.status_code}")
        return False

def test_list_feedback():
    """Test listing feedback with filters."""
    print_header("Step 4: List Feedback with Filters")
    
    # List all feedback
    response = requests.get(
        f"{BASE_URL}/feedback",
        headers=get_headers(),
        params={"limit": 10}
    )
    
    if response.status_code == 200:
        data = response.json()
        print_success(f"Retrieved {len(data['items'])} feedback entries")
        print_info(f"  Total: {data['total']}")
        
        # Test with filters
        response = requests.get(
            f"{BASE_URL}/feedback",
            headers=get_headers(),
            params={
                "failure_type": "selector_not_found",
                "limit": 5
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Filtered by failure_type: {len(data['items'])} entries")
            return True
    
    print_fail(f"Failed to list feedback: {response.status_code}")
    return False

def test_submit_correction(feedback_id):
    """Test submitting a correction."""
    print_header("Step 5: Submit Correction")
    
    correction_data = {
        "corrected_step": {
            "action": "click",
            "selector": ".login-btn",  # Corrected selector
            "selector_type": "css",
            "description": "Click login button with updated selector"
        },
        "correction_source": "human",
        "correction_confidence": 0.95,
        "notes": "Updated selector to match new UI design"
    }
    
    response = requests.post(
        f"{BASE_URL}/feedback/{feedback_id}/correction",
        headers=get_headers(),
        json=correction_data
    )
    
    if response.status_code == 200:
        feedback = response.json()
        print_success(f"Submitted correction for feedback ID: {feedback['id']}")
        print_info(f"  Correction Source: {feedback['correction_source']}")
        print_info(f"  Confidence: {feedback['correction_confidence']}")
        print_info(f"  Corrected Selector: {feedback['corrected_step']['selector']}")
        return True
    else:
        print_fail(f"Failed to submit correction: {response.status_code}")
        print_fail(response.text)
        return False

def test_update_feedback(feedback_id):
    """Test updating feedback."""
    print_header("Step 6: Update Feedback")
    
    update_data = {
        "is_anomaly": True,
        "anomaly_score": 0.85,
        "anomaly_type": "intermittent_failure",
        "notes": "This failure appears intermittently, might be timing issue"
    }
    
    response = requests.put(
        f"{BASE_URL}/feedback/{feedback_id}",
        headers=get_headers(),
        json=update_data
    )
    
    if response.status_code == 200:
        feedback = response.json()
        print_success(f"Updated feedback ID: {feedback['id']}")
        print_info(f"  Is Anomaly: {feedback['is_anomaly']}")
        print_info(f"  Anomaly Score: {feedback['anomaly_score']}")
        return True
    else:
        print_fail(f"Failed to update feedback: {response.status_code}")
        return False

def test_get_execution_feedback():
    """Test getting feedback for a specific execution."""
    print_header("Step 7: Get Execution Feedback")
    
    # Get an execution with feedback
    response = requests.get(
        f"{BASE_URL}/executions",
        headers=get_headers(),
        params={"limit": 1}
    )
    
    if response.status_code != 200 or not response.json()["items"]:
        print_fail("No executions found")
        return False
    
    execution_id = response.json()["items"][0]["id"]
    
    response = requests.get(
        f"{BASE_URL}/executions/{execution_id}/feedback",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        feedback_items = response.json()
        print_success(f"Retrieved {len(feedback_items)} feedback entries for execution {execution_id}")
        if feedback_items:
            print_info(f"  First entry: {feedback_items[0]['failure_type']}")
        return True
    else:
        print_fail(f"Failed to get execution feedback: {response.status_code}")
        return False

def test_get_feedback_stats():
    """Test getting feedback statistics."""
    print_header("Step 8: Get Feedback Statistics")
    
    response = requests.get(
        f"{BASE_URL}/feedback/stats/summary",
        headers=get_headers()
    )
    
    if response.status_code == 200:
        stats = response.json()
        print_success("Retrieved feedback statistics")
        print_info(f"  Total Feedback: {stats['total_feedback']}")
        print_info(f"  Total Failures: {stats['total_failures']}")
        print_info(f"  Total Corrected: {stats['total_corrected']}")
        print_info(f"  Correction Rate: {stats['correction_rate']}%")
        print_info(f"  Total Anomalies: {stats['total_anomalies']}")
        
        if stats['top_failure_types']:
            print_info(f"\n  Top Failure Types:")
            for ft in stats['top_failure_types'][:3]:
                print_info(f"    - {ft['type']}: {ft['count']}")
        
        return True
    else:
        print_fail(f"Failed to get feedback stats: {response.status_code}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  SPRINT 4: EXECUTION FEEDBACK SYSTEM TEST")
    print("=" * 70)
    
    # Login
    if not login():
        print("\n❌ Tests failed - unable to authenticate")
        return 1
    
    # Run tests
    feedback_id = test_create_feedback()
    if not feedback_id:
        print("\n❌ Tests failed - unable to create feedback")
        return 1
    
    if not test_get_feedback(feedback_id):
        return 1
    
    if not test_list_feedback():
        return 1
    
    if not test_submit_correction(feedback_id):
        return 1
    
    if not test_update_feedback(feedback_id):
        return 1
    
    if not test_get_execution_feedback():
        return 1
    
    if not test_get_feedback_stats():
        return 1
    
    # Summary
    print("\n" + "=" * 70)
    print_success("ALL TESTS PASSED!")
    print("=" * 70)
    print("\n📋 Feedback System Features Verified:")
    print_success("  [OK] Create feedback entries")
    print_success("  [OK] Retrieve feedback by ID")
    print_success("  [OK] List feedback with filters")
    print_success("  [OK] Submit corrections")
    print_success("  [OK] Update feedback metadata")
    print_success("  [OK] Get execution-specific feedback")
    print_success("  [OK] Get feedback statistics")
    print("\n🎯 Sprint 4 Backend Complete!")
    print("   Next: Implement frontend UI components\n")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
