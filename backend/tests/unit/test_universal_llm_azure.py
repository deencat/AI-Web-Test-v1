"""
Unit tests for UniversalLLMService Azure endpoint handling.
"""
import json
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from app.services.universal_llm import UniversalLLMService


@pytest.mark.asyncio
async def test_call_azure_normalizes_resource_endpoint_to_openai_v1(monkeypatch):
    """Resource root endpoints should call /openai/v1/chat/completions."""
    service = UniversalLLMService()
    monkeypatch.setattr(service, "azure_api_key", "test-key", raising=False)
    monkeypatch.setattr(service, "azure_endpoint", "https://chatgpt-uat.openai.azure.com", raising=False)

    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json = Mock(return_value={"choices": [{"message": {"role": "assistant", "content": "ok"}}]})

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    async def mock_get_http_client():
        return mock_client

    monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

    await service._call_azure(
        messages=[{"role": "user", "content": "hello"}],
        model="ChatGPT-UAT",
    )

    called_url = mock_client.post.await_args.args[0]
    payload = mock_client.post.await_args.kwargs["json"]
    assert called_url == "https://chatgpt-uat.openai.azure.com/openai/v1/chat/completions"
    assert payload["model"] == "ChatGPT-UAT"


@pytest.mark.asyncio
async def test_call_azure_fallbacks_to_deployments_api_on_404(monkeypatch):
    """When v1 endpoint returns 404, retry using Azure deployments endpoint."""
    service = UniversalLLMService()
    monkeypatch.setattr(service, "azure_api_key", "test-key", raising=False)
    monkeypatch.setattr(service, "azure_endpoint", "https://chatgpt-uat.openai.azure.com", raising=False)

    request = httpx.Request("POST", "https://chatgpt-uat.openai.azure.com/openai/v1/chat/completions")
    response_404 = httpx.Response(
        404,
        request=request,
        content=json.dumps({"error": {"code": "404", "message": "Resource not found"}}).encode(),
    )

    first_response = Mock()
    first_response.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError(
            "Not found",
            request=request,
            response=response_404,
        )
    )
    first_response.text = response_404.text

    second_response = Mock()
    second_response.raise_for_status = Mock()
    second_response.json = Mock(
        return_value={
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"total_tokens": 12},
        }
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[first_response, second_response])

    async def mock_get_http_client():
        return mock_client

    monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

    result = await service._call_azure(
        messages=[{"role": "user", "content": "hello"}],
        model="ChatGPT-UAT",
    )

    assert result["choices"][0]["message"]["content"] == "ok"
    assert mock_client.post.await_count == 2

    first_url = mock_client.post.await_args_list[0].args[0]
    second_url = mock_client.post.await_args_list[1].args[0]
    second_payload = mock_client.post.await_args_list[1].kwargs["json"]

    assert first_url == "https://chatgpt-uat.openai.azure.com/openai/v1/chat/completions"
    assert second_url.startswith(
        "https://chatgpt-uat.openai.azure.com/openai/deployments/ChatGPT-UAT/chat/completions?api-version="
    )
    assert "model" not in second_payload
