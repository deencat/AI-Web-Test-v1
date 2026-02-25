"""
Quick test for 10A.8 improve-tests (iterative workflow).
- Ensures DB has test case IDs (from generate-tests or seed).
- POST /api/v2/improve-tests with max_iterations=1.
- Polls workflow status until completed/failed/cancelled, then prints results.

Run from backend dir with server running: python scripts/test_improve_tests_10a8.py
"""
import os
import sys
import time
import json

# Backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_test_case_ids(limit=3):
    """Return list of test case IDs from DB (for improve-tests)."""
    from app.db.session import SessionLocal
    from app.crud.test_case import get_test_cases
    db = SessionLocal()
    try:
        test_cases, total = get_test_cases(db, skip=0, limit=limit)
        return [tc.id for tc in test_cases], total
    finally:
        db.close()

def main():
    try:
        import requests
    except ImportError:
        print("Install requests: pip install requests")
        return 1

    base = os.environ.get("API_BASE", "http://127.0.0.1:8000")
    improve_url = f"{base}/api/v2/improve-tests"
    workflow_url = lambda wid: f"{base}/api/v2/workflows/{wid}"
    results_url = lambda wid: f"{base}/api/v2/workflows/{wid}/results"

    ids, total = get_test_case_ids(3)
    if not ids:
        print("No test cases in DB. Create some via POST /api/v2/generate-tests first, or seed data.")
        return 1
    print(f"Using test_case_ids: {ids} (total in DB: {total})")

    try:
        r = requests.post(
            improve_url,
            json={
                "test_case_ids": ids,
                "user_instruction": "Add clearer assertions",
                "max_iterations": 1,
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.Timeout:
        print("POST timed out. Is the server running at", base, "?")
        return 1
    except requests.exceptions.RequestException as e:
        print("POST failed:", e)
        if hasattr(e, "response") and e.response is not None:
            print(e.response.text[:500])
        return 1

    workflow_id = data.get("workflow_id")
    if not workflow_id:
        print("Response missing workflow_id:", data)
        return 1
    print(f"Started workflow_id: {workflow_id}")
    print("Polling status every 2s...")

    for _ in range(120):
        time.sleep(2)
        try:
            r = requests.get(workflow_url(workflow_id), timeout=5)
            r.raise_for_status()
            status_data = r.json()
        except Exception as e:
            print(f"  GET status failed: {e}")
            continue
        status = status_data.get("status")
        print(f"  status={status}")
        if status in ("completed", "failed", "cancelled"):
            break
    else:
        print("Timeout waiting for completion")
        return 1

    if status == "completed":
        try:
            r = requests.get(results_url(workflow_id), timeout=5)
            r.raise_for_status()
            results = r.json()
            print("Results:", json.dumps(results, indent=2))
        except Exception as e:
            print("GET results failed:", e)
    else:
        print("Status payload:", json.dumps(status_data, indent=2))
        if status_data.get("error"):
            print("Error:", status_data["error"])

    print("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
