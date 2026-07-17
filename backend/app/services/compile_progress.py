"""In-memory progress for long-running product wiki compile jobs."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable, Optional

ProgressCallback = Callable[[str, int, str], Awaitable[None] | None]


@dataclass
class CompileProgressState:
    product_id: str
    status: str = "idle"  # idle | running | done | error
    step: str = ""
    percent: int = 0
    detail: str = ""
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None


_store: dict[str, CompileProgressState] = {}
_lock = asyncio.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CompileProgressStore:
    @staticmethod
    async def try_start(product_id: str) -> Optional[CompileProgressState]:
        async with _lock:
            current = _store.get(product_id)
            if current and current.status == "running":
                return None
            state = CompileProgressState(
                product_id=product_id,
                status="running",
                step="Starting",
                percent=0,
                detail="Preparing summary update…",
                started_at=_now_iso(),
                updated_at=_now_iso(),
            )
            _store[product_id] = state
            return state

    @staticmethod
    async def update(product_id: str, *, step: str, percent: int, detail: str = "") -> None:
        async with _lock:
            state = _store.get(product_id)
            if not state:
                return
            state.step = step
            state.percent = max(0, min(100, percent))
            if detail:
                state.detail = detail
            state.updated_at = _now_iso()

    @staticmethod
    async def complete(product_id: str, result: dict[str, Any]) -> None:
        async with _lock:
            state = _store.get(product_id)
            if not state:
                return
            state.status = "done"
            state.step = "Complete"
            state.percent = 100
            state.result = result
            state.updated_at = _now_iso()

    @staticmethod
    async def fail(product_id: str, error: str) -> None:
        async with _lock:
            state = _store.get(product_id)
            if not state:
                state = CompileProgressState(product_id=product_id)
                _store[product_id] = state
            state.status = "error"
            state.step = "Failed"
            state.error = error
            state.updated_at = _now_iso()

    @staticmethod
    def get(product_id: str) -> Optional[CompileProgressState]:
        return _store.get(product_id)

    @staticmethod
    def reporter(product_id: str) -> ProgressCallback:
        async def _report(step: str, percent: int, detail: str = "") -> None:
            await CompileProgressStore.update(product_id, step=step, percent=percent, detail=detail)

        return _report
