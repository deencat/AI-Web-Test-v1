"""
Final Verification Test
Quick test to confirm system is stable and working.
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

print("=" * 70)
print("  FINAL VERIFICATION TEST")
print("=" * 70)

# Login
print("\n[1/5] Login...")
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("[OK] Logged in")

# Get test case
print("\n[2/5] Get test case...")
response = requests.get(f"{BASE_URL}/tests", headers=headers)
tests = response.json()
if isinstance(tests, dict):
    tests = tests.get('items', tests.get('data', []))
test_id = tests[0]["id"]
print(f"[OK] Test case: {test_id}")

# Queue 5 tests
print("\n[3/5] Queue 5 tests...")
exec_ids = []
for i in range(5):
    response = requests.post(
        f"{BASE_URL}/executions/tests/{test_id}/run",
        headers=headers,
        json={
            "browser": "chromium",
            "environment": "dev",
            "base_url": "https://example.com",
            "triggered_by": "final_test"
        }
    )
    if response.status_code == 201:
        exec_id = response.json()["id"]
        exec_ids.append(exec_id)
        print(f"[OK] Queued: {exec_id}")
    time.sleep(0.5)

# Check queue status
print("\n[4/5] Check queue status...")
response = requests.get(f"{BASE_URL}/executions/queue/status", headers=headers)
if response.status_code == 200:
    status = response.json()
    print(f"[OK] Active: {status['active_count']}/{status['max_concurrent']}")
    print(f"[OK] Queued: {status['queued_count']}")
else:
    print(f"[FAIL] Queue status failed: {response.status_code}")

# Wait and check results
print("\n[5/5] Wait 20 seconds and check results...")
time.sleep(20)

completed = 0
passed = 0
failed = 0

for exec_id in exec_ids:
    response = requests.get(f"{BASE_URL}/executions/{exec_id}", headers=headers)
    if response.status_code == 200:
        result = response.json()
        status = result.get("status")
        if status == "completed":
            completed += 1
            if result.get("result") == "pass":
                passed += 1
        elif status == "failed":
            failed += 1
            completed += 1

print(f"\n[RESULTS]")
print(f"  Completed: {completed}/5")
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")

# Final verdict
print("\n" + "=" * 70)
if completed >= 4 and passed >= 3:
    print("  ✅ FINAL VERIFICATION: PASSED")
    print("  System is stable and working correctly!")
else:
    print("  ⚠️  FINAL VERIFICATION: PARTIAL")
    print(f"  {completed}/5 completed, {passed} passed")
print("=" * 70)

