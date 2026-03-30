"""
Convert ObservationAgent ``flow_steps`` (browser-use crawl) into natural-language
executable step strings for Phase 2 / 3-tier execution.

Shared by EvolutionAgent (stored test cases) and AnalysisAgent (real-time scoring runs).
The same list is serialized to ``flow_steps.json`` / ``playwright_flow_recording.json``.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def compact_observed_flow_steps(flow_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Drop consecutive duplicate steps (same action + target + page_url) often produced by
    browser-use retries. Preserves order. If everything would collapse (pathological input),
    returns the original list.
    """
    if not flow_steps:
        return []
    ordered = sorted(flow_steps, key=lambda s: s.get("order", 999))
    out: List[Dict[str, Any]] = []
    prev_key: Optional[tuple] = None
    for s in ordered:
        action = (s.get("action") or "").lower()
        target = (s.get("target") or "").strip()
        page_url = (s.get("page_url") or "").strip()
        key = (action, target, page_url)
        if key == prev_key:
            continue
        prev_key = key
        out.append(s)
    return out if out else list(flow_steps)


def flow_steps_to_natural_language_steps(
    flow_steps: List[Dict[str, Any]],
    login_credentials: Optional[Dict[str, Any]] = None,
    *,
    dedupe_consecutive: bool = False,
) -> Optional[List[str]]:
    """
    Map ordered flow_steps to strings like "Navigate to …", "Click '…'", "Input '…' into …".

    ``login_credentials`` may include email/username/password for filling login fields.
    When ``dedupe_consecutive`` is True, applies :func:`compact_observed_flow_steps` first
    (drops consecutive duplicate action/target/page from browser-use retries).
    """
    if not flow_steps:
        return None
    if dedupe_consecutive:
        flow_steps = compact_observed_flow_steps(flow_steps)
        if not flow_steps:
            return None
    creds = login_credentials if isinstance(login_credentials, dict) else {}
    steps: List[str] = []
    login_email = (creds.get("email") or creds.get("username") or "").strip()
    login_password = (creds.get("password") or "").strip()
    ordered = sorted(flow_steps, key=lambda s: s.get("order", 999))
    for s in ordered:
        action = (s.get("action") or "").lower()
        target = (s.get("target") or "").strip()
        element_type = (s.get("element_type") or "").lower()
        input_type = (s.get("input_type") or "text").lower()
        if action == "navigate":
            steps.append(f"Navigate to {target}" if target else "Navigate to start URL")
        elif action == "click":
            steps.append(f"Click '{target}'" if target else "Click the button/link")
        elif action == "input":
            if "password" in target.lower() or input_type == "password" or element_type == "password":
                value = login_password if login_password else "[user's password]"
            elif any(k in target.lower() for k in ("email", "username", "e-mail", "account")):
                value = login_email if login_email else "[user's email]"
            else:
                value = "[value]"
            steps.append(f"Input '{value}' into {target}" if target else f"Input '{value}' into input field")
        else:
            if target:
                steps.append(f"{action.capitalize()} '{target}'")
            else:
                steps.append(action.capitalize())
    return steps if steps else None
