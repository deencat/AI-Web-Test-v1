"""
Start FastAPI server with proper Windows asyncio configuration for Playwright/Stagehand.
This script ensures WindowsProactorEventLoopPolicy is set before Uvicorn creates its event loop.
"""
import asyncio
import sys
import uvicorn

# CRITICAL: Set Windows event loop policy BEFORE any async operations
# This must be done before importing any Playwright/Stagehand code
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("[INFO] Set WindowsProactorEventLoopPolicy for Playwright compatibility")

if __name__ == "__main__":
    # Start Uvicorn with custom config
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
        loop="asyncio"  # Use asyncio event loop (respects our policy)
    )
