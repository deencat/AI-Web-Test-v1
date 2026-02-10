"""
Unit tests for UniversalLLMService Google provider conversion.
"""
import pytest
from unittest.mock import AsyncMock, Mock

from app.services.universal_llm import UniversalLLMService


@pytest.mark.asyncio
async def test_call_google_converts_response(monkeypatch):
    """Ensure Gemini response maps to OpenAI-style structure."""
    service = UniversalLLMService()
    monkeypatch.setattr(service, "google_api_key", "test-key", raising=False)

    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json = Mock(
        return_value={
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Hello from Gemini"}
                        ]
                    }
                }
            ],
            "usageMetadata": {"totalTokenCount": 123}
        }
    )

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    async def mock_get_http_client():
        return mock_client

    monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

    result = await service._call_google(
        messages=[{"role": "user", "content": "Hi"}],
        model="gemini-1.5-flash"
    )

    assert result["choices"][0]["message"]["content"] == "Hello from Gemini"
    assert result["usage"]["total_tokens"] == 123
    mock_response.raise_for_status.assert_called_once()
