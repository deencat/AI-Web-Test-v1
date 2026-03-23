"""StagehandExecutionService applies HTTP Basic auth in navigation steps when runtime creds are set."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.stagehand_service import StagehandExecutionService


@pytest.mark.asyncio
async def test_execute_navigation_embeds_runtime_credentials():
    service = StagehandExecutionService(headless=True)
    service.page = MagicMock()
    service.page.goto = AsyncMock()
    service.set_runtime_http_credentials(
        {"username": "user", "password": "3.comUXuat"}
    )

    await service._execute_navigation(
        "Navigate to https://wwwuat.three.com.hk/path"
    )

    assert service.page.goto.called
    called_url = service.page.goto.call_args[0][0]
    assert "user:" in called_url
    assert "wwwuat.three.com.hk" in called_url

    service.set_runtime_http_credentials(None)
    service.page.goto.reset_mock()
    await service._execute_navigation("Navigate to https://example.com/x")
    plain_url = service.page.goto.call_args[0][0]
    assert plain_url == "https://example.com/x"
