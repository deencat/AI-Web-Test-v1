"""
Build Playwright-oriented locator metadata from browser-use DOM interaction snapshots.

Used by ObservationAgent when exporting flow_steps / playwright_flow_recording.
XPath and CDP backend_node_id can be brittle across runs; prefer data-testid / getByRole when present.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = 1

# Attributes worth keeping for codegen and debugging (keep payload bounded)
STABLE_ATTR_KEYS = frozenset(
    {
        "id",
        "name",
        "role",
        "type",
        "href",
        "data-testid",
        "data-test",
        "data-cy",
        "data-selenium",
        "aria-label",
        "placeholder",
        "autocomplete",
        "accept",
    }
)


def pick_stable_attributes(attributes: Optional[Dict[str, str]]) -> Dict[str, str]:
    if not attributes:
        return {}
    return {k: v for k, v in attributes.items() if k in STABLE_ATTR_KEYS and v}


def build_playwright_suggestions(
    *,
    attributes: Dict[str, str],
    ax_name: Optional[str],
    node_name: str,
    xpath: str,
) -> List[Dict[str, Any]]:
    """Ordered Playwright-style locator strategies (prefer stable IDs over raw XPath)."""
    suggestions: List[Dict[str, Any]] = []
    tid = attributes.get("data-testid") or attributes.get("data-test") or attributes.get("data-cy")
    if tid:
        suggestions.append(
            {
                "kind": "testId",
                "snippet": f"page.getByTestId({tid!r})",
                "test_id": tid,
            }
        )
    role = (attributes.get("role") or "").strip() or None
    tag = (node_name or "").lower()
    if not role:
        if tag == "button":
            role = "button"
        elif tag == "a":
            role = "link"
    name = (ax_name or "").strip() or None
    if role and name:
        suggestions.append(
            {
                "kind": "role",
                "snippet": f"page.getByRole({role!r}, {{ name: {name!r} }})",
                "role": role,
                "name": name,
            }
        )
    el_id = (attributes.get("id") or "").strip()
    if el_id:
        # Escape simple id for CSS
        safe = el_id.replace("\\", "\\\\").replace('"', '\\"')
        suggestions.append({"kind": "css_id", "snippet": f'page.locator("#{safe}")', "id": el_id})
    if xpath:
        suggestions.append({"kind": "xpath", "snippet": f"page.locator({xpath!r})", "xpath": xpath})
    return suggestions


def build_locator_bundle(
    *,
    xpath: str = "",
    backend_node_id: Optional[int] = None,
    frame_id: Optional[str] = None,
    attributes: Optional[Dict[str, str]] = None,
    ax_name: Optional[str] = None,
    node_name: str = "",
    stable_hash: Optional[int] = None,
    element_hash: Optional[int] = None,
) -> Dict[str, Any]:
    attrs = attributes or {}
    stable = pick_stable_attributes(attrs)
    suggestions = build_playwright_suggestions(
        attributes=attrs, ax_name=ax_name, node_name=node_name, xpath=xpath or ""
    )
    bundle: Dict[str, Any] = {
        "xpath": xpath or None,
        "backend_node_id": backend_node_id,
        "frame_id": frame_id,
        "attributes": stable,
        "playwright_suggestions": suggestions,
    }
    if stable_hash is not None:
        bundle["stable_hash"] = stable_hash
    if element_hash is not None:
        bundle["element_hash"] = element_hash
    return bundle


def wrap_playwright_flow_recording(
    *,
    start_url: str,
    steps: List[Dict[str, Any]],
    goal_reached: bool,
) -> Dict[str, Any]:
    """Top-level object stored on observation result for API consumers and codegen pipelines."""
    return {
        "schema_version": SCHEMA_VERSION,
        "source": "browser-use-observation",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "start_url": start_url,
        "goal_reached": goal_reached,
        "steps": steps,
        "notes": (
            "Steps mirror flow_steps with locator bundles. Prefer playwright_suggestions[0] when "
            "stable; xpath/backend_node_id are fallbacks and may break after DOM changes."
        ),
    }
