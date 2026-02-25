"""
Unit tests for UniversalLLMService OpenRouter behavior.
"""
import json
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from app.services.universal_llm import UniversalLLMService


@pytest.mark.asyncio
async def test_call_openrouter_retries_without_free_suffix_on_404_no_endpoint(monkeypatch):
    """When OpenRouter returns no endpoints for :free model, retry once without :free."""
    service = UniversalLLMService()
    monkeypatch.setattr(service, "openrouter_api_key", "test-key", raising=False)

    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    response_404 = httpx.Response(
        404,
        request=request,
        content=json.dumps(
            {
                "error": {
                    "message": "No endpoints found for mistralai/mistral-7b-instruct:free.",
                    "code": 404,
                }
            }
        ).encode(),
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
            "model": "mistralai/mistral-7b-instruct",
            "usage": {"total_tokens": 10},
        }
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=first_response)
    mock_client.post.side_effect = [first_response, second_response]

    async def mock_get_http_client():
        return mock_client

    monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

    result = await service._call_openrouter(
        messages=[{"role": "user", "content": "hello"}],
        model="mistralai/mistral-7b-instruct:free",
    )

    assert result["choices"][0]["message"]["content"] == "ok"
    assert mock_client.post.await_count == 2
    first_model = mock_client.post.await_args_list[0].kwargs["json"]["model"]
    second_model = mock_client.post.await_args_list[1].kwargs["json"]["model"]
    assert first_model == "mistralai/mistral-7b-instruct:free"
    assert second_model == "mistralai/mistral-7b-instruct"
