"""
Unit tests for Sprint 10.15 — vLLM Thinking Mode Toggle.

TDD: Tests cover all gating logic for chat_template_kwargs injection.

Coverage:
  UniversalLLMService._call_local_vllm:
    1. enable_thinking=True + thinking-capable model  →  chat_template_kwargs injected
    2. enable_thinking=False + thinking-capable model →  chat_template_kwargs absent
    3. enable_thinking=True + non-capable model        →  chat_template_kwargs absent
    4. enable_thinking=True + default model (DeepSeek) →  chat_template_kwargs absent
    5. All other providers (azure, google) unaffected by enable_thinking kwarg

  LocalVllmClient.__init__ / chat_completion:
    6. enable_thinking=True + capable model   →  self.enable_thinking=True
    7. enable_thinking=True + non-capable     →  self.enable_thinking=False (gated at init)
    8. enable_thinking=False + capable model  →  self.enable_thinking=False
    9. chat_completion with thinking ON  →  extra_body present in SDK call
   10. chat_completion with thinking OFF →  extra_body absent from SDK call
   11. chat_completion raises RuntimeError when SDK unavailable
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ok_response(content: str = "OK") -> Mock:
    """Build a minimal httpx mock response."""
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_response.json = Mock(return_value={
        "choices": [{"message": {"role": "assistant", "content": content}}]
    })
    return mock_response


def _make_universal_service():
    """Return a fresh UniversalLLMService with the local vLLM endpoint table."""
    from app.services.universal_llm import UniversalLLMService
    return UniversalLLMService()


# ---------------------------------------------------------------------------
# 1. enable_thinking=True + thinking-capable model → chat_template_kwargs injected
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_call_local_vllm_injects_thinking_flag_for_capable_model(monkeypatch):
    """When enable_thinking=True and model is thinking-capable, payload must
    contain chat_template_kwargs: {enable_thinking: true}."""
    service = _make_universal_service()

    mock_response = _make_ok_response()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    async def mock_get_http_client():
        return mock_client

    monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

    await service._call_local_vllm(
        messages=[{"role": "user", "content": "Think about this"}],
        model="RedHatAI/Qwen3.6-35B-A3B-NVFP4",
        enable_thinking=True,
    )

    payload = mock_client.post.await_args.kwargs["json"]
    assert "chat_template_kwargs" in payload, "chat_template_kwargs must be present"
    assert payload["chat_template_kwargs"] == {"enable_thinking": True}


# ---------------------------------------------------------------------------
# 2. enable_thinking=False + thinking-capable model → flag absent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_call_local_vllm_omits_thinking_flag_when_disabled(monkeypatch):
    """When enable_thinking=False, chat_template_kwargs must NOT be in the payload
    even for a thinking-capable model."""
    service = _make_universal_service()

    mock_response = _make_ok_response()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    async def mock_get_http_client():
        return mock_client

    monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

    await service._call_local_vllm(
        messages=[{"role": "user", "content": "Hello"}],
        model="RedHatAI/Qwen3.6-35B-A3B-NVFP4",
        enable_thinking=False,
    )

    payload = mock_client.post.await_args.kwargs["json"]
    assert "chat_template_kwargs" not in payload


# ---------------------------------------------------------------------------
# 3. enable_thinking=True + non-capable model → flag absent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_call_local_vllm_omits_thinking_flag_for_non_capable_model(monkeypatch):
    """Even when enable_thinking=True, non-capable models must not receive the flag."""
    service = _make_universal_service()

    mock_response = _make_ok_response()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    async def mock_get_http_client():
        return mock_client

    monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

    for non_capable_model in ("openai/gpt-oss-20b", "DeepSeek-V4-Flash-4bit"):
        mock_client.post.reset_mock()
        await service._call_local_vllm(
            messages=[{"role": "user", "content": "Hello"}],
            model=non_capable_model,
            enable_thinking=True,
        )
        payload = mock_client.post.await_args.kwargs["json"]
        assert "chat_template_kwargs" not in payload, (
            f"chat_template_kwargs must NOT be sent for {non_capable_model}"
        )


# ---------------------------------------------------------------------------
# 4. enable_thinking=True + default model (DeepSeek) → flag absent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_call_local_vllm_default_model_no_thinking_flag(monkeypatch):
    """Calling without a model (defaults to DeepSeek) must never inject the flag."""
    service = _make_universal_service()

    mock_response = _make_ok_response()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    async def mock_get_http_client():
        return mock_client

    monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

    await service._call_local_vllm(
        messages=[{"role": "user", "content": "Hello"}],
        model=None,          # defaults to DeepSeek-V4-Flash-4bit
        enable_thinking=True,
    )

    payload = mock_client.post.await_args.kwargs["json"]
    assert "chat_template_kwargs" not in payload


# ---------------------------------------------------------------------------
# 5. Other providers unaffected — chat_completion routes correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_chat_completion_enable_thinking_ignored_for_azure(monkeypatch):
    """enable_thinking kwarg must be silently accepted and NOT forwarded to Azure."""
    from app.services.universal_llm import UniversalLLMService

    service = UniversalLLMService()
    monkeypatch.setattr(service, "azure_api_key", "test-key", raising=False)
    monkeypatch.setattr(service, "azure_endpoint", "https://chatgpt-uat.openai.azure.com", raising=False)

    mock_response = _make_ok_response()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    async def mock_get_http_client():
        return mock_client

    monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

    # Must not raise even when enable_thinking=True is passed
    result = await service.chat_completion(
        messages=[{"role": "user", "content": "Hello"}],
        provider="azure",
        model="ChatGPT-UAT",
        enable_thinking=True,  # should be ignored
    )

    payload = mock_client.post.await_args.kwargs["json"]
    assert "chat_template_kwargs" not in payload
    assert "enable_thinking" not in payload


# ---------------------------------------------------------------------------
# LocalVllmClient unit tests
# ---------------------------------------------------------------------------

class TestLocalVllmClientThinking:
    """Unit tests for LocalVllmClient enable_thinking parameter."""

    def test_init_sets_enable_thinking_true_for_capable_model(self):
        """enable_thinking=True with a capable model → self.enable_thinking=True."""
        from llm.local_vllm_client import LocalVllmClient
        with patch("llm.local_vllm_client._OPENAI_AVAILABLE", False):
            client = LocalVllmClient(
                model="RedHatAI/Qwen3.6-35B-A3B-NVFP4",
                enable_thinking=True,
            )
        assert client.enable_thinking is True

    def test_init_gates_thinking_for_non_capable_model(self):
        """enable_thinking=True with a NON-capable model → self.enable_thinking=False."""
        from llm.local_vllm_client import LocalVllmClient
        with patch("llm.local_vllm_client._OPENAI_AVAILABLE", False):
            for model in ("openai/gpt-oss-20b", "DeepSeek-V4-Flash-4bit"):
                client = LocalVllmClient(model=model, enable_thinking=True)
                assert client.enable_thinking is False, (
                    f"Thinking must be gated for non-capable model {model}"
                )

    def test_init_thinking_false_by_default(self):
        """enable_thinking should default to False."""
        from llm.local_vllm_client import LocalVllmClient
        with patch("llm.local_vllm_client._OPENAI_AVAILABLE", False):
            client = LocalVllmClient(model="RedHatAI/Qwen3.6-35B-A3B-NVFP4")
        assert client.enable_thinking is False

    def test_chat_completion_injects_extra_body_when_thinking_on(self):
        """chat_completion passes extra_body to SDK .create() when thinking is on."""
        from llm.local_vllm_client import LocalVllmClient

        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_openai_client.chat.completions.create.return_value = mock_response

        with patch("llm.local_vllm_client._OPENAI_AVAILABLE", True), \
             patch("llm.local_vllm_client.OpenAI", return_value=mock_openai_client):
            client = LocalVllmClient(
                model="RedHatAI/Qwen3.6-35B-A3B-NVFP4",
                enable_thinking=True,
            )

        client.chat_completion(messages=[{"role": "user", "content": "Think"}])

        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        assert "extra_body" in call_kwargs
        assert call_kwargs["extra_body"] == {"chat_template_kwargs": {"enable_thinking": True}}

    def test_chat_completion_omits_extra_body_when_thinking_off(self):
        """chat_completion must NOT pass extra_body when enable_thinking is False."""
        from llm.local_vllm_client import LocalVllmClient

        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = MagicMock()

        with patch("llm.local_vllm_client._OPENAI_AVAILABLE", True), \
             patch("llm.local_vllm_client.OpenAI", return_value=mock_openai_client):
            client = LocalVllmClient(
                model="RedHatAI/Qwen3.6-35B-A3B-NVFP4",
                enable_thinking=False,
            )

        client.chat_completion(messages=[{"role": "user", "content": "Hello"}])

        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        assert "extra_body" not in call_kwargs

    def test_chat_completion_raises_when_sdk_unavailable(self):
        """chat_completion must raise RuntimeError when openai SDK is not installed."""
        from llm.local_vllm_client import LocalVllmClient
        with patch("llm.local_vllm_client._OPENAI_AVAILABLE", False):
            client = LocalVllmClient(model="RedHatAI/Qwen3.6-35B-A3B-NVFP4")

        with pytest.raises(RuntimeError, match="not available"):
            client.chat_completion(messages=[{"role": "user", "content": "test"}])


# ---------------------------------------------------------------------------
# UserSettingsService unit tests — thinking_capable in model_options
# ---------------------------------------------------------------------------

class TestUserSettingsServiceThinkingCapable:
    """Verify that thinking_capable is surfaced correctly in provider model_options."""

    def test_qwen_is_thinking_capable(self):
        """RedHatAI/Qwen3.6-35B-A3B-NVFP4 must have thinking_capable=True."""
        from app.services.user_settings_service import UserSettingsService
        service = UserSettingsService()
        providers = service.get_available_providers()

        vllm = next(p for p in providers if p.name == "local_vllm")
        qwen_option = next(
            m for m in vllm.model_options
            if m.id == "RedHatAI/Qwen3.6-35B-A3B-NVFP4"
        )
        assert qwen_option.thinking_capable is True

    def test_non_capable_models_are_not_thinking_capable(self):
        """gpt-oss-20b and DeepSeek must have thinking_capable=False."""
        from app.services.user_settings_service import UserSettingsService
        service = UserSettingsService()
        providers = service.get_available_providers()

        vllm = next(p for p in providers if p.name == "local_vllm")
        non_capable = [
            m for m in vllm.model_options
            if m.id in ("openai/gpt-oss-20b", "DeepSeek-V4-Flash-4bit")
        ]
        assert len(non_capable) == 2, "Both non-capable models should appear"
        for m in non_capable:
            assert m.thinking_capable is False, f"{m.id} must NOT be thinking-capable"

    def test_non_vllm_providers_have_no_thinking_capable_models(self):
        """No model outside local_vllm should have thinking_capable=True."""
        from app.services.user_settings_service import UserSettingsService
        service = UserSettingsService()
        providers = service.get_available_providers()

        for p in providers:
            if p.name == "local_vllm":
                continue
            for m in p.model_options:
                assert m.thinking_capable is False, (
                    f"Provider {p.name}, model {m.id} must not be thinking-capable"
                )
