"""
Unit tests for Sprint 10.7 — ExecutionService auto-injects UAT credentials.

TDD RED → GREEN:

G1 fix: ExecutionService.execute_test() calls http_credentials_for_url(base_url)
        before new_context() so UAT tests get credentials injected automatically
        and non-UAT tests run with no credentials (no 401, no profile required).

Tests:
  1. UAT URL + no profile → new_context called with UAT creds
  2. Non-UAT URL + no profile → new_context called without http_credentials key
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.execution_service import ExecutionService, ExecutionConfig
from app.utils.http_auth_credentials import UAT_HTTP_CREDENTIALS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_case(title: str = "Test", steps=None):
    """Build a minimal TestCase-like mock."""
    tc = MagicMock()
    tc.id = 1
    tc.title = title
    tc.description = "desc"
    tc.steps = steps or ["Navigate to the page"]
    tc.test_data = None
    return tc


def _make_browser_page_context():
    """Return (mock_browser, mock_context, mock_page) with async-safe close methods."""
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
    """Create a mock playwright instance that launches to mock_browser."""
    mock_pw = AsyncMock()
    mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_pw.stop = AsyncMock()
    return mock_pw


def _configure_crud(mock_crud, execution_id: int):
    """Configure crud_execution mock with a minimal execution."""
    execution = MagicMock()
    execution.id = execution_id
    execution.status = "pending"
    mock_crud.get_execution.return_value = execution
    mock_crud.start_execution.return_value = execution
    mock_crud.update_execution_result = MagicMock()
    mock_crud.create_execution_step = MagicMock()
    return execution


def _configure_3tier(mock_3tier_cls):
    """Configure ThreeTierExecutionService mock to return success for all steps."""
    instance = AsyncMock()
    instance.execute_step = AsyncMock(return_value={
        "success": True, "tier_used": "tier1", "method": "css", "error": None,
    })
    mock_3tier_cls.return_value = instance
    return instance


# ---------------------------------------------------------------------------
# Test 1 — UAT URL, no browser profile, no explicit credentials
#           Expected: new_context() receives UAT creds automatically
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_test_uat_url_injects_uat_credentials():
    """UAT base_url → http_credentials_for_url returns UAT creds → new_context called with them."""

    uat_url = "https://wwwuat.three.com.hk/some/path"
    test_case = _make_test_case(steps=[f"Navigate to {uat_url}"])
    db = MagicMock()

    mock_browser, _mock_context, _mock_page = _make_browser_page_context()
    mock_pw_instance = _make_playwright_instance(mock_browser)

    with (
        patch("app.services.execution_service.crud_execution") as mock_crud,
        patch("app.services.execution_service.ThreeTierExecutionService") as mock_3tier,
    ):
        _configure_crud(mock_crud, execution_id=10)
        _configure_3tier(mock_3tier)

        service = ExecutionService(ExecutionConfig(headless=True))
        service.playwright = mock_pw_instance
        service.browser = mock_browser

        # http_credentials is NOT provided — service must auto-inject from URL
        await service.execute_test(
            db=db,
            test_case=test_case,
            user_id=1,
            base_url=uat_url,
            environment="dev",
            execution_id=10,
            http_credentials=None,
        )

    # Verify new_context was called with UAT creds
    mock_browser.new_context.assert_awaited_once()
    _, kwargs = mock_browser.new_context.call_args
    assert kwargs.get("http_credentials") == UAT_HTTP_CREDENTIALS, (
        f"Expected UAT creds {UAT_HTTP_CREDENTIALS} but got {kwargs.get('http_credentials')}"
    )


# ---------------------------------------------------------------------------
# Test 2 — Non-UAT URL, no browser profile, no explicit credentials
#           Expected: new_context() is NOT given http_credentials
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_test_non_uat_url_no_credentials_injected():
    """Non-UAT base_url → http_credentials_for_url returns None → new_context has no http_credentials."""

    non_uat_url = "https://www.example.com/"
    test_case = _make_test_case(steps=[f"Navigate to {non_uat_url}"])
    db = MagicMock()

    mock_browser, _mock_context, _mock_page = _make_browser_page_context()
    mock_pw_instance = _make_playwright_instance(mock_browser)

    with (
        patch("app.services.execution_service.crud_execution") as mock_crud,
        patch("app.services.execution_service.ThreeTierExecutionService") as mock_3tier,
    ):
        _configure_crud(mock_crud, execution_id=20)
        _configure_3tier(mock_3tier)

        service = ExecutionService(ExecutionConfig(headless=True))
        service.playwright = mock_pw_instance
        service.browser = mock_browser

        await service.execute_test(
            db=db,
            test_case=test_case,
            user_id=1,
            base_url=non_uat_url,
            environment="dev",
            execution_id=20,
            http_credentials=None,  # No explicit credentials
        )

    # Verify new_context was NOT given http_credentials
    mock_browser.new_context.assert_awaited_once()
    _, kwargs = mock_browser.new_context.call_args
    assert "http_credentials" not in kwargs or kwargs.get("http_credentials") is None, (
        f"Expected no http_credentials but got {kwargs.get('http_credentials')}"
    )
