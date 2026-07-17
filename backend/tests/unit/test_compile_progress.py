"""Unit tests for in-memory compile progress store."""
import asyncio

from app.services.compile_progress import CompileProgressStore


def test_compile_progress_lifecycle():
    async def _run():
        product_id = "test-product-progress"

        started = await CompileProgressStore.try_start(product_id)
        assert started is not None
        assert started.status == "running"

        duplicate = await CompileProgressStore.try_start(product_id)
        assert duplicate is None

        await CompileProgressStore.update(
            product_id,
            step="Analysing UX/UI flows",
            percent=42,
            detail="Flow 1/2",
        )
        state = CompileProgressStore.get(product_id)
        assert state is not None
        assert state.percent == 42
        assert state.step == "Analysing UX/UI flows"

        await CompileProgressStore.complete(product_id, {"message": "done", "journeys_extracted": 2})
        done = CompileProgressStore.get(product_id)
        assert done is not None
        assert done.status == "done"
        assert done.percent == 100
        assert done.result == {"message": "done", "journeys_extracted": 2}

    asyncio.run(_run())


def test_compile_progress_fail():
    async def _run():
        product_id = "test-product-fail"
        await CompileProgressStore.fail(product_id, "vision timeout")
        state = CompileProgressStore.get(product_id)
        assert state is not None
        assert state.status == "error"
        assert state.error == "vision timeout"

    asyncio.run(_run())
