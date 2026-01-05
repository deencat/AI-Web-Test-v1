"""
Quick script to create a test case with multiple versions for E2E testing
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

# Login to get token
print("1. Logging in...")
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={
        "username": "admin",
        "password": "admin123"
    }
)
print(f"   Login status: {login_response.status_code}")

if login_response.status_code != 200:
    print(f"   ERROR: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Create a test case
print("\n2. Creating test case...")
test_case_data = {
    "title": "Login Flow Test",
    "description": "Test the login functionality of the application",
    "url": "https://example.com/login",
    "test_type": "e2e",
    "expected_result": "User should be able to login successfully",
    "steps": [
        {"action": "navigate", "url": "https://example.com/login"},
        {"action": "type", "selector": "#username", "value": "testuser"},
        {"action": "type", "selector": "#password", "value": "password123"},
        {"action": "click", "selector": "#login-button"},
        {"action": "assert", "selector": ".dashboard", "condition": "visible"}
    ]
}

create_response = requests.post(
    f"{BASE_URL}/tests",
    headers=headers,
    json=test_case_data
)
print(f"   Create status: {create_response.status_code}")

if create_response.status_code not in [200, 201]:
    print(f"   ERROR: {create_response.text}")
    exit(1)

test_case = create_response.json()
test_id = test_case["id"]
print(f"   ✅ Created test case ID: {test_id}")

# Update test case multiple times to create versions
print("\n3. Creating multiple versions...")

version_updates = [
    {
        "steps": [
            {"action": "navigate", "url": "https://example.com/login"},
            {"action": "type", "selector": "#username", "value": "testuser"},
            {"action": "type", "selector": "#password", "value": "password123"},
            {"action": "click", "selector": "#login-button"},
            {"action": "assert", "selector": ".dashboard", "condition": "visible"},
            {"action": "assert", "selector": ".welcome-message", "condition": "contains", "value": "Welcome"}
        ],
        "change_reason": "Added welcome message assertion"
    },
    {
        "steps": [
            {"action": "navigate", "url": "https://example.com/login"},
            {"action": "type", "selector": "#username", "value": "admin"},
            {"action": "type", "selector": "#password", "value": "admin123"},
            {"action": "click", "selector": "#login-button"},
            {"action": "wait", "duration": 2000},
            {"action": "assert", "selector": ".dashboard", "condition": "visible"},
            {"action": "assert", "selector": ".welcome-message", "condition": "contains", "value": "Welcome Admin"}
        ],
        "change_reason": "Changed to admin credentials and added wait"
    },
    {
        "steps": [
            {"action": "navigate", "url": "https://example.com/login"},
            {"action": "type", "selector": "#username", "value": "admin"},
            {"action": "type", "selector": "#password", "value": "admin123"},
            {"action": "click", "selector": "#login-button"},
            {"action": "wait", "duration": 2000},
            {"action": "assert", "selector": ".dashboard", "condition": "visible"},
            {"action": "assert", "selector": ".welcome-message", "condition": "contains", "value": "Welcome Admin"},
            {"action": "click", "selector": ".profile-button"},
            {"action": "assert", "selector": ".profile-menu", "condition": "visible"}
        ],
        "change_reason": "Added profile menu verification"
    }
]

for i, update in enumerate(version_updates, start=2):
    print(f"   Creating version {i}...")
    time.sleep(0.5)  # Small delay between versions
    
    update_response = requests.put(
        f"{BASE_URL}/tests/{test_id}",
        headers=headers,
        json={
            "title": test_case_data["title"],
            "description": test_case_data["description"],
            "url": test_case_data["url"],
            "test_type": test_case_data["test_type"],
            "expected_result": test_case_data["expected_result"],
            "steps": update["steps"],
            "change_reason": update["change_reason"]
        }
    )
    
    if update_response.status_code == 200:
        print(f"     ✅ Version {i} created")
    else:
        print(f"     ❌ Failed to create version {i}: {update_response.text}")

# Verify versions were created
print("\n4. Verifying versions...")
versions_response = requests.get(
    f"{BASE_URL}/tests/{test_id}/versions",
    headers=headers
)

if versions_response.status_code == 200:
    versions = versions_response.json()
    print(f"   ✅ Total versions: {len(versions)}")
    for v in versions:
        print(f"      - Version {v['version_number']}: {v.get('change_reason', 'Initial version')}")
else:
    print(f"   ❌ Failed to fetch versions: {versions_response.text}")

print("\n✅ Test data creation complete!")
print(f"💡 You can now run E2E tests - they will use test case ID: {test_id}")
