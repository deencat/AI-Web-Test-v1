"""Temporary evaluator inspect for exec 1154 / test 1417 — delete after eval."""
import json
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def login() -> str:
    login_data = urllib.parse.urlencode(
        {"username": "admin", "password": "admin123"}
    ).encode()
    req = urllib.request.Request(
        f"{BASE}/auth/login", data=login_data, method="POST"
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def get(path: str, token: str):
    req = urllib.request.Request(
        f"{BASE}{path}", headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    token = login()
    test = get("/tests/1417", token)
    print("TEST", test.get("id"), test.get("title"))
    steps = test.get("steps") or []
    print("STEPS_COUNT", len(steps) if isinstance(steps, list) else type(steps))
    if isinstance(steps, list):
        for i, s in enumerate(steps, 1):
            if isinstance(s, str):
                txt = s
            elif isinstance(s, dict):
                txt = (
                    s.get("action")
                    or s.get("description")
                    or s.get("step")
                    or json.dumps(s)[:200]
                )
            else:
                txt = str(s)
            marker = " <<<" if "228" in txt or "36 month" in txt.lower() else ""
            print(f"  {i}. {txt[:160]}{marker}")

    exe = get("/executions/1154", token)
    print(
        "EXEC",
        exe.get("id"),
        "status",
        exe.get("status"),
        "test_case_id",
        exe.get("test_case_id"),
    )
    results = (
        exe.get("step_results")
        or exe.get("results")
        or exe.get("steps")
        or []
    )
    print("RESULT_KEYS", sorted(exe.keys()))
    print("STEP_RESULTS_TYPE", type(results), "LEN", len(results) if isinstance(results, list) else None)
    if isinstance(results, list):
        for s in results:
            if not isinstance(s, dict):
                print(" ", s)
                continue
            sn = s.get("step_number") or s.get("step_index") or s.get("order")
            desc = (
                s.get("description")
                or s.get("action")
                or s.get("instruction")
                or s.get("step_description")
                or ""
            )[:120]
            print(
                f"  step={sn} status={s.get('status')} tier={s.get('tier')} "
                f"success={s.get('success')} error={str(s.get('error'))[:80]} | {desc}"
            )


if __name__ == "__main__":
    main()
