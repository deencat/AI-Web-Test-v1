"""
Local vLLM Client — OpenAI-compatible interface for on-premises vLLM servers.

Sprint 10.13: Supports three on-premises models, each on its own HTTP endpoint.
No external API key is required; vLLM ignores auth by default.

Endpoint mapping (can be overridden via env vars):
  openai/gpt-oss-20b          -> LOCAL_VLLM_GPT_OSS_20B_ENDPOINT
  RedHatAI/Qwen3.6-35B-A3B-NVFP4 -> LOCAL_VLLM_QWEN3_35B_ENDPOINT
  DeepSeek-V4-Flash-4bit      -> LOCAL_VLLM_DEEPSEEK_ENDPOINT  (default)

Interface is compatible with AzureClient / OpenRouterClient so all agents
and AzureOpenAIAdapter can use it without modification.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "DeepSeek-V4-Flash-4bit"

# Per-model default endpoints — must match stagehand_service.py values
_DEFAULT_ENDPOINTS: dict = {
    "openai/gpt-oss-20b": "http://192.168.206.190:8000/openai--gpt-oss-20b/v1",
    "RedHatAI/Qwen3.6-35B-A3B-NVFP4": "http://192.168.206.190:8000/redhatai--qwen3.6-35b-a3b-nvfp4/v1",
    "DeepSeek-V4-Flash-4bit": "http://192.168.206.164/v1",
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
    ):
        """
        Args:
            model: vLLM model name, e.g. "DeepSeek-V4-Flash-4bit".
            api_key: Optional auth token (vLLM ignores it; defaults to LOCAL_VLLM_API_KEY env or "local").
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
        """
        self.model = model
        self.deployment = model  # AzureClient / OpenRouterClient compatibility alias
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.endpoint = _resolve_endpoint(model)
        self.api_key = api_key or os.getenv("LOCAL_VLLM_API_KEY", "local")

        if _OPENAI_AVAILABLE:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.endpoint.rstrip("/"),
            )
            self.enabled = True
            logger.info(
                "LocalVllmClient initialised: model=%s endpoint=%s",
                self.model,
                self.endpoint,
            )
        else:
            self.client = None
            self.enabled = False
            logger.warning("openai SDK not available — install with: pip install openai")
