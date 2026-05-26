"""
Local vLLM Client — OpenAI-compatible interface for on-premises vLLM servers.

Sprint 10.13: Supports three on-premises models, each on its own HTTP endpoint.
No external API key is required; vLLM ignores auth by default.

Sprint 10.15: Adds enable_thinking constructor parameter.  When True and the
model is thinking-capable (currently only RedHatAI/Qwen3.6-35B-A3B-NVFP4),
chat_completion() injects extra_body={"chat_template_kwargs":{"enable_thinking":True}}
into the OpenAI SDK .create() call.  Non-capable models are unaffected.

Endpoint mapping (can be overridden via env vars):
  openai/gpt-oss-20b          -> LOCAL_VLLM_GPT_OSS_20B_ENDPOINT
  RedHatAI/Qwen3.6-35B-A3B-NVFP4 -> LOCAL_VLLM_QWEN3_35B_ENDPOINT
  DeepSeek-V4-Flash-4bit      -> LOCAL_VLLM_DEEPSEEK_ENDPOINT  (default)

Interface is compatible with AzureClient / OpenRouterClient so all agents
and AzureOpenAIAdapter can use it without modification.
"""

import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Sprint 10.15: models that support chain-of-thought thinking via chat_template_kwargs
_THINKING_CAPABLE_MODELS: frozenset = frozenset({
    "RedHatAI/Qwen3.6-35B-A3B-NVFP4",
})

_DEFAULT_MODEL = "DeepSeek-V4-Flash-4bit"

# Per-model default endpoints — must match stagehand_service.py values
_DEFAULT_ENDPOINTS: dict = {
    "openai/gpt-oss-20b": "http://192.168.206.190:8000/openai--gpt-oss-20b/v1",
    "RedHatAI/Qwen3.6-35B-A3B-NVFP4": "http://192.168.206.190:8000/redhatai--qwen3.6-35b-a3b-nvfp4/v1",
    "DeepSeek-V4-Flash-4bit": "http://192.168.206.164:1235/v1",
}

_ENV_ENDPOINT_KEYS: dict = {
    "openai/gpt-oss-20b": "LOCAL_VLLM_GPT_OSS_20B_ENDPOINT",
    "RedHatAI/Qwen3.6-35B-A3B-NVFP4": "LOCAL_VLLM_QWEN3_35B_ENDPOINT",
    "DeepSeek-V4-Flash-4bit": "LOCAL_VLLM_DEEPSEEK_ENDPOINT",
}

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    logger.warning("openai SDK not installed — LocalVllmClient unavailable. Install with: pip install openai")


def _resolve_endpoint(model: str) -> str:
    """Return the HTTP endpoint for the given model, respecting env overrides."""
    env_key = _ENV_ENDPOINT_KEYS.get(model)
    default = _DEFAULT_ENDPOINTS.get(model, _DEFAULT_ENDPOINTS[_DEFAULT_MODEL])
    if env_key:
        return os.getenv(env_key, default)
    return os.getenv("LOCAL_VLLM_DEEPSEEK_ENDPOINT", default)


class LocalVllmClient:
    """
    Thin OpenAI-compatible client for on-premises vLLM inference servers.

    Attributes:
        model (str): Model name as understood by the vLLM server.
        deployment (str): Alias for model (AzureClient compatibility).
        endpoint (str): Base URL of the vLLM OpenAI-compatible endpoint.
        enabled (bool): True when openai SDK is available (no API key needed).
        client: openai.OpenAI instance or None.
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        api_key: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        enable_thinking: bool = False,
    ):
        """
        Args:
            model: vLLM model name, e.g. "DeepSeek-V4-Flash-4bit".
            api_key: Optional auth token (vLLM ignores it; defaults to LOCAL_VLLM_API_KEY env or "local").
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            enable_thinking: Sprint 10.15 — when True and the model is thinking-capable,
                chat_completion() will inject extra_body={"chat_template_kwargs":{"enable_thinking":True}}
                into every SDK .create() call.  Silently ignored for non-capable models.
        """
        self.model = model
        self.deployment = model  # AzureClient / OpenRouterClient compatibility alias
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.endpoint = _resolve_endpoint(model)
        self.api_key = api_key or os.getenv("LOCAL_VLLM_API_KEY", "local")
        # Sprint 10.15: gated by both this flag AND model capability
        self.enable_thinking = enable_thinking and model in _THINKING_CAPABLE_MODELS

        if _OPENAI_AVAILABLE:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.endpoint.rstrip("/"),
            )
            self.enabled = True
            logger.info(
                "LocalVllmClient initialised: model=%s endpoint=%s enable_thinking=%s",
                self.model,
                self.endpoint,
                self.enable_thinking,
            )
        else:
            self.client = None
            self.enabled = False
            logger.warning("openai SDK not available — install with: pip install openai")

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the vLLM server via the OpenAI SDK.

        Sprint 10.15: when self.enable_thinking is True (set only for thinking-capable
        models), injects extra_body={"chat_template_kwargs":{"enable_thinking":True}}
        into the SDK call so vLLM enables chain-of-thought reasoning.

        Args:
            messages: OpenAI-style message list.
            temperature: Override instance temperature.
            max_tokens: Override instance max_tokens.

        Returns:
            Raw openai.types.chat.ChatCompletion object (dict-like).

        Raises:
            RuntimeError: if the openai SDK is not available.
        """
        if not self.enabled or self.client is None:
            raise RuntimeError(
                "LocalVllmClient is not available — openai SDK missing or client not initialised."
            )

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        # Sprint 10.15: thinking mode — only for capable models, gated at __init__
        if self.enable_thinking:
            kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": True}}

        return self.client.chat.completions.create(**kwargs)
