"""
Build Playwright-oriented locator metadata from browser-use DOM interaction snapshots.

Used by ObservationAgent when exporting flow_steps / playwright_flow_recording.
XPath and CDP backend_node_id can be brittle across runs; prefer data-testid / getByRole when present.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Safe for simple compound class selectors (alphanumeric + hyphen + underscore).
_CLASS_TOKEN_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

SCHEMA_VERSION = 1

# How many HTML class tokens to fold into a compound CSS selector (replay disambiguation).
MAX_CLASS_TOKENS_FOR_REPLAY_CSS = 8

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


def normalize_browser_use_attributes(
    attributes: Optional[Dict[str, Any]],
    *,
    class_attr_fallback: Optional[str] = None,
) -> Dict[str, str]:
    """
    Merge browser-use / CDP attribute dicts so ``class`` is available for replay CSS.

    Some snapshots expose ``className`` instead of ``class``, or omit class on the dict entirely
    while exposing it on the element model via ``class_name``.
    """
    raw: Dict[str, str] = {}
    for k, v in (attributes or {}).items():
        if v is None:
            continue
        raw[str(k)] = str(v).strip() if isinstance(v, (str, int, float)) else str(v)
    cls = (raw.get("class") or raw.get("className") or "").strip()
    if not cls and class_attr_fallback:
        cls = str(class_attr_fallback).strip()
    if cls:
        raw["class"] = cls
    return raw


def tokenize_html_class(class_str: str) -> List[str]:
    """Split HTML class attribute into non-empty tokens."""
    if not (class_str or "").strip():
        return []
    return [t for t in str(class_str).split() if t.strip()]


def css_selector_from_tag_and_classes(node_name: str, class_str: str) -> str:
    """
    Build a compound class CSS selector for record-and-replay (e.g. div.p-3.d-flex).
    Skips tokens that are unsafe for simple .class chaining (e.g. brackets, colons).
    """
    tokens = tokenize_html_class(class_str)[:MAX_CLASS_TOKENS_FOR_REPLAY_CSS]
    tag = (node_name or "div").strip().lower() or "div"
    if not tokens:
        return ""
    safe: List[str] = []
    for t in tokens:
        t = t.strip()
        if not t or not _CLASS_TOKEN_RE.match(t):
            continue
        safe.append(t)
    if not safe:
        return ""
    return f"{tag}.{'.'.join(safe)}"


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
    class_str = (attributes.get("class") or "").strip()
    compound = css_selector_from_tag_and_classes(node_name, class_str)
    if compound:
        suggestions.append(
            {
                "kind": "css",
                "selector": compound,
                "snippet": f"page.locator({compound!r})",
            }
        )
    if xpath:
        suggestions.append({"kind": "xpath", "snippet": f"page.locator({xpath!r})", "xpath": xpath})
    return suggestions


def normalize_strict_replay_locator(step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge nested ``locator`` with top-level fields from ``playwright_step_ir.json``.

    Persisted IR steps often omit a nested ``locator`` object and place ``xpath`` /
    ``playwright_suggestions`` / ``class_tokens`` on the step root; strict replay must see both.
    When ``class_tokens`` exist but there is no ``kind=css`` suggestion yet, append a compound-class
    selector for record-and-replay disambiguation.
    """
    loc = step.get("locator") if isinstance(step.get("locator"), dict) else {}
    xp_step = str(step.get("xpath") or "").strip()
    xp_loc = str(loc.get("xpath") or "").strip()
    xpath = xp_step or xp_loc or None

    sug_step = step.get("playwright_suggestions") if isinstance(step.get("playwright_suggestions"), list) else []
    sug_loc = loc.get("playwright_suggestions") if isinstance(loc.get("playwright_suggestions"), list) else []
    sug = sug_step if sug_step else sug_loc
    suggestions: List[Dict[str, Any]] = [s for s in sug if isinstance(s, dict)]

    attrs_step = step.get("attributes") if isinstance(step.get("attributes"), dict) else {}
    attrs_loc = loc.get("attributes") if isinstance(loc.get("attributes"), dict) else {}
    attrs = {**attrs_loc, **attrs_step}

    ct = step.get("class_tokens")
    if not isinstance(ct, list):
        inner_ct = loc.get("class_tokens")
        ct = inner_ct if isinstance(inner_ct, list) else []
    class_tokens = [t for t in ct if isinstance(t, str) and t.strip()]

    merged: Dict[str, Any] = {**loc}
    if xpath:
        merged["xpath"] = xpath
    else:
        merged.pop("xpath", None)
    merged["playwright_suggestions"] = suggestions
    merged["attributes"] = dict(attrs)
    if class_tokens:
        merged["class_tokens"] = class_tokens

    has_css = any(str(s.get("kind") or "") == "css" for s in suggestions)
    if not has_css and class_tokens:
        tag = str(step.get("element_type") or "div").lower() or "div"
        compound = css_selector_from_tag_and_classes(tag, " ".join(class_tokens))
        if compound:
            merged["playwright_suggestions"] = list(suggestions) + [
                {
                    "kind": "css",
                    "selector": compound,
                    "snippet": f"page.locator({compound!r})",
                }
            ]
    return merged


def build_locator_bundle(
    *,
    xpath: str = "",
    backend_node_id: Optional[int] = None,
    frame_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    ax_name: Optional[str] = None,
    node_name: str = "",
    stable_hash: Optional[int] = None,
    element_hash: Optional[int] = None,
    class_attr_fallback: Optional[str] = None,
) -> Dict[str, Any]:
    merged_fb = class_attr_fallback
    if not (merged_fb or "").strip():
        merged_fb = None
    attrs = normalize_browser_use_attributes(
        attributes,
        class_attr_fallback=merged_fb,
    )
    stable = pick_stable_attributes(attrs)
    suggestions = build_playwright_suggestions(
        attributes=attrs, ax_name=ax_name, node_name=node_name, xpath=xpath or ""
    )
    class_tokens = tokenize_html_class(str(attrs.get("class") or ""))[:8]
    bundle: Dict[str, Any] = {
        "xpath": xpath or None,
        "backend_node_id": backend_node_id,
        "frame_id": frame_id,
        "attributes": stable,
        "playwright_suggestions": suggestions,
    }
    if class_tokens:
        bundle["class_tokens"] = class_tokens
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
            "Steps mirror flow_steps with locator bundles. Prefer stable strategies (testId, role, id); "
            "xpath is positional; kind=css compound-class selectors are optional replay disambiguators when "
            "browser-use supplies a class attribute."
        ),
    }
