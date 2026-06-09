"""
Sprint 10.19 — LLM Execution Context

A ContextVar that propagates execution metadata through async call stacks.
UniversalLLMService reads this to tag every LLM log entry without callers
needing to thread extra parameters.

Usage:
    from app.utils.llm_execution_context import set_llm_context, llm_exec_ctx

    token = set_llm_context(execution_id=42, step_number=3, tier=2, caller="chat_completion")
    try:
        ...  # await nested async code — context is inherited automatically
    finally:
        llm_exec_ctx.reset(token)
"""
from contextvars import ContextVar
from typing import Optional

# ---------------------------------------------------------------------------
# Default value: a sentinel dict with None fields so callers can always
# call .get() without guarding against None.
# ---------------------------------------------------------------------------
_DEFAULT_CTX: dict = {
    "execution_id": None,
    "step_number": None,
    "tier": None,
    "caller": None,
}

llm_exec_ctx: ContextVar[dict] = ContextVar("llm_exec_ctx", default=_DEFAULT_CTX)


def set_llm_context(
    *,
    execution_id: Optional[int],
    step_number: Optional[int],
    tier: Optional[int],
    caller: str,
):
    """Set the LLM execution context for the current async task.

    Returns the reset token — callers MUST reset the ContextVar when the
    guarded scope exits so that nested calls don't bleed context.

    Example::

        token = set_llm_context(execution_id=1, step_number=2, tier=1, caller="tier1")
        try:
            await some_llm_call()
        finally:
            llm_exec_ctx.reset(token)
    """
    ctx = {
        "execution_id": execution_id,
        "step_number": step_number,
        "tier": tier,
        "caller": caller,
    }
    return llm_exec_ctx.set(ctx)
