"""
Sprint 10.19 — LLM Response & Timing Logger

Writes one JSONL entry per LLM call to:
  - logs/llm/exec_{execution_id}.jsonl   (calls inside an execution context)
  - logs/llm/misc.jsonl                  (all other calls)

The server console log is NOT changed.  Existing logger.info/debug calls in
universal_llm.py continue to emit the same one-liner summary to the console;
the full structured detail (including thinking traces) goes only to these files.

File-count rotation: when the number of *.jsonl files in the log dir exceeds
LLM_LOG_MAX_FILES (default 200), the oldest file by mtime is deleted.

Public API consumed by universal_llm.py:
  - LLMResponseLogger.write(entry: dict) -> None   (async, swallows I/O errors)
  - extract_thinking_from_response(response: dict)
      -> tuple[thinking_content, stripped_content, thinking_tokens]
  - build_prompt_preview(messages: list, *, full_prompt: bool) -> str
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers (importable for direct use in tests)
# ---------------------------------------------------------------------------

_THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)
_PROMPT_PREVIEW_MAX = 500


def extract_thinking_from_response(
    response: dict,
) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """Extract chain-of-thought thinking from an LLM API response dict.

    Supports two formats:
    1. ``choices[0].message.reasoning_content``  — OpenAI-compat vLLM field
    2. ``<think>...</think>`` block embedded in ``choices[0].message.content``

    Returns:
        (thinking_content, stripped_content, thinking_tokens)
        where *stripped_content* has the ``<think>`` block removed.
        thinking_tokens is taken from
        ``usage.completion_tokens_details.reasoning_tokens`` when available.
    """
    choices = response.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    raw_content: Optional[str] = message.get("content")

    # --- Format 1: dedicated reasoning_content field -----------------------
    reasoning_content: Optional[str] = message.get("reasoning_content")
    if reasoning_content:
        # content is already clean (no embedded <think> block)
        thinking_tokens = _extract_reasoning_tokens(response)
        return reasoning_content, raw_content, thinking_tokens

    # --- Format 2: inline <think>…</think> block ---------------------------
    if raw_content:
        match = _THINK_RE.search(raw_content)
        if match:
            thinking_text = match.group(1)
            stripped = _THINK_RE.sub("", raw_content).strip()
            return thinking_text, stripped, None

    return None, raw_content, None


def _extract_reasoning_tokens(response: dict) -> Optional[int]:
    usage = response.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    val = details.get("reasoning_tokens")
    return int(val) if val is not None else None


def build_prompt_preview(messages: list[dict], *, full_prompt: bool) -> str:
    """Return a prompt representation suitable for logging.

    When *full_prompt* is False (default), returns the last user-message content
    truncated to _PROMPT_PREVIEW_MAX characters.
    When *full_prompt* is True, returns the full messages list serialised as JSON.
    """
    if full_prompt:
        return json.dumps(messages, ensure_ascii=False)

    # Find last user message content
    for msg in reversed(messages):
        content = msg.get("content", "")
        if isinstance(content, str):
            return content[:_PROMPT_PREVIEW_MAX]
        # Multimodal: grab text part
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    return part.get("text", "")[:_PROMPT_PREVIEW_MAX]

    return ""


# ---------------------------------------------------------------------------
# LLMResponseLogger
# ---------------------------------------------------------------------------

class LLMResponseLogger:
    """Async JSONL logger for LLM call metadata.

    Designed as a singleton when used via ``llm_response_logger`` module-level
    instance, but also instantiable with a custom *log_dir* for testing.
    """

    def __init__(
        self,
        log_dir: str = "logs/llm",
        max_files: int = 200,
        full_prompt: bool = False,
    ) -> None:
        self._log_dir = Path(log_dir)
        self._max_files = max_files
        self._full_prompt = full_prompt
        # Per-file async locks to prevent interleaved JSON lines
        self._locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def write(self, entry: dict) -> None:
        """Append *entry* as a JSON line to the appropriate JSONL file.

        Swallows all I/O errors so that a logging failure never kills execution.
        """
        try:
            execution_id = entry.get("execution_id")
            filename = f"exec_{execution_id}.jsonl" if execution_id is not None else "misc.jsonl"
            path = self._log_dir / filename
            line = json.dumps(entry, ensure_ascii=False, default=str)
            await self._append_line(path, line)
            await self._maybe_rotate()
        except Exception as exc:  # noqa: BLE001
            logger.debug("LLMResponseLogger: swallowed write error: %s", exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _append_line(self, path: Path, line: str) -> None:
        """Write one JSONL line to *path*, creating the file if needed."""
        file_key = str(path)
        async with self._global_lock:
            if file_key not in self._locks:
                self._locks[file_key] = asyncio.Lock()
        lock = self._locks[file_key]

        async with lock:
            await asyncio.to_thread(self._sync_append, path, line)

    @staticmethod
    def _sync_append(path: Path, line: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    async def _maybe_rotate(self) -> None:
        """Delete the oldest JSONL file when count exceeds *max_files*."""
        async with self._global_lock:
            files = sorted(
                self._log_dir.glob("*.jsonl"),
                key=lambda p: p.stat().st_mtime,
            )
            while len(files) > self._max_files:
                oldest = files.pop(0)
                try:
                    oldest.unlink()
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# Module-level singleton (used by universal_llm.py)
# ---------------------------------------------------------------------------

def _make_singleton() -> LLMResponseLogger:
    """Create the singleton logger, reading config from environment / settings."""
    try:
        from app.core.config import settings  # type: ignore

        log_dir = getattr(settings, "LLM_LOG_DIR", "logs/llm")
        max_files = int(getattr(settings, "LLM_LOG_MAX_FILES", 200))
        full_prompt = bool(getattr(settings, "LLM_LOG_FULL_PROMPT", False))
    except Exception:  # settings unavailable (tests, CLI)
        log_dir = "logs/llm"
        max_files = 200
        full_prompt = False

    return LLMResponseLogger(log_dir=log_dir, max_files=max_files, full_prompt=full_prompt)


llm_logger = _make_singleton()
