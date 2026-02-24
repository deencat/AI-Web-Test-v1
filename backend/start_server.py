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

# On Windows, reload must be False so the same process that sets the policy runs the app.
# With reload=True, a child process runs the app and may get SelectorEventLoop, which
# does not support subprocesses (browser-use and Playwright will raise NotImplementedError).
USE_RELOAD = sys.platform != 'win32'

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=USE_RELOAD,
        log_level="info",
        loop="asyncio",
    )
