"""
LLM Client Factory (Sprint 10.6 Phase 0 — Task 0.1).

Single entry-point that maps (provider, model) -> the correct LLM client instance.

Supported providers
-------------------
  azure       — AzureClient (uses AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT)
  cerebras    — CerebrasClient (uses CEREBRAS_API_KEY)
  google      — GoogleClient (uses GOOGLE_API_KEY via generativelanguage.googleapis.com)
  openrouter  — OpenRouterClient (uses OPENROUTER_API_KEY via openrouter.ai)

Fallback behaviour
------------------
If the requested provider is unrecognised, its required env key is absent, or its
constructor raises, the factory logs a warning and returns an AzureClient using the
default Azure deployment name.  Callers can always inspect client.enabled to decide
whether to proceed or skip LLM-enhanced paths.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Default Azure model used as fallback target
_AZURE_DEFAULT_MODEL: str = "ChatGPT-UAT"


def get_llm_client(provider: Optional[str], model: str):
    """
    Return an LLM client for the given provider and model.

    Args:
        provider: One of "azure", "cerebras", "google", "openrouter".
                  Case-insensitive; leading/trailing whitespace is stripped.
                  None or "" are treated as "azure".
        model: Model / deployment name to use, e.g. "ChatGPT-UAT",
               "llama3.1-8b", "gemini-2.0-flash-exp",
               "qwen/qwen3-coder-480b-a35b:free".

    Returns:
        A client instance with:
          - .enabled (bool)
          - .deployment / .model (str)
          - .client (SDK client or None)
        Falls back to AzureClient(deployment=_AZURE_DEFAULT_MODEL) on any error.
    """
    provider_key = (provider or "azure").strip().lower()

    try:
        if provider_key == "azure":
            return _get_azure_client(model)

        if provider_key == "cerebras":
            return _get_cerebras_client(model)

        if provider_key == "google":
            client = _get_google_client(model)
            if client.enabled:
                return client
            logger.warning(
                "GoogleClient not enabled (missing GOOGLE_API_KEY?), falling back to Azure"
            )
            return _get_azure_client(_AZURE_DEFAULT_MODEL)

        if provider_key == "openrouter":
            client = _get_openrouter_client(model)
            if client.enabled:
                return client
            logger.warning(
                "OpenRouterClient not enabled (missing OPENROUTER_API_KEY?), falling back to Azure"
            )
            return _get_azure_client(_AZURE_DEFAULT_MODEL)

        logger.warning(
            f"Unknown LLM provider '{provider}' — falling back to Azure/{_AZURE_DEFAULT_MODEL}"
        )
        return _get_azure_client(_AZURE_DEFAULT_MODEL)

    except Exception as exc:  # pragma: no cover — safety net
        logger.warning(
            f"Failed to create '{provider}' client ({exc}), falling back to Azure"
        )
        return _get_azure_client(_AZURE_DEFAULT_MODEL)


# ---------------------------------------------------------------------------
# Private factory helpers — each isolated so they can be monkeypatched in tests
# ---------------------------------------------------------------------------

def _get_azure_client(model: str):
    from llm.azure_client import AzureClient
    return AzureClient(deployment=model)


def _get_cerebras_client(model: str):
    from llm.cerebras_client import CerebrasClient
    return CerebrasClient(model=model)


def _get_google_client(model: str):
    from llm.google_client import GoogleClient
    return GoogleClient(model=model)


def _get_openrouter_client(model: str):
    from llm.openrouter_client import OpenRouterClient
    return OpenRouterClient(model=model)
