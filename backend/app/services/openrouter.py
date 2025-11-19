"""OpenRouter API integration for LLM chat completions."""
import httpx
from typing import List, Dict, Optional
from app.core.config import settings


class OpenRouterService:
    """Service for interacting with OpenRouter API."""
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "anthropic/claude-3.5-sonnet",  # Claude is available globally
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> dict:
        """
        Call OpenRouter API for chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (default: gpt-4-turbo)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            API response dict with choices, usage, etc.
            
        Raises:
            ValueError: If API key is not configured
            Exception: If API call fails
        """
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set in environment. "
                "Please add it to backend/.env file."
            )
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Make API call with timeout
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8000",  # Optional: for OpenRouter analytics
                        "X-Title": "AI Web Test"  # Optional: app identifier
                    },
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.TimeoutException:
                raise Exception("OpenRouter API request timed out (60s)")
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text if e.response else "Unknown error"
                raise Exception(f"OpenRouter API error ({e.response.status_code}): {error_detail}")
            except httpx.HTTPError as e:
                raise Exception(f"OpenRouter API connection error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """
        Test if OpenRouter API is accessible and working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Respond with 'OK' if you receive this."}
            ]
            response = await self.chat_completion(messages, max_tokens=10)
            return "choices" in response and len(response["choices"]) > 0
        except Exception:
            return False

