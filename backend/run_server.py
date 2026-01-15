"""
Uvicorn server runner with Windows ProactorEventLoop fix.
This ensures Playwright works correctly on Windows.
"""
import sys
import asyncio
import uvicorn

# CRITICAL: Must set this BEFORE uvicorn starts
# Playwright requires ProactorEventLoop on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("[STARTUP] ProactorEventLoop policy set for Windows/Playwright compatibility")

if __name__ == "__main__":
    # For development with debug mode, disable reload to maintain event loop
    # If you need reload, restart server manually after code changes
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disabled to maintain ProactorEventLoop
        log_level="info",
        loop="asyncio"  # Use asyncio event loop
    )
