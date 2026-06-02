"""
AI-Powered Failure Root Cause Analysis service — Sprint 10.12.

Generates a plain-English root cause explanation when all 3 tiers of execution
are exhausted (error_type == "all_tiers_exhausted").

Design decisions (ADR-002-43):
- Only fires on all_tiers_exhausted — no LLM cost on partial failures.
- DOM snapshot is capped server-side (~16 000 chars ≈ 4 000 tokens) before
  being included in the prompt; it is never returned to the client.
- LLM call uses the project's existing UniversalLLMService.
- Exceptions from the LLM are caught and return None so execution is never
  disrupted by a failed RCA call.
"""
import logging
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

from app.services.universal_llm import UniversalLLMService

logger = logging.getLogger(__name__)

# DOM snapshot character cap (~4 000 tokens at a rough 4 chars/token estimate)
_DOM_CHAR_LIMIT = 16_000
_TRUNCATION_MARKER = "... [truncated]"


def _cap_dom_snapshot(raw_html: Optional[str]) -> str:
    """
    Trim the DOM snapshot to at most _DOM_CHAR_LIMIT characters.

    Args:
        raw_html: Raw HTML string from page.inner_html(); may be None or empty.

    Returns:
        Capped string safe to embed in an LLM prompt.
        Returns empty string for None / empty input.
    """
    if not raw_html:
        return ""
    if len(raw_html) <= _DOM_CHAR_LIMIT:
        return raw_html
    return raw_html[:_DOM_CHAR_LIMIT] + _TRUNCATION_MARKER


def _extract_tier_error(execution_history: List[Dict[str, Any]], tier: int) -> str:
    """Return the error string for *tier* from execution_history, or 'N/A'."""
    for entry in execution_history:
        if entry.get("tier") == tier and not entry.get("success", True):
            return entry.get("error") or "N/A"
    return "N/A"


def _build_rca_prompt(
    instruction: str,
    page_url: str,
    execution_history: List[Dict[str, Any]],
    dom_snapshot: str,
) -> str:
    """
    Build the LLM prompt for root cause analysis.

    Args:
        instruction: The natural-language step description that failed.
        page_url: URL of the page at the moment of failure.
        execution_history: List of per-tier execution result dicts.
        dom_snapshot: Capped DOM snapshot string (may be empty).

    Returns:
        Formatted prompt string.
    """
    t1_err = _extract_tier_error(execution_history, 1)
    t2_err = _extract_tier_error(execution_history, 2)
    t3_err = _extract_tier_error(execution_history, 3)

    dom_section = (
        f"\nRelevant DOM snapshot (may be truncated):\n{dom_snapshot}"
        if dom_snapshot
        else "\nDOM snapshot: unavailable"
    )

    return (
        "You are a web test automation debugger.\n\n"
        f'Step: "{instruction}"\n'
        f"URL at failure: {page_url}\n\n"
        "Per-tier errors:\n"
        f"- Tier 1 (Playwright direct): {t1_err}\n"
        f"- Tier 2 (XPath hybrid):      {t2_err}\n"
        f"- Tier 3 (AI Stagehand):      {t3_err}\n"
        f"{dom_section}\n\n"
        "In 2–3 sentences: explain the likely root cause of the failure and "
        "suggest what the test step or the page may need to fix it."
    )


async def generate_root_cause_analysis(
    page: Page,
    step_data: Dict[str, Any],
    execution_history: List[Dict[str, Any]],
    error_type: str = "all_tiers_exhausted",
    provider: str = "openrouter",
    model: Optional[str] = None,
    enable_thinking: bool = False,
    custom_endpoint: Optional[str] = None,
) -> Optional[str]:
    """
    Generate an AI root cause analysis string for a failed test step.

    Only fires when *error_type* == ``"all_tiers_exhausted"``.  If the LLM
    call fails for any reason the function returns ``None`` — it must never
    raise an exception that would interrupt test execution.

    Args:
        page:              Playwright Page at the point of failure.
        step_data:         Step dict with at minimum an ``"instruction"`` key.
        execution_history: Per-tier result list from ThreeTierExecutionService.
        error_type:        Error category string; only "all_tiers_exhausted" triggers RCA.
        provider:          LLM provider name passed to UniversalLLMService.
        model:             Optional model override.

    Returns:
        Plain-English root cause string (2–3 sentences), or None.
    """
    if error_type != "all_tiers_exhausted":
        return None

    instruction = step_data.get("instruction") or str(step_data)
    page_url = getattr(page, "url", "unknown")

    # Fetch and cap DOM snapshot — failure is non-fatal
    dom_snapshot = ""
    try:
        raw_html = await page.inner_html("body")
        dom_snapshot = _cap_dom_snapshot(raw_html)
    except Exception as exc:
        logger.debug("[RCA] DOM snapshot unavailable: %s", exc)

    prompt = _build_rca_prompt(
        instruction=instruction,
        page_url=page_url,
        execution_history=execution_history,
        dom_snapshot=dom_snapshot,
    )

    try:
        llm = UniversalLLMService()
        response = await llm.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            provider=provider,
            model=model,
            temperature=0.2,
            max_tokens=256,
            enable_thinking=enable_thinking,
            custom_endpoint=custom_endpoint,
        )
        content = response["choices"][0]["message"]["content"]
        logger.info("[RCA] Root cause analysis generated (%d chars)", len(content))
        return content.strip() if content else None
    except Exception as exc:
        logger.warning("[RCA] LLM call failed — returning None: %s", exc)
        return None
