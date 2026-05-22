"""
Start FastAPI server with proper Windows asyncio configuration for Playwright/Stagehand.
This script ensures WindowsProactorEventLoopPolicy is set before Uvicorn creates its event loop.

When ENABLE_SERVER_FILE_LOGGING=true in .env, server logs are also written to backend/logs/.
"""
import asyncio
import logging
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env so we can read ENABLE_SERVER_FILE_LOGGING before starting the app
load_dotenv(Path(__file__).resolve().parent / ".env")
import os  # noqa: E402
_ENABLE_FILE_LOGGING = os.getenv("ENABLE_SERVER_FILE_LOGGING", "false").lower() in ("true", "1", "yes")
from app.utils.server_logging import suppress_noisy_file_loggers  # noqa: E402

# CRITICAL: Set Windows event loop policy BEFORE any async operations
# This must be done before importing any Playwright/Stagehand code
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("[INFO] Set WindowsProactorEventLoopPolicy for Playwright compatibility")

# Optional: send server logs to backend/logs/ when ENABLE_SERVER_FILE_LOGGING is set in .env
if _ENABLE_FILE_LOGGING:
    from datetime import datetime
    _log_dir = Path(__file__).resolve().parent / "logs"
    _log_dir.mkdir(parents=True, exist_ok=True)
    _log_file = _log_dir / f"server_{datetime.now().strftime('%Y%m%d')}.log"
    _file_handler = logging.FileHandler(_log_file, encoding="utf-8")
    _file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    _file_handler.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(_file_handler)
    logging.getLogger().setLevel(logging.INFO)
    suppress_noisy_file_loggers()
    # Tee stdout/stderr to log file from the very start (so start_server prints and all later print() go to file)
    class _Tee:
        def __init__(self, stream, fpath):
            self._stream = stream
            self._file = open(fpath, "a", encoding="utf-8")
        def write(self, data):
            try: self._stream.write(data); self._stream.flush()
            except Exception: pass
            try: self._file.write(data); self._file.flush()
            except Exception: pass
        def flush(self):
            try: self._stream.flush(); self._file.flush()
            except Exception: pass
        def isatty(self): return getattr(self._stream, "isatty", lambda: False)()
    try:
        sys.stdout = _Tee(sys.__stdout__, _log_file)
        sys.stderr = _Tee(sys.__stderr__, _log_file)
    except Exception:
        pass
    print(f"[INFO] Server log file: {_log_file} (stdout/stderr teed to file)")

import uvicorn  # noqa: E402

# On Windows, reload must be False so the same process that sets the policy runs the app.
# With reload=True, a child process runs the app and may get SelectorEventLoop, which
# does not support subprocesses (browser-use and Playwright will raise NotImplementedError).
USE_RELOAD = sys.platform != 'win32'

_MCP_SECRET = os.getenv("AWT_MCP_SECRET", "")

if __name__ == "__main__":
    # ---------------------------------------------------------------------------
    # Start MCP server (port 8001) as a background subprocess when AWT_MCP_SECRET
    # is configured. Hermes Agent connects to this for crawl/execute/health tools.
    # If AWT_MCP_SECRET is not set, the MCP server is skipped (no-op for teams that
    # don't use Hermes yet).
    # ---------------------------------------------------------------------------
    _mcp_proc = None
    if _MCP_SECRET:
        _mcp_script = Path(__file__).resolve().parent / "mcp_server.py"
        _mcp_proc = subprocess.Popen(
            [sys.executable, str(_mcp_script)],
            # Inherit stdout/stderr so MCP logs appear in the same terminal
            stdout=None,
            stderr=None,
        )
        print(f"[INFO] MCP server started (pid {_mcp_proc.pid}) on port 8001")
    else:
        print("[INFO] AWT_MCP_SECRET not set — MCP server skipped (Hermes integration disabled)")

    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=USE_RELOAD,
            reload_dirs=["app"] if USE_RELOAD else None,  # Only watch app/ — prevents test-file saves from killing running executions
            log_level="info",
            loop="asyncio",
        )
    finally:
        # Clean up MCP server when main server exits (Ctrl+C / crash)
        if _mcp_proc is not None and _mcp_proc.poll() is None:
            _mcp_proc.terminate()
            print("[INFO] MCP server stopped")
