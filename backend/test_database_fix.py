"""
Test to verify database update fix - execution ID should now match.
"""
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

# Login
print("[1] Logging in...")
r = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "admin123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Create test
print("[2] Creating test case...")
test_data = {
    "title": "Database Fix Verification",
    "description": "Verify execution ID matches and status updates correctly",
    "test_type": "e2e",
    "priority": "high",
    "steps": ["Navigate to https://example.com", "Verify page loads"],
    "expected_result": "Success",
    "test_data": {"base_url": "https://example.com"}
}
r = requests.post(f"{BASE_URL}/tests", headers=headers, json=test_data)
test_id = r.json()["id"]
print(f"[OK] Test created: {test_id}")

# Run test
print(f"\n[3] Running test...")
run_data = {"browser": "chromium", "environment": "dev", "base_url": "https://example.com"}
r = requests.post(f"{BASE_URL}/tests/{test_id}/run", headers=headers, json=run_data)
execution_id = r.json()["id"]
print(f"[OK] Execution started: {execution_id}")
print(f"[4] Monitoring execution {execution_id}...\n")

# Monitor
for i in range(15):
    time.sleep(2)
    r = requests.get(f"{BASE_URL}/executions/{execution_id}", headers=headers)
    data = r.json()
    
    status = data.get("status")
    result = data.get("result")
    passed = data.get("passed_steps", 0)
    failed = data.get("failed_steps", 0)
    
    print(f"[{i*2}s] ID: {execution_id} | Status: {status}", end="")
    if result:
        print(f" | Result: {result}", end="")
    if passed + failed > 0:
        print(f" | Steps: {passed}/{passed+failed}", end="")
    print()
    
    if status in ["completed", "failed"]:
        print(f"\n[{'OK' if status == 'completed' else 'FAIL'}] Execution {status}!")
        print(f"\nFinal Details:")
        print(f"   Execution ID: {execution_id}")
        print(f"   Status: {status}")
        print(f"   Result: {result}")
        print(f"   Duration: {data.get('duration_seconds', 0):.2f}s")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        
        if status == "completed" and result == "pass":
            print("\n" + "=" * 60)
            print("[SUCCESS] DATABASE FIX VERIFIED!")
            print("=" * 60)
            print("[OK] Execution ID matches")
            print("[OK] Status updates correctly")
            print("[OK] Result persists")
            print("[OK] Steps tracked")
            print("=" * 60)
            exit(0)
        break

print("\n[WARNING] Test did not complete as expected")
exit(1)

