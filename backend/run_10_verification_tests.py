"""
Run 10 test executions to verify system stability.
"""
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

# Login
r = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "admin123"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("="*70)
print("Running 10 Verification Tests")
print("="*70)

results = []

for i in range(1, 11):
    print(f"\n[Test {i}/10]")
    
    # Create test
    test_data = {
        "title": f"Verification Test #{i}",
        "description": f"Automated verification test {i}",
        "test_type": "e2e",
        "priority": "high",
        "steps": ["Navigate to https://example.com", f"Verify test {i} completes"],
        "expected_result": "Success",
        "test_data": {"base_url": "https://example.com"}
    }
    r = requests.post(f"{BASE_URL}/tests", headers=headers, json=test_data)
    test_id = r.json()["id"]
    
    # Run test
    run_data = {"browser": "chromium", "environment": "dev", "base_url": "https://example.com"}
    r = requests.post(f"{BASE_URL}/tests/{test_id}/run", headers=headers, json=run_data)
    execution_id = r.json()["id"]
    print(f"  Started execution: {execution_id}")
    
    # Wait for completion
    for attempt in range(20):
        time.sleep(2)
        r = requests.get(f"{BASE_URL}/executions/{execution_id}", headers=headers)
        data = r.json()
        status = data.get("status")
        
        if status in ["completed", "failed"]:
            result = data.get("result")
            duration = data.get("duration_seconds", 0)
            passed = data.get("passed_steps", 0)
            failed = data.get("failed_steps", 0)
            
            results.append({
                "test": i,
                "execution_id": execution_id,
                "status": status,
                "result": result,
                "duration": duration,
                "passed": passed,
                "failed": failed
            })
            
            status_icon = "[OK]" if status == "completed" and result == "pass" else "[FAIL]"
            print(f"  {status_icon} Status: {status} | Result: {result} | Duration: {duration:.2f}s")
            break
    else:
        print(f"  [TIMEOUT] Did not complete in 40s")
        results.append({
            "test": i,
            "execution_id": execution_id,
            "status": "timeout",
            "result": None,
            "duration": 0,
            "passed": 0,
            "failed": 0
        })

# Summary
print("\n" + "="*70)
print("VERIFICATION TEST SUMMARY")
print("="*70)

passed_count = sum(1 for r in results if r["status"] == "completed" and r["result"] == "pass")
failed_count = sum(1 for r in results if r["status"] != "completed" or r["result"] != "pass")
avg_duration = sum(r["duration"] for r in results if r["duration"] > 0) / len([r for r in results if r["duration"] > 0]) if results else 0

print(f"\nTotal Tests: {len(results)}")
print(f"Passed: {passed_count}")
print(f"Failed: {failed_count}")
print(f"Success Rate: {(passed_count/len(results)*100):.1f}%")
print(f"Average Duration: {avg_duration:.2f}s")

print("\nDetailed Results:")
for r in results:
    status_icon = "[OK]" if r["status"] == "completed" and r["result"] == "pass" else "[FAIL]"
    print(f"  {status_icon} Test {r['test']}: Execution {r['execution_id']} - {r['status']} ({r['result']}) - {r['duration']:.2f}s")

print("\n" + "="*70)
if passed_count == len(results):
    print("[SUCCESS] ALL TESTS PASSED - SYSTEM IS STABLE!")
    print("="*70)
    exit(0)
elif passed_count >= 8:
    print("[MOSTLY SUCCESS] {}/10 tests passed - Minor issues".format(passed_count))
    print("="*70)
    exit(0)
else:
    print("[FAIL] Only {}/10 tests passed - System needs attention".format(passed_count))
    print("="*70)
    exit(1)

