#!/usr/bin/env python3
"""
Simple script to run a single error test and show detailed results.
"""
import requests
import time

API_BASE = "http://localhost:8000/api/v1"

# Login first
print("Logging in...")
login_response = requests.post(
    f"{API_BASE}/auth/login",
    data={
        "username": "admin",
        "password": "admin123"
    }
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print(f"✓ Logged in successfully\n")

# Run test #143 (fill h1 element - should FAIL)
test_id = 143
print(f"Running test #{test_id} (Wrong Action on Element - fill h1)...")
response = requests.post(
    f"{API_BASE}/executions/tests/{test_id}/run",
    headers=headers,
    json={
        "base_url": "https://example.com",
        "browser": "chromium"
    }
)

if response.status_code not in [200, 201]:
    print(f"Error starting execution: {response.text}")
    exit(1)

exec_data = response.json()
exec_id = exec_data.get('id') or exec_data.get('execution_id')
print(f"Execution #{exec_id} started")

# Wait for completion
print("Waiting for execution to complete...")
for i in range(15):
    time.sleep(1)
    result = requests.get(f"{API_BASE}/executions/{exec_id}", headers=headers)
    if result.status_code == 200:
        data = result.json()
        status = data.get('status')
        if status in ['COMPLETED', 'FAILED']:
            break
    print(".", end="", flush=True)

print("\n")

# Get final result
result = requests.get(f"{API_BASE}/executions/{exec_id}", headers=headers)
if result.status_code == 200:
    data = result.json()
    print(f"Result: {data.get('result')}")
    print(f"Status: {data.get('status')}")
    print(f"Steps: {data.get('passed_steps')}/{data.get('failed_steps')}/{data.get('total_steps')} (passed/failed/total)")
    
    # Check for feedback
    feedback_response = requests.get(
        f"{API_BASE}/execution-feedback/?execution_id={exec_id}",
        headers=headers
    )
    if feedback_response.status_code == 200:
        feedback = feedback_response.json()
        if feedback:
            print(f"\n✓ Feedback entries: {len(feedback)}")
            for fb in feedback:
                print(f"  - Step {fb.get('step_index')}: {fb.get('failure_type')} - {fb.get('error_message')[:80]}")
        else:
            print("\n✗ No feedback entries found")
    else:
        print(f"\n✗ Could not fetch feedback: {feedback_response.status_code}")
else:
    print(f"Error getting result: {result.status_code}")

print("\n✓ Check the server terminal for [DEBUG] logs showing detailed_step data")
