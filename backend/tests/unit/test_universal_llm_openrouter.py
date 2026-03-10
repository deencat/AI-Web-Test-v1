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


# ---------------------------------------------------------------------------
# Sprint 10.5: Data-policy error detection & immediate raise (no retry)
# ---------------------------------------------------------------------------

def _make_404_response(message: str) -> httpx.Response:
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    return httpx.Response(
        404,
        request=request,
        content=json.dumps({"error": {"message": message, "code": 404}}).encode(),
    )


def _make_http_status_error(response: httpx.Response) -> httpx.HTTPStatusError:
    return httpx.HTTPStatusError("Not found", request=response.request, response=response)


class TestIsDataPolicyError:
    """Unit tests for the _is_data_policy_error static method."""

    def test_method_exists(self):
        assert hasattr(UniversalLLMService, "_is_data_policy_error")

    def test_detects_data_policy_free_model_publication(self):
        resp = _make_404_response(
            "No endpoints found matching your data policy (Free model publication). "
            "Configure: https://openrouter.ai/settings/privacy"
        )
        err = _make_http_status_error(resp)
        assert UniversalLLMService._is_data_policy_error(err) is True

    def test_detects_data_policy_lowercase(self):
        resp = _make_404_response("no endpoints found matching your data policy")
        err = _make_http_status_error(resp)
        assert UniversalLLMService._is_data_policy_error(err) is True

    def test_does_not_match_plain_no_endpoints_found(self):
        """Regular model-unavailable 404 must NOT be classified as a data-policy error."""
        resp = _make_404_response("No endpoints found for mistralai/mistral-7b-instruct:free.")
        err = _make_http_status_error(resp)
        assert UniversalLLMService._is_data_policy_error(err) is False

    def test_does_not_match_non_404_status(self):
        request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
        resp = httpx.Response(
            500,
            request=request,
            content=json.dumps({"error": {"message": "data policy issue", "code": 500}}).encode(),
        )
        err = _make_http_status_error(resp)
        assert UniversalLLMService._is_data_policy_error(err) is False

    def test_returns_false_for_unrelated_error(self):
        resp = _make_404_response("model not found")
        err = _make_http_status_error(resp)
        assert UniversalLLMService._is_data_policy_error(err) is False


class TestCallOpenRouterDataPolicyBehaviour:
    """_call_openrouter must raise immediately with an actionable message on data-policy 404."""

    @pytest.mark.asyncio
    async def test_raises_immediately_without_retry_on_data_policy_error(self, monkeypatch):
        """No retry attempts must be made when the error is a data-policy block."""
        service = UniversalLLMService()
        monkeypatch.setattr(service, "openrouter_api_key", "test-key", raising=False)

        data_policy_response = _make_404_response(
            "No endpoints found matching your data policy (Free model publication). "
            "Configure: https://openrouter.ai/settings/privacy"
        )
        mock_response = Mock()
        mock_response.raise_for_status = Mock(
            side_effect=_make_http_status_error(data_policy_response)
        )
        mock_response.text = data_policy_response.text

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        monkeypatch.setattr(service, "_get_http_client", AsyncMock(return_value=mock_client))

        with pytest.raises(Exception) as exc_info:
            await service._call_openrouter(
                messages=[{"role": "user", "content": "hello"}],
                model="openai/gpt-oss-120b:free",
            )

        # Must fail on the FIRST attempt only — no retry
        assert mock_client.post.await_count == 1, (
            f"Expected 1 attempt (no retry), got {mock_client.post.await_count}"
        )

        error_message = str(exc_info.value)
        assert "data policy" in error_message.lower() or "privacy" in error_message.lower(), (
            f"Error message should mention data policy or privacy settings, got: {error_message}"
        )

    @pytest.mark.asyncio
    async def test_actionable_error_message_contains_settings_link(self, monkeypatch):
        """Error message must include the OpenRouter privacy settings URL."""
        service = UniversalLLMService()
        monkeypatch.setattr(service, "openrouter_api_key", "test-key", raising=False)

        data_policy_response = _make_404_response(
            "No endpoints found matching your data policy (Free model publication). "
            "Configure: https://openrouter.ai/settings/privacy"
        )
        mock_response = Mock()
        mock_response.raise_for_status = Mock(
            side_effect=_make_http_status_error(data_policy_response)
        )
        mock_response.text = data_policy_response.text

        monkeypatch.setattr(
            service, "_get_http_client", AsyncMock(return_value=AsyncMock(post=AsyncMock(return_value=mock_response)))
        )

        with pytest.raises(Exception) as exc_info:
            await service._call_openrouter(
                messages=[{"role": "user", "content": "hello"}],
                model="openai/gpt-oss-120b:free",
            )

        assert "openrouter.ai/settings/privacy" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_regular_model_unavailable_still_retries(self, monkeypatch):
        """A plain 'No endpoints found' error (not data-policy) must still trigger a retry."""
        service = UniversalLLMService()
        monkeypatch.setattr(service, "openrouter_api_key", "test-key", raising=False)

        plain_404_response = _make_404_response(
            "No endpoints found for some-model:free."
        )
        first_mock = Mock()
        first_mock.raise_for_status = Mock(
            side_effect=_make_http_status_error(plain_404_response)
        )
        first_mock.text = plain_404_response.text

        second_mock = Mock()
        second_mock.raise_for_status = Mock()
        second_mock.json = Mock(return_value={
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "model": "google/gemini-2.0-flash-exp:free",
            "usage": {"total_tokens": 5},
        })

        mock_client = AsyncMock()
        mock_client.post.side_effect = [first_mock, second_mock]
        monkeypatch.setattr(service, "_get_http_client", AsyncMock(return_value=mock_client))

        result = await service._call_openrouter(
            messages=[{"role": "user", "content": "hello"}],
            model="some-model:free",
        )

        assert mock_client.post.await_count == 2, "Regular unavailable error should retry"
        assert result["choices"][0]["message"]["content"] == "ok"
