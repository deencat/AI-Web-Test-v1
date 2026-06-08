"""
Universal LLM service that supports multiple providers.
Handles Google Gemini, Cerebras, and OpenRouter.
"""
import base64
import datetime
import httpx
import logging
import os
import time
from typing import List, Dict, Optional, Union
from app.core.config import settings

_svc_logger = logging.getLogger(__name__)

# Sprint 10.15 / 10.18: vLLM models that accept chat_template_kwargs: { enable_thinking }.
# Sprint 10.18: chat_template_kwargs is ALWAYS sent for these models — even when
# enable_thinking=False — so that models whose built-in default is thinking=on
# (e.g. Qwen3.6-35B-A3B-MLX-8bit) are explicitly overridden.
_THINKING_CAPABLE_VLLM_MODELS: frozenset = frozenset({
    "RedHatAI/Qwen3.6-35B-A3B-NVFP4",
    "Qwen3.6-35B-A3B-MLX-8bit",  # Sprint 10.18: always-off override required
})

# Sprint 10.17: providers that support multimodal vision requests
_VISION_CAPABLE_PROVIDERS: frozenset = frozenset({"azure", "openrouter", "google"})


class VisionNotSupportedError(Exception):
    """Raised when the configured provider/model does not support vision (image) input.

    Callers (ScreenshotVerificationService) catch this and escalate to Tier 3.
    """


class UniversalLLMService:
    """Service for interacting with multiple LLM providers."""

    OPENROUTER_DEFAULT_FALLBACK_MODEL = "google/gemini-2.0-flash-exp:free"
    CEREBRAS_DEFAULT_FALLBACK_MODEL = "llama3.1-8b"
    
    def __init__(self):
        # Use settings object which loads from .env via pydantic_settings
        # Fallback to os.getenv for compatibility
        self.google_api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
        self.cerebras_api_key = settings.CEREBRAS_API_KEY or os.getenv("CEREBRAS_API_KEY")
        self.openrouter_api_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.azure_api_key = settings.AZURE_OPENAI_API_KEY or os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = settings.AZURE_OPENAI_ENDPOINT or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_version = settings.AZURE_OPENAI_API_VERSION or os.getenv("AZURE_OPENAI_API_VERSION") or "2024-02-01"

        # Per-model endpoint overrides: maps deployment name -> {endpoint, api_version, api_key}
        # gpt-5.2 lives on a separate Azure resource (hutch, eastus2) with a newer API version.
        _gpt52_endpoint = getattr(settings, "AZURE_OPENAI_GPT52_ENDPOINT", None) or os.getenv("AZURE_OPENAI_GPT52_ENDPOINT")
        _gpt52_api_version = getattr(settings, "AZURE_OPENAI_GPT52_API_VERSION", "2024-12-01-preview") or "2024-12-01-preview"
        _gpt52_api_key = getattr(settings, "AZURE_OPENAI_GPT52_API_KEY", None) or os.getenv("AZURE_OPENAI_GPT52_API_KEY")
        self._azure_model_endpoints: dict = {
            "gpt-5.2": {
                "endpoint": _gpt52_endpoint,
                "api_version": _gpt52_api_version,
                "api_key": _gpt52_api_key or self.azure_api_key,
            }
        }

        # Sprint 10.13: Local vLLM per-model endpoint table (OpenAI-compatible, no real auth)
        _local_api_key = getattr(settings, "LOCAL_VLLM_API_KEY", "local") or os.getenv("LOCAL_VLLM_API_KEY", "local")
        # Sprint 10.18: MLX model uses its own API key env var (default "1235")
        _mlx_api_key = getattr(settings, "LOCAL_VLLM_MLX_API_KEY", None) or os.getenv("LOCAL_VLLM_MLX_API_KEY", "1235")
        self._local_vllm_model_endpoints: dict = {
            "openai/gpt-oss-20b": {
                "endpoint": getattr(settings, "LOCAL_VLLM_GPT_OSS_20B_ENDPOINT", "http://192.168.206.190:8000/openai--gpt-oss-20b/v1") or os.getenv("LOCAL_VLLM_GPT_OSS_20B_ENDPOINT", "http://192.168.206.190:8000/openai--gpt-oss-20b/v1"),
                "api_key": _local_api_key,
            },
            "RedHatAI/Qwen3.6-35B-A3B-NVFP4": {
                "endpoint": getattr(settings, "LOCAL_VLLM_QWEN3_35B_ENDPOINT", "http://192.168.206.190:8000/redhatai--qwen3.6-35b-a3b-nvfp4/v1") or os.getenv("LOCAL_VLLM_QWEN3_35B_ENDPOINT", "http://192.168.206.190:8000/redhatai--qwen3.6-35b-a3b-nvfp4/v1"),
                "api_key": _local_api_key,
            },
            "DeepSeek-V4-Flash-4bit": {
                "endpoint": getattr(settings, "LOCAL_VLLM_DEEPSEEK_ENDPOINT", "http://192.168.206.164:1235/v1") or os.getenv("LOCAL_VLLM_DEEPSEEK_ENDPOINT", "http://192.168.206.164:1235/v1"),
                "api_key": _local_api_key,
            },
            # Sprint 10.18: MLX 8-bit quantisation on http://192.168.206.164:1235/v1
            # Endpoint collision with DeepSeek is intentional; vLLM dispatches via model field.
            "Qwen3.6-35B-A3B-MLX-8bit": {
                "endpoint": getattr(settings, "LOCAL_VLLM_MLX_ENDPOINT", "http://192.168.206.164:1235/v1") or os.getenv("LOCAL_VLLM_MLX_ENDPOINT", "http://192.168.206.164:1235/v1"),
                "api_key": _mlx_api_key,
            },
        }

        # OPT-1: HTTP Session Reuse - Create shared httpx client for connection pooling
        # This reduces connection overhead by 20-30% for multiple LLM calls
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = "openrouter",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        enable_thinking: bool = False,
        custom_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        azure_api_version: Optional[str] = None,
    ) -> dict:
        """
        Call LLM API for chat completion with provider selection.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            provider: Provider to use (google, cerebras, openrouter)
            model: Model to use (provider-specific)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            enable_thinking: Sprint 10.15 — when True and provider is local_vllm
                and the model supports it, injects chat_template_kwargs into the
                request payload.  Ignored for all other providers.
            custom_endpoint: Phase 2 — optional override endpoint for local_vllm
                models not in the hardcoded routing table.  Ignored for other
                providers.
            
        Returns:
            Unified API response dict with choices, usage, etc.
            
        Raises:
            ValueError: If API key is not configured
            Exception: If API call fails
        """
        provider = provider.lower()
        _t0 = time.monotonic()
        _error: Optional[str] = None
        _response: Optional[dict] = None
        try:
            if provider == "google":
                _response = await self._call_google(messages, model, temperature, max_tokens)
            elif provider == "cerebras":
                _response = await self._call_cerebras(messages, model, temperature, max_tokens)
            elif provider == "azure":
                _response = await self._call_azure(
                    messages, model, temperature, max_tokens,
                    endpoint_override=azure_endpoint,
                    api_version_override=azure_api_version,
                )
            elif provider == "local_vllm":
                _response = await self._call_local_vllm(
                    messages,
                    model,
                    temperature,
                    max_tokens,
                    enable_thinking=enable_thinking,
                    custom_endpoint=custom_endpoint,
                    api_key=api_key,
                )
            else:  # default to openrouter
                _response = await self._call_openrouter(messages, model, temperature, max_tokens)
        except Exception as exc:
            _error = str(exc)
            raise
        finally:
            await self._write_llm_log(
                messages=messages,
                provider=provider,
                model=model or "",
                response=_response,
                error=_error,
                elapsed_ms=(time.monotonic() - _t0) * 1000,
                caller="chat_completion",
            )
        return _response  # type: ignore[return-value]

    async def _write_llm_log(
        self,
        *,
        messages: list,
        provider: str,
        model: str,
        response: Optional[dict],
        error: Optional[str],
        elapsed_ms: float,
        caller: str,
    ) -> None:
        """Build and write one JSONL log entry for this LLM call (swallows errors)."""
        try:
            from app.utils.llm_execution_context import llm_exec_ctx
            from app.utils.llm_response_logger import (
                llm_logger,
                build_prompt_preview,
                extract_thinking_from_response,
            )

            ctx = llm_exec_ctx.get()
            full_prompt = bool(getattr(settings, "LLM_LOG_FULL_PROMPT", False))

            # Extract thinking / tokens from response (if any)
            thinking_content = None
            response_content = None
            thinking_tokens = None
            prompt_tokens = None
            completion_tokens = None
            total_tokens = None

            if response:
                thinking_content, response_content, thinking_tokens = (
                    extract_thinking_from_response(response)
                )
                usage = response.get("usage") or {}
                prompt_tokens = usage.get("prompt_tokens")
                completion_tokens = usage.get("completion_tokens")
                total_tokens = usage.get("total_tokens")

            # Brief console summary (existing logger, no change to format)
            thinking_info = f" (thinking: {thinking_tokens}tok)" if thinking_tokens else ""
            _svc_logger.info(
                "[LLM] provider=%s model=%s tier=%s step=%s → %.0fms %stok%s",
                provider,
                model,
                ctx.get("tier"),
                ctx.get("step_number"),
                elapsed_ms,
                total_tokens or "?",
                thinking_info,
            )

            entry = {
                "ts": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(datetime.datetime.utcnow().microsecond / 1000):03d}Z",
                "execution_id": ctx.get("execution_id"),
                "step_number": ctx.get("step_number"),
                "tier": ctx.get("tier"),
                "caller": ctx.get("caller") or caller,
                "provider": provider,
                "model": model,
                "prompt_chars": sum(len(str(m.get("content", ""))) for m in messages),
                "prompt_preview": build_prompt_preview(messages, full_prompt=full_prompt),
                "response_time_ms": round(elapsed_ms, 1),
                "thinking_content": thinking_content,
                "response_content": response_content,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "thinking_tokens": thinking_tokens,
                "total_tokens": total_tokens,
                "success": error is None,
                "error": error,
            }
            await llm_logger.write(entry)
        except Exception as log_exc:  # noqa: BLE001
            _svc_logger.debug("LLM logging failed (non-fatal): %s", log_exc)

    # ------------------------------------------------------------------
    # Sprint 10.17: Multimodal vision completion
    # ------------------------------------------------------------------

    async def vision_completion(
        self,
        image_bytes: bytes,
        system_prompt: str,
        user_text: str,
        provider: str = "openrouter",
        model: Optional[str] = None,
        max_tokens: int = 256,
    ) -> dict:
        """Call a vision-capable LLM with an image + text prompt.

        Args:
            image_bytes: Raw PNG/JPEG screenshot bytes.
            system_prompt: System instruction (e.g. PASS/FAIL response format).
            user_text: User message describing the verification task.
            provider: LLM provider. Must be one of: azure, openrouter, google.
                      cerebras and local_vllm raise VisionNotSupportedError.
            model: Optional model override.
            max_tokens: Maximum tokens in the response.

        Returns:
            Unified response dict (same structure as chat_completion).

        Raises:
            VisionNotSupportedError: When provider does not support vision.
            ValueError: When required API credentials are missing.
            Exception: On API errors.
        """
        provider = provider.lower()

        if provider not in _VISION_CAPABLE_PROVIDERS:
            raise VisionNotSupportedError(
                f"Provider '{provider}' does not support vision requests. "
                "Use azure, openrouter, or google for verify_screenshot steps."
            )

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        _t0 = time.monotonic()
        _error: Optional[str] = None
        _response: Optional[dict] = None
        try:
            if provider == "google":
                _response = await self._call_google_vision(image_b64, system_prompt, user_text, model, max_tokens)
            elif provider == "azure":
                _response = await self._call_azure_vision(image_b64, system_prompt, user_text, model, max_tokens)
            else:  # openrouter
                _response = await self._call_openrouter_vision(image_b64, system_prompt, user_text, model, max_tokens)
        except Exception as exc:
            _error = str(exc)
            raise
        finally:
            # Log vision call using a synthetic text messages list for prompt_preview
            _vision_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ]
            await self._write_llm_log(
                messages=_vision_messages,
                provider=provider,
                model=model or "",
                response=_response,
                error=_error,
                elapsed_ms=(time.monotonic() - _t0) * 1000,
                caller="vision_verification",
            )
        return _response  # type: ignore[return-value]

    async def _call_openrouter_vision(
        self,
        image_b64: str,
        system_prompt: str,
        user_text: str,
        model: Optional[str],
        max_tokens: int,
    ) -> dict:
        """Call OpenRouter with a multimodal (vision) message."""
        if not self.openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Required for vision requests via OpenRouter."
            )

        resolved_model = model or self.OPENROUTER_DEFAULT_FALLBACK_MODEL

        messages: List[Dict] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            },
        ]

        payload = {
            "model": resolved_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }

        client = await self._get_http_client()
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "AI Web Test",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise Exception("OpenRouter vision API request timed out (90s)")
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "Unknown error"
            raise Exception(f"OpenRouter vision API error ({e.response.status_code}): {error_detail}")
        except httpx.HTTPError as e:
            raise Exception(f"OpenRouter vision API connection error: {str(e)}")

    async def _call_azure_vision(
        self,
        image_b64: str,
        system_prompt: str,
        user_text: str,
        model: Optional[str],
        max_tokens: int,
    ) -> dict:
        """Call Azure OpenAI with a multimodal (vision) message.

        Uses the same endpoint/URL resolution as _call_azure:
        - Tries v1/chat/completions first (works for gpt-5.x)
        - Falls back to deployments/<model>/chat/completions
        - Uses max_completion_tokens for gpt-5.x models (not max_tokens)
        """
        resolved_model = model or "ChatGPT-UAT"
        model_override = self._azure_model_endpoints.get(resolved_model, {})
        effective_endpoint = model_override.get("endpoint") or self.azure_endpoint
        effective_api_version = model_override.get("api_version") or self.azure_api_version
        effective_api_key = model_override.get("api_key") or self.azure_api_key

        if not effective_api_key or not effective_endpoint:
            raise ValueError(
                "AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT not set for vision requests."
            )

        resource_base = (
            effective_endpoint.split("/openai")[0]
            if "/openai" in effective_endpoint
            else effective_endpoint
        )

        # gpt-5.x requires max_completion_tokens, older models use max_tokens
        token_limit_field = "max_completion_tokens" if resolved_model.startswith("gpt-5") else "max_tokens"

        messages: List[Dict] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            },
        ]

        # Candidate 1: v1 endpoint (preferred for gpt-5.x)
        v1_base = effective_endpoint if "/openai/v1" in effective_endpoint else f"{resource_base}/openai/v1"
        v1_url = f"{v1_base.rstrip('/')}/chat/completions"
        v1_payload: Dict = {
            "model": resolved_model,
            "messages": messages,
            token_limit_field: max_tokens,
            "temperature": 0.1,
        }

        # Candidate 2: deployments endpoint (classic Azure format)
        deployment_url = (
            f"{resource_base}/openai/deployments/{resolved_model}/chat/completions"
            f"?api-version={effective_api_version}"
        )
        deployment_payload: Dict = {
            "messages": messages,
            token_limit_field: max_tokens,
            "temperature": 0.1,
        }

        candidates = [
            {"url": v1_url, "payload": v1_payload},
            {"url": deployment_url, "payload": deployment_payload},
        ]

        client = await self._get_http_client()
        for index, candidate in enumerate(candidates):
            try:
                response = await client.post(
                    candidate["url"],
                    headers={"api-key": effective_api_key, "Content-Type": "application/json"},
                    json=candidate["payload"],
                )
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                raise Exception("Azure vision API request timed out (90s)")
            except httpx.HTTPStatusError as e:
                can_retry = (
                    index < len(candidates) - 1
                    and e.response is not None
                    and e.response.status_code == 404
                )
                if can_retry:
                    logger.info(
                        "[Azure Vision] v1 URL returned 404, retrying with deployment URL"
                    )
                    continue
                error_detail = e.response.text if e.response else "Unknown error"
                raise Exception(f"Azure vision API error ({e.response.status_code}): {error_detail}")
            except httpx.HTTPError as e:
                raise Exception(f"Azure vision API connection error: {str(e)}")

        raise Exception("Azure vision API error: all endpoint strategies failed")

    async def _call_google_vision(
        self,
        image_b64: str,
        system_prompt: str,
        user_text: str,
        model: Optional[str],
        max_tokens: int,
    ) -> dict:
        """Call Google Gemini with a multimodal (vision) message."""
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY not set for vision requests.")

        resolved_model = model or "gemini-1.5-flash"
        base_url = "https://generativelanguage.googleapis.com/v1beta"

        # Gemini multimodal: combine system + user text, then inline image
        combined_text = f"{system_prompt}\n\n{user_text}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": combined_text},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_b64,
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": max_tokens},
        }

        client = await self._get_http_client()
        try:
            response = await client.post(
                f"{base_url}/models/{resolved_model}:generateContent?key={self.google_api_key}",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            if "candidates" in data and data["candidates"]:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "choices": [
                        {"message": {"role": "assistant", "content": content}, "finish_reason": "stop"}
                    ],
                    "model": resolved_model,
                    "usage": {"total_tokens": data.get("usageMetadata", {}).get("totalTokenCount", 0)},
                }
            raise Exception("No candidates in Gemini vision response")
        except httpx.TimeoutException:
            raise Exception("Google Gemini vision API request timed out (90s)")
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "Unknown error"
            raise Exception(f"Google Gemini vision API error ({e.response.status_code}): {error_detail}")
        except httpx.HTTPError as e:
            raise Exception(f"Google Gemini vision API connection error: {str(e)}")

    async def _call_google(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> dict:
        """Call Google Gemini API."""
        if not self.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set in environment. "
                "Get your key from: https://aistudio.google.com/app/apikey"
            )
        
        # Use default model if not specified
        if not model:
            model = "gemini-1.5-flash"
        
        # Google Gemini API endpoint
        base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        # Convert OpenAI-style messages to Gemini format
        gemini_contents = []
        for msg in messages:
            role = "user" if msg["role"] in ["user", "system"] else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        # Prepare request payload
        payload = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens or 8192,  # Increased default from 2000 to 8192 for complete responses
            }
        }
        
        # OPT-1: Reuse HTTP client for connection pooling (20-30% faster)
        client = await self._get_http_client()
        try:
            response = await client.post(
                f"{base_url}/models/{model}:generateContent?key={self.google_api_key}",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            # Convert Gemini response to OpenAI format for consistency
            if "candidates" in data and len(data["candidates"]) > 0:
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": content
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "model": model,
                    "usage": {
                        "total_tokens": data.get("usageMetadata", {}).get("totalTokenCount", 0)
                    }
                }
            raise Exception("No candidates in Gemini response")
            
        except httpx.TimeoutException:
            raise Exception("Google Gemini API request timed out (90s)")
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "Unknown error"
            raise Exception(f"Google Gemini API error ({e.response.status_code}): {error_detail}")
        except httpx.HTTPError as e:
            raise Exception(f"Google Gemini API connection error: {str(e)}")
    
    async def _call_cerebras(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> dict:
        """Call Cerebras API (OpenAI-compatible)."""
        if not self.cerebras_api_key:
            raise ValueError(
                "CEREBRAS_API_KEY not set in environment. "
                "Get your key from: https://cloud.cerebras.ai/"
            )
        
        # Cerebras API endpoint (OpenAI-compatible)
        base_url = "https://api.cerebras.ai/v1"

        candidate_models = self._build_cerebras_model_candidates(model)

        # OPT-1: Reuse HTTP client for connection pooling (20-30% faster)
        client = await self._get_http_client()
        for index, candidate_model in enumerate(candidate_models):
            payload = {
                "model": candidate_model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            try:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.cerebras_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                raise Exception("Cerebras API request timed out (90s)")
            except httpx.HTTPStatusError as e:
                can_retry_with_next_model = (
                    index < len(candidate_models) - 1
                    and self._is_model_unavailable_error(e)
                )
                if can_retry_with_next_model:
                    continue

                error_detail = e.response.text if e.response else "Unknown error"
                raise Exception(f"Cerebras API error ({e.response.status_code}): {error_detail}")
            except httpx.HTTPError as e:
                raise Exception(f"Cerebras API connection error: {str(e)}")
    
    async def _call_azure(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        endpoint_override: Optional[str] = None,
        api_version_override: Optional[str] = None,
    ) -> dict:
        """Call Azure OpenAI API (OpenAI-compatible)."""
        # Resolve per-model endpoint overrides (e.g. gpt-5.2 uses a dedicated resource)
        model_override = self._azure_model_endpoints.get(model or "", {})
        effective_endpoint = (
            endpoint_override
            or model_override.get("endpoint")
            or self.azure_endpoint
        )
        effective_api_version = (
            api_version_override
            or model_override.get("api_version")
            or self.azure_api_version
        )
        effective_api_key = model_override.get("api_key") or self.azure_api_key

        if not effective_api_key:
            raise ValueError(
                "AZURE_OPENAI_API_KEY not set in environment. "
                "Please add your Azure OpenAI API key to backend/.env file."
            )

        if not effective_endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT not set in environment. "
                "Please add your Azure endpoint to backend/.env file."
            )

        # Use default model if not specified (deployment name)
        if not model:
            model = "ChatGPT-UAT"

        # OPT-1: Reuse HTTP client for connection pooling (20-30% faster)
        client = await self._get_http_client()
        request_candidates = self._build_azure_request_candidates(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            endpoint=effective_endpoint,
            api_version=effective_api_version,
        )

        for index, request_candidate in enumerate(request_candidates):
            try:
                response = await client.post(
                    request_candidate["url"],
                    headers={
                        "api-key": effective_api_key,
                        "Content-Type": "application/json"
                    },
                    json=request_candidate["payload"]
                )
                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                raise Exception("Azure OpenAI API request timed out (90s)")
            except httpx.HTTPStatusError as e:
                can_retry_with_fallback = (
                    index < len(request_candidates) - 1
                    and e.response is not None
                    and e.response.status_code == 404
                )
                if can_retry_with_fallback:
                    continue

                error_detail = e.response.text if e.response else "Unknown error"
                raise Exception(f"Azure OpenAI API error ({e.response.status_code}): {error_detail}")
            except httpx.HTTPError as e:
                raise Exception(f"Azure OpenAI API connection error: {str(e)}")

        raise Exception("Azure OpenAI API error: all endpoint strategies failed")

    def _build_azure_request_candidates(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        """Build Azure request candidates for v1 and deployment API formats."""
        resolved_endpoint = (endpoint or self.azure_endpoint or "").rstrip("/")
        resolved_api_version = api_version or self.azure_api_version
        resource_base = resolved_endpoint.split("/openai")[0] if "/openai" in resolved_endpoint else resolved_endpoint
        token_limit_field = "max_completion_tokens" if model.startswith("gpt-5") else "max_tokens"

        v1_base = resolved_endpoint if "/openai/v1" in resolved_endpoint else f"{resource_base}/openai/v1"
        v1_url = f"{v1_base.rstrip('/')}/chat/completions"

        v1_payload: Dict[str, object] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            v1_payload[token_limit_field] = max_tokens

        deployment_url = (
            f"{resource_base}/openai/deployments/{model}/chat/completions"
            f"?api-version={resolved_api_version}"
        )
        deployment_payload: Dict[str, object] = {
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            deployment_payload[token_limit_field] = max_tokens

        request_candidates: List[Dict[str, object]] = [
            {"url": v1_url, "payload": v1_payload},
            {"url": deployment_url, "payload": deployment_payload},
        ]
        return request_candidates

    async def _call_local_vllm(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        enable_thinking: bool = False,
        custom_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> dict:
        """Call an on-premises vLLM server (OpenAI-compatible /v1/chat/completions).

        Sprint 10.13: supports three local models, each at its own endpoint.
        Falls back to DeepSeek-V4-Flash-4bit when no model is specified.

        Sprint 10.15: when enable_thinking=True AND the model is thinking-capable,
        injects chat_template_kwargs: { enable_thinking: true } into the request body.
        For non-capable models this flag is silently ignored regardless of the setting.

        Phase 2: when model is not in the hardcoded endpoint table and custom_endpoint
        is provided, uses that endpoint with api_key="local".
        """
        if not model:
            model = "DeepSeek-V4-Flash-4bit"

        model_cfg = self._local_vllm_model_endpoints.get(model)
        if not model_cfg:
            # Phase 2: fall back to custom endpoint for user-defined models
            if custom_endpoint:
                model_cfg = {"endpoint": custom_endpoint, "api_key": api_key or "local"}
            else:
                raise ValueError(
                    f"Unknown local_vllm model '{model}'. "
                    f"Supported models: {list(self._local_vllm_model_endpoints.keys())}. "
                    "Set a custom endpoint in Settings to use unlisted models."
                )

        endpoint = model_cfg["endpoint"].rstrip("/")
        api_key = api_key or model_cfg.get("api_key", "local")

        payload: Dict[str, object] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Sprint 10.18: for thinking-capable models always inject chat_template_kwargs
        # (even when False) so models whose built-in default is thinking=on are overridden.
        if model in _THINKING_CAPABLE_VLLM_MODELS:
            payload["chat_template_kwargs"] = {"enable_thinking": enable_thinking}

        client = await self._get_http_client()
        try:
            response = await client.post(
                f"{endpoint}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise Exception(f"Local vLLM ({model}) request timed out (90s)")
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else "Unknown error"
            raise Exception(f"Local vLLM ({model}) error ({e.response.status_code}): {error_detail}")
        except httpx.HTTPError as e:
            raise Exception(f"Local vLLM ({model}) connection error: {str(e)}")

    async def _call_openrouter(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> dict:
        """Call OpenRouter API."""
        if not self.openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set in environment. "
                "Please add it to backend/.env file."
            )
        
        # OpenRouter API endpoint
        base_url = "https://openrouter.ai/api/v1"

        candidate_models = self._build_openrouter_model_candidates(model)

        # OPT-1: Reuse HTTP client for connection pooling (20-30% faster)
        client = await self._get_http_client()
        for index, candidate_model in enumerate(candidate_models):
            payload = {
                "model": candidate_model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            try:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "AI Web Test"
                    },
                    json=payload
                )
                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                raise Exception("OpenRouter API request timed out (90s)")
            except httpx.HTTPStatusError as e:
                # Data-policy errors affect the entire account — retrying with
                # another model will not help.  Raise immediately with a clear
                # message that guides the user to the OpenRouter privacy settings.
                if self._is_data_policy_error(e):
                    raise Exception(
                        "OpenRouter free models are blocked by your account's data policy. "
                        "To fix this, go to https://openrouter.ai/settings/privacy and "
                        "enable 'Allow AI training' (Free model publication). "
                        "Alternatively, switch to a paid model that does not require this setting."
                    )

                can_retry_with_next_model = (
                    index < len(candidate_models) - 1
                    and self._is_model_unavailable_error(e)
                )
                if can_retry_with_next_model:
                    continue

                error_detail = e.response.text if e.response else "Unknown error"
                raise Exception(f"OpenRouter API error ({e.response.status_code}): {error_detail}")
            except httpx.HTTPError as e:
                raise Exception(f"OpenRouter API connection error: {str(e)}")

    @staticmethod
    def _is_data_policy_error(error: httpx.HTTPStatusError) -> bool:
        """Return True when OpenRouter rejects a request due to the account's
        data/privacy policy (Free model publication setting).

        This error looks like a model-unavailable 404 but affects ALL free models
        regardless of which one is requested.  It must not trigger a retry loop.
        """
        response = error.response
        if response is None or response.status_code != 404:
            return False
        return "data policy" in response.text.lower()

    @staticmethod
    def _is_model_unavailable_error(error: httpx.HTTPStatusError) -> bool:
        """Return True for provider responses indicating the selected model is unavailable."""
        response = error.response
        if response is None or response.status_code not in (400, 404):
            return False

        error_text = response.text.lower()
        unavailable_markers = [
            "no endpoints found",
            "model not found",
            "invalid model",
            "unknown model",
            "does not exist",
        ]
        return any(marker in error_text for marker in unavailable_markers)

    def _build_openrouter_model_candidates(self, requested_model: Optional[str]) -> List[str]:
        """Build OpenRouter model retry candidates in priority order without duplicates."""
        primary_model = requested_model or settings.OPENROUTER_MODEL
        candidates: List[str] = [primary_model]

        if primary_model and primary_model.endswith(":free"):
            candidates.append(primary_model[:-5])

        candidates.extend(
            [
                settings.OPENROUTER_MODEL,
                self.OPENROUTER_DEFAULT_FALLBACK_MODEL,
            ]
        )
        return self._unique_non_empty(candidates)

    def _build_cerebras_model_candidates(self, requested_model: Optional[str]) -> List[str]:
        """Build Cerebras model retry candidates in priority order without duplicates."""
        primary_model = requested_model or settings.CEREBRAS_MODEL or self.CEREBRAS_DEFAULT_FALLBACK_MODEL
        candidates: List[str] = [
            primary_model,
            settings.CEREBRAS_MODEL,
            self.CEREBRAS_DEFAULT_FALLBACK_MODEL,
        ]
        return self._unique_non_empty(candidates)

    @staticmethod
    def _unique_non_empty(values: List[Optional[str]]) -> List[str]:
        """Return non-empty strings in original order without duplicates."""
        unique_values: List[str] = []
        seen = set()
        for value in values:
            if not value:
                continue
            if value in seen:
                continue
            seen.add(value)
            unique_values.append(value)
        return unique_values
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """
        OPT-1: Get or create shared HTTP client for connection pooling.
        Reusing the same client reduces connection overhead by 20-30%.
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=90.0,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
            )
        return self._http_client
    
    async def close(self):
        """Close the HTTP client when service is no longer needed."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
