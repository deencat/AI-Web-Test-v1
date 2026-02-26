"""
Start FastAPI server with proper Windows asyncio configuration for Playwright/Stagehand.
This script ensures WindowsProactorEventLoopPolicy is set before Uvicorn creates its event loop.

When ENABLE_SERVER_FILE_LOGGING=true in .env, server logs are also written to backend/logs/.
"""
import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env so we can read ENABLE_SERVER_FILE_LOGGING before starting the app
load_dotenv(Path(__file__).resolve().parent / ".env")
import os  # noqa: E402
_ENABLE_FILE_LOGGING = os.getenv("ENABLE_SERVER_FILE_LOGGING", "false").lower() in ("true", "1", "yes")

# CRITICAL: Set Windows event loop policy BEFORE any async operations
# This must be done before importing any Playwright/Stagehand code
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("[INFO] Set WindowsProactorEventLoopPolicy for Playwright compatibility")

# Optional: send server logs to backend/logs/ when ENABLE_SERVER_FILE_LOGGING is set in .env
if _ENABLE_FILE_LOGGING:
    _log_dir = Path(__file__).resolve().parent / "logs"
    _log_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    _log_file = _log_dir / f"server_{datetime.now().strftime('%Y%m%d')}.log"
    _file_handler = logging.FileHandler(_log_file, encoding="utf-8")
    _file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    _file_handler.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(_file_handler)
    logging.getLogger().setLevel(logging.INFO)
    print(f"[INFO] Server log file: {_log_file}")

import uvicorn  # noqa: E402

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
