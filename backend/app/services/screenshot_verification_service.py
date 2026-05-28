"""
Sprint 10.17: AI Screenshot Verification Service

Captures a screenshot of the current page and calls UniversalLLMService.vision_completion()
to obtain a PASS / FAIL verdict.  Falls back gracefully when the configured provider does
not support vision (via VisionNotSupportedError).

Verdict format (stored in execution_steps.ai_verification_result as JSON):
  {"verdict": "PASS"|"FAIL", "reason": "...", "provider": "...", "model": "..."}
"""
import logging
import re
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

from app.services.universal_llm import UniversalLLMService, VisionNotSupportedError

logger = logging.getLogger(__name__)

# Strict PASS/FAIL regex — LLM responses that don't match are treated as FAIL
_VERDICT_RE = re.compile(r"^(PASS|FAIL):\s*(.+)$", re.IGNORECASE | re.DOTALL)

_SYSTEM_PROMPT = (
    "You are a strict UI verification assistant. "
    "Your ONLY job is to check whether ALL expected items are LITERALLY VISIBLE as text in the screenshot.\n"
    "Rules:\n"
    "1. Respond PASS ONLY if every single expected item is clearly visible as text in the screenshot.\n"
    "2. Respond FAIL if ANY expected item is missing, not shown, or not clearly visible.\n"
    "3. Do NOT assume, guess, or infer — only report what you can directly read in the screenshot.\n"
    "4. Use EXACTLY one of these two formats (no other text):\n"
    "PASS: <one-sentence reason>\n"
    "FAIL: <one-sentence reason stating which item is missing>"
)


def _build_user_text(instruction: str, expected_items: List[str]) -> str:
    """Build the user message for the vision LLM."""
    if expected_items:
        items_str = ", ".join(f'"{item}"' for item in expected_items)
        enforcement = (
            "\nIMPORTANT: Each item listed above MUST be literally visible as text in the screenshot. "
            "If ANY item is absent or not clearly shown, you MUST respond FAIL."
        )
    else:
        items_str = "(none specified — check that the instruction is satisfied)"
        enforcement = ""
    return (
        f'Verification task: "{instruction}"\n'
        f"Expected items that MUST be visible on screen: {items_str}"
        f"{enforcement}"
    )


def _parse_verdict(raw: str) -> Dict[str, str]:
    """Parse LLM response into a verdict dict.

    Returns ``{"verdict": "FAIL", "reason": "LLM response unparseable"}`` when
    the response does not match the PASS/FAIL format so the step fails safely
    rather than silently passing.
    """
    raw = (raw or "").strip()
    match = _VERDICT_RE.match(raw)
    if match:
        verdict = match.group(1).upper()
        reason = match.group(2).strip()
        return {"verdict": verdict, "reason": reason}
    return {"verdict": "FAIL", "reason": "LLM response unparseable"}


class ScreenshotVerificationService:
    """Verifies page content using a vision-capable LLM.

    Workflow:
    1. Capture a screenshot via Playwright (viewport or full-page).
    2. Base64-encode the image.
    3. Call UniversalLLMService.vision_completion() with the encoded image and
       a structured prompt describing the expected items.
    4. Parse the PASS/FAIL verdict from the response.
    5. Return a result dict consumed by Tier 2.

    Raises VisionNotSupportedError when the provider/model does not support
    vision requests (cerebras, local_vllm).  Tier 2 catches this and escalates
    to Tier 3.
    """

    def __init__(self, llm_service: Optional[UniversalLLMService] = None) -> None:
        self._llm = llm_service or UniversalLLMService()

    async def verify(
        self,
        page: Page,
        instruction: str,
        expected_items: Optional[List[str]] = None,
        screenshot_region: str = "viewport",
        provider: str = "openrouter",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Capture a screenshot and obtain a vision AI verdict.

        Args:
            page: Active Playwright Page.
            instruction: Natural-language description of what to verify.
            expected_items: Specific text/labels that should be visible.
            screenshot_region: ``"viewport"`` (default) or ``"fullpage"``.
            provider: LLM provider for vision calls (azure, openrouter, google).
            model: Optional model override.

        Returns:
            ``{"verdict": "PASS"|"FAIL", "reason": str,
               "provider": str, "model": str | None}``

        Raises:
            VisionNotSupportedError: Propagated from UniversalLLMService when
                the provider does not support vision.
        """
        items = expected_items or []

        full_page = screenshot_region == "fullpage"
        logger.info(
            "[ScreenshotVerification] Capturing %s screenshot for: %s",
            screenshot_region,
            instruction,
        )

        image_bytes: bytes = await page.screenshot(full_page=full_page)

        user_text = _build_user_text(instruction, items)

        logger.info(
            "[ScreenshotVerification] Calling vision LLM (%s) for verification",
            provider,
        )

        # VisionNotSupportedError is intentionally NOT caught here — let callers
        # (Tier 2) decide whether to escalate to Tier 3.
        response = await self._llm.vision_completion(
            image_bytes=image_bytes,
            system_prompt=_SYSTEM_PROMPT,
            user_text=user_text,
            provider=provider,
            model=model,
            max_tokens=256,
        )

        raw_text: str = (
            response.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        verdict_dict = _parse_verdict(raw_text)
        result: Dict[str, Any] = {
            **verdict_dict,
            "provider": provider,
            "model": model,
        }

        logger.info(
            "[ScreenshotVerification] Verdict: %s — %s",
            result["verdict"],
            result["reason"],
        )
        return result
