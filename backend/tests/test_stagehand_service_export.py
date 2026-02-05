import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.services.stagehand_service import StagehandExecutionService


@pytest.mark.asyncio
async def test_export_profile_handles_local_storage_security_error():
    service = StagehandExecutionService()

    mock_context = SimpleNamespace()
    mock_context.cookies = AsyncMock(return_value=[{"name": "session", "value": "abc"}])

    security_error = Exception(
        "SecurityError: Failed to read the 'localStorage' property from 'Window': Access is denied for this document."
    )

    mock_page = SimpleNamespace()
    mock_page.context = mock_context
    mock_page.evaluate = AsyncMock(
        side_effect=[security_error, {"session_key": "session_value"}]
    )

    service.page = SimpleNamespace(_page=mock_page)

    profile_data = await service.export_browser_profile()

    assert profile_data["cookies"] == [{"name": "session", "value": "abc"}]
    assert profile_data["localStorage"] == {}
    assert profile_data["sessionStorage"] == {"session_key": "session_value"}


@pytest.mark.asyncio
async def test_export_profile_skips_storage_on_restricted_url():
    service = StagehandExecutionService()

    mock_context = SimpleNamespace()
    mock_context.cookies = AsyncMock(return_value=[{"name": "session", "value": "abc"}])

    mock_page = SimpleNamespace()
    mock_page.context = mock_context
    mock_page.url = "about:blank"
    mock_page.evaluate = AsyncMock()

    service.page = SimpleNamespace(_page=mock_page)

    profile_data = await service.export_browser_profile()

    assert profile_data["cookies"] == [{"name": "session", "value": "abc"}]
    assert profile_data["localStorage"] == {}
    assert profile_data["sessionStorage"] == {}
    mock_page.evaluate.assert_not_called()
