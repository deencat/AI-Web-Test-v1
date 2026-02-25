"""
API v2: Server-Sent Events (SSE) Stream Endpoint

GET /api/v2/workflows/{workflow_id}/stream
Streams real-time progress events for a workflow.
"""
import asyncio
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.services.progress_tracker import get_progress_tracker, ProgressTracker

router = APIRouter()


def _sse_format(event_type: str, data: dict) -> str:
    """Format one SSE message: event type + data line + double newline."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def _event_generator(workflow_id: str, progress_tracker: ProgressTracker, request: Request):
    """Async generator that yields SSE-formatted bytes.

    NOTE: We intentionally do NOT call request.is_disconnected() here.
    Calling receive() from inside a StreamingResponse generator breaks the
    Starlette/uvicorn ASGI lifecycle and can stall the stream after a few
    events.  Natural termination happens via terminal events or the 300s
    timeout; uvicorn raises CancelledError on a broken-pipe disconnect.
    """
    try:
        async for event in progress_tracker.subscribe(
            workflow_id,
            timeout_seconds=300.0,
            keepalive_interval=15.0,
        ):
            ev_type = event.get("event", "message")
            if ev_type == "_keepalive":
                yield ": keepalive\n\n".encode("utf-8")
                continue
            payload = {
                "event": ev_type,
                "data": event.get("data", {}),
                "timestamp": event.get("timestamp", ""),
            }
            yield _sse_format(ev_type, payload).encode("utf-8")
    except asyncio.CancelledError:
        pass
    finally:
        await progress_tracker.cleanup(workflow_id)


@router.get(
    "/{workflow_id}/stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "SSE stream of workflow progress events",
            "content": {"text/event-stream": {}},
        },
    },
    summary="Stream workflow progress (SSE)",
    description="""
    Stream real-time progress events for a workflow using Server-Sent Events (SSE).

    **Event Types:**
    - `agent_started`: Agent begins execution
    - `agent_progress`: Agent progress update
    - `agent_completed`: Agent finishes execution
    - `workflow_completed`: All agents complete
    - `workflow_failed`: Workflow failed with error

    **Usage:**
    ```javascript
    const eventSource = new EventSource('/api/v2/workflows/{workflow_id}/stream');
    eventSource.addEventListener('agent_started', (e) => {
        const data = JSON.parse(e.data);
        console.log('Agent started:', data.data.agent);
    });
    eventSource.addEventListener('workflow_completed', (e) => {
        eventSource.close();
    });
    ```
    """,
)
async def stream_workflow_progress(
    request: Request,
    workflow_id: str,
    progress_tracker: ProgressTracker = Depends(get_progress_tracker),
):
    """Stream workflow progress via Server-Sent Events."""
    return StreamingResponse(
        _event_generator(workflow_id, progress_tracker, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
