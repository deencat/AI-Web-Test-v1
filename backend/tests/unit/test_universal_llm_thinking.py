"""
Unit tests for Sprint 10.15 + Sprint 10.18 — vLLM Thinking Mode Toggle.

TDD: Tests cover all gating logic for chat_template_kwargs injection.

Coverage (Sprint 10.15 baseline):
  UniversalLLMService._call_local_vllm:
    1. enable_thinking=True + thinking-capable model  →  chat_template_kwargs injected (True)
    2. enable_thinking=False + thinking-capable model →  chat_template_kwargs injected (False) [10.18]
    3. enable_thinking=True + non-capable model        →  chat_template_kwargs absent
    4. enable_thinking=True + default model (DeepSeek) →  chat_template_kwargs absent
    5. All other providers (azure, google) unaffected by enable_thinking kwarg

  LocalVllmClient.__init__ / chat_completion:
    6. enable_thinking=True + capable model   →  self.enable_thinking=True
    7. enable_thinking=True + non-capable     →  self.enable_thinking=False (gated at init)
    8. enable_thinking=False + capable model  →  self.enable_thinking=False
    9. chat_completion with thinking ON  →  extra_body present with enable_thinking=True
   10. chat_completion with thinking OFF + capable model →  extra_body present with enable_thinking=False [10.18]
   11. chat_completion raises RuntimeError when SDK unavailable

Coverage (Sprint 10.18 additions):
   12. Qwen3.6-35B-A3B-MLX-8bit is in _THINKING_CAPABLE_VLLM_MODELS
   13. _call_local_vllm: Qwen3.6-35B-A3B-MLX-8bit + enable_thinking=False → explicit {false}
   14. _call_local_vllm: Qwen3.6-35B-A3B-MLX-8bit + enable_thinking=True  → explicit {true}
   15. DeepSeek-V4-Flash-4bit never receives chat_template_kwargs regardless of toggle
   16. LocalVllmClient: MLX model IS thinking-capable
   17. LocalVllmClient: MLX + thinking OFF → extra_body present with enable_thinking=False
   18. UserSettingsService: Qwen3.6-35B-A3B-MLX-8bit thinking_capable=True
   19. UserSettingsService: non-capable models unchanged
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
# 2. enable_thinking=False + thinking-capable model → flag INJECTED with False
#    (Sprint 10.18: always-explicit for capable models so built-in default is overridden)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_call_local_vllm_injects_explicit_false_for_capable_model_thinking_off(monkeypatch):
    """Sprint 10.18: when enable_thinking=False and model is thinking-capable,
    payload MUST contain chat_template_kwargs: {enable_thinking: false} so that
    a model whose built-in default is thinking=on is explicitly overridden."""
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
    assert "chat_template_kwargs" in payload, (
        "Sprint 10.18: chat_template_kwargs must be present even when thinking is off "
        "so capable models do not default to thinking=on"
    )
    assert payload["chat_template_kwargs"] == {"enable_thinking": False}


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

    def test_chat_completion_injects_explicit_false_for_capable_model_thinking_off(self):
        """Sprint 10.18: chat_completion MUST send extra_body with enable_thinking=False
        for thinking-capable models even when the toggle is off, so the model's
        built-in thinking-on default is explicitly overridden."""
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
        assert "extra_body" in call_kwargs, (
            "Sprint 10.18: extra_body must be present for capable model even when thinking=False"
        )
        assert call_kwargs["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}

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


# ---------------------------------------------------------------------------
# Sprint 10.18 additions
# ---------------------------------------------------------------------------

class TestSprint1018MLXModel:
    """Sprint 10.18: Qwen3.6-35B-A3B-MLX-8bit always-off thinking override."""

    # ------------------------------------------------------------------
    # _THINKING_CAPABLE_VLLM_MODELS membership
    # ------------------------------------------------------------------

    def test_mlx_model_is_in_thinking_capable_vllm_models(self):
        """Qwen3.6-35B-A3B-MLX-8bit must appear in _THINKING_CAPABLE_VLLM_MODELS."""
        from app.services.universal_llm import _THINKING_CAPABLE_VLLM_MODELS
        assert "Qwen3.6-35B-A3B-MLX-8bit" in _THINKING_CAPABLE_VLLM_MODELS

    def test_mlx_model_is_in_local_vllm_client_thinking_capable_models(self):
        """Qwen3.6-35B-A3B-MLX-8bit must appear in local_vllm_client._THINKING_CAPABLE_MODELS."""
        from llm.local_vllm_client import _THINKING_CAPABLE_MODELS
        assert "Qwen3.6-35B-A3B-MLX-8bit" in _THINKING_CAPABLE_MODELS

    # ------------------------------------------------------------------
    # UniversalLLMService._call_local_vllm — always-explicit injection
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_call_local_vllm_mlx_thinking_off_sends_explicit_false(self, monkeypatch):
        """Qwen3.6-35B-A3B-MLX-8bit with enable_thinking=False must inject
        chat_template_kwargs: {enable_thinking: false} to override the model's
        built-in default of thinking=on."""
        service = _make_universal_service()

        mock_response = _make_ok_response()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        async def mock_get_http_client():
            return mock_client

        monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

        await service._call_local_vllm(
            messages=[{"role": "user", "content": "Hello"}],
            model="Qwen3.6-35B-A3B-MLX-8bit",
            enable_thinking=False,
        )

        payload = mock_client.post.await_args.kwargs["json"]
        assert "chat_template_kwargs" in payload, (
            "Must inject chat_template_kwargs for MLX model even when thinking=False"
        )
        assert payload["chat_template_kwargs"] == {"enable_thinking": False}

    @pytest.mark.asyncio
    async def test_call_local_vllm_mlx_thinking_on_sends_explicit_true(self, monkeypatch):
        """Qwen3.6-35B-A3B-MLX-8bit with enable_thinking=True must inject
        chat_template_kwargs: {enable_thinking: true}."""
        service = _make_universal_service()

        mock_response = _make_ok_response()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        async def mock_get_http_client():
            return mock_client

        monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

        await service._call_local_vllm(
            messages=[{"role": "user", "content": "Think"}],
            model="Qwen3.6-35B-A3B-MLX-8bit",
            enable_thinking=True,
        )

        payload = mock_client.post.await_args.kwargs["json"]
        assert payload.get("chat_template_kwargs") == {"enable_thinking": True}

    @pytest.mark.asyncio
    async def test_deepseek_never_receives_chat_template_kwargs(self, monkeypatch):
        """DeepSeek-V4-Flash-4bit must NEVER receive chat_template_kwargs
        regardless of the enable_thinking toggle value."""
        service = _make_universal_service()

        mock_response = _make_ok_response()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        async def mock_get_http_client():
            return mock_client

        monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

        for toggle in (True, False):
            mock_client.post.reset_mock()
            await service._call_local_vllm(
                messages=[{"role": "user", "content": "Hello"}],
                model="DeepSeek-V4-Flash-4bit",
                enable_thinking=toggle,
            )
            payload = mock_client.post.await_args.kwargs["json"]
            assert "chat_template_kwargs" not in payload, (
                f"chat_template_kwargs must NOT be sent for DeepSeek "
                f"(enable_thinking={toggle})"
            )

    @pytest.mark.asyncio
    async def test_gpt_oss_20b_never_receives_chat_template_kwargs(self, monkeypatch):
        """openai/gpt-oss-20b must never receive chat_template_kwargs."""
        service = _make_universal_service()

        mock_response = _make_ok_response()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        async def mock_get_http_client():
            return mock_client

        monkeypatch.setattr(service, "_get_http_client", mock_get_http_client)

        await service._call_local_vllm(
            messages=[{"role": "user", "content": "Hello"}],
            model="openai/gpt-oss-20b",
            enable_thinking=True,
        )
        payload = mock_client.post.await_args.kwargs["json"]
        assert "chat_template_kwargs" not in payload

    # ------------------------------------------------------------------
    # LocalVllmClient — MLX model behaviour
    # ------------------------------------------------------------------

    def test_local_vllm_client_mlx_init_thinking_capable(self):
        """LocalVllmClient: MLX model with enable_thinking=True → self.enable_thinking=True."""
        from llm.local_vllm_client import LocalVllmClient
        with patch("llm.local_vllm_client._OPENAI_AVAILABLE", False):
            client = LocalVllmClient(
                model="Qwen3.6-35B-A3B-MLX-8bit",
                enable_thinking=True,
            )
        assert client.enable_thinking is True

    def test_local_vllm_client_mlx_thinking_off_extra_body_explicit_false(self):
        """LocalVllmClient: MLX + thinking OFF must send extra_body with enable_thinking=False."""
        from llm.local_vllm_client import LocalVllmClient

        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = MagicMock()

        with patch("llm.local_vllm_client._OPENAI_AVAILABLE", True), \
             patch("llm.local_vllm_client.OpenAI", return_value=mock_openai_client):
            client = LocalVllmClient(
                model="Qwen3.6-35B-A3B-MLX-8bit",
                enable_thinking=False,
            )

        client.chat_completion(messages=[{"role": "user", "content": "Hello"}])

        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        assert "extra_body" in call_kwargs, (
            "extra_body must be present for MLX model even when thinking=False"
        )
        assert call_kwargs["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}

    def test_local_vllm_client_mlx_thinking_on_extra_body_explicit_true(self):
        """LocalVllmClient: MLX + thinking ON must send extra_body with enable_thinking=True."""
        from llm.local_vllm_client import LocalVllmClient

        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.return_value = MagicMock()

        with patch("llm.local_vllm_client._OPENAI_AVAILABLE", True), \
             patch("llm.local_vllm_client.OpenAI", return_value=mock_openai_client):
            client = LocalVllmClient(
                model="Qwen3.6-35B-A3B-MLX-8bit",
                enable_thinking=True,
            )

        client.chat_completion(messages=[{"role": "user", "content": "Think"}])

        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        assert call_kwargs.get("extra_body") == {"chat_template_kwargs": {"enable_thinking": True}}

    def test_local_vllm_client_non_capable_no_extra_body(self):
        """Non-capable models (DeepSeek, gpt-oss-20b) must never receive extra_body
        regardless of the enable_thinking parameter."""
        from llm.local_vllm_client import LocalVllmClient

        for model in ("DeepSeek-V4-Flash-4bit", "openai/gpt-oss-20b"):
            mock_openai_client = MagicMock()
            mock_openai_client.chat.completions.create.return_value = MagicMock()

            with patch("llm.local_vllm_client._OPENAI_AVAILABLE", True), \
                 patch("llm.local_vllm_client.OpenAI", return_value=mock_openai_client):
                client = LocalVllmClient(model=model, enable_thinking=True)

            client.chat_completion(messages=[{"role": "user", "content": "Hello"}])
            call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
            assert "extra_body" not in call_kwargs, (
                f"extra_body must NOT be present for non-capable model {model}"
            )

    # ------------------------------------------------------------------
    # UserSettingsService — MLX model in thinking_capable_models
    # ------------------------------------------------------------------

    def test_mlx_model_is_thinking_capable_in_settings_service(self):
        """UserSettingsService: Qwen3.6-35B-A3B-MLX-8bit must have thinking_capable=True."""
        from app.services.user_settings_service import UserSettingsService
        service = UserSettingsService()
        providers = service.get_available_providers()

        vllm = next(p for p in providers if p.name == "local_vllm")
        mlx_option = next(
            (m for m in vllm.model_options if m.id == "Qwen3.6-35B-A3B-MLX-8bit"),
            None,
        )
        assert mlx_option is not None, "Qwen3.6-35B-A3B-MLX-8bit must appear in local_vllm models"
        assert mlx_option.thinking_capable is True

    def test_existing_qwen_nvfp4_still_thinking_capable(self):
        """Sprint 10.18 regression: RedHatAI/Qwen3.6-35B-A3B-NVFP4 must still be thinking-capable."""
        from app.services.user_settings_service import UserSettingsService
        service = UserSettingsService()
        providers = service.get_available_providers()

        vllm = next(p for p in providers if p.name == "local_vllm")
        nvfp4_option = next(
            m for m in vllm.model_options if m.id == "RedHatAI/Qwen3.6-35B-A3B-NVFP4"
        )
        assert nvfp4_option.thinking_capable is True

    def test_deepseek_and_gpt_oss_not_thinking_capable(self):
        """DeepSeek-V4-Flash-4bit and openai/gpt-oss-20b must still have thinking_capable=False."""
        from app.services.user_settings_service import UserSettingsService
        service = UserSettingsService()
        providers = service.get_available_providers()

        vllm = next(p for p in providers if p.name == "local_vllm")
        non_capable = [
            m for m in vllm.model_options
            if m.id in ("openai/gpt-oss-20b", "DeepSeek-V4-Flash-4bit")
        ]
        assert len(non_capable) == 2
        for m in non_capable:
            assert m.thinking_capable is False, f"{m.id} must NOT be thinking-capable"
