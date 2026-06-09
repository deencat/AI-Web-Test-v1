"""
Unit tests for Sprint 10.19 — LLM Response & Timing Log.

TDD: All tests written BEFORE implementation.

Coverage:
  LLMResponseLogger:
    1.  JSONL file is created on first write
    2.  Entry written is valid JSON with all required fields
    3.  File-count rotation deletes oldest file when limit exceeded
    4.  Failed LLM call writes success=false entry with error field
    5.  Multiple writes to same execution_id append to same file
    6.  Calls with no execution context go to misc.jsonl
    7.  thinking_content is extracted from reasoning_content field
    8.  thinking_content is extracted from <think>...</think> block in content
    9.  response_content has <think> block stripped
   10.  prompt_preview truncated to 500 chars by default
   11.  LLM_LOG_FULL_PROMPT=True stores full message list
   12.  Log write failure does NOT propagate (is swallowed safely)

  llm_execution_context:
   13.  set_llm_context returns a reset token and sets the ContextVar correctly
   14.  get() returns None-defaults when context is not set
   15.  reset token correctly resets to prior state
"""
import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_success_response(content: str = "test answer", usage: dict | None = None) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": usage or {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


def _make_thinking_response(thinking: str, content: str) -> dict:
    """Simulate a vLLM response with reasoning_content (OpenAI-compatible field)."""
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                    "reasoning_content": thinking,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 30,
            "total_tokens": 50,
            "completion_tokens_details": {"reasoning_tokens": 15},
        },
    }


def _make_inline_thinking_response(thinking: str, answer: str) -> dict:
    """Simulate a model that embeds thinking inline with <think> tags."""
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": f"<think>{thinking}</think>{answer}",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 20, "completion_tokens": 30, "total_tokens": 50},
    }


# ---------------------------------------------------------------------------
# 1. JSONL file created on first write
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_jsonl_file_created_on_first_write(tmp_path):
    """LLMResponseLogger creates the log file the first time an entry is written."""
    from app.utils.llm_response_logger import LLMResponseLogger

    logger = LLMResponseLogger(log_dir=str(tmp_path))
    entry = {
        "ts": "2026-06-04T10:00:00Z",
        "execution_id": 42,
        "step_number": 1,
        "tier": 2,
        "caller": "test",
        "provider": "azure",
        "model": "gpt-5.2",
        "success": True,
        "response_time_ms": 1234.5,
        "prompt_preview": "hello",
        "response_content": "world",
        "thinking_content": None,
        "thinking_tokens": None,
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
        "error": None,
    }
    await logger.write(entry)

    expected_file = tmp_path / "exec_42.jsonl"
    assert expected_file.exists(), "exec_42.jsonl should be created after first write"


# ---------------------------------------------------------------------------
# 2. Entry is valid JSON with all required fields
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_written_entry_is_valid_json(tmp_path):
    """Each line appended by write() is valid JSON containing all required keys."""
    from app.utils.llm_response_logger import LLMResponseLogger

    logger = LLMResponseLogger(log_dir=str(tmp_path))
    entry = {
        "ts": "2026-06-04T10:00:00Z",
        "execution_id": 7,
        "step_number": 3,
        "tier": 1,
        "caller": "unit_test",
        "provider": "google",
        "model": "gemini-1.5-flash",
        "success": True,
        "response_time_ms": 800.0,
        "prompt_preview": "some prompt",
        "response_content": "some response",
        "thinking_content": None,
        "thinking_tokens": None,
        "prompt_tokens": 8,
        "completion_tokens": 4,
        "total_tokens": 12,
        "error": None,
    }
    await logger.write(entry)

    lines = (tmp_path / "exec_7.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])

    required_fields = {
        "ts", "execution_id", "step_number", "tier", "caller",
        "provider", "model", "success", "response_time_ms",
        "prompt_preview", "response_content",
        "thinking_content", "thinking_tokens",
        "prompt_tokens", "completion_tokens", "total_tokens",
        "error",
    }
    missing = required_fields - set(parsed.keys())
    assert not missing, f"Missing fields in log entry: {missing}"


# ---------------------------------------------------------------------------
# 3. File-count rotation deletes oldest file when limit exceeded
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rotation_deletes_oldest_file(tmp_path):
    """When file count exceeds LLM_LOG_MAX_FILES the oldest file is removed."""
    from app.utils.llm_response_logger import LLMResponseLogger

    max_files = 5
    logger = LLMResponseLogger(log_dir=str(tmp_path), max_files=max_files)

    # Pre-create files with earlier mtime so they sort correctly
    for i in range(max_files):
        f = tmp_path / f"exec_{i}.jsonl"
        f.write_text('{"dummy": true}\n')
        # stagger modification times so oldest is deterministic
        os.utime(f, times=(1000000 + i, 1000000 + i))

    # Trigger a write that creates a new (6th) file → rotation should delete oldest
    entry = {
        "ts": "2026-06-04T10:00:00Z",
        "execution_id": 99,
        "step_number": 1,
        "tier": 1,
        "caller": "test",
        "provider": "cerebras",
        "model": "llama3",
        "success": True,
        "response_time_ms": 500.0,
        "prompt_preview": "hi",
        "response_content": "hello",
        "thinking_content": None,
        "thinking_tokens": None,
        "prompt_tokens": 2,
        "completion_tokens": 2,
        "total_tokens": 4,
        "error": None,
    }
    await logger.write(entry)

    remaining = list(tmp_path.glob("*.jsonl"))
    assert len(remaining) == max_files, (
        f"Expected {max_files} files after rotation, found {len(remaining)}: "
        f"{[f.name for f in remaining]}"
    )
    # The oldest file (exec_0.jsonl) must be gone
    assert not (tmp_path / "exec_0.jsonl").exists(), "Oldest file should have been rotated out"


# ---------------------------------------------------------------------------
# 4. Failed LLM call writes success=false entry with error field
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_failed_llm_call_writes_failure_entry(tmp_path):
    """A failed LLM call produces a JSONL entry with success=false and error populated."""
    from app.utils.llm_response_logger import LLMResponseLogger

    logger = LLMResponseLogger(log_dir=str(tmp_path))
    entry = {
        "ts": "2026-06-04T10:00:00Z",
        "execution_id": 10,
        "step_number": 2,
        "tier": 2,
        "caller": "chat_completion",
        "provider": "openrouter",
        "model": "gpt-4o",
        "success": False,
        "response_time_ms": 300.0,
        "prompt_preview": "failing prompt",
        "response_content": None,
        "thinking_content": None,
        "thinking_tokens": None,
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "error": "OpenRouter API error (429): Rate limit exceeded",
    }
    await logger.write(entry)

    lines = (tmp_path / "exec_10.jsonl").read_text().strip().splitlines()
    parsed = json.loads(lines[0])
    assert parsed["success"] is False
    assert "429" in parsed["error"]


# ---------------------------------------------------------------------------
# 5. Multiple writes to same execution_id append to same file
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_multiple_writes_same_execution_appends(tmp_path):
    """Two write() calls with the same execution_id produce two lines in one file."""
    from app.utils.llm_response_logger import LLMResponseLogger

    logger = LLMResponseLogger(log_dir=str(tmp_path))
    base_entry = {
        "ts": "2026-06-04T10:00:00Z",
        "execution_id": 55,
        "step_number": 1,
        "tier": 1,
        "caller": "chat_completion",
        "provider": "azure",
        "model": "ChatGPT-UAT",
        "success": True,
        "response_time_ms": 1000.0,
        "prompt_preview": "step 1",
        "response_content": "done",
        "thinking_content": None,
        "thinking_tokens": None,
        "prompt_tokens": 5,
        "completion_tokens": 3,
        "total_tokens": 8,
        "error": None,
    }
    await logger.write(base_entry)
    second = {**base_entry, "step_number": 2, "prompt_preview": "step 2"}
    await logger.write(second)

    lines = (tmp_path / "exec_55.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2


# ---------------------------------------------------------------------------
# 6. Calls with no execution context go to misc.jsonl
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_execution_context_writes_to_misc(tmp_path):
    """When execution_id is None the logger writes to misc.jsonl."""
    from app.utils.llm_response_logger import LLMResponseLogger

    logger = LLMResponseLogger(log_dir=str(tmp_path))
    entry = {
        "ts": "2026-06-04T10:00:00Z",
        "execution_id": None,
        "step_number": None,
        "tier": None,
        "caller": "test_generation",
        "provider": "google",
        "model": "gemini-1.5-flash",
        "success": True,
        "response_time_ms": 900.0,
        "prompt_preview": "generate tests for...",
        "response_content": "[{...}]",
        "thinking_content": None,
        "thinking_tokens": None,
        "prompt_tokens": 100,
        "completion_tokens": 200,
        "total_tokens": 300,
        "error": None,
    }
    await logger.write(entry)

    misc_file = tmp_path / "misc.jsonl"
    assert misc_file.exists(), "misc.jsonl should be created for calls without execution_id"
    lines = misc_file.read_text().strip().splitlines()
    assert len(lines) == 1


# ---------------------------------------------------------------------------
# 7. thinking_content extracted from reasoning_content field
# ---------------------------------------------------------------------------

def test_extract_thinking_from_reasoning_content():
    """extract_thinking() returns reasoning_content when present."""
    from app.utils.llm_response_logger import extract_thinking_from_response

    response = _make_thinking_response("I am thinking...", "Final answer")
    thinking, stripped_content, thinking_tokens = extract_thinking_from_response(response)

    assert thinking == "I am thinking..."
    assert stripped_content == "Final answer"
    assert thinking_tokens == 15  # from completion_tokens_details.reasoning_tokens


# ---------------------------------------------------------------------------
# 8. thinking_content extracted from <think>...</think> block
# ---------------------------------------------------------------------------

def test_extract_thinking_from_inline_tags():
    """extract_thinking() strips <think> block from content and returns it separately."""
    from app.utils.llm_response_logger import extract_thinking_from_response

    response = _make_inline_thinking_response("chain of thought here", "the answer")
    thinking, stripped_content, thinking_tokens = extract_thinking_from_response(response)

    assert thinking == "chain of thought here"
    assert stripped_content == "the answer"
    assert thinking_tokens is None  # not reported separately for inline


# ---------------------------------------------------------------------------
# 9. response_content has <think> block stripped (verify full round-trip)
# ---------------------------------------------------------------------------

def test_inline_thinking_stripped_from_response_content():
    """The content field stored in the log has the <think> block removed."""
    from app.utils.llm_response_logger import extract_thinking_from_response

    raw_content = "<think>reasoning</think>   plain answer"
    response = {
        "choices": [{"message": {"role": "assistant", "content": raw_content}}],
        "usage": {},
    }
    _, stripped, _ = extract_thinking_from_response(response)
    assert "reasoning" not in stripped
    assert stripped.strip() == "plain answer"


# ---------------------------------------------------------------------------
# 10. prompt_preview truncated to 500 chars by default
# ---------------------------------------------------------------------------

def test_build_prompt_preview_truncated():
    """build_prompt_preview() returns at most 500 characters when full_prompt=False."""
    from app.utils.llm_response_logger import build_prompt_preview

    long_content = "x" * 1000
    messages = [{"role": "user", "content": long_content}]
    preview = build_prompt_preview(messages, full_prompt=False)

    assert len(preview) <= 500


# ---------------------------------------------------------------------------
# 11. LLM_LOG_FULL_PROMPT=True stores full message list
# ---------------------------------------------------------------------------

def test_build_prompt_preview_full():
    """build_prompt_preview() returns the serialised full message list when full_prompt=True."""
    from app.utils.llm_response_logger import build_prompt_preview

    messages = [
        {"role": "system", "content": "You are a helper"},
        {"role": "user", "content": "a" * 1000},
    ]
    preview = build_prompt_preview(messages, full_prompt=True)

    # Should contain both messages (serialized as JSON)
    parsed = json.loads(preview)
    assert len(parsed) == 2
    assert parsed[1]["content"] == "a" * 1000


# ---------------------------------------------------------------------------
# 12. Log write failure does NOT propagate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_write_failure_does_not_propagate(tmp_path):
    """Even if the underlying file write raises, write() swallows the exception."""
    from app.utils.llm_response_logger import LLMResponseLogger

    logger = LLMResponseLogger(log_dir=str(tmp_path))

    async def _bad_write(path, line):
        raise OSError("disk full")

    with patch.object(logger, "_append_line", side_effect=_bad_write):
        # Should not raise
        await logger.write({"execution_id": 1, "ts": "now"})


# ---------------------------------------------------------------------------
# 13. set_llm_context sets the ContextVar correctly
# ---------------------------------------------------------------------------

def test_set_llm_context_sets_contextvar():
    """set_llm_context() stores execution_id, step_number, tier and caller in llm_exec_ctx."""
    from app.utils.llm_execution_context import set_llm_context, llm_exec_ctx

    token = set_llm_context(execution_id=42, step_number=3, tier=2, caller="chat_completion")
    ctx = llm_exec_ctx.get()

    assert ctx["execution_id"] == 42
    assert ctx["step_number"] == 3
    assert ctx["tier"] == 2
    assert ctx["caller"] == "chat_completion"

    llm_exec_ctx.reset(token)


# ---------------------------------------------------------------------------
# 14. get() returns None-defaults when context is not set
# ---------------------------------------------------------------------------

def test_llm_exec_ctx_defaults_when_not_set():
    """llm_exec_ctx.get() returns a dict with None values when not initialised."""
    from app.utils.llm_execution_context import llm_exec_ctx

    # Use a fresh context by running in a separate thread-like isolation
    # We can just reset via default
    default = llm_exec_ctx.get(None)
    # Either None (not set) or the default dict if we define one — both acceptable
    if default is not None:
        assert default.get("execution_id") is None
        assert default.get("step_number") is None
        assert default.get("tier") is None


# ---------------------------------------------------------------------------
# 15. reset token correctly resets to prior state
# ---------------------------------------------------------------------------

def test_set_llm_context_reset_token():
    """The reset token returned by set_llm_context() correctly restores previous state."""
    from app.utils.llm_execution_context import set_llm_context, llm_exec_ctx

    token1 = set_llm_context(execution_id=10, step_number=1, tier=1, caller="first")
    token2 = set_llm_context(execution_id=20, step_number=2, tier=2, caller="second")

    assert llm_exec_ctx.get()["execution_id"] == 20

    llm_exec_ctx.reset(token2)
    assert llm_exec_ctx.get()["execution_id"] == 10

    llm_exec_ctx.reset(token1)
