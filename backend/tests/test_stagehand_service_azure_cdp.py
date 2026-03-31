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


# ---------------------------------------------------------------------------
# gpt-5.2 dedicated endpoint routing — Sprint 10.9
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_initialize_with_gpt52_uses_hutch_endpoint(monkeypatch):
    """When model=gpt-5.2, AZURE_API_BASE must be set to the hutch eastus2 endpoint."""
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "default-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://chatgpt-uat.openai.azure.com/openai/v1")
    monkeypatch.setenv("AZURE_OPENAI_GPT52_ENDPOINT", "https://hutch-mkklgrll-eastus2.cognitiveservices.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_GPT52_API_VERSION", "2024-12-01-preview")
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)

    monkeypatch.setattr(stagehand_service, "Stagehand", DummyStagehand)
    monkeypatch.setattr(stagehand_service, "StagehandConfig", lambda **kwargs: SimpleNamespace(**kwargs))

    service = StagehandExecutionService(headless=False)

    await service.initialize_with_cdp(
        cdp_endpoint="http://localhost:9222",
        user_config={"provider": "azure", "model": "gpt-5.2"},
    )

    assert service.stagehand.config.model_name == "azure/gpt-5.2"
    assert "hutch-mkklgrll-eastus2" in os.environ.get("AZURE_API_BASE", ""), (
        f"AZURE_API_BASE must point to hutch endpoint, got: {os.environ.get('AZURE_API_BASE')}"
    )
    assert os.environ.get("AZURE_API_VERSION") == "2024-12-01-preview"


@pytest.mark.asyncio
async def test_initialize_with_gpt52_uses_dedicated_api_key_when_set(monkeypatch):
    """When AZURE_OPENAI_GPT52_API_KEY is set, it should be used instead of default key."""
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "default-key")
    monkeypatch.setenv("AZURE_OPENAI_GPT52_ENDPOINT", "https://hutch-mkklgrll-eastus2.cognitiveservices.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_GPT52_API_KEY", "gpt52-specific-key")
    monkeypatch.setenv("AZURE_OPENAI_GPT52_API_VERSION", "2024-12-01-preview")
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)

    monkeypatch.setattr(stagehand_service, "Stagehand", DummyStagehand)
    monkeypatch.setattr(stagehand_service, "StagehandConfig", lambda **kwargs: SimpleNamespace(**kwargs))

    service = StagehandExecutionService(headless=False)

    await service.initialize_with_cdp(
        cdp_endpoint="http://localhost:9222",
        user_config={"provider": "azure", "model": "gpt-5.2"},
    )

    assert service.stagehand.config.model_api_key == "gpt52-specific-key"


@pytest.mark.asyncio
async def test_gpt52_falls_back_to_default_endpoint_when_not_configured(monkeypatch):
    """When AZURE_OPENAI_GPT52_ENDPOINT is not set, gpt-5.2 uses the default Azure endpoint."""
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "default-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://chatgpt-uat.openai.azure.com/openai/v1")
    monkeypatch.delenv("AZURE_OPENAI_GPT52_ENDPOINT", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)

    monkeypatch.setattr(stagehand_service, "Stagehand", DummyStagehand)
    monkeypatch.setattr(stagehand_service, "StagehandConfig", lambda **kwargs: SimpleNamespace(**kwargs))

    service = StagehandExecutionService(headless=False)

    await service.initialize_with_cdp(
        cdp_endpoint="http://localhost:9222",
        user_config={"provider": "azure", "model": "gpt-5.2"},
    )

    assert "chatgpt-uat" in os.environ.get("AZURE_API_BASE", "")
