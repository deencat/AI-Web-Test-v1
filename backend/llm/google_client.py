"""
Google Generative AI LLM Client — OpenAI-compatible interface via Google's v1beta endpoint.

Uses GOOGLE_API_KEY env var. Interface is compatible with AzureClient so all agents
and the AzureOpenAIAdapter can use it without modification.

Supported models (free quota via GOOGLE_API_KEY):
    gemini-2.0-flash-exp
    gemini-1.5-flash
    gemini-1.5-pro
    gemini-2.0-flash-thinking-exp:free
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    logger.warning("openai SDK not installed — GoogleClient unavailable. Install with: pip install openai")


class GoogleClient:
    """
    Thin wrapper around Google's OpenAI-compatible generative AI endpoint.

    Attributes:
        model (str): Model identifier, e.g. "gemini-2.0-flash-exp"
        deployment (str): Alias for model (AzureClient compatibility)
        enabled (bool): True when GOOGLE_API_KEY is set and openai SDK is available
        client: openai.OpenAI instance configured for Google, or None
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        """
        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            model: Gemini model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
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
            logger.info(f"GoogleClient initialized with model: {self.model}")
        else:
            self.client = None
            self.enabled = False
            if not _OPENAI_AVAILABLE:
                logger.warning("openai SDK not available — install with: pip install openai")
            else:
                logger.warning("Google API key not provided — set GOOGLE_API_KEY")
