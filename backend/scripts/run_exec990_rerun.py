"""Trigger and poll OGP-PPD Exec #990 equivalent re-run (test case 1399)."""
import json
import os
import sys
import time

import requests

os.environ["NO_PROXY"] = "127.0.0.1,localhost"

BASE = "http://127.0.0.1:8000/api/v1"
WATCH_STEPS = {14, 24, 36}
CONTEXT_STEPS = {13, 23, 35}


def main() -> int:
    session = requests.Session()
    session.trust_env = False

    login = session.post(
        f"{BASE}/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    print("login", login.status_code)
    if login.status_code != 200:
        print(login.text[:500])
        return 1

    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    run = session.post(
        f"{BASE}/executions/tests/1399/run",
        headers=headers,
        json={
            "browser": "chromium",
            "environment": "dev",
            "base_url": "https://web.three.com.hk",
            "triggered_by": "gan-harness-iteration-004",
        },
    )
    print("run", run.status_code, run.text[:400])
    if run.status_code not in (200, 201):
        return 1

    exec_id = run.json()["id"]
    print("exec_id", exec_id)
    seen: set[int] = set()
    last_rows: list = []

    for poll in range(90):
        status_resp = session.get(f"{BASE}/executions/{exec_id}", headers=headers)
        data = status_resp.json() if status_resp.status_code == 200 else {}
        status = data.get("status")
        passed = data.get("passed_steps")
        failed = data.get("failed_steps")

        steps_resp = session.get(f"{BASE}/executions/{exec_id}/steps", headers=headers)
        step_rows = []
        if steps_resp.status_code == 200:
            for row in steps_resp.json():
                sn = row.get("step_number")
                if sn in WATCH_STEPS or sn in CONTEXT_STEPS:
                    step_rows.append(
                        (
                            sn,
                            row.get("result"),
                            row.get("action_method"),
                            (row.get("step_description") or "")[:55],
                            row.get("screenshot_path"),
                        )
                    )
                    if sn in WATCH_STEPS and row.get("result") in ("PASS", "FAIL", "SKIPPED"):
                        seen.add(sn)

        print(f"poll {poll}: status={status} passed={passed} failed={failed}")
        if step_rows:
            print(" ", step_rows)
            last_rows = step_rows

        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            print(
                "FINAL",
                json.dumps(
                    {
                        "exec_id": exec_id,
                        "status": status,
                        "passed": passed,
                        "failed": failed,
                        "key_steps": last_rows,
                    },
                    indent=2,
                ),
            )
            return 0

        if WATCH_STEPS.issubset(seen):
            print("WATCH_DONE", exec_id)
            print(json.dumps({"exec_id": exec_id, "key_steps": last_rows}, indent=2))
            return 0

        time.sleep(20)

    print("TIMEOUT", exec_id)
    print(json.dumps({"exec_id": exec_id, "key_steps": last_rows}, indent=2))
    return 2


if __name__ == "__main__":
    sys.exit(main())
