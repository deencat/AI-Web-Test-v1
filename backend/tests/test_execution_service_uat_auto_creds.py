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


# ---------------------------------------------------------------------------
# Test 3 — Non-UAT base_url but UAT URL embedded in a test step
#           (real-world case: frontend sends 'https://web.three.com.hk' as base_url
#            while the actual step says "Navigate to https://wwwuat.three.com.hk/path")
#           Expected: step scan detects UAT hostname → new_context called WITH UAT creds
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_test_uat_url_in_step_injects_creds_when_base_url_is_non_uat():
    """
    Non-UAT base_url + UAT URL inside a step → credentials should still be auto-injected.

    This covers the production scenario where the frontend sends base_url='https://web.three.com.hk'
    (fallback) but the test step says 'Navigate to https://wwwuat.three.com.hk/path'.
    """
    non_uat_base_url = "https://web.three.com.hk"
    uat_step_url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/"
    test_case = _make_test_case(
        steps=[f"Navigate to {uat_step_url} in a web browser"]
    )
    db = MagicMock()

    mock_browser, _mock_context, _mock_page = _make_browser_page_context()
    mock_pw_instance = _make_playwright_instance(mock_browser)

    with (
        patch("app.services.execution_service.crud_execution") as mock_crud,
        patch("app.services.execution_service.ThreeTierExecutionService") as mock_3tier,
    ):
        _configure_crud(mock_crud, execution_id=30)
        _configure_3tier(mock_3tier)

        service = ExecutionService(ExecutionConfig(headless=True))
        service.playwright = mock_pw_instance
        service.browser = mock_browser

        # base_url is NOT a UAT URL; credentials NOT provided explicitly
        await service.execute_test(
            db=db,
            test_case=test_case,
            user_id=1,
            base_url=non_uat_base_url,
            environment="dev",
            execution_id=30,
            http_credentials=None,
        )

    # Verify new_context WAS called with UAT creds (found via step scan)
    mock_browser.new_context.assert_awaited_once()
    _, kwargs = mock_browser.new_context.call_args
    assert kwargs.get("http_credentials") == UAT_HTTP_CREDENTIALS, (
        f"Expected UAT creds injected from step URL, but got {kwargs.get('http_credentials')}"
    )


# ---------------------------------------------------------------------------
# Test 4 — Chrome-like user agent is always injected into new_context()
#           Expected: new_context() receives user_agent matching Chrome UA string
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_test_injects_chrome_user_agent():
    """
    Sprint 10.9 — Preprod loop-back fix (ADR-002-19-B):
    ExecutionService must inject a Chrome-like user_agent into new_context() so the
    preprod server does not detect HeadlessChrome automation and redirect the session.
    """
    from app.services.execution_service import STEALTH_USER_AGENT

    test_case = _make_test_case(steps=["Navigate to https://www.example.com"])
    db = MagicMock()

    mock_browser, _mock_context, _mock_page = _make_browser_page_context()
    mock_pw_instance = _make_playwright_instance(mock_browser)

    with (
        patch("app.services.execution_service.crud_execution") as mock_crud,
        patch("app.services.execution_service.ThreeTierExecutionService") as mock_3tier,
    ):
        _configure_crud(mock_crud, execution_id=40)
        _configure_3tier(mock_3tier)

        service = ExecutionService(ExecutionConfig(headless=True))
        service.playwright = mock_pw_instance
        service.browser = mock_browser

        await service.execute_test(
            db=db,
            test_case=test_case,
            user_id=1,
            base_url="https://www.example.com",
            environment="dev",
            execution_id=40,
            http_credentials=None,
        )

    mock_browser.new_context.assert_awaited_once()
    _, kwargs = mock_browser.new_context.call_args
    actual_ua = kwargs.get("user_agent", "")
    assert "Chrome" in actual_ua and "HeadlessChrome" not in actual_ua, (
        f"Expected a real Chrome UA string (without 'HeadlessChrome'), got: {actual_ua!r}"
    )
    assert actual_ua == STEALTH_USER_AGENT, (
        f"Expected STEALTH_USER_AGENT={STEALTH_USER_AGENT!r}, got {actual_ua!r}"
    )


# ---------------------------------------------------------------------------
# Test 5 — Chromium is launched with anti-automation args
#           Expected: launch() called with --disable-blink-features=AutomationControlled
#           and --disable-dev-shm-usage (Linux crash prevention)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_test_chromium_launch_has_anti_automation_args():
    """
    Sprint 10.9 — Anti-automation flag hardening (ADR-002-19-B):
    Chromium launch must include --disable-blink-features=AutomationControlled and
    --disable-dev-shm-usage to mirror the ObservationAgent's hardened browser defaults.
    """
    test_case = _make_test_case(steps=["Navigate to https://www.example.com"])
    db = MagicMock()

    mock_browser, _mock_context, _mock_page = _make_browser_page_context()
    mock_pw_instance = _make_playwright_instance(mock_browser)

    with (
        patch("app.services.execution_service.crud_execution") as mock_crud,
        patch("app.services.execution_service.ThreeTierExecutionService") as mock_3tier,
    ):
        _configure_crud(mock_crud, execution_id=50)
        _configure_3tier(mock_3tier)

        service = ExecutionService(ExecutionConfig(headless=True))
        service.playwright = mock_pw_instance
        # Do NOT pre-set service.browser so initialize() is called and launch() is invoked
        service.browser = None

        await service.execute_test(
            db=db,
            test_case=test_case,
            user_id=1,
            base_url="https://www.example.com",
            environment="dev",
            execution_id=50,
            http_credentials=None,
        )

    mock_pw_instance.chromium.launch.assert_awaited_once()
    _, launch_kwargs = mock_pw_instance.chromium.launch.call_args
    launch_args = launch_kwargs.get("args", [])
    assert "--disable-blink-features=AutomationControlled" in launch_args, (
        f"Expected --disable-blink-features=AutomationControlled in launch args: {launch_args}"
    )
    assert "--disable-dev-shm-usage" in launch_args, (
        f"Expected --disable-dev-shm-usage in launch args: {launch_args}"
    )


# ---------------------------------------------------------------------------
# Test 6 — Initial bootstrap navigation uses real step URL, not placeholder base_url
#           Expected: first page.goto() call uses the URL embedded in test steps
#           and waits only for domcontentloaded to avoid long marketing-page load stalls
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_test_initial_navigation_uses_step_url_when_base_url_is_placeholder():
    """
    Sprint 10.9 — Initial navigation bug:
    SavedTestsPage intentionally sends base_url='https://web.three.com.hk' as a placeholder,
    expecting ExecutionService to extract the actual URL from the test steps. The initial
    bootstrap page.goto() must therefore use the first step URL, not the placeholder.
    """
    placeholder_base_url = "https://web.three.com.hk"
    actual_step_url = "https://wwwuat.three.com.hk/DTPPD/postpaid/preprod4/en/"
    test_case = _make_test_case(steps=[f"Navigate to {actual_step_url} in a web browser"])
    db = MagicMock()

    mock_browser, _mock_context, mock_page = _make_browser_page_context()
    mock_pw_instance = _make_playwright_instance(mock_browser)

    with (
        patch("app.services.execution_service.crud_execution") as mock_crud,
        patch("app.services.execution_service.ThreeTierExecutionService") as mock_3tier,
        patch("app.services.execution_service.auto_dismiss_blocking_modals", AsyncMock(return_value=False)),
    ):
        _configure_crud(mock_crud, execution_id=60)
        _configure_3tier(mock_3tier)

        service = ExecutionService(ExecutionConfig(headless=True))
        service.playwright = mock_pw_instance
        service.browser = mock_browser

        await service.execute_test(
            db=db,
            test_case=test_case,
            user_id=1,
            base_url=placeholder_base_url,
            environment="dev",
            execution_id=60,
            http_credentials=None,
        )

    assert mock_page.goto.await_count >= 1, "Expected at least one bootstrap page.goto() call"
    first_call = mock_page.goto.await_args_list[0]
    first_args, first_kwargs = first_call.args, first_call.kwargs
    assert first_args[0] == actual_step_url, (
        f"Expected initial navigation to use step URL {actual_step_url!r}, got {first_args[0]!r}"
    )
    assert first_kwargs.get("wait_until") == "domcontentloaded", (
        f"Expected initial navigation wait_until='domcontentloaded', got {first_kwargs.get('wait_until')!r}"
    )
