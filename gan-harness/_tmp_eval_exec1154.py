"""Evaluator helper via curl.exe (urllib blocked: loopback from external IP)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

BASE = "http://127.0.0.1:8000/api/v1"
OUT_DIR = os.path.join(os.path.dirname(__file__), "_eval_artifacts")
os.makedirs(OUT_DIR, exist_ok=True)


def curl_json(method: str, path: str, token: str | None = None, body: dict | None = None, form: str | None = None):
    cmd = ["curl.exe", "-s", "-X", method, f"{BASE}{path}"]
    if form is not None:
        cmd += ["-H", "Content-Type: application/x-www-form-urlencoded", "-d", form]
    elif body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    raw = subprocess.check_output(cmd, text=True)
    if not raw.strip():
        return {}
    return json.loads(raw)


def dump(name: str, obj) -> str:
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, default=str)
    return path


def summarize_steps(tc: dict) -> list[str]:
    steps = tc.get("steps")
    if isinstance(steps, str):
        return [s for s in steps.splitlines() if s.strip()]
    if isinstance(steps, list):
        out = []
        for s in steps:
            if isinstance(s, str):
                out.append(s)
            elif isinstance(s, dict):
                out.append(str(s.get("description") or s.get("instruction") or s))
            else:
                out.append(str(s))
        return out
    return []


def find_plan_step(step_results):
    if not isinstance(step_results, list):
        return None
    for sr in step_results:
        text = " ".join(
            str(sr.get(k) or "")
            for k in (
                "instruction",
                "description",
                "step_description",
                "action",
                "message",
                "error",
                "step",
            )
        )
        if "228" in text:
            return sr
    return None


def login() -> str:
    data = curl_json(
        "POST",
        "/auth/login",
        form="username=admin&password=admin123",
    )
    return data["access_token"]


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "inspect"
    token = login()
    print("token_ok")

    if action == "inspect":
        tc = curl_json("GET", "/tests/1417", token)
        ex = curl_json("GET", "/executions/1154", token)
        dump("tc1417.json", tc)
        dump("ex1154.json", ex)
        steps = summarize_steps(tc)
        print("title:", tc.get("title"))
        print("url:", tc.get("url"))
        print("requires_runtime_credentials:", tc.get("requires_runtime_credentials"))
        print("step_count:", len(steps))
        for i, s in enumerate(steps, 1):
            marker = " <== PLAN" if "228" in s else ""
            print(f"{i}. {s[:160]}{marker}")
        print("--- exec 1154 ---")
        print(
            "status:",
            ex.get("status"),
            "base_url:",
            ex.get("base_url"),
            "profile:",
            ex.get("browser_profile_id"),
        )
        print(
            "passed/failed/total:",
            ex.get("passed_steps"),
            ex.get("failed_steps"),
            ex.get("total_steps"),
        )
        print("exec keys:", sorted(ex.keys()))
        sr = ex.get("step_results") or ex.get("results") or ex.get("steps") or []
        print("step_results_len:", len(sr) if hasattr(sr, "__len__") else None)
        plan = find_plan_step(sr)
        if plan:
            dump("ex1154_plan_step.json", plan)
            print("plan_step:", json.dumps(plan, default=str)[:1000])
        # Also dump feedback if available
        try:
            fb = curl_json("GET", "/executions/1154/feedback?skip=0&limit=100", token)
            dump("ex1154_feedback.json", fb)
            print("feedback_items:", len(fb) if isinstance(fb, list) else type(fb).__name__)
        except Exception as e:
            print("feedback_err:", e)
        return

    if action == "start":
        ex = curl_json("GET", "/executions/1154", token)
        tc = curl_json("GET", "/tests/1417", token)
        base_url = ex.get("base_url") or tc.get("url")
        body = {
            "browser": ex.get("browser") or "chromium",
            "environment": ex.get("environment") or "dev",
            "base_url": base_url,
            "triggered_by": "gan-evaluator",
        }
        if ex.get("browser_profile_id"):
            body["browser_profile_id"] = ex["browser_profile_id"]
        creds_path = os.environ.get("AWT_LOGIN_CREDS_JSON")
        if creds_path and os.path.isfile(creds_path):
            with open(creds_path, encoding="utf-8") as f:
                body["login_credentials"] = json.load(f)
        print("start_body:", {k: v for k, v in body.items() if k != "login_credentials"})
        started = curl_json("POST", "/tests/1417/execute", token, body)
        dump("started_execution.json", started)
        print("started_id:", started.get("id"), "status:", started.get("status"))
        print(json.dumps(started, default=str)[:500])
        return

    if action == "poll":
        exec_id = sys.argv[2]
        timeout_s = float(sys.argv[3]) if len(sys.argv) > 3 else 900
        deadline = time.time() + timeout_s
        last = None
        ex = {}
        while time.time() < deadline:
            ex = curl_json("GET", f"/executions/{exec_id}", token)
            status = ex.get("status")
            line = (
                f"status={status} passed={ex.get('passed_steps')} "
                f"failed={ex.get('failed_steps')} current={ex.get('current_step')}"
            )
            if line != last:
                print(line)
                last = line
            if status in (
                "passed",
                "failed",
                "cancelled",
                "error",
                "completed",
                "success",
            ):
                dump(f"ex{exec_id}_final.json", ex)
                sr = ex.get("step_results") or ex.get("results") or []
                plan = find_plan_step(sr)
                if plan:
                    dump(f"ex{exec_id}_plan_step.json", plan)
                    print("PLAN_STEP:", json.dumps(plan, default=str)[:1500])
                print("FINAL", status)
                return
            time.sleep(5)
        dump(f"ex{exec_id}_timeout.json", ex)
        print("TIMEOUT")
        return

    raise SystemExit(f"unknown action: {action}")


if __name__ == "__main__":
    main()
