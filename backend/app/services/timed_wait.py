"""
Timed wait step helpers — Feature 4 / ADR-010.

Detect intentional fixed-duration pauses (NL + canonical + structured) and
sleep in cancel-aware chunks so ADR-009 Stop works mid-wait.

Does NOT handle condition waits ("wait for …") or ADR-002 readiness sleeps.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

MAX_TIMED_WAIT_MS = 120_000
MIN_TIMED_WAIT_MS = 100
DEFAULT_CHUNK_MS = 250

# Reject condition / readiness phrasing as timed sleep (v1: any "wait for/until").
_CONDITION_WAIT_RE = re.compile(
    r"^\s*wait\s+(for|until)\b",
    re.IGNORECASE,
)

# Canonical / compact: wait: 10s, wait:10s, sleep: 3s
_CANONICAL_RE = re.compile(
    r"^\s*(wait|sleep|delay)\s*:\s*(\d+(?:\.\d+)?)\s*"
    r"(ms|milliseconds?|s|secs?|seconds?|m|mins?|minutes?)?\s*$",
    re.IGNORECASE,
)

# NL with unit: Wait 10 seconds, WAIT 10000ms, sleep 3, delay 3 seconds
# Bare number after sleep/delay/wait requires optional unit (default seconds).
_NL_DURATION_RE = re.compile(
    r"^\s*(wait|sleep|delay)\s+(\d+(?:\.\d+)?)\s*"
    r"(ms|milliseconds?|s|secs?|seconds?|m|mins?|minutes?)?\s*$",
    re.IGNORECASE,
)


def _unit_to_ms(amount: float, unit: Optional[str]) -> int:
    u = (unit or "s").lower()
    if u in ("ms", "millisecond", "milliseconds"):
        return int(round(amount))
    if u in ("m", "min", "mins", "minute", "minutes"):
        return int(round(amount * 60_000))
    # s, sec, secs, second, seconds, or missing → seconds
    return int(round(amount * 1000))


def _clamp_duration_ms(ms: int) -> int:
    if ms < MIN_TIMED_WAIT_MS:
        return MIN_TIMED_WAIT_MS
    if ms > MAX_TIMED_WAIT_MS:
        logger.warning(
            "[timed_wait] Duration %sms exceeds cap %sms — clamping",
            ms,
            MAX_TIMED_WAIT_MS,
        )
        return MAX_TIMED_WAIT_MS
    return ms


def _parse_duration_from_text(text: str) -> Optional[int]:
    """Parse a standalone duration string like '10s', '10000ms', '3' (seconds)."""
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    m = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*(ms|milliseconds?|s|secs?|seconds?|m|mins?|minutes?)?",
        s,
        re.IGNORECASE,
    )
    if not m:
        return None
    amount = float(m.group(1))
    unit = m.group(2)
    # Pure int with no unit → treat as milliseconds (Tier 1 legacy)
    if unit is None and re.fullmatch(r"\d+", s):
        return _clamp_duration_ms(int(s))
    return _clamp_duration_ms(_unit_to_ms(amount, unit))


def parse_timed_wait_ms(
    instruction: Optional[str],
    step_dict: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """
    Return duration in ms if this step is a timed wait; else None.

    Priority:
      1. Structured timeout_ms / timeout when action=wait or kind=timed
      2. Structured value that parses as duration (same structured wait)
      3. Instruction NL / canonical patterns

    Rejects ``wait for`` / ``wait until`` (condition waits).
    Caps at MAX_TIMED_WAIT_MS (120s).
    """
    step = step_dict or {}
    action = (step.get("action") or "").lower().strip()
    kind = (step.get("kind") or "").lower().strip()
    is_structured_wait = action == "wait" or kind == "timed"

    if is_structured_wait:
        for key in ("timeout_ms", "timeout"):
            raw = step.get(key)
            if raw is not None and raw != "":
                try:
                    return _clamp_duration_ms(int(float(raw)))
                except (TypeError, ValueError):
                    parsed = _parse_duration_from_text(str(raw))
                    if parsed is not None:
                        return parsed
        # value may be "10s" or "10000"
        value = step.get("value")
        if value is not None and value != "":
            parsed = _parse_duration_from_text(str(value))
            if parsed is not None:
                return parsed

    text = (instruction or step.get("instruction") or "").strip()
    if not text:
        # Structured wait without any duration → not a successful timed parse
        return None

    if _CONDITION_WAIT_RE.match(text):
        return None

    # Ambiguous: "wait 10 seconds for the modal" — reject if " for " / " until " mid-phrase
    lower = text.lower()
    if re.search(r"\bwait\b.+\b(for|until)\b", lower):
        return None

    for pattern in (_CANONICAL_RE, _NL_DURATION_RE):
        m = pattern.match(text)
        if m:
            amount = float(m.group(2))
            unit = m.group(3)
            verb = m.group(1).lower()
            # bare "wait 10" / "sleep 3" without unit → seconds
            if unit is None and verb in ("wait", "sleep", "delay"):
                # Require unit for "wait N" alone only if we want strictness;
                # spec accepts "sleep 3" as 3000ms.
                return _clamp_duration_ms(_unit_to_ms(amount, "s"))
            return _clamp_duration_ms(_unit_to_ms(amount, unit))

    # Structured wait + instruction that didn't match → try parsing instruction as duration only
    if is_structured_wait:
        parsed = _parse_duration_from_text(text)
        if parsed is not None:
            return parsed

    return None


async def sleep_cancel_aware(
    duration_ms: int,
    cancel_check: Optional[Callable[[], bool]] = None,
    *,
    chunk_ms: int = DEFAULT_CHUNK_MS,
) -> bool:
    """
    Sleep in chunks (default 250ms, max 500ms).

    Returns True if cancel_check became true (abort early), False if full sleep completed.
    """
    remaining = max(0, int(duration_ms))
    chunk = max(1, min(int(chunk_ms), 500))

    while remaining > 0:
        if cancel_check and cancel_check():
            return True
        sleep_ms = min(chunk, remaining)
        await asyncio.sleep(sleep_ms / 1000.0)
        remaining -= sleep_ms
        if cancel_check and cancel_check():
            return True
    return False
