"""
Browser-Use LLM Adapter - Adapts Azure OpenAI to browser-use LLM interface

This adapter allows browser-use library to use Azure OpenAI for LLM-guided navigation.
Browser-use expects an LLM object conforming to BaseChatModel protocol with:
  - model, provider, name, model_name attributes
  - async ainvoke(messages, output_format=None, **kwargs) -> ChatInvokeCompletion

Key design decisions:
  1. browser-use's token tracking service wraps ainvoke with a tracked_ainvoke
     that passes output_format as the SECOND POSITIONAL argument (not in kwargs).
     Our ainvoke signature MUST match: ainvoke(self, messages, output_format=None, **kwargs)

  2. browser-use passes `output_format` (a Pydantic model class, e.g. AgentOutput)
     We MUST parse the LLM JSON response into that Pydantic model so that
     computed @property fields like `current_state` are available.

  3. We return ChatInvokeCompletion (browser-use's own response type) with
     ChatInvokeUsage for proper token tracking.
"""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
from llm.azure_client import get_azure_client

logger = logging.getLogger(__name__)

# Try to import browser-use types
try:
    from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage
    BROWSER_USE_VIEWS_AVAILABLE = True
except ImportError:
    BROWSER_USE_VIEWS_AVAILABLE = False

try:
    from browser_use.llm.base import BaseChatModel as BrowserUseLLM
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    # Create stub base class if browser-use not available
    class BrowserUseLLM:
        """Stub base class when browser-use not available"""
        pass


def _normalize_messages(messages: list) -> List[Dict[str, str]]:
    """
    Normalize browser-use / LangChain message formats to Azure OpenAI format.

    browser-use may send messages as:
      - LangChain/browser-use Message objects (with .role / .content attributes)
      - Dicts with content as a list of parts: [{"type": "text", "text": "..."}]

    Azure OpenAI expects {"role": str, "content": str}.
    """
    normalized: List[Dict[str, str]] = []
    for msg in messages:
        # Extract role / content regardless of message type
        if hasattr(msg, 'content') and hasattr(msg, 'role'):
            role = msg.role
            content = msg.content
        elif isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", "")
        else:
            logger.warning(f"Unexpected message format: {type(msg)}")
            continue

        # Flatten list-based content to a single string
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(str(part["text"]))
                elif hasattr(part, 'text'):
                    # ContentPartTextParam or similar objects
                    text_parts.append(str(part.text))
                else:
                    text_parts.append(str(part))
            content_str = "".join(text_parts)
        else:
            content_str = str(content)

        normalized.append({"role": role, "content": content_str})
    return normalized


class AzureOpenAIAdapter:
    """
    Adapter to use Azure OpenAI with browser-use library.

    Conforms to browser-use's BaseChatModel protocol:
      - model: str
      - provider: str (property)
      - name: str (property)
      - model_name: str (property)
      - ainvoke(messages, output_format=None, **kwargs) -> ChatInvokeCompletion
    """

    _verified_api_keys: bool = True  # Protocol field

    def __init__(self, azure_client=None):
        if not BROWSER_USE_AVAILABLE:
            logger.warning("browser-use not available - adapter will not work")

        self.azure_client = azure_client or get_azure_client()

        if not self.azure_client or not self.azure_client.enabled:
            logger.warning("Azure OpenAI client not enabled - adapter will fail")

        self._provider = 'azure-openai'

        model_name = self.azure_client.deployment if self.azure_client and self.azure_client.enabled else 'unknown'
        self.model = model_name

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def name(self) -> str:
        return f"{self._provider}_{self.model}"

    @property
    def model_name(self) -> str:
        return self.model

    # ------------------------------------------------------------------
    # Core Azure OpenAI call (shared by achat / ainvoke)
    # ------------------------------------------------------------------

    async def _call_azure(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000,
        force_json: bool = False,
    ):
        """
        Call Azure OpenAI chat completion and return the raw SDK response object.
        Runs the synchronous SDK call in a thread-pool executor.
        """
        if not self.azure_client or not self.azure_client.client:
            raise ValueError("Azure OpenAI client not initialized / enabled")

        create_kwargs: dict = dict(
            model=self.azure_client.deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if force_json:
            # Force the model to produce valid JSON (Azure supports this)
            create_kwargs["response_format"] = {"type": "json_object"}

        def _sync():
            return self.azure_client.client.chat.completions.create(**create_kwargs)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync)

    # ------------------------------------------------------------------
    # achat  -  simple text response
    # ------------------------------------------------------------------

    async def achat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Simple async chat completion. Returns assistant text."""
        normalized = _normalize_messages(messages)
        resp = await self._call_azure(
            normalized,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 2000),
        )
        if resp.choices and len(resp.choices) > 0:
            return resp.choices[0].message.content
        raise ValueError("No response from Azure OpenAI")

    # ------------------------------------------------------------------
    # ainvoke  -  browser-use entry-point (returns ChatInvokeCompletion)
    # ------------------------------------------------------------------

    async def ainvoke(self, input_data, output_format=None, **kwargs):
        """
        Browser-use compatible ainvoke.

        IMPORTANT: browser-use's token tracking service wraps this method:
            async def tracked_ainvoke(messages, output_format=None, **kwargs):
                result = await original_ainvoke(messages, output_format, **kwargs)
        So output_format is passed as the SECOND POSITIONAL argument.
        Our signature MUST accept it as a positional parameter.

        Args:
            input_data: List of BaseMessage objects or dicts
            output_format: Pydantic model class (e.g. AgentOutput) or None
            **kwargs: Additional args (session_id, temperature, max_tokens, etc.)

        Returns:
            ChatInvokeCompletion with .completion, .usage, .stop_reason
        """
        if not self.azure_client or not self.azure_client.enabled:
            raise ValueError("Azure OpenAI client not enabled")

        # -- Also check kwargs as fallback for output_format --
        if output_format is None:
            output_format = kwargs.pop("output_format", None)
        else:
            kwargs.pop("output_format", None)
        kwargs.pop("session_id", None)  # not used by us

        logger.info(f"ainvoke called: output_format={output_format.__name__ if output_format else None}, "
                     f"input type={type(input_data).__name__}")

        # -- Normalise messages --------------------------------------------------
        if isinstance(input_data, dict):
            messages = input_data.get("messages", [])
        elif isinstance(input_data, list):
            messages = input_data
        else:
            raise ValueError(f"Unexpected input_data type: {type(input_data)}")

        formatted = _normalize_messages(messages)

        # -- Call Azure OpenAI (force JSON when we need structured output) --------
        force_json = output_format is not None
        temperature = kwargs.get("temperature", 0.3)
        max_tokens = kwargs.get("max_tokens", 4096)

        response = await self._call_azure(
            formatted,
            temperature=temperature,
            max_tokens=max_tokens,
            force_json=force_json,
        )

        # -- Extract response text -----------------------------------------------
        if not (response.choices and len(response.choices) > 0):
            raise ValueError("No response from Azure OpenAI")
        response_text: str = response.choices[0].message.content
        stop_reason = getattr(response.choices[0], 'finish_reason', None)
        logger.debug(f"LLM response length: {len(response_text)} chars, stop_reason: {stop_reason}")

        # -- Parse into Pydantic model (AgentOutput) if output_format given -------
        completion: Any = response_text  # Default: raw text
        if output_format is not None:
            try:
                # Clean response_text: strip markdown code fences if present
                clean = response_text.strip()
                if clean.startswith("```"):
                    first_nl = clean.index("\n")
                    clean = clean[first_nl + 1:]
                if clean.endswith("```"):
                    clean = clean[:-3].rstrip()

                completion = output_format.model_validate_json(clean)
                logger.info(f"Successfully parsed LLM response into {output_format.__name__}")
            except Exception as e:
                logger.warning(
                    f"Failed to parse LLM response into {output_format.__name__}: {e}. "
                    f"Response (first 500 chars): {response_text[:500]}"
                )
                # Fallback: try parsing as dict and constructing the model
                try:
                    parsed_dict = json.loads(response_text)
                    completion = output_format.model_validate(parsed_dict)
                    logger.info("Fallback dict parsing succeeded")
                except Exception as e2:
                    logger.error(f"Fallback parsing also failed: {e2}")
                    raise ValueError(
                        f"LLM response missing required fields. "
                        f"Expected format: {output_format.__name__}. "
                        f"Response: {response_text[:300]}"
                    ) from e2

        # -- Build ChatInvokeUsage for browser-use token tracking -----------------
        usage: Optional[Any] = None
        if hasattr(response, "usage") and response.usage:
            if BROWSER_USE_VIEWS_AVAILABLE:
                usage = ChatInvokeUsage(
                    prompt_tokens=getattr(response.usage, "prompt_tokens", 0),
                    completion_tokens=getattr(response.usage, "completion_tokens", 0),
                    total_tokens=getattr(response.usage, "total_tokens", 0),
                    prompt_cached_tokens=getattr(response.usage, "prompt_cached_tokens", 0) or 0,
                    prompt_cache_creation_tokens=getattr(response.usage, "prompt_cache_creation_tokens", 0) or 0,
                    prompt_image_tokens=getattr(response.usage, "prompt_image_tokens", 0) or 0,
                )
            else:
                usage = {
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                    "prompt_cached_tokens": 0,
                    "prompt_cache_creation_tokens": 0,
                    "prompt_image_tokens": 0,
                }

        # -- Return ChatInvokeCompletion (browser-use's expected return type) -----
        if BROWSER_USE_VIEWS_AVAILABLE:
            return ChatInvokeCompletion(
                completion=completion,
                usage=usage,
                stop_reason=stop_reason,
            )
        else:
            # Fallback: return a duck-typed object
            class _FallbackResponse:
                def __init__(self, completion, usage, stop_reason):
                    self.completion = completion
                    self.usage = usage
                    self.stop_reason = stop_reason
            return _FallbackResponse(completion=completion, usage=usage, stop_reason=stop_reason)

    # ------------------------------------------------------------------
    # astream  -  streaming (optional, not required for basic operation)
    # ------------------------------------------------------------------

    async def astream(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        """Stream chat completion (falls back to full response for simplicity)."""
        logger.info("Streaming not natively supported; falling back to full response.")
        full_response = await self.achat(messages, **kwargs)
        yield full_response
