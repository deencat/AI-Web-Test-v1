#!/usr/bin/env bash
set -euo pipefail

# Cron-ready runner for saved test case 101.
#
# Example cron entry:
# */30 * * * * cd /home/dt-qa/alex_workspace/AI-Web-Test-v1-main && ./run_test_101_scheduled.sh >> /var/log/aiwebtest-test101.log 2>&1
#
# Environment variables:
#   AIWEBTEST_API_BASE_URL            Default: http://localhost:8000/api/v1
#   AIWEBTEST_TEST_CASE_ID            Default: 101
#   AIWEBTEST_USERNAME                Default: admin
#   AIWEBTEST_PASSWORD                Default: admin123
#   AIWEBTEST_BACKEND_DIR             Default: <repo>/backend
#   AIWEBTEST_BROWSER                 Default: chromium
#   AIWEBTEST_ENVIRONMENT             Default: dev
#   AIWEBTEST_TARGET_URL              Optional explicit target URL override
#   AIWEBTEST_TRIGGERED_BY            Default: scheduled
#   AIWEBTEST_POLL_INTERVAL_SECONDS   Default: 15
#   AIWEBTEST_POLL_TIMEOUT_SECONDS    Default: 7200
#   AIWEBTEST_REQUEST_TIMEOUT_SECONDS Default: 30
#   AIWEBTEST_ENSURE_OPTION_C         Default: 1
#   AIWEBTEST_APPEND_BACKEND_SERVER_LOG Default: 1
#   AIWEBTEST_SERVER_LOG_FILE         Optional explicit backend server log path
#   AIWEBTEST_DRY_RUN                 Default: 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  sed -n '1,22p' "$0"
  exit 0
fi

export AIWEBTEST_API_BASE_URL="${AIWEBTEST_API_BASE_URL:-http://localhost:8000/api/v1}"
export AIWEBTEST_TEST_CASE_ID="${AIWEBTEST_TEST_CASE_ID:-101}"
export AIWEBTEST_USERNAME="${AIWEBTEST_USERNAME:-admin}"
export AIWEBTEST_PASSWORD="${AIWEBTEST_PASSWORD:-admin123}"
export AIWEBTEST_BACKEND_DIR="${AIWEBTEST_BACKEND_DIR:-${SCRIPT_DIR}/backend}"
export AIWEBTEST_BROWSER="${AIWEBTEST_BROWSER:-chromium}"
export AIWEBTEST_ENVIRONMENT="${AIWEBTEST_ENVIRONMENT:-dev}"
export AIWEBTEST_TARGET_URL="${AIWEBTEST_TARGET_URL:-}"
export AIWEBTEST_TRIGGERED_BY="${AIWEBTEST_TRIGGERED_BY:-scheduled}"
export AIWEBTEST_POLL_INTERVAL_SECONDS="${AIWEBTEST_POLL_INTERVAL_SECONDS:-15}"
export AIWEBTEST_POLL_TIMEOUT_SECONDS="${AIWEBTEST_POLL_TIMEOUT_SECONDS:-7200}"
export AIWEBTEST_REQUEST_TIMEOUT_SECONDS="${AIWEBTEST_REQUEST_TIMEOUT_SECONDS:-30}"
export AIWEBTEST_ENSURE_OPTION_C="${AIWEBTEST_ENSURE_OPTION_C:-1}"
export AIWEBTEST_APPEND_BACKEND_SERVER_LOG="${AIWEBTEST_APPEND_BACKEND_SERVER_LOG:-1}"
export AIWEBTEST_SERVER_LOG_FILE="${AIWEBTEST_SERVER_LOG_FILE:-}"
export AIWEBTEST_DRY_RUN="${AIWEBTEST_DRY_RUN:-0}"

python3 - <<'PY'
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def env_int(name: str) -> int:
    value = os.environ[name]
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {value!r}") from exc


def env_bool(name: str) -> bool:
    return os.environ[name].strip().lower() in {"1", "true", "yes", "on"}


def log(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


API_BASE_URL = os.environ["AIWEBTEST_API_BASE_URL"].rstrip("/")
TEST_CASE_ID = env_int("AIWEBTEST_TEST_CASE_ID")
USERNAME = os.environ["AIWEBTEST_USERNAME"]
PASSWORD = os.environ["AIWEBTEST_PASSWORD"]
BACKEND_DIR = Path(os.environ["AIWEBTEST_BACKEND_DIR"])
BROWSER = os.environ["AIWEBTEST_BROWSER"]
ENVIRONMENT = os.environ["AIWEBTEST_ENVIRONMENT"]
TARGET_URL_OVERRIDE = os.environ["AIWEBTEST_TARGET_URL"].strip()
TRIGGERED_BY = os.environ["AIWEBTEST_TRIGGERED_BY"]
POLL_INTERVAL_SECONDS = env_int("AIWEBTEST_POLL_INTERVAL_SECONDS")
POLL_TIMEOUT_SECONDS = env_int("AIWEBTEST_POLL_TIMEOUT_SECONDS")
REQUEST_TIMEOUT_SECONDS = env_int("AIWEBTEST_REQUEST_TIMEOUT_SECONDS")
ENSURE_OPTION_C = env_bool("AIWEBTEST_ENSURE_OPTION_C")
APPEND_BACKEND_SERVER_LOG = env_bool("AIWEBTEST_APPEND_BACKEND_SERVER_LOG")
SERVER_LOG_FILE_OVERRIDE = os.environ["AIWEBTEST_SERVER_LOG_FILE"].strip()
DRY_RUN = env_bool("AIWEBTEST_DRY_RUN")


def request_json(method: str, path: str, *, token: str | None = None, json_body=None, form_body=None):
    if json_body is not None and form_body is not None:
        raise RuntimeError("Only one of json_body or form_body may be set")

    url = f"{API_BASE_URL}{path}"
    headers = {"Accept": "application/json"}
    data = None

    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif form_body is not None:
        data = urllib.parse.urlencode(form_body).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed with HTTP {exc.code}: {raw_body}") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(f"{method} {path} failed: {reason}") from exc

    if not raw_body:
        return None

    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{method} {path} returned non-JSON response: {raw_body}") from exc


def infer_target_url(test_case: dict) -> str:
    if TARGET_URL_OVERRIDE:
        return TARGET_URL_OVERRIDE

    test_data = test_case.get("test_data") or {}
    if isinstance(test_data, dict):
        for key in ("base_url", "url", "target_url"):
            value = str(test_data.get(key) or "").strip()
            if value:
                return value

        detailed_steps = test_data.get("detailed_steps") or []
        if isinstance(detailed_steps, list):
            for step in detailed_steps:
                if not isinstance(step, dict):
                    continue
                if str(step.get("action") or "").lower() == "navigate":
                    for key in ("value", "url"):
                        value = str(step.get(key) or "").strip()
                        if value:
                            return value

    for step in test_case.get("steps") or []:
        match = URL_PATTERN.search(str(step))
        if match:
            return match.group(0).rstrip(".,)")

    raise RuntimeError(
        "Could not determine a target URL for this test case. "
        "Set AIWEBTEST_TARGET_URL explicitly for cron runs."
    )


def truncate(value: str, limit: int = 500) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def resolve_backend_server_log_path() -> Path:
    if SERVER_LOG_FILE_OVERRIDE:
        return Path(SERVER_LOG_FILE_OVERRIDE)
    return BACKEND_DIR / "logs" / f"server_{time.strftime('%Y%m%d')}.log"


def begin_backend_server_log_capture():
    if not APPEND_BACKEND_SERVER_LOG:
        return None

    log_path = resolve_backend_server_log_path()
    if not log_path.exists():
        log(
            "Backend server log file not found at {path}. "
            "To append full backend execution logs here, start backend/start_server.py "
            "with ENABLE_SERVER_FILE_LOGGING=true and restart the backend.".format(path=log_path)
        )
        return None

    start_offset = log_path.stat().st_size
    log(f"Will append backend server log from {log_path} starting at byte {start_offset}")
    return log_path, start_offset


def append_backend_server_log_segment(capture) -> None:
    if not capture:
        return

    log_path, start_offset = capture
    if not log_path.exists():
        log(f"Backend server log file disappeared before capture completed: {log_path}")
        return

    end_offset = log_path.stat().st_size
    if end_offset <= start_offset:
        log("No new backend server log output captured during this run")
        return

    log("----- BEGIN backend server log -----")
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(start_offset)
        chunk = handle.read()

    if chunk:
        print(chunk, end="" if chunk.endswith("\n") else "\n", flush=True)

    log("----- END backend server log -----")


def ensure_option_c_strategy(token: str) -> None:
    settings = request_json("GET", "/settings/execution", token=token)
    current_strategy = str(settings.get("fallback_strategy") or "").strip().lower()

    if current_strategy == "option_c":
        log("Execution fallback strategy already set to option_c")
        return

    if not ENSURE_OPTION_C:
        raise RuntimeError(
            f"Current fallback_strategy is {current_strategy or 'unset'!r}, not option_c. "
            "Either set AIWEBTEST_ENSURE_OPTION_C=1 or configure the user settings manually."
        )

    log(f"Updating execution fallback strategy from {current_strategy or 'unset'} to option_c")
    request_json(
        "PUT",
        "/settings/execution",
        token=token,
        json_body={
            "fallback_strategy": "option_c",
            "max_retry_per_tier": settings.get("max_retry_per_tier", 1),
            "timeout_per_tier_seconds": settings.get("timeout_per_tier_seconds", 30),
            "track_fallback_reasons": settings.get("track_fallback_reasons", True),
            "track_strategy_effectiveness": settings.get("track_strategy_effectiveness", True),
        },
    )


def login() -> str:
    log(f"Authenticating to {API_BASE_URL} as {USERNAME}")
    token_response = request_json(
        "POST",
        "/auth/login",
        form_body={"username": USERNAME, "password": PASSWORD},
    )
    token = token_response.get("access_token")
    if not token:
        raise RuntimeError("Login succeeded but no access_token was returned")
    return token


def poll_execution(token: str, execution_id: int) -> int:
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    last_signature = None

    while True:
        execution = request_json("GET", f"/executions/{execution_id}", token=token)
        status = str(execution.get("status") or "").lower()
        result = str(execution.get("result") or "").lower()
        signature = (
            status,
            result,
            execution.get("passed_steps"),
            execution.get("failed_steps"),
            execution.get("skipped_steps"),
        )

        if signature != last_signature:
            log(
                "Execution {execution_id} status={status} result={result} "
                "passed_steps={passed} failed_steps={failed} skipped_steps={skipped}".format(
                    execution_id=execution_id,
                    status=status or "unknown",
                    result=result or "n/a",
                    passed=execution.get("passed_steps", 0),
                    failed=execution.get("failed_steps", 0),
                    skipped=execution.get("skipped_steps", 0),
                )
            )
            last_signature = signature

        if status in TERMINAL_STATUSES:
            duration = execution.get("duration_seconds")
            if duration is not None:
                log(f"Execution {execution_id} finished in {duration} seconds")

            if status == "completed" and result == "pass":
                log(f"Execution {execution_id} passed")
                return 0

            detail = truncate(str(execution.get("error_message") or execution.get("console_log") or ""))
            if detail:
                log(f"Execution {execution_id} failure detail: {detail}")
            else:
                log(f"Execution {execution_id} ended with status={status} result={result or 'n/a'}")
            return 1

        if time.monotonic() >= deadline:
            log(f"Timed out waiting for execution {execution_id} after {POLL_TIMEOUT_SECONDS} seconds")
            return 124

        time.sleep(max(POLL_INTERVAL_SECONDS, 1))


def main() -> int:
    if POLL_INTERVAL_SECONDS < 1:
        raise RuntimeError("AIWEBTEST_POLL_INTERVAL_SECONDS must be at least 1")

    token = login()
    ensure_option_c_strategy(token)

    test_case = request_json("GET", f"/tests/{TEST_CASE_ID}", token=token)
    target_url = infer_target_url(test_case)

    payload = {
        "browser": BROWSER,
        "environment": ENVIRONMENT,
        "base_url": target_url,
        "triggered_by": TRIGGERED_BY,
    }

    if DRY_RUN:
        log("Dry run enabled; execution will not be triggered")
        print(
            json.dumps(
                {
                    "api_base_url": API_BASE_URL,
                    "test_case_id": TEST_CASE_ID,
                    "resolved_target_url": target_url,
                    "payload": payload,
                },
                indent=2,
            )
        )
        return 0

    backend_log_capture = begin_backend_server_log_capture()

    try:
        log(f"Triggering test case {TEST_CASE_ID} against {target_url}")
        start_response = request_json(
            "POST",
            f"/executions/tests/{TEST_CASE_ID}/run",
            token=token,
            json_body=payload,
        )

        execution_id = int(start_response["id"])
        message = str(start_response.get("message") or "Execution started")
        log(f"Execution {execution_id} created: {message}")

        return poll_execution(token, execution_id)
    finally:
        append_backend_server_log_segment(backend_log_capture)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("Interrupted")
        sys.exit(130)
    except Exception as exc:
        log(f"ERROR: {exc}")
        sys.exit(1)
PY