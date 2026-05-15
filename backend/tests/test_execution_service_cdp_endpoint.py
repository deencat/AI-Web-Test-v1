"""
Unit tests — ExecutionService passes 127.0.0.1 (not localhost) as CDP endpoint.

Background
----------
On Windows, `localhost` can resolve to IPv6 [::1] while Playwright's Chromium
only binds its remote-debugging port on IPv4 127.0.0.1. This causes a
"unexpected status 400" when Stagehand tries to connect via CDP, followed by
Stagehand launching a second browser (two browsers visible, execution fails).

Copying an existing DB from Linux appeared to "fix" the issue only because
those test cases happened to succeed at Tier 1 (no CDP connection needed).
A fresh DB is more likely to invoke Tier 2/3, triggering the CDP failure.

Fix: always use "http://127.0.0.1:9222" as the CDP endpoint (IPv4 explicit).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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
# Test — CDP endpoint must use 127.0.0.1, not localhost
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_test_cdp_endpoint_uses_ipv4_not_localhost():
    """ThreeTierExecutionService must receive cdp_endpoint='http://127.0.0.1:9222'.

    Using 'http://localhost:9222' breaks on Windows because localhost can
    resolve to the IPv6 address [::1], which Playwright's Chromium does not
    bind, returning HTTP 400 and causing Stagehand to spawn a second browser.
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

    assert cdp_endpoint == "http://127.0.0.1:9222", (
        f"CDP endpoint must be 'http://127.0.0.1:9222' (explicit IPv4) to work "
        f"on Windows — got {cdp_endpoint!r}. "
        f"Using 'localhost' can resolve to IPv6 [::1] and returns HTTP 400."
    )
