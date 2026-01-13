"""
Script to create test cases that will intentionally fail for testing feedback system.
"""

import requests
from typing import Dict

BASE_URL = "http://localhost:8000/api/v1"

def login() -> str:
    """Login and get access token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def create_failing_test_case(token: str) -> int:
    """Create a test case with invalid selectors that will fail."""
    headers = {"Authorization": f"Bearer {token}"}
    
    test_case_data = {
        "name": "Test Case - Intentional Failures for Feedback Testing",
        "description": "Test with invalid selectors to trigger feedback capture",
        "test_data": {
            "url": "https://example.com",
            "steps": [
                {
                    "step_number": 1,
                    "action": "navigate",
                    "selector": "",
                    "value": "https://example.com",
                    "description": "Navigate to example.com",
                    "expected_result": "Page loads successfully"
                },
                {
                    "step_number": 2,
                    "action": "click",
                    "selector": "#non-existent-button-id",
                    "value": "",
                    "description": "Click button that doesn't exist",
                    "expected_result": "Button is clicked"
                },
                {
                    "step_number": 3,
                    "action": "fill",
                    "selector": "input[name='fake-input']",
                    "value": "Test value",
                    "description": "Fill input that doesn't exist",
                    "expected_result": "Input is filled"
                }
            ]
        },
        "tags": ["feedback-testing", "intentional-failure"]
    }
    
    # Try to find existing test templates
    response = requests.get(f"{BASE_URL}/test-templates", headers=headers)
    if response.status_code == 200:
        templates = response.json().get("items", [])
        if templates:
            test_case_data["template_id"] = templates[0]["id"]
    
    response = requests.post(
        f"{BASE_URL}/tests",
        headers=headers,
        json=test_case_data
    )
    
    if response.status_code == 201:
        test_case_id = response.json()["id"]
        print(f"✅ Created test case #{test_case_id}")
        print(f"   Name: {test_case_data['name']}")
        print(f"   Steps: {len(test_case_data['test_data']['steps'])}")
        return test_case_id
    else:
        print(f"❌ Failed to create test case: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def execute_test(token: str, test_case_id: int):
    """Execute the test case."""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/executions/tests/{test_case_id}/execute",
        headers=headers,
        json={
            "browser": "chromium",
            "headless": True
        }
    )
    
    if response.status_code == 201:
        execution_id = response.json()["id"]
        print(f"\n✅ Started execution #{execution_id}")
        print(f"   Wait for completion, then check:")
        print(f"   - UI: http://localhost:3000/executions/{execution_id}")
        print(f"   - API: {BASE_URL}/executions/{execution_id}/feedback")
        return execution_id
    else:
        print(f"\n❌ Failed to start execution: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("Creating Test Case with Intentional Failures")
    print("=" * 70)
    
    token = login()
    print("✅ Logged in successfully\n")
    
    test_case_id = create_failing_test_case(token)
    
    if test_case_id:
        print("\n" + "=" * 70)
        print("Execute the test?")
        print("=" * 70)
        choice = input("Run test now? (y/n): ")
        
        if choice.lower() == 'y':
            execute_test(token, test_case_id)
        else:
            print(f"\nYou can execute later via:")
            print(f"  UI: Create new execution for test case #{test_case_id}")
            print(f"  API: POST {BASE_URL}/executions/tests/{test_case_id}/execute")
