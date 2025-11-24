"""
Quick test to verify database updates are working.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "admin123"})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create simple test
test_data = {
    "title": "DB Update Test",
    "description": "Quick test to verify database updates",
    "test_type": "e2e",
    "priority": "high",
    "steps": ["Navigate to https://example.com", "Verify title"],
    "expected_result": "Success",
    "test_data": {"base_url": "https://example.com"}
}
response = requests.post(f"{BASE_URL}/tests", headers=headers, json=test_data)
test_id = response.json()["id"]
print(f"✅ Created test: {test_id}")

# Run test
run_data = {"browser": "chromium", "environment": "dev", "base_url": "https://example.com"}
response = requests.post(f"{BASE_URL}/tests/{test_id}/run", headers=headers, json=run_data)
execution_id = response.json()["id"]
print(f"✅ Started execution: {execution_id}")

# Monitor for 30 seconds
print("\n📊 Monitoring execution status...")
for i in range(10):
    time.sleep(3)
    response = requests.get(f"{BASE_URL}/executions/{execution_id}", headers=headers)
    data = response.json()
    status = data.get("status")
    result = data.get("result")
    
    print(f"[{i*3}s] Status: {status}", end="")
    if result:
        print(f" | Result: {result}", end="")
    if data.get("passed_steps"):
        print(f" | Steps: {data.get('passed_steps')}/{data.get('passed_steps') + data.get('failed_steps')}", end="")
    print()
    
    if status in ["completed", "failed"]:
        print(f"\n{'✅' if status == 'completed' else '❌'} Execution {status}!")
        print(f"Final Status: {status}")
        print(f"Final Result: {result}")
        print(f"Duration: {data.get('duration_seconds', 0):.2f}s")
        
        if status == "completed":
            print("\n🎉 DATABASE UPDATES ARE WORKING!")
        break
else:
    print("\n⚠️ Still pending after 30s - database updates may have issue")

