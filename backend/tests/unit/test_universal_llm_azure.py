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


# ---------------------------------------------------------------------------
# gpt-5.2 endpoint routing — Sprint 10.8 Developer B
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_call_azure_gpt52_uses_dedicated_endpoint(monkeypatch):
    """When model is gpt-5.2 and GPT52 endpoint is configured, that endpoint is used."""
    service = UniversalLLMService()
    monkeypatch.setattr(service, "azure_api_key", "default-key", raising=False)
    monkeypatch.setattr(service, "azure_endpoint", "https://chatgpt-uat.openai.azure.com", raising=False)
    monkeypatch.setattr(
        service,
        "_azure_model_endpoints",
        {
            "gpt-5.2": {
                "endpoint": "https://hutch-mkklgrll-eastus2.cognitiveservices.azure.com",
                "api_version": "2024-12-01-preview",
                "api_key": "default-key",
            }
        },
        raising=False,
    )

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
        model="gpt-5.2",
    )

    called_url = mock_client.post.await_args.args[0]
    assert "hutch-mkklgrll-eastus2" in called_url, (
        f"gpt-5.2 must use the dedicated endpoint, got: {called_url}"
    )
    assert "chatgpt-uat" not in called_url, (
        f"gpt-5.2 must NOT route to the UAT endpoint, got: {called_url}"
    )


@pytest.mark.asyncio
async def test_call_azure_gpt52_uses_preview_api_version(monkeypatch):
    """gpt-5.2 deployments must use the 2024-12-01-preview API version in the fallback URL."""
    service = UniversalLLMService()
    monkeypatch.setattr(service, "azure_api_key", "default-key", raising=False)
    monkeypatch.setattr(service, "azure_endpoint", "https://chatgpt-uat.openai.azure.com", raising=False)
    monkeypatch.setattr(
        service,
        "_azure_model_endpoints",
        {
            "gpt-5.2": {
                "endpoint": "https://hutch-mkklgrll-eastus2.cognitiveservices.azure.com",
                "api_version": "2024-12-01-preview",
                "api_key": "default-key",
            }
        },
        raising=False,
    )

    import httpx

    request = httpx.Request(
        "POST",
        "https://hutch-mkklgrll-eastus2.cognitiveservices.azure.com/openai/v1/chat/completions",
    )
    response_404 = httpx.Response(
        404,
        request=request,
        content=b'{"error": {"code": "404"}}',
    )

    first_response = Mock()
    first_response.raise_for_status = Mock(
        side_effect=httpx.HTTPStatusError("Not found", request=request, response=response_404)
    )
    first_response.text = response_404.text

    second_response = Mock()
    second_response.raise_for_status = Mock()
    second_response.json = Mock(
        return_value={"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=[first_response, second_response])

    async def mock_get_http_client():
        return mock_client

    monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

    await service._call_azure(
        messages=[{"role": "user", "content": "hello"}],
        model="gpt-5.2",
    )

    deployment_url = mock_client.post.await_args_list[1].args[0]
    assert "2024-12-01-preview" in deployment_url, (
        f"gpt-5.2 fallback URL must include 2024-12-01-preview, got: {deployment_url}"
    )


@pytest.mark.asyncio
async def test_call_azure_gpt52_falls_back_to_default_endpoint_when_not_configured(monkeypatch):
    """When GPT52 endpoint is not configured, gpt-5.2 uses the default Azure endpoint."""
    service = UniversalLLMService()
    monkeypatch.setattr(service, "azure_api_key", "default-key", raising=False)
    monkeypatch.setattr(service, "azure_endpoint", "https://chatgpt-uat.openai.azure.com", raising=False)
    # No GPT52 endpoint configured
    monkeypatch.setattr(service, "_azure_model_endpoints", {}, raising=False)

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
        model="gpt-5.2",
    )

    called_url = mock_client.post.await_args.args[0]
    assert "chatgpt-uat.openai.azure.com" in called_url
