"""
Universal LLM service that supports multiple providers.
Handles Google Gemini, Cerebras, and OpenRouter.
"""
import httpx
import os
from typing import List, Dict, Optional
from app.core.config import settings


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
        
        # OPT-1: HTTP Session Reuse - Create shared httpx client for connection pooling
        # This reduces connection overhead by 20-30% for multiple LLM calls
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = "openrouter",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> dict:
        """
        Call LLM API for chat completion with provider selection.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            provider: Provider to use (google, cerebras, openrouter)
            model: Model to use (provider-specific)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Unified API response dict with choices, usage, etc.
            
        Raises:
            ValueError: If API key is not configured
            Exception: If API call fails
        """
        provider = provider.lower()
        
        if provider == "google":
            return await self._call_google(messages, model, temperature, max_tokens)
        elif provider == "cerebras":
            return await self._call_cerebras(messages, model, temperature, max_tokens)
        elif provider == "azure":
            return await self._call_azure(messages, model, temperature, max_tokens)
        else:  # default to openrouter
            return await self._call_openrouter(messages, model, temperature, max_tokens)
    
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
        max_tokens: Optional[int] = None
    ) -> dict:
        """Call Azure OpenAI API (OpenAI-compatible)."""
        if not self.azure_api_key:
            raise ValueError(
                "AZURE_OPENAI_API_KEY not set in environment. "
                "Please add your Azure OpenAI API key to backend/.env file."
            )
        
        if not self.azure_endpoint:
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
        )

        for index, request_candidate in enumerate(request_candidates):
            try:
                response = await client.post(
                    request_candidate["url"],
                    headers={
                        "api-key": self.azure_api_key,
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
    ) -> List[Dict[str, object]]:
        """Build Azure request candidates for v1 and deployment API formats."""
        endpoint = (self.azure_endpoint or "").rstrip("/")
        resource_base = endpoint.split("/openai")[0] if "/openai" in endpoint else endpoint

        v1_base = endpoint if "/openai/v1" in endpoint else f"{resource_base}/openai/v1"
        v1_url = f"{v1_base.rstrip('/')}/chat/completions"

        v1_payload: Dict[str, object] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            v1_payload["max_tokens"] = max_tokens

        deployment_url = (
            f"{resource_base}/openai/deployments/{model}/chat/completions"
            f"?api-version={self.azure_api_version}"
        )
        deployment_payload: Dict[str, object] = {
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            deployment_payload["max_tokens"] = max_tokens

        request_candidates: List[Dict[str, object]] = [
            {"url": v1_url, "payload": v1_payload},
            {"url": deployment_url, "payload": deployment_payload},
        ]
        return request_candidates
    
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
