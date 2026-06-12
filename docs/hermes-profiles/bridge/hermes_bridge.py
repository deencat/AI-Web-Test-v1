#!/usr/bin/env python3
"""Hermes Factory Bridge — post delegate events to AWT (HF-6.6 stub).

Usage:
  export HERMES_BRIDGE_SECRET=...
  export AWT_AGENT_EVENTS_URL=http://localhost:8000/api/v1/agent/hermes/events
  python hermes_bridge.py post-event --job-id <uuid> --type delegate_complete --profile qa-test-gen
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


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
    body = {
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
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Post a Hermes Bridge event to AWT")
    parser.add_argument("command", choices=["post-event"])
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--type", dest="event_type", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--parent-profile")
    parser.add_argument("--session-id", dest="hermes_session_id")
    parser.add_argument("--message")
    parser.add_argument("--summary", help="JSON object for payload_summary")
    args = parser.parse_args()

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
