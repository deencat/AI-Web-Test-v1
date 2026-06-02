"""
Unit tests — ExecutionService uses a dynamic CDP port, not the hardcoded 9222.

Background
----------
The original implementation launched Chromium with --remote-debugging-port=9222
and hardcoded "http://127.0.0.1:9222" as the CDP endpoint passed to Stagehand.
Two failure modes were observed:

1. (Windows — localhost → IPv6): "localhost" can resolve to [::1] on Windows
   while Chromium only binds the debugging port on IPv4 127.0.0.1. Fix: always
   use the explicit IPv4 literal "127.0.0.1" (still applies).

2. (Windows — port 9222 already in use): VS Code's JavaScript debug adapter,
   Microsoft Edge background process, or a prior test run that did not clean up
   can hold port 9222. When Chromium cannot bind to the port it silently starts
   without a DevTools server; the hardcoded endpoint then hits the unrelated
   process which returns HTTP 400. Playwright 1.56 + Chromium 136 raises:
     "Unexpected status 400 ... try connecting via ws://"
   This does NOT happen on devices without a conflicting process on port 9222.

Fix: allocate a free port at browser-launch time via _find_free_port() so each
execution gets its own dedicated debugging port, eliminating port conflicts.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import re

from app.services.execution_service import ExecutionService, ExecutionConfig


# ---------------------------------------------------------------------------
# Shared helpers (mirrors pattern in test_execution_service_uat_auto_creds.py)
# ---------------------------------------------------------------------------

def _make_test_case(steps=None):
    tc = MagicMock()
    tc.id = 1
    tc.title = "CDP endpoint test"
    tc.description = "desc"
    tc.steps = steps or ["Navigate to https://example.com"]
    tc.test_data = None
    return tc


def _make_browser_page_context():
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.close = AsyncMock()
    mock_page.context = MagicMock()

    mock_context = AsyncMock()
    mock_context.set_default_timeout = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_context.close = AsyncMock()

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    return mock_browser, mock_context, mock_page


def _make_playwright_instance(mock_browser):
    mock_pw = AsyncMock()
    mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_pw.stop = AsyncMock()
    return mock_pw


def _configure_crud(mock_crud, execution_id: int):
    execution = MagicMock()
    execution.id = execution_id
    execution.status = "pending"
    mock_crud.get_execution.return_value = execution
    mock_crud.start_execution.return_value = execution
    mock_crud.update_execution_result = MagicMock()
    mock_crud.create_execution_step = MagicMock()
    return execution


def _configure_3tier(mock_3tier_cls):
    instance = AsyncMock()
    instance.execute_step = AsyncMock(return_value={
        "success": True, "tier_used": "tier1", "method": "css", "error": None,
    })
    mock_3tier_cls.return_value = instance
    return instance


# ---------------------------------------------------------------------------
# Test — CDP endpoint must use a dynamic port on 127.0.0.1
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_test_cdp_endpoint_uses_ipv4_not_localhost():
    """ThreeTierExecutionService must receive a cdp_endpoint on 127.0.0.1.

    The endpoint must:
    - use the explicit IPv4 literal 127.0.0.1 (never 'localhost', which can
      resolve to IPv6 [::1] on Windows where Chromium only binds IPv4).
    - use the dynamically allocated port stored in self._cdp_port, NOT the
      hardcoded 9222, so port conflicts with VS Code / Edge / prior runs on
      this machine do not cause HTTP 400 from Playwright 1.56+ Chromium 136.
    """
    test_case = _make_test_case()
    db = MagicMock()

    mock_browser, _ctx, _page = _make_browser_page_context()
    mock_pw = _make_playwright_instance(mock_browser)

    with (
        patch("app.services.execution_service.crud_execution") as mock_crud,
        patch("app.services.execution_service.ThreeTierExecutionService") as mock_3tier,
    ):
        _configure_crud(mock_crud, execution_id=1)
        _configure_3tier(mock_3tier)

        service = ExecutionService(ExecutionConfig(headless=True))
        service.playwright = mock_pw
        service.browser = mock_browser

        await service.execute_test(
            db=db,
            test_case=test_case,
            user_id=1,
            base_url="https://example.com",
            environment="dev",
            execution_id=1,
        )

    mock_3tier.assert_called_once()
    _, kwargs = mock_3tier.call_args
    cdp_endpoint = kwargs.get("cdp_endpoint")

    # Must use explicit IPv4, not 'localhost'
    assert "localhost" not in (cdp_endpoint or ""), (
        f"CDP endpoint must not contain 'localhost' — got {cdp_endpoint!r}. "
        f"On Windows, localhost can resolve to IPv6 [::1] and returns HTTP 400."
    )

    # Must match http://127.0.0.1:<port> with any port number
    assert re.match(r"^http://127\.0\.0\.1:\d+$", cdp_endpoint or ""), (
        f"CDP endpoint must be 'http://127.0.0.1:<port>' — got {cdp_endpoint!r}. "
        f"A dynamic port prevents HTTP 400 when port 9222 is already in use."
    )


@pytest.mark.asyncio
async def test_execute_test_cdp_port_matches_launch_arg():
    """The port in the CDP endpoint must match the --remote-debugging-port arg.

    Verifies that _cdp_port is used consistently in both the Chromium launch
    args and the cdp_endpoint passed to ThreeTierExecutionService.
    """
    test_case = _make_test_case()
    db = MagicMock()

    mock_browser, _ctx, _page = _make_browser_page_context()
    mock_pw = _make_playwright_instance(mock_browser)

    captured_launch_args = []

    async def capture_launch(**kwargs):
        captured_launch_args.extend(kwargs.get("args", []))
        return mock_browser

    mock_pw.chromium.launch = AsyncMock(side_effect=capture_launch)

    with (
        patch("app.services.execution_service.crud_execution") as mock_crud,
        patch("app.services.execution_service.ThreeTierExecutionService") as mock_3tier,
        patch("app.services.execution_service._find_free_port", return_value=54321),
    ):
        _configure_crud(mock_crud, execution_id=1)
        _configure_3tier(mock_3tier)

        service = ExecutionService(ExecutionConfig(headless=True))
        service.playwright = mock_pw
        # Don't pre-set service.browser — let initialize() run via the mock

        await service.execute_test(
            db=db,
            test_case=test_case,
            user_id=1,
            base_url="https://example.com",
            environment="dev",
            execution_id=1,
        )

    _, kwargs = mock_3tier.call_args
    cdp_endpoint = kwargs.get("cdp_endpoint")

    assert cdp_endpoint == "http://127.0.0.1:54321", (
        f"cdp_endpoint should use the port from _find_free_port() — got {cdp_endpoint!r}"
    )
    assert "--remote-debugging-port=54321" in captured_launch_args, (
        f"Chromium launch args should contain --remote-debugging-port=54321, "
        f"got: {captured_launch_args}"
    )
