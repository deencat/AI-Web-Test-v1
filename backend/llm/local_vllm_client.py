"""
Local vLLM Client — OpenAI-compatible interface for on-premises vLLM servers.

Sprint 10.13: Supports three on-premises models, each on its own HTTP endpoint.
No external API key is required; vLLM ignores auth by default.

Sprint 10.15: Adds enable_thinking constructor parameter.  When True and the
model is thinking-capable (currently only RedHatAI/Qwen3.6-35B-A3B-NVFP4),
chat_completion() injects extra_body={"chat_template_kwargs":{"enable_thinking":True}}
into the OpenAI SDK .create() call.  Non-capable models are unaffected.

Sprint 10.18: Adds Qwen3.6-35B-A3B-MLX-8bit (8-bit MLX quantisation, same
endpoint as DeepSeek at http://192.168.206.164:1235/v1, auth token 1235).
Because this model defaults to thinking=on, chat_completion() now ALWAYS
injects chat_template_kwargs for any thinking-capable model — sending
{"enable_thinking": False} when the toggle is off so the model's built-in
default is explicitly overridden.  Per-model API keys are resolved via a
dedicated env var (LOCAL_VLLM_MLX_API_KEY) to prevent token leakage.

Endpoint mapping (can be overridden via env vars):
  openai/gpt-oss-20b               -> LOCAL_VLLM_GPT_OSS_20B_ENDPOINT
  RedHatAI/Qwen3.6-35B-A3B-NVFP4  -> LOCAL_VLLM_QWEN3_35B_ENDPOINT
  DeepSeek-V4-Flash-4bit           -> LOCAL_VLLM_DEEPSEEK_ENDPOINT  (default)
  Qwen3.6-35B-A3B-MLX-8bit         -> LOCAL_VLLM_MLX_ENDPOINT

Interface is compatible with AzureClient / OpenRouterClient so all agents
and AzureOpenAIAdapter can use it without modification.
"""

import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Sprint 10.15 / 10.18: models that support chain-of-thought thinking via chat_template_kwargs.
# For thinking-capable models, chat_template_kwargs is ALWAYS sent (even when enable_thinking=False)
# so that models whose built-in default is thinking=on can be explicitly overridden.
_THINKING_CAPABLE_MODELS: frozenset = frozenset({
    "RedHatAI/Qwen3.6-35B-A3B-NVFP4",
    "Qwen3.6-35B-A3B-MLX-8bit",  # Sprint 10.18: always-off override required
})

_DEFAULT_MODEL = "DeepSeek-V4-Flash-4bit"

# Per-model default endpoints — must match stagehand_service.py values
_DEFAULT_ENDPOINTS: dict = {
    "openai/gpt-oss-20b": "http://192.168.206.190:8000/openai--gpt-oss-20b/v1",
    "RedHatAI/Qwen3.6-35B-A3B-NVFP4": "http://192.168.206.190:8000/redhatai--qwen3.6-35b-a3b-nvfp4/v1",
    "DeepSeek-V4-Flash-4bit": "http://192.168.206.164:1235/v1",
    "Qwen3.6-35B-A3B-MLX-8bit": "http://192.168.206.164:1235/v1",  # Sprint 10.18: MLX server
}

_ENV_ENDPOINT_KEYS: dict = {
    "openai/gpt-oss-20b": "LOCAL_VLLM_GPT_OSS_20B_ENDPOINT",
    "RedHatAI/Qwen3.6-35B-A3B-NVFP4": "LOCAL_VLLM_QWEN3_35B_ENDPOINT",
    "DeepSeek-V4-Flash-4bit": "LOCAL_VLLM_DEEPSEEK_ENDPOINT",
    "Qwen3.6-35B-A3B-MLX-8bit": "LOCAL_VLLM_MLX_ENDPOINT",  # Sprint 10.18
}

# Sprint 10.18: per-model API key env vars and their defaults.
# Prevents token leakage between vLLM deployments that use different auth tokens.
_MODEL_API_KEY_ENV: dict = {
    "Qwen3.6-35B-A3B-MLX-8bit": ("LOCAL_VLLM_MLX_API_KEY", "1235"),
}

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    logger.warning("openai SDK not installed — LocalVllmClient unavailable. Install with: pip install openai")


def _resolve_endpoint(model: str, override: Optional[str] = None) -> str:
    """Return the HTTP endpoint for the given model, respecting env overrides.

    Resolution order:
    1. ``override`` argument (Phase 2 custom endpoint passed by caller).
    2. Per-model env var (e.g. LOCAL_VLLM_QWEN3_35B_ENDPOINT).
    3. Hardcoded default for the model.
    4. LOCAL_VLLM_CUSTOM_ENDPOINT env var (global fallback for unlisted models).
    5. Default DeepSeek endpoint.
    """
    if override:
        return override
    env_key = _ENV_ENDPOINT_KEYS.get(model)
    default = _DEFAULT_ENDPOINTS.get(model)
    if default is None:
        # Unknown model — use global custom endpoint env var, then DeepSeek as last resort
        default = os.getenv("LOCAL_VLLM_CUSTOM_ENDPOINT", _DEFAULT_ENDPOINTS[_DEFAULT_MODEL])
    if env_key:
        return os.getenv(env_key, default)
    return default


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
        endpoint: Optional[str] = None,
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
            endpoint: Phase 2 — optional override endpoint URL.  When provided, replaces the
                hardcoded endpoint table lookup (useful for custom/unlisted models).
        """
        self.model = model
        self.deployment = model  # AzureClient / OpenRouterClient compatibility alias
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.endpoint = _resolve_endpoint(model, override=endpoint)
        # Sprint 10.18: resolve API key — prefer explicit arg, then per-model env var,
        # then global LOCAL_VLLM_API_KEY env var.
        if api_key:
            self.api_key = api_key
        elif model in _MODEL_API_KEY_ENV:
            env_var, default = _MODEL_API_KEY_ENV[model]
            self.api_key = os.getenv(env_var, default)
        else:
            self.api_key = os.getenv("LOCAL_VLLM_API_KEY", "local")
        # Sprint 10.15/10.18: store user's choice; gated for non-capable models so
        # self.enable_thinking is always False for models not in _THINKING_CAPABLE_MODELS.
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

        # Sprint 10.18: for thinking-capable models always send chat_template_kwargs
        # (even when False) so the model's built-in default of thinking=on is overridden.
        if self.model in _THINKING_CAPABLE_MODELS:
            kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": self.enable_thinking}}

        return self.client.chat.completions.create(**kwargs)
