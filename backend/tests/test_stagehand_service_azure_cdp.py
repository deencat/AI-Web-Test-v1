import os
from types import SimpleNamespace

import pytest

from app.services import stagehand_service
from app.services.stagehand_service import StagehandExecutionService


class DummyStagehand:
    def __init__(self, config):
        self.config = config
        self.page = object()

    async def init(self):
        return None


@pytest.mark.asyncio
async def test_initialize_with_cdp_uses_openai_provider_for_azure(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://chatgpt-uat.openai.azure.com/openai/v1")
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)

    monkeypatch.setattr(stagehand_service, "Stagehand", DummyStagehand)
    monkeypatch.setattr(stagehand_service, "StagehandConfig", lambda **kwargs: SimpleNamespace(**kwargs))

    service = StagehandExecutionService(headless=False)

    await service.initialize_with_cdp(
        cdp_endpoint="http://localhost:9222",
        user_config={"provider": "azure", "model": "ChatGPT-UAT"},
    )

    assert service.stagehand.config.model_name == "azure/ChatGPT-UAT"
    assert service.stagehand.config.model_api_key == "azure-test-key"
    assert service.stagehand.config.local_browser_launch_options["cdp_url"] == "http://localhost:9222"
    assert os.environ.get("AZURE_API_BASE") == "https://chatgpt-uat.openai.azure.com"
