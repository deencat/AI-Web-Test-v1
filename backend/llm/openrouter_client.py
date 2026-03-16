"""
OpenRouter LLM Client — OpenAI-compatible interface via openrouter.ai.

Uses OPENROUTER_API_KEY env var. Interface is compatible with AzureClient so all agents
and the AzureOpenAIAdapter can use it without modification.

Full model catalogue (including free models): https://openrouter.ai/models
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    logger.warning("openai SDK not installed — OpenRouterClient unavailable. Install with: pip install openai")


class OpenRouterClient:
    """
    Thin wrapper around the OpenRouter inference API (OpenAI-compatible).

    Attributes:
        model (str): Full OpenRouter model identifier, e.g. "qwen/qwen3-coder-480b-a35b:free"
        deployment (str): Alias for model (AzureClient compatibility)
        enabled (bool): True when OPENROUTER_API_KEY is set and openai SDK is available
        client: openai.OpenAI instance configured for OpenRouter, or None
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = _DEFAULT_MODEL,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        """
        Args:
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY env var)
            model: OpenRouter model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.model = model
        self.deployment = model  # AzureClient compatibility alias
        self.temperature = temperature
        self.max_tokens = max_tokens

        if _OPENAI_AVAILABLE and self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=_BASE_URL,
            )
            self.enabled = True
            logger.info(f"OpenRouterClient initialized with model: {self.model}")
        else:
            self.client = None
            self.enabled = False
            if not _OPENAI_AVAILABLE:
                logger.warning("openai SDK not available — install with: pip install openai")
            else:
                logger.warning("OpenRouter API key not provided — set OPENROUTER_API_KEY")
