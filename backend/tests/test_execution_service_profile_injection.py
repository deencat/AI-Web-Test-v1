"""
Unit tests for browser profile injection in ExecutionService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.execution_service import ExecutionService, ExecutionConfig


@pytest.mark.asyncio
async def test_apply_profile_cookies_injects_context_cookies():
    service = ExecutionService(ExecutionConfig())

    page = MagicMock()
    context = MagicMock()
    context.add_cookies = AsyncMock()
    page.context = context

    profile_data = {
        "cookies": [
            {
                "name": "session",
                "value": "abc123",
                "domain": ".example.com",
                "path": "/"
            }
        ]
    }

    await service._apply_profile_cookies(page, profile_data)

    context.add_cookies.assert_awaited_once_with(profile_data["cookies"])


@pytest.mark.asyncio
async def test_apply_profile_storage_injects_local_and_session_storage():
    service = ExecutionService(ExecutionConfig())

    page = MagicMock()
    page.evaluate = AsyncMock()

    profile_data = {
        "localStorage": {"token": "local-token"},
        "sessionStorage": {"session": "session-token"}
    }

    await service._apply_profile_storage(page, profile_data)

    assert page.evaluate.await_count == 2
