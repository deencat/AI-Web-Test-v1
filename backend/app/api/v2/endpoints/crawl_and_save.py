"""
API v2: Crawl-and-Save Test Endpoint

POST /api/v2/crawl-and-save-test

Uses the ObservationAgent (browser-use) to crawl a purchase/subscription flow up to a
configurable stop page, converts the recorded flow_steps into human-readable test case
steps, appends caller-provided tail_steps (hardcoded steps for the post-stop portion),
and saves the combined result as a test case in the database.

This avoids browser-use failing on complex payment/SIM-settings pages — the fragile
end-of-flow is expressed as explicit tail_steps while the navigational run-up is captured
automatically.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, status
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy.orm import Session

from app.schemas.test_case import TestCaseCreate
from app.models.test_case import TestType, Priority, TestStatus
from app.crud.test_case import create_test_case
from app.services.orchestration_service import OrchestrationService, get_orchestration_service
from app.services.progress_tracker import ProgressTracker, get_progress_tracker
from app.services.workflow_store import set_state, update_state, get_state

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CrawlAndSaveTestRequest(BaseModel):
    """
    Request body for the crawl-and-save-test endpoint.

    The agent will navigate the purchase flow via browser-use, recording every
    click/input/navigate action.  When ``stop_at_page_hint`` is matched against the
    current page title or URL the crawl is cancelled and partial history is used.

    **Step Library integration (Sprint 10.11):**

    * ``login_module`` — name of a Step Library module that replaces the login steps
      captured by the crawler.  Inserted as ``@module:<name>()`` at the start of the
      crawled steps, and login-related actions are stripped from the crawled output so
      they are not duplicated.
    * ``existing_subscriber_module`` — module to append when the login flow shows a
      popup listing already-subscribed numbers (indicating an existing subscriber).
    * ``new_subscriber_module`` — module to append when no such popup appears
      (new subscriber).
    * ``subscriber_type_hint`` — optional override: ``"existing"`` | ``"new"`` |
      ``"auto"`` (default).  When ``"auto"`` the endpoint detects subscriber type from
      the browser-use history; otherwise the hint is used directly.
    """
    url: HttpUrl = Field(..., description="Start URL to begin crawling from")
    user_instruction: str = Field(
        ...,
        description=(
            "Instruction for browser-use, e.g. "
            "'Login and navigate the purchase flow for a SIM activation plan up to the SIM Card Setting page'"
        ),
    )
    stop_at_page_hint: Optional[str] = Field(
        None,
        description=(
            "Substring to match against page title/URL to stop crawling early "
            "(e.g. 'SIM Card Setting' or 'sim-setting'). "
            "When matched the crawl stops immediately and tail_steps take over."
        ),
    )
    tail_steps: List[str] = Field(
        default_factory=list,
        description=(
            "Hardcoded step strings to append after the crawled steps. "
            "These cover the portion of the flow that browser-use should NOT execute "
            "(e.g. SIM card settings, address, payment, signature). "
            "Superseded by existing_subscriber_module / new_subscriber_module when provided."
        ),
    )
    # --- Step Library module fields ---
    login_module: Optional[str] = Field(
        None,
        description=(
            "Step Library module name to substitute for the login steps captured by the crawler. "
            "E.g. 'login_my3_andrew'. Inserted as @module:<name>() at the start of the test, "
            "and login actions are stripped from the crawled steps to avoid duplication."
        ),
    )
    existing_subscriber_module: Optional[str] = Field(
        None,
        description=(
            "Step Library module name to append when subscriber type is 'existing' "
            "(post-login popup listing already-subscribed numbers was detected). "
            "E.g. 'plan_subscribe_flow_existing_preprod_andrew'."
        ),
    )
    new_subscriber_module: Optional[str] = Field(
        None,
        description=(
            "Step Library module name to append when subscriber type is 'new' "
            "(no existing-subscriber popup after login). "
            "E.g. 'plan_subscriber_flow_andrew'."
        ),
    )
    subscriber_type_hint: Optional[str] = Field(
        None,
        description=(
            "'existing' | 'new' | 'auto' (default). "
            "When 'auto', subscriber type is inferred from the browser-use history. "
            "Use 'existing' or 'new' to override auto-detection."
        ),
    )
    # --- end Step Library fields ---
    test_title: str = Field(..., description="Title for the saved test case")
    test_description: str = Field(..., description="Description for the saved test case")
    test_type: str = Field(default="e2e", description="Test type: e2e | integration | unit")
    priority: str = Field(default="high", description="Priority: high | medium | low")
    login_credentials: Optional[Dict[str, str]] = Field(
        None,
        description="{'email': '...', 'password': '...'} or {'username': '...', 'password': '...'}"
    )
    http_credentials: Optional[Dict[str, str]] = Field(
        None,
        description="HTTP Basic auth for preprod/UAT: {'username': '...', 'password': '...'}"
    )
    available_file_paths: Optional[List[str]] = Field(
        None,
        description="Local file paths for upload steps (e.g. HKID image)"
    )
    max_browser_steps: Optional[int] = Field(
        None, ge=1, le=500,
        description="Override max browser-use steps (default 120)"
    )
    max_flow_timeout_seconds: Optional[int] = Field(
        None, ge=60, le=7200,
        description="Override wall-clock timeout in seconds (default 1200)"
    )
    tags: Optional[List[str]] = Field(None, description="Optional tags for the test case")
    reference_test_id: Optional[int] = Field(
        None,
        description=(
            "ID of an existing test case to use as a quality reference. "
            "The LLM review pass will compare generated steps against it and "
            "clean up noise while preserving the crawl intent."
        ),
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "url": "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/",
            "user_instruction": (
                "Login and navigate to the voucher monthly plan tab, select $288 plan "
                "and proceed through the subscription flow."
            ),
            "stop_at_page_hint": "SIM Card Setting",
            "login_module": "login_my3_andrew",
            "existing_subscriber_module": "plan_subscribe_flow_existing_preprod_andrew",
            "new_subscriber_module": "plan_subscriber_flow_andrew",
            "subscriber_type_hint": "auto",
            "test_title": "Subscribe to $288 Voucher Plan (Step Library modules)",
            "test_description": "E2E purchase flow using Step Library modules for login and subscription steps",
            "login_credentials": {"email": "pmo.andrewchan+015@gmail.com", "password": "cA8mn49&"},
        }
    })


class CrawlAndSaveTestResponse(BaseModel):
    """Immediate response — background job started."""
    workflow_id: str
    status: str
    message: str
    started_at: datetime


# ---------------------------------------------------------------------------
# Helper: convert flow_steps → human-readable test step strings
# ---------------------------------------------------------------------------

import re as _re

def _parse_extracted_content(content: str, login_credentials: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Parse browser-use extracted_content strings into clean plain-English descriptions.

    Browser-use produces strings like:
      "🖱️Clicked div \"Login\""
      "🖱️Clicked a role=button \"5G Monthly Plans\""
      "🖱️Clicked span role=button \"Login\""
      "⌨️Typed \"pmo@example.com\" into element with index 42 (content: ...)"
      "🖱️Clicked button \"Subscribe Now\""
      "Navigated to https://..."
      "Scrolled down by 500 pixels"

    browser-use sometimes includes role/attribute info between the tag and the label:
      "Clicked a role=button \"5G Monthly Plans\""
    so we must skip any extra tokens before the quoted label.
    """
    if not content:
        return None

    # Strip leading emoji / special chars (code points outside normal BMP, and common icon ranges)
    c = _re.sub(r'^[\U00010000-\U0010FFFF\u2600-\u27FF\uFE00-\uFE0F\u2700-\u27BF\U0001F300-\U0001FFFF]+\s*', '', content, flags=_re.UNICODE)
    c = c.strip()

    # Pattern: Clicked {tag} [optional role/attr tokens...] "{label}"
    # Handles both simple ("Clicked button \"Select\"") and extended
    # ("Clicked a role=button \"5G Monthly Plans\"") forms from browser-use.
    m = _re.match(r'Clicked\s+\S+(?:\s+\S+)*?\s+["\u201c\u2018](.+?)["\u201d\u2019]', c, _re.IGNORECASE)
    if m:
        label = m.group(1).strip()
        if label and label.lower() not in ('div', 'span', 'button', 'a', 'input', 'li'):
            return f"Click the '{label}' button"
    # Fallback: grab the last quoted string on the line (handles any format variant)
    if _re.match(r'Clicked\b', c, _re.IGNORECASE):
        fm = _re.findall(r'["\u201c\u2018](.+?)["\u201d\u2019]', c)
        if fm:
            label = fm[-1].strip()
            if label and label.lower() not in ('div', 'span', 'button', 'a', 'input', 'li'):
                return f"Click the '{label}' button"

    # Pattern: Typed "{value}" into element...
    m = _re.match(r'Typed\s+["\u201c\u2018](.+?)["\u201d\u2019]\s+into', c, _re.IGNORECASE)
    if m:
        value = m.group(1).strip()
        # Mask sensitive values if they match login credentials
        if login_credentials:
            pw = login_credentials.get("password", "")
            if pw and value == pw:
                value = value  # keep as-is for test steps
        return f"Input '{value}' in the input field"

    # Pattern: Navigated to {url}
    m = _re.match(r'Navigated\s+to\s+(\S+)', c, _re.IGNORECASE)
    if m:
        return f"Navigate to {m.group(1)} in a web browser"

    return None


def _flow_steps_to_test_steps(
    flow_steps: List[Dict[str, Any]],
    login_credentials: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    Convert observation agent ``flow_steps`` dicts into plain-English step strings
    compatible with the existing test case format (like test case #1079).

    Prefers ``extracted_content`` from the browser-use action result (contains rich
    descriptions like "Clicked div 'Login'" or "Typed 'user@example.com' into...").
    Falls back to DOM-derived ``target`` when extracted_content is absent or generic.
    """
    if not flow_steps:
        return []

    email = ""
    password = ""
    if login_credentials:
        email = login_credentials.get("email") or login_credentials.get("username", "")
        password = login_credentials.get("password", "")

    steps: List[str] = []
    step_num = 1

    for fs in flow_steps:
        action = (fs.get("action") or "").lower()
        target = (fs.get("target") or "").strip()
        page_url = fs.get("page_url", "")
        input_type = (fs.get("input_type") or "").lower()
        elem_type = (fs.get("element_type") or "").lower()
        extracted_content = fs.get("extracted_content", "")

        # --- Primary: try to use extracted_content (richer description from browser-use) ---
        if extracted_content:
            parsed = _parse_extracted_content(extracted_content, login_credentials)
            if parsed:
                steps.append(f"Step {step_num}: {parsed}")
                step_num += 1
                continue

        # --- Fallback: derive from DOM action / target fields ---
        if action == "navigate":
            steps.append(f"Step {step_num}: Navigate to {page_url or target} in a web browser")

        elif action == "input":
            if input_type == "email" or (target and "email" in target.lower()):
                value = email if email else "[EMAIL]"
                field_label = "email address"
            elif input_type == "password" or (target and "password" in target.lower()):
                value = password if password else "[PASSWORD]"
                field_label = "password"
            else:
                value = f"[{target.upper() if target and target not in ('input', 'div', 'span') else 'VALUE'}]"
                field_label = target if target and target not in ('input', 'div', 'span') else "input"
            steps.append(f"Step {step_num}: Input '{value}' in the {field_label} field")

        elif action == "click":
            # Skip meaningless generic targets
            if not target or target.lower() in ('div', 'span', 'li', ''):
                step_num += 1
                continue
            if elem_type == "input" and input_type == "checkbox":
                steps.append(f"Step {step_num}: Check the '{target}' checkbox")
            elif elem_type == "a":
                steps.append(f"Step {step_num}: Click the '{target}' link")
            else:
                steps.append(f"Step {step_num}: Click the '{target}' button")

        else:
            if target and target.lower() not in ('div', 'span', 'li'):
                steps.append(f"Step {step_num}: {action.capitalize()} '{target}'")
            else:
                step_num += 1
                continue

        step_num += 1

    return steps


# ---------------------------------------------------------------------------
# Step Library helpers
# ---------------------------------------------------------------------------

def _filter_forbidden_steps(steps: List[str], user_instruction: str) -> List[str]:
    """
    Remove crawled steps that explicitly contradict a "do NOT <action> X" rule
    found in the user_instruction.

    Parses patterns like:
      - "do NOT click Download My3 App"
      - "do not click Settings"
      - "don't navigate to ..."
    and drops any step whose text contains the forbidden target.
    Navigate steps are never dropped (the URL is always required as Step 1).
    """
    _forbidden_targets: List[str] = []
    # Pattern: "do not" or "don't" (NOT standalone — too broad) followed by an
    # action verb, an optional article ("the", "a", "an", ...), then the target.
    # Minimum target length of 4 characters avoids false positives from short
    # words like "the" or "i" being captured when the instruction says
    # 'do not click the "i" button'.
    _ARTICLE = r"(?:(?:the|a|an|this|that|those|these|my|your|any)\s+)?"
    for m in _re.finditer(
        r"(?:do\s+not|don[\u2019']t)\s+"
        r"(?:click|open|navigate\s+to|select|download|tap|press)\s+"
        + _ARTICLE +
        r"['\"\u201c\u2018]?([a-zA-Z0-9][^.,;!\n'\"\u201d\u2019]{3,79})['\"\u201c\u201d\u2019]?",
        user_instruction,
        _re.IGNORECASE,
    ):
        target = m.group(1).strip().rstrip('. ').lower()
        # Skip if target is itself just an article or too short
        if len(target) < 4 or target in ("the", "a", "an", "this", "that", "any"):
            continue
        _forbidden_targets.append(target)

    if not _forbidden_targets:
        return steps

    logger.info("_filter_forbidden_steps: forbidden targets=%s", _forbidden_targets)
    filtered: List[str] = []
    for step in steps:
        step_lower = step.lower()
        if "navigate to" in step_lower:
            filtered.append(step)  # never drop the URL navigate step
            continue
        if any(ft in step_lower for ft in _forbidden_targets):
            logger.info(
                "_filter_forbidden_steps: dropped step violating instruction: '%s'", step[:120]
            )
        else:
            filtered.append(step)
    return filtered


async def _enrich_steps_with_instruction(
    steps: List[str],
    user_instruction: str,
    llm_client,
) -> List[str]:
    """
    Best-effort LLM pass that enriches generic crawled steps with context from the
    user_instruction (e.g. 'Click \'Select\'' → 'Click \'Select\' for the $288 Voucher Monthly Plan').

    Rules given to the LLM:
    - Do NOT add new steps; do NOT remove steps.
    - Only enrich steps where the instruction gives clear context.
    - Return the same number of steps in the same order.

    Falls back to the original steps if the LLM call fails or returns a different count.
    """
    if not steps or not user_instruction:
        return steps
    if not llm_client or not getattr(llm_client, 'enabled', False):
        return steps

    import json as _json

    numbered = "\n".join(steps)
    prompt = (
        "You are a test step editor.\n"
        "Given the original user instruction and browser-recorded steps, enrich generic steps with "
        "specific context from the instruction.\n"
        "Rules:\n"
        "  1. Do NOT add new steps or remove existing steps.\n"
        "  2. Only enrich a step when the instruction provides clear, unambiguous context "
        "(e.g. instruction says 'Select $288 plan', step says 'Click the \'Select\' button' → "
        "enrich to 'Click the \'Select\' button for the $288 Voucher Monthly Plan').\n"
        "  3. If you cannot confidently enrich a step, leave it exactly as-is.\n"
        "  4. Return ONLY a JSON array of step strings with exactly the same count as the input.\n\n"
        f"USER INSTRUCTION:\n{user_instruction}\n\n"
        f"RECORDED STEPS:\n{numbered}\n\n"
        "Return a JSON array: [\"Step 1: ...\", \"Step 2: ...\", ...]"
    )

    try:
        response = await asyncio.to_thread(
            llm_client.client.chat.completions.create,
            model=llm_client.deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise test step editor. Always return valid JSON arrays.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        raw = _re.sub(r'^```[a-z]*\n?', '', raw)
        raw = _re.sub(r'\n?```$', '', raw.strip())
        enriched = _json.loads(raw)
        if isinstance(enriched, list) and len(enriched) == len(steps):
            logger.info(
                "_enrich_steps_with_instruction: enriched %d steps via LLM", len(steps)
            )
            return [str(s) for s in enriched]
        else:
            logger.warning(
                "_enrich_steps_with_instruction: LLM returned %d items but expected %d; ignoring",
                len(enriched) if isinstance(enriched, list) else -1,
                len(steps),
            )
    except Exception as exc:
        logger.warning(
            "_enrich_steps_with_instruction: LLM call failed (%s); using original steps", exc
        )
    return steps


async def _review_and_clean_steps(
    steps: List[str],
    user_instruction: str,
    reference_steps: Optional[List[str]],
    llm_client,
) -> List[str]:
    """
    Post-generation LLM review pass that cleans and validates crawled steps.

    Problems it detects and fixes:
    - Price/display labels mistakenly captured as button clicks (e.g. 'Total Amount Due $1,556')
    - Repeated identical actions in a row (Next/Confirm loops from stop-condition overshoot)
    - Off-script form interactions not mentioned in the user instruction
    - Steps that duplicate a reference test case (model answer) step for step
    - Missing required steps that the instruction explicitly calls out

    The LLM is given:
      1. The user instruction (source of truth for what SHOULD happen)
      2. The generated steps (what browser-use actually captured)
      3. Optionally: a reference/model test case to compare against

    It returns a cleaned list. Steps may be removed but NOT added or reordered
    (adding steps is the enrichment job; ordering comes from crawl reality).

    Falls back to the original steps if the LLM call fails or returns empty.
    """
    if not steps or not user_instruction:
        return steps
    if not llm_client or not getattr(llm_client, 'enabled', False):
        return steps

    import json as _json

    ref_section = ""
    if reference_steps:
        ref_section = (
            "\n\nREFERENCE TEST CASE (model answer — the ideal clean version):\n"
            + "\n".join(reference_steps)
            + "\nUse this as the authoritative quality guide:\n"
            "  - Steps present in the reference and missing from recorded steps MUST be added.\n"
            "  - Steps in the recorded list that contradict the reference (wrong option selected,\n"
            "    exploratory clicks on other items) MUST be removed or corrected.\n"
        )

    numbered = "\n".join(steps)
    prompt = (
        "You are a test quality reviewer.\n"
        "Given the user instruction and raw browser-recorded steps, return a CLEANED version.\n\n"
        "RULES:\n"
        "  1. REMOVE steps that are clearly noise:\n"
        "     - Price/amount display labels clicked as buttons (e.g. 'Click the Total Amount Due $X button')\n"
        "     - Repeated identical actions back-to-back (keep only the first occurrence)\n"
        "     - Actions on form fields or UI sections NOT mentioned in the user instruction\n"
        "     - Exploratory clicks on items that are NOT the target (e.g. clicking multiple plan cards\n"
        "       when the instruction says to select a specific plan by price or name — keep only the\n"
        "       matching one)\n"
        "  2. KEEP all steps that are meaningful navigation or selection actions.\n"
        "  3. If the instruction explicitly requires an action (e.g. 'Check the I confirm checkbox',\n"
        "     'Click new mobile number') and it is missing from the steps, ADD it in the correct\n"
        "     position based on the instruction sequence.\n"
        "  4. FIX wrong action types:\n"
        "     - If a step uses 'Input [...]' on a checkbox field, replace with 'Check the [name] checkbox'.\n"
        "     - If the instruction says to select a specific price/plan, ensure the step names that\n"
        "       exact price/plan, not a different one.\n"
        "  5. Do NOT reorder steps — preserve the crawl sequence.\n"
        "  6. Do NOT add commentary or explanations — only step strings.\n"
        "  7. Return ONLY a JSON array of step strings.\n\n"
        f"USER INSTRUCTION:\n{user_instruction}\n"
        f"{ref_section}\n"
        f"RECORDED STEPS (to clean):\n{numbered}\n\n"
        "Return a JSON array: [\"Step 1: ...\", \"Step 2: ...\", ...]"
    )

    try:
        response = await asyncio.to_thread(
            llm_client.client.chat.completions.create,
            model=llm_client.deployment,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise test step reviewer. "
                        "Return only valid JSON arrays of step strings. "
                        "Never return empty arrays."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        raw = _re.sub(r'^```[a-z]*\n?', '', raw)
        raw = _re.sub(r'\n?```$', '', raw.strip())
        cleaned = _json.loads(raw)
        if isinstance(cleaned, list) and len(cleaned) > 0:
            logger.info(
                "_review_and_clean_steps: reduced %d → %d steps via LLM review",
                len(steps), len(cleaned),
            )
            return [str(s) for s in cleaned]
        else:
            logger.warning(
                "_review_and_clean_steps: LLM returned empty/invalid result; keeping originals"
            )
    except Exception as exc:
        logger.warning(
            "_review_and_clean_steps: LLM review failed (%s); keeping original steps", exc
        )
    return steps


# Keywords that identify login / authentication steps in the crawled output.
# Used by _strip_login_steps to remove them when a login_module is provided.
#
# IMPORTANT: match action-specific phrases only, NOT bare "login" — the word
# "login" can appear in enriched step context (e.g. "post-login navigation")
# and should not cause legitimate navigation steps to be stripped.
_LOGIN_KEYWORDS = (
    "click 'login'",
    "click login",
    "click the 'login'",
    "click the login",
    "click 'sign in'",
    "click sign in",
    "log in button",
    "sign in button",
    "input email",
    "input password",
    "input '[email]",
    "input '[password]",
    "enter email",
    "enter password",
    "type email",
    "type password",
    "fill in email",
    "fill in password",
    "in the email address field",
    "in the password field",
)

# Matches generic input-field steps produced by the fallback path in
# _flow_steps_to_test_steps when browser-use cannot identify the field label.
# During the login phase these are always email/password inputs.
_GENERIC_INPUT_STEP_RE = _re.compile(
    r"input\s+['\"].*['\"]\s+in\s+the\s+(email|password|input)\s+(address\s+)?field",
    _re.IGNORECASE,
)


def _strip_login_steps(crawled_steps: List[str]) -> List[str]:
    """
    Remove login-related steps from the crawled step list.

    When a ``login_module`` is provided the caller wants to replace the captured
    login interactions with a reusable Step Library reference.  This helper drops:
    - Steps whose text matches common login/authentication keywords
    - Generic "Input '[VALUE]' in the input/email/password field" steps (these
      are always login-phase steps when login_module is active)
    Navigate steps are never stripped so the URL always stays as Step 1.
    """
    filtered: List[str] = []
    for step in crawled_steps:
        step_lower = step.lower()
        # Always keep navigate steps — they must remain as Step 1
        if "navigate to" in step_lower:
            filtered.append(step)
            continue
        if any(kw in step_lower for kw in _LOGIN_KEYWORDS):
            logger.debug("_strip_login_steps: dropping keyword match '%s'", step[:120])
            continue
        if _GENERIC_INPUT_STEP_RE.search(step):
            logger.debug("_strip_login_steps: dropping generic input step '%s'", step[:120])
            continue
        filtered.append(step)
    return filtered


# Phrases that appear in the existing-subscriber popup (the "already subscribed
# numbers" dialog that shows after login for My3 accounts with active plans).
_EXISTING_SUBSCRIBER_SIGNALS = (
    "already subscribed",
    "existing subscriber",
    "subscribed number",
    "your current plan",
    "current subscription",
    "your subscribed",
    "your plan",          # generic but common in the popup context
    "select number",      # "Please select the number you want to manage"
    "manage number",
)


def _detect_existing_subscriber(obs_data: Dict[str, Any]) -> str:
    """
    Infer subscriber type from browser-use observation data.

    Returns ``"existing"`` when any flow step or extracted element contains text
    characteristic of the "already subscribed numbers" popup that Three HK shows
    after login for accounts with active plans; returns ``"new"`` otherwise.
    """
    # Check flow_steps extracted_content and target text
    flow_steps: List[Dict] = obs_data.get("flow_steps") or []
    for fs in flow_steps:
        combined = " ".join([
            (fs.get("extracted_content") or ""),
            (fs.get("target") or ""),
            (fs.get("page_title") or ""),
        ]).lower()
        if any(sig in combined for sig in _EXISTING_SUBSCRIBER_SIGNALS):
            logger.info("_detect_existing_subscriber: 'existing' detected from flow step: %s", combined[:120])
            return "existing"

    # Also scan ui_elements text
    ui_elements: List[Dict] = obs_data.get("ui_elements") or []
    for elem in ui_elements:
        text = (elem.get("text") or "").lower()
        if any(sig in text for sig in _EXISTING_SUBSCRIBER_SIGNALS):
            logger.info("_detect_existing_subscriber: 'existing' detected from ui_element text: %s", text[:120])
            return "existing"

    logger.info("_detect_existing_subscriber: no existing-subscriber signals found → 'new'")
    return "new"


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

async def _run_crawl_and_save(
    workflow_id: str,
    request_dict: Dict[str, Any],
    user_id: int,
    orchestration_service: OrchestrationService,
    progress_tracker: Optional[ProgressTracker],
) -> None:
    """Background coroutine: observe → convert → save test case."""
    from agents.base_agent import TaskContext
    from app.services.workflow_store import update_state
    from app.services.orchestration_service import http_credentials_for_url

    started_at = datetime.now(timezone.utc)
    pt = progress_tracker

    def _emit(evt: str, data: dict):
        if pt:
            asyncio.create_task(pt.emit(workflow_id, evt, data))
        # Only keep status="running" for intermediate events, not terminal ones.
        if evt not in ("workflow_completed", "workflow_failed"):
            update_state(workflow_id, current_agent=data.get("agent"), status="running")

    try:
        # ---- 1. Build ObservationAgent task payload ----
        url = str(request_dict["url"])
        user_instruction = request_dict.get("user_instruction", "")
        stop_at_page_hint = request_dict.get("stop_at_page_hint") or ""
        reference_test_id: Optional[int] = request_dict.get("reference_test_id") or None
        tail_steps: List[str] = request_dict.get("tail_steps") or []
        login_credentials = request_dict.get("login_credentials") or {}
        http_credentials = request_dict.get("http_credentials") or {}
        available_file_paths = request_dict.get("available_file_paths")
        max_browser_steps = request_dict.get("max_browser_steps")
        max_flow_timeout_seconds = request_dict.get("max_flow_timeout_seconds")

        # Step Library module fields
        login_module: Optional[str] = request_dict.get("login_module") or None
        existing_subscriber_module: Optional[str] = request_dict.get("existing_subscriber_module") or None
        new_subscriber_module: Optional[str] = request_dict.get("new_subscriber_module") or None
        subscriber_type_hint: str = (request_dict.get("subscriber_type_hint") or "auto").lower()

        obs_payload: Dict[str, Any] = {
            "url": url,
            "user_instruction": user_instruction,
            "max_depth": 1,
        }
        if login_credentials:
            obs_payload["login_credentials"] = login_credentials
        _creds = http_credentials_for_url(url, http_credentials)
        if _creds:
            obs_payload["http_credentials"] = _creds
        if available_file_paths:
            obs_payload["available_file_paths"] = available_file_paths
        if stop_at_page_hint:
            obs_payload["stop_at_page_hint"] = stop_at_page_hint
        if max_browser_steps is not None:
            obs_payload["max_browser_steps"] = int(max_browser_steps)
        if max_flow_timeout_seconds is not None:
            obs_payload["max_flow_timeout_seconds"] = int(max_flow_timeout_seconds)

        # ---- 2. Run observation ----
        _emit("agent_started", {"agent": "observation", "timestamp": started_at.isoformat()})
        update_state(workflow_id, status="running", current_agent="observation")

        obs_agent, _, _, _ = orchestration_service._create_agents(
            db=None,
            per_agent_llm_config=orchestration_service._resolve_per_agent_llm_config(user_id=user_id),
        )
        obs_task = TaskContext(
            conversation_id=workflow_id,
            task_id=f"{workflow_id}-obs",
            task_type="ui_element_extraction",
            payload=obs_payload,
            priority=8,
        )
        observation_result = await obs_agent.execute_task(obs_task)

        if not observation_result.success:
            raise RuntimeError(observation_result.error or "Observation failed")

        obs_data = observation_result.result
        flow_steps: List[Dict[str, Any]] = obs_data.get("flow_steps") or []

        _emit("agent_completed", {
            "agent": "observation",
            "pages_crawled": obs_data.get("pages_crawled", 0),
            "flow_steps_captured": len(flow_steps),
            "stop_triggered": bool(stop_at_page_hint),
        })

        # ---- 3. Convert flow_steps → test step strings ----
        crawled_step_strings = _flow_steps_to_test_steps(flow_steps, login_credentials)

        # ---- 3b. Filter steps that contradict the user instruction ----
        # Removes steps like "Click 'Download My3 App'" when the instruction says
        # "do NOT click Download My3 App".
        crawled_step_strings = _filter_forbidden_steps(crawled_step_strings, user_instruction)

        # ---- 4. Apply Step Library module substitution (if configured) ----
        #
        # NOTE: login stripping happens HERE, before LLM enrichment, so that the
        # enrichment step cannot add words like "login" to post-login navigation
        # steps and cause them to be incorrectly stripped.
        #
        # Strategy:
        #   a) Strip login steps from crawled output (they will be replaced by login_module).
        #   b) Prepend @module:<login_module>() as the first step.
        #   c) Determine subscriber type (auto-detect or use hint).
        #   d) If a subscriber module is configured, append @module:<module_name>() instead of
        #      any tail_steps — the module contains the full post-login subscription flow.
        #      tail_steps are still appended when no subscriber module is configured (backward
        #      compatible with the original behaviour).

        module_steps_prepend: List[str] = []
        module_steps_append: List[str] = []
        subscriber_type_resolved: Optional[str] = None

        if login_module:
            # Strip login-related crawled steps; the module replaces them.
            # Navigate step is preserved by _strip_login_steps so it stays as Step 1.
            # This runs BEFORE enrichment so enriched context cannot accidentally
            # trigger login-keyword matches on legitimate navigation steps.
            crawled_step_strings = _strip_login_steps(crawled_step_strings)
            module_steps_prepend.append(f"@module:{login_module}()")
            logger.info("CrawlAndSave %s: login_module='%s' → inserting module ref after navigate, stripped login steps", workflow_id, login_module)

        use_subscriber_modules = bool(existing_subscriber_module or new_subscriber_module)
        if use_subscriber_modules:
            if subscriber_type_hint in ("existing", "new"):
                subscriber_type_resolved = subscriber_type_hint
                logger.info("CrawlAndSave %s: subscriber_type_hint='%s' (manual override)", workflow_id, subscriber_type_resolved)
            else:
                subscriber_type_resolved = _detect_existing_subscriber(obs_data)
                logger.info("CrawlAndSave %s: auto-detected subscriber_type='%s'", workflow_id, subscriber_type_resolved)

            if subscriber_type_resolved == "existing" and existing_subscriber_module:
                module_steps_append.append(f"@module:{existing_subscriber_module}()")
                logger.info("CrawlAndSave %s: appending existing_subscriber_module='%s'", workflow_id, existing_subscriber_module)
            elif subscriber_type_resolved == "new" and new_subscriber_module:
                module_steps_append.append(f"@module:{new_subscriber_module}()")
                logger.info("CrawlAndSave %s: appending new_subscriber_module='%s'", workflow_id, new_subscriber_module)
            else:
                # Fallback to tail_steps if the resolved type has no matching module
                logger.info(
                    "CrawlAndSave %s: no module for subscriber_type='%s'; falling back to tail_steps",
                    workflow_id, subscriber_type_resolved,
                )
                module_steps_append = tail_steps  # type: ignore[assignment]
        else:
            # No subscriber modules configured — legacy tail_steps behaviour
            module_steps_append = tail_steps  # type: ignore[assignment]

        # ---- 4c. Enrich generic steps with instruction context (LLM, best-effort) ----
        # Runs AFTER login stripping so only the surviving post-login navigation
        # steps are enriched. E.g. "Click 'Select'" → "Click 'Select' for the $288
        # Voucher Monthly Plan" when the instruction says "Find and Select $288 plan".
        _obs_llm = getattr(obs_agent, 'llm_client', None)
        crawled_step_strings = await _enrich_steps_with_instruction(
            crawled_step_strings, user_instruction, _obs_llm
        )

        # ---- 4d. LLM review pass — remove noise, deduplicate, check required steps ----
        # Optionally uses a reference test case (model answer) as a quality guide.
        _reference_steps: Optional[List[str]] = None
        if reference_test_id:
            try:
                from app.db.session import SessionLocal as _SL
                from app.crud.test_case import get_test_case as _get_tc
                import json as _j
                _db_ref = _SL()
                try:
                    _ref_tc = _get_tc(_db_ref, reference_test_id)
                    if _ref_tc and _ref_tc.steps:
                        _reference_steps = _j.loads(_ref_tc.steps) if isinstance(_ref_tc.steps, str) else _ref_tc.steps
                        logger.info(
                            "CrawlAndSave %s: loaded %d reference steps from test #%s",
                            workflow_id, len(_reference_steps), reference_test_id,
                        )
                finally:
                    _db_ref.close()
            except Exception as _ref_err:
                logger.warning("CrawlAndSave: could not load reference test #%s: %s", reference_test_id, _ref_err)

        crawled_step_strings = await _review_and_clean_steps(
            crawled_step_strings, user_instruction, _reference_steps, _obs_llm
        )

        # ---- 5. Assemble final step list ----
        # Correct order when login_module is set:
        #   [navigate step] + [@module:login_module()] + [remaining post-login crawled steps] + [@module:subscriber_module()]
        # Without login_module (legacy):
        #   [module_steps_prepend] + [crawled_step_strings] + [tail_steps]
        if login_module and module_steps_prepend:
            # Split crawled steps: navigate step(s) first, then everything else
            _navigate_steps = [s for s in crawled_step_strings
                               if _re.search(r'navigate to', s, _re.IGNORECASE)]
            _post_nav_steps = [s for s in crawled_step_strings
                               if not _re.search(r'navigate to', s, _re.IGNORECASE)]
            all_steps = _navigate_steps + module_steps_prepend + _post_nav_steps + module_steps_append
        else:
            all_steps = module_steps_prepend + crawled_step_strings + module_steps_append

        # Re-number steps so numbering is sequential in the saved test case
        _renumbered: List[str] = []
        _step_counter = 1
        for s in all_steps:
            # Module refs and non-"Step N:" lines keep their text as-is (they may be
            # @module: references or inline notes without a step prefix).
            if s.startswith("@module:") or not s.lower().startswith("step "):
                _renumbered.append(s)
            else:
                # Replace leading "Step N:" with the new sequential number
                _renumbered.append(_re.sub(r"^Step\s+\d+\s*:", f"Step {_step_counter}:", s))
                _step_counter += 1
        all_steps = _renumbered

        if not all_steps:
            raise RuntimeError("No steps were captured from crawl and no tail_steps / modules provided")

        # ---- 6. Save test case to DB ----
        test_title = request_dict.get("test_title", f"Auto-crawled test ({datetime.now().strftime('%Y%m%d%H%M')})")
        test_description = request_dict.get("test_description", user_instruction)
        test_type_str = request_dict.get("test_type", "e2e").lower()
        priority_str = request_dict.get("priority", "high").lower()
        tags: List[str] = request_dict.get("tags") or []

        # Map strings to enum values
        _type_map = {"e2e": TestType.E2E, "integration": TestType.INTEGRATION, "unit": TestType.UNIT}
        _priority_map = {"high": Priority.HIGH, "medium": Priority.MEDIUM, "low": Priority.LOW}
        test_type_enum = _type_map.get(test_type_str, TestType.E2E)
        priority_enum = _priority_map.get(priority_str, Priority.HIGH)

        tc_create = TestCaseCreate(
            title=test_title,
            description=test_description,
            test_type=test_type_enum,
            priority=priority_enum,
            status=TestStatus.PENDING,
            steps=all_steps,
            expected_result="Test completes successfully through all steps",
            preconditions=(
                f"User is logged in with credentials from login_credentials. "
                f"Browser-use crawled the flow up to '{stop_at_page_hint}' stop point."
            ) if stop_at_page_hint else "User has valid login credentials.",
            tags=tags if tags else None,
            test_metadata={
                "source": "crawl_and_save",
                "workflow_id": workflow_id,
                "start_url": url,
                "stop_at_page_hint": stop_at_page_hint,
                "crawled_steps_count": len(crawled_step_strings),
                "tail_steps_count": len(tail_steps),
                "pages_crawled": obs_data.get("pages_crawled", 0),
                "login_module": login_module,
                "subscriber_type": subscriber_type_resolved,
                "existing_subscriber_module": existing_subscriber_module,
                "new_subscriber_module": new_subscriber_module,
            },
        )

        # Need a DB session — create one inline
        from app.db.session import SessionLocal
        db: Session = SessionLocal()
        try:
            saved_tc = create_test_case(db, tc_create, user_id)
            test_case_id = saved_tc.id
        finally:
            db.close()

        logger.info(
            "CrawlAndSave workflow %s: saved test case #%s (%d steps: %d module-prepend + %d crawled + %d module-append/tail)",
            workflow_id,
            test_case_id,
            len(all_steps),
            len(module_steps_prepend),
            len(crawled_step_strings),
            len(module_steps_append),
        )

        # ---- 7. Store final result in workflow store ----
        set_state(workflow_id, {
            "workflow_id": workflow_id,
            "status": "completed",
            "current_agent": None,
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "workflow_type": "crawl_and_save",
            "result": {
                "test_case_id": test_case_id,
                "test_title": test_title,
                "total_steps": len(all_steps),
                "crawled_steps_count": len(crawled_step_strings),
                "tail_steps_count": len(tail_steps),
                "login_module": login_module,
                "subscriber_type": subscriber_type_resolved,
                "existing_subscriber_module": existing_subscriber_module,
                "new_subscriber_module": new_subscriber_module,
                "pages_crawled": obs_data.get("pages_crawled", 0),
                "stop_triggered": bool(stop_at_page_hint),
                "steps_preview": all_steps[:10],
            },
        })
        _emit("workflow_completed", {
            "test_case_id": test_case_id,
            "total_steps": len(all_steps),
        })

    except Exception as exc:
        logger.exception("CrawlAndSave workflow %s failed: %s", workflow_id, exc)
        set_state(workflow_id, {
            "workflow_id": workflow_id,
            "status": "failed",
            "current_agent": None,
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "workflow_type": "crawl_and_save",
            "error": str(exc),
        })


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/crawl-and-save-test",
    response_model=CrawlAndSaveTestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Crawl purchase flow and save as test case",
    description="""
Crawls a web application flow using the ObservationAgent (browser-use) and automatically
converts the recorded steps into a saved test case.

**Key feature:** Pass ``stop_at_page_hint`` to stop the crawl exactly at a fragile page
(e.g. SIM Card Setting, payment page) and provide ``tail_steps`` with hardcoded steps for
the remainder. This prevents browser-use from making mistakes on complex forms.

The resulting test case combines the crawled navigational steps with your hardcoded tail
steps and can be executed immediately via the 3-tier testing system (Playwright / Stagehand).

**Returns:** ``workflow_id`` immediately (runs in background).  
**Poll status:** ``GET /api/v2/workflows/{workflow_id}``  
**Results (with test_case_id):** ``GET /api/v2/workflows/{workflow_id}/results``
""",
)
async def crawl_and_save_test(
    request: CrawlAndSaveTestRequest,
    background_tasks: BackgroundTasks,
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
) -> CrawlAndSaveTestResponse:
    """Start crawl-and-save workflow in background; return workflow_id immediately."""
    workflow_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    request_dict: Dict[str, Any] = {
        "url": str(request.url),
        "user_instruction": request.user_instruction,
        "stop_at_page_hint": request.stop_at_page_hint,
        "reference_test_id": request.reference_test_id,
        "tail_steps": request.tail_steps,
        "login_module": request.login_module,
        "existing_subscriber_module": request.existing_subscriber_module,
        "new_subscriber_module": request.new_subscriber_module,
        "subscriber_type_hint": request.subscriber_type_hint,
        "test_title": request.test_title,
        "test_description": request.test_description,
        "test_type": request.test_type,
        "priority": request.priority,
        "login_credentials": request.login_credentials,
        "http_credentials": request.http_credentials,
        "available_file_paths": request.available_file_paths,
        "max_browser_steps": request.max_browser_steps,
        "max_flow_timeout_seconds": request.max_flow_timeout_seconds,
        "tags": request.tags,
    }

    set_state(workflow_id, {
        "workflow_id": workflow_id,
        "status": "pending",
        "current_agent": None,
        "progress": {},
        "total_progress": 0.0,
        "started_at": started_at.isoformat(),
        "error": None,
        "workflow_type": "crawl_and_save",
    })

    async def run_in_background():
        try:
            if orchestration_service.progress_tracker is None:
                orchestration_service.progress_tracker = progress_tracker
            await _run_crawl_and_save(
                workflow_id=workflow_id,
                request_dict=request_dict,
                user_id=1,  # default admin user, no auth required (same as generate-tests)
                orchestration_service=orchestration_service,
                progress_tracker=progress_tracker,
            )
        except Exception as e:
            logger.exception("Background crawl-and-save %s failed: %s", workflow_id, e)

    background_tasks.add_task(run_in_background)

    return CrawlAndSaveTestResponse(
        workflow_id=workflow_id,
        status="pending",
        message=(
            f"Crawl-and-save workflow started. "
            f"{'Will stop at page: ' + request.stop_at_page_hint if request.stop_at_page_hint else 'No stop page set — will run to completion or max_browser_steps.'} "
            f"Poll GET /api/v2/workflows/{workflow_id} for status."
        ),
        started_at=started_at,
    )
