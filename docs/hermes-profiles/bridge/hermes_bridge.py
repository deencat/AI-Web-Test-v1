#!/usr/bin/env python3
"""Hermes Factory Bridge — run jobs and POST delegate events to AWT (HF-6.6).

Commands:
  serve          — HTTP server: POST /run accepts job JSON from AWT (HF-3.7 / HF-6.6)
  post-event     — Post a single event (smoke test)

Environment:
  HERMES_BRIDGE_SECRET       — shared with AWT backend/.env
  AWT_AGENT_EVENTS_URL       — e.g. http://awt:8000/api/v1/agent/hermes/events
  HERMES_BRIDGE_PORT         — default 8790
  HERMES_ORCHESTRATOR_CMD    — optional CLI (e.g. qa-orchestrator); if unset uses demo mode
  HERMES_BRIDGE_DEMO_MODE    — force demo delegate simulation (1/true)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [bridge] %(message)s")
logger = logging.getLogger("hermes_bridge")

_DELEGATE_CHAINS: dict[str, list[tuple[str, str]]] = {
    "full_cycle": [
        ("qa-journey-planner", "Planned backlog journeys"),
        ("qa-test-gen", "Generated test cases"),
        ("qa-dispatcher", "Executed regression suite"),
        ("qa-reporter", "Summarized results"),
    ],
    "drain_backlog": [
        ("qa-journey-planner", "Drained backlog queue"),
        ("qa-test-gen", "Generated tests for backlog items"),
    ],
    "generate_journey": [
        ("qa-journey-planner", "Resolved journey spec"),
        ("qa-test-gen", "Generated journey test case"),
    ],
    "run_regression": [
        ("qa-dispatcher", "Ran tagged regression tests"),
        ("qa-reporter", "Regression summary"),
    ],
    "scan_changes": [
        ("qa-change-detector", "Scanned registry URLs for material changes"),
    ],
    "heal_failures": [
        ("qa-healer", "Attempted heals on recent failures"),
    ],
}

# Demo payload_summary per job_type + profile (UI timeline smoke — not HF-3.1d pass)
_DEMO_DELEGATE_PAYLOADS: dict[tuple[str, str], dict[str, Any]] = {
    ("drain_backlog", "qa-journey-planner"): {
        "status": "success",
        "items_for_test_gen": [
            {
                "backlog_id": 42,
                "journey_slug": "5g-voucher-monthly",
                "project": "Three-HK",
            },
        ],
    },
    ("drain_backlog", "qa-test-gen"): {
        "status": "success",
        "test_case_id": 1291,
        "workflow_id": "demo-wf-001",
        "test_title": "[demo] 5G Voucher — new subscriber",
    },
    ("generate_journey", "qa-journey-planner"): {
        "status": "success",
        "journey_slug": "diy-dashboard",
    },
    ("generate_journey", "qa-test-gen"): {
        "status": "success",
        "test_case_id": 1292,
        "workflow_id": "demo-wf-002",
    },
}

_DEMO_JOB_COMPLETE_EXTRA: dict[str, dict[str, Any]] = {
    "drain_backlog": {"test_case_ids": [1291]},
    "generate_journey": {"test_case_ids": [1292]},
}


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def post_event(
    *,
    events_url: str,
    secret: str,
    job_id: str,
    event_type: str,
    profile: str | None = None,
    parent_profile: str | None = None,
    hermes_session_id: str | None = None,
    message: str | None = None,
    payload_summary: dict | None = None,
    payload_full: dict | None = None,
    llm_turns: list | None = None,
) -> dict:
    body: dict[str, Any] = {
        "job_id": job_id,
        "event_type": event_type,
        "profile": profile,
        "parent_profile": parent_profile,
        "hermes_session_id": hermes_session_id,
        "message": message,
        "payload_summary": payload_summary,
        "payload_full": payload_full,
        "llm_turns": llm_turns,
    }
    body = {k: v for k, v in body.items() if v is not None}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        events_url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _demo_mode() -> bool:
    if _env_bool("HERMES_BRIDGE_DEMO_MODE"):
        return True
    return not os.environ.get("HERMES_ORCHESTRATOR_CMD", "").strip()


def _run_orchestrator_cli(job_type: str, project: str | None, params: dict) -> None:
    cmd_base = os.environ.get("HERMES_ORCHESTRATOR_CMD", "qa-orchestrator").strip()
    payload = json.dumps(
        {"job_type": job_type, "project": project, "params": params},
    )
    result = subprocess.run(
        [cmd_base, "job", "run", "--json", payload],
        capture_output=True,
        text=True,
        timeout=int(os.environ.get("HERMES_ORCHESTRATOR_TIMEOUT", "3600")),
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"orchestrator exit {result.returncode}: {result.stderr or result.stdout}",
        )


def _simulate_delegates(
    *,
    events_url: str,
    secret: str,
    job_id: str,
    job_type: str,
    params: dict,
) -> None:
    session_id = f"sess_{job_id.replace('-', '')[:12]}"
    post_event(
        events_url=events_url,
        secret=secret,
        job_id=job_id,
        event_type="job_started",
        profile="qa-orchestrator",
        hermes_session_id=session_id,
        message=f"Bridge started {job_type}",
        payload_summary={"mode": "demo", "params": params},
    )
    post_event(
        events_url=events_url,
        secret=secret,
        job_id=job_id,
        event_type="delegate_start",
        profile="qa-orchestrator",
        parent_profile=None,
        hermes_session_id=session_id,
        message="Delegating to specialists",
    )

    chain = _DELEGATE_CHAINS.get(job_type, [("qa-orchestrator", f"Completed {job_type}")])
    for profile, msg in chain:
        post_event(
            events_url=events_url,
            secret=secret,
            job_id=job_id,
            event_type="delegate_start",
            profile=profile,
            parent_profile="qa-orchestrator",
            hermes_session_id=session_id,
            message=f"Delegate start: {profile}",
        )
        payload_summary: dict[str, Any] = {"status": "success", "profile": profile}
        demo_extra = _DEMO_DELEGATE_PAYLOADS.get((job_type, profile))
        if demo_extra:
            payload_summary = {**payload_summary, **demo_extra}
        post_event(
            events_url=events_url,
            secret=secret,
            job_id=job_id,
            event_type="delegate_complete",
            profile=profile,
            parent_profile="qa-orchestrator",
            hermes_session_id=session_id,
            message=msg,
            payload_summary=payload_summary,
            llm_turns=[
                {
                    "role": "assistant",
                    "content": f"[demo] {profile}: {msg}",
                    "tokens": 128,
                }
            ],
        )

    job_complete_summary: dict[str, Any] = {"status": "success", "job_type": job_type}
    job_extra = _DEMO_JOB_COMPLETE_EXTRA.get(job_type)
    if job_extra:
        job_complete_summary = {**job_complete_summary, **job_extra}
    post_event(
        events_url=events_url,
        secret=secret,
        job_id=job_id,
        event_type="job_complete",
        profile="qa-orchestrator",
        hermes_session_id=session_id,
        message=f"Bridge completed {job_type}",
        payload_summary=job_complete_summary,
    )


def execute_job(job_id: str, job_type: str, project: str | None, params: dict) -> None:
    events_url = os.environ.get("AWT_AGENT_EVENTS_URL", "")
    secret = os.environ.get("HERMES_BRIDGE_SECRET", "")
    if not events_url or not secret:
        raise RuntimeError("Set AWT_AGENT_EVENTS_URL and HERMES_BRIDGE_SECRET")

    params = params or {}
    if _demo_mode():
        logger.info("Job %s (%s) — demo delegate simulation", job_id, job_type)
        _simulate_delegates(
            events_url=events_url,
            secret=secret,
            job_id=job_id,
            job_type=job_type,
            params=params,
        )
        return

    logger.info("Job %s (%s) — invoking orchestrator CLI", job_id, job_type)
    session_id = f"sess_{job_id.replace('-', '')[:12]}"
    post_event(
        events_url=events_url,
        secret=secret,
        job_id=job_id,
        event_type="job_started",
        profile="qa-orchestrator",
        hermes_session_id=session_id,
        message=f"Orchestrator CLI started for {job_type}",
    )
    try:
        _run_orchestrator_cli(job_type, project, params)
        post_event(
            events_url=events_url,
            secret=secret,
            job_id=job_id,
            event_type="job_complete",
            profile="qa-orchestrator",
            hermes_session_id=session_id,
            message="Orchestrator CLI finished",
            payload_summary={"status": "success"},
        )
    except Exception as exc:
        post_event(
            events_url=events_url,
            secret=secret,
            job_id=job_id,
            event_type="error",
            profile="qa-orchestrator",
            hermes_session_id=session_id,
            message=str(exc),
            payload_summary={"status": "failed"},
        )
        raise


def _run_job_background(job_id: str, job_type: str, project: str | None, params: dict) -> None:
    try:
        execute_job(job_id, job_type, project, params)
    except Exception as exc:
        logger.exception("Job %s failed: %s", job_id, exc)


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = "HermesFactoryBridge/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info("%s - %s", self.address_string(), fmt % args)

    def _check_auth(self) -> bool:
        secret = os.environ.get("HERMES_BRIDGE_SECRET", "")
        if not secret:
            return True
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {secret}"

    def _json_response(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.rstrip("/") in ("", "/health", "/healthz"):
            self._json_response(200, {"status": "ok", "service": "hermes-factory-bridge"})
            return
        self._json_response(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/run":
            self._json_response(404, {"error": "not found"})
            return
        if not self._check_auth():
            self._json_response(401, {"error": "unauthorized"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._json_response(400, {"error": "invalid json"})
            return

        job_id = data.get("job_id")
        job_type = data.get("job_type")
        if not job_id or not job_type:
            self._json_response(400, {"error": "job_id and job_type required"})
            return

        project = data.get("project")
        params = data.get("params") or {}
        threading.Thread(
            target=_run_job_background,
            args=(job_id, job_type, project, params),
            daemon=True,
        ).start()
        self._json_response(202, {"accepted": True, "job_id": job_id})


def serve(port: int) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), BridgeHandler)
    logger.info("Listening on 0.0.0.0:%s (POST /run, GET /health)", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        server.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes Factory Bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    serve_p = sub.add_parser("serve", help="Run HTTP bridge server")
    serve_p.add_argument("--port", type=int, default=int(os.environ.get("HERMES_BRIDGE_PORT", "8790")))

    post_p = sub.add_parser("post-event", help="Post one event to AWT")
    post_p.add_argument("--job-id", required=True)
    post_p.add_argument("--type", dest="event_type", required=True)
    post_p.add_argument("--profile")
    post_p.add_argument("--parent-profile")
    post_p.add_argument("--session-id", dest="hermes_session_id")
    post_p.add_argument("--message")
    post_p.add_argument("--summary", help="JSON object for payload_summary")

    args = parser.parse_args()

    if args.command == "serve":
        serve(args.port)
        return 0

    secret = os.environ.get("HERMES_BRIDGE_SECRET", "")
    url = os.environ.get("AWT_AGENT_EVENTS_URL", "")
    if not secret or not url:
        print("Set HERMES_BRIDGE_SECRET and AWT_AGENT_EVENTS_URL", file=sys.stderr)
        return 1

    summary = json.loads(args.summary) if args.summary else None
    try:
        result = post_event(
            events_url=url,
            secret=secret,
            job_id=args.job_id,
            event_type=args.event_type,
            profile=args.profile,
            parent_profile=args.parent_profile,
            hermes_session_id=args.hermes_session_id,
            message=args.message,
            payload_summary=summary,
        )
        print(json.dumps(result, indent=2))
        return 0
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8"), file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    raise SystemExit(main())
