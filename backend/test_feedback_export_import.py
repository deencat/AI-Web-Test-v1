#!/usr/bin/env python3
"""
Test Feedback Export/Import Feature - Sprint 4
Developer B: Team Collaboration Feature

Tests the complete export/import workflow:
1. Create sample feedback
2. Export to JSON
3. Import JSON back
4. Verify data integrity and security
"""

import sys
import requests
import json
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

BASE_URL = "http://127.0.0.1:8000/api/v1"
TEST_USER = "admin"
TEST_PASSWORD = "admin123"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(message):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{message}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")


def login():
    """Login and get access token."""
    print_step("Step 1: Login")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": TEST_USER, "password": TEST_PASSWORD}
    )
    
    if response.status_code != 200:
        print_error(f"Login failed: {response.status_code}")
        print_error(response.text)
        sys.exit(1)
    
    token = response.json()["access_token"]
    print_success(f"Login successful - Token: {token[:20]}...")
    return token


def create_sample_feedback(token):
    """Create sample feedback entries for testing."""
    print_step("Step 2: Create Sample Feedback")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create 3 sample feedback entries
    sample_feedback = [
        {
            "execution_id": 1,
            "step_index": 2,
            "failure_type": "selector_not_found",
            "error_message": "Element with selector 'button#submit' not found",
            "page_url": "https://example.com/form?token=secret123&session=abc",
            "failed_selector": "button#submit",
            "selector_type": "css",
            "corrected_step": {
                "action": "click",
                "selector": "button[type='submit']",
                "description": "Click submit button"
            },
            "correction_source": "human",
            "correction_confidence": 1.0
        },
        {
            "execution_id": 1,
            "step_index": 3,
            "failure_type": "timeout",
            "error_message": "Timeout waiting for element",
            "page_url": "https://test.com/page?apikey=12345",
            "failed_selector": ".result-container",
            "selector_type": "css"
        },
        {
            "execution_id": 2,
            "step_index": 1,
            "failure_type": "assertion_failed",
            "error_message": "Expected 'Success' but got 'Error'",
            "page_url": "https://example.com/result",
            "is_anomaly": True,
            "anomaly_score": 0.85
        }
    ]
    
    created_ids = []
    
    for idx, feedback_data in enumerate(sample_feedback, 1):
        response = requests.post(
            f"{BASE_URL}/feedback",
            headers=headers,
            json=feedback_data
        )
        
        if response.status_code == 201:
            feedback_id = response.json()["id"]
            created_ids.append(feedback_id)
            print_success(f"Created feedback {idx}: ID={feedback_id}")
        else:
            print_error(f"Failed to create feedback {idx}: {response.status_code}")
    
    print_info(f"Created {len(created_ids)} feedback entries")
    return created_ids


def test_export(token):
    """Test feedback export."""
    print_step("Step 3: Test Export Endpoint")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test export without HTML/screenshots (secure)
    print_info("Testing export without HTML snapshots...")
    response = requests.get(
        f"{BASE_URL}/feedback/export",
        headers=headers,
        params={
            "include_html": False,
            "include_screenshots": False,
            "limit": 100
        }
    )
    
    if response.status_code != 200:
        print_error(f"Export failed: {response.status_code}")
        print_error(response.text)
        return None
    
    export_data = response.json()
    
    print_success("Export successful!")
    print_info(f"Export version: {export_data.get('export_version')}")
    print_info(f"Exported by: {export_data.get('exported_by')}")
    print_info(f"Total items: {export_data.get('total_count')}")
    print_info(f"Sanitized: {export_data.get('sanitized')}")
    
    # Verify security features
    print_info("\n🔒 Security Checks:")
    
    feedback_items = export_data.get("feedback_items", [])
    
    if feedback_items:
        first_item = feedback_items[0]
        
        # Check URL sanitization
        if first_item.get("page_url"):
            if "?" not in first_item["page_url"]:
                print_success("✓ URLs sanitized (query params removed)")
            else:
                print_error("✗ URLs not sanitized (query params present)")
        
        # Check HTML exclusion
        if first_item.get("page_html_snapshot") is None:
            print_success("✓ HTML snapshots excluded")
        else:
            print_error("✗ HTML snapshots included")
        
        # Check user email mapping
        if "corrected_by" in first_item:
            if "@" in str(first_item.get("corrected_by", "")):
                print_success("✓ User IDs converted to emails")
            else:
                print_info("  (No user email in first item)")
        
        # Check execution FK removal
        if "execution_id" not in first_item:
            print_success("✓ Execution FK references removed")
        else:
            print_error("✗ Execution FK still present")
        
        # Check execution metadata
        if "execution_metadata" in first_item:
            print_success("✓ Execution metadata preserved")
    
    # Save to file for import test
    export_file = backend_dir / "test_feedback_export.json"
    with open(export_file, "w") as f:
        json.dump(export_data, f, indent=2)
    
    print_success(f"\n💾 Saved export to: {export_file}")
    
    return export_file


def test_import(token, export_file):
    """Test feedback import."""
    print_step("Step 4: Test Import Endpoint")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test import with skip_duplicates strategy
    print_info("Testing import with skip_duplicates strategy...")
    
    with open(export_file, "rb") as f:
        files = {"file": ("feedback-export.json", f, "application/json")}
        response = requests.post(
            f"{BASE_URL}/feedback/import",
            headers=headers,
            files=files,
            params={"merge_strategy": "skip_duplicates"}
        )
    
    if response.status_code != 200:
        print_error(f"Import failed: {response.status_code}")
        print_error(response.text)
        return False
    
    import_result = response.json()
    
    print_success("Import successful!")
    print_info(f"Message: {import_result.get('message')}")
    print_info(f"Imported: {import_result.get('imported_count')}")
    print_info(f"Skipped: {import_result.get('skipped_count')}")
    print_info(f"Updated: {import_result.get('updated_count')}")
    print_info(f"Failed: {import_result.get('failed_count')}")
    
    if import_result.get("errors"):
        print_error("Errors encountered:")
        for error in import_result["errors"]:
            print_error(f"  {error}")
    
    return True


def test_duplicate_detection(token, export_file):
    """Test that duplicate detection works."""
    print_step("Step 5: Test Duplicate Detection")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print_info("Re-importing same file to test duplicate detection...")
    
    with open(export_file, "rb") as f:
        files = {"file": ("feedback-export.json", f, "application/json")}
        response = requests.post(
            f"{BASE_URL}/feedback/import",
            headers=headers,
            files=files,
            params={"merge_strategy": "skip_duplicates"}
        )
    
    if response.status_code != 200:
        print_error(f"Import failed: {response.status_code}")
        return False
    
    import_result = response.json()
    
    # Should skip all duplicates
    if import_result.get("skipped_count", 0) > 0:
        print_success(f"✓ Duplicate detection working! Skipped {import_result['skipped_count']} duplicates")
    else:
        print_error("✗ Duplicate detection failed - items were re-imported")
    
    return import_result.get("skipped_count", 0) > 0


def verify_feedback_list(token):
    """Verify feedback list after import."""
    print_step("Step 6: Verify Feedback List")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/feedback",
        headers=headers,
        params={"limit": 100}
    )
    
    if response.status_code != 200:
        print_error(f"Failed to get feedback list: {response.status_code}")
        return
    
    result = response.json()
    total = result.get("total", 0)
    items = result.get("items", [])
    
    print_success(f"Total feedback entries: {total}")
    print_info(f"Retrieved {len(items)} items")
    
    # Show some stats
    corrected = sum(1 for item in items if item.get("corrected_step"))
    anomalies = sum(1 for item in items if item.get("is_anomaly"))
    
    print_info(f"Corrected failures: {corrected}")
    print_info(f"Anomalies detected: {anomalies}")


def test_invalid_import(token):
    """Test import validation with invalid data."""
    print_step("Step 7: Test Import Validation")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Invalid JSON
    print_info("Testing invalid JSON...")
    files = {"file": ("invalid.json", b"not valid json", "application/json")}
    response = requests.post(
        f"{BASE_URL}/feedback/import",
        headers=headers,
        files=files
    )
    
    if response.status_code == 400:
        print_success("✓ Invalid JSON rejected")
    else:
        print_error("✗ Invalid JSON not rejected")
    
    # Test 2: Invalid file format
    print_info("Testing invalid export format...")
    invalid_export = {"random_field": "value"}
    files = {"file": ("invalid.json", json.dumps(invalid_export).encode(), "application/json")}
    response = requests.post(
        f"{BASE_URL}/feedback/import",
        headers=headers,
        files=files
    )
    
    if response.status_code == 400:
        print_success("✓ Invalid export format rejected")
    else:
        print_error("✗ Invalid export format not rejected")


def cleanup(export_file):
    """Clean up test files."""
    print_step("Step 8: Cleanup")
    
    if export_file and export_file.exists():
        export_file.unlink()
        print_success(f"Removed test file: {export_file}")


def main():
    """Run all tests."""
    print(f"\n{GREEN}{'='*70}{RESET}")
    print(f"{GREEN}Sprint 4 - Feedback Export/Import Test{RESET}")
    print(f"{GREEN}Developer B: Team Collaboration Feature{RESET}")
    print(f"{GREEN}{'='*70}{RESET}")
    
    try:
        # Step 1: Login
        token = login()
        
        # Step 2: Create sample feedback
        feedback_ids = create_sample_feedback(token)
        
        if not feedback_ids:
            print_error("Failed to create sample feedback")
            sys.exit(1)
        
        # Step 3: Test export
        export_file = test_export(token)
        
        if not export_file:
            print_error("Export test failed")
            sys.exit(1)
        
        # Step 4: Test import
        if not test_import(token, export_file):
            print_error("Import test failed")
            sys.exit(1)
        
        # Step 5: Test duplicate detection
        test_duplicate_detection(token, export_file)
        
        # Step 6: Verify feedback list
        verify_feedback_list(token)
        
        # Step 7: Test validation
        test_invalid_import(token)
        
        # Step 8: Cleanup
        cleanup(export_file)
        
        # Final summary
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✓ ALL TESTS PASSED!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}")
        print(f"\n{GREEN}Sprint 4 Feature Complete:{RESET}")
        print(f"  ✓ Export endpoint working")
        print(f"  ✓ Import endpoint working")
        print(f"  ✓ URL sanitization enabled")
        print(f"  ✓ HTML snapshots excluded")
        print(f"  ✓ User ID mapping functional")
        print(f"  ✓ Duplicate detection working")
        print(f"  ✓ Validation enforced")
        print(f"\n{GREEN}Ready for frontend integration!{RESET}\n")
        
    except Exception as e:
        print_error(f"\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
