"""
Progress Tracker - Emits Real-Time Progress Events

Emits progress events to in-memory queues per workflow. SSE endpoint subscribes
and streams events to the frontend. Optional Redis backend can be added later.

Reference: Sprint 10 - Frontend Integration & Real-time Agent Progress
"""
from typing import Dict, Any, Optional, AsyncIterator
from datetime import datetime, timezone
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

# Terminal event types: stream ends after these
TERMINAL_EVENTS = frozenset({"workflow_completed", "workflow_failed"})


class ProgressTracker:
    """
    Emits real-time progress events. In-memory: each workflow_id has an asyncio.Queue.
    SSE endpoint subscribes to the queue and streams to clients.
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._queues: Dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    async def _get_queue(self, workflow_id: str) -> asyncio.Queue:
        async with self._lock:
            if workflow_id not in self._queues:
                self._queues[workflow_id] = asyncio.Queue()
            return self._queues[workflow_id]

    async def emit(
        self,
        workflow_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Emit a progress event. Events are queued for subscribers (e.g. SSE endpoint).
        """
        event = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.debug("ProgressTracker.emit: workflow=%s event=%s", workflow_id, event_type)
        queue = await self._get_queue(workflow_id)
        await queue.put(event)
        if self.redis:
            try:
                await self.redis.publish(
                    f"workflow:{workflow_id}",
                    json.dumps(event),
                )
            except Exception as e:
                logger.warning("Redis publish failed: %s", e)

    async def subscribe(
        self,
        workflow_id: str,
        *,
        timeout_seconds: float = 300.0,
        keepalive_interval: float = 15.0,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Subscribe to workflow events. Yields event dicts until workflow_completed,
        workflow_failed, or timeout. Yields _keepalive when idle for keepalive_interval.
        """
        queue = await self._get_queue(workflow_id)
        start = asyncio.get_event_loop().time()
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=keepalive_interval)
            except asyncio.TimeoutError:
                if asyncio.get_event_loop().time() - start >= timeout_seconds:
                    logger.info("ProgressTracker subscribe timeout workflow=%s", workflow_id)
                    break
                yield {"event": "_keepalive", "data": {}, "timestamp": datetime.now(timezone.utc).isoformat()}
                continue
            yield event
            if event.get("event") in TERMINAL_EVENTS:
                break

    async def cleanup(self, workflow_id: str) -> None:
        """Remove queue for workflow (call after stream ends to free memory)."""
        async with self._lock:
            self._queues.pop(workflow_id, None)


_tracker: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """Return singleton ProgressTracker (shared by orchestration and SSE)."""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker
