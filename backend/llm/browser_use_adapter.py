"""
Browser-Use LLM Adapter - Adapts Azure OpenAI to browser-use LLM interface

This adapter allows browser-use library to use Azure OpenAI for LLM-guided navigation.
Browser-use expects an LLM object with async chat completion methods.
"""

import logging
from typing import List, Dict, Any, Optional, AsyncIterator
from llm.azure_client import get_azure_client

logger = logging.getLogger(__name__)

# Try to import browser-use LLM base class
try:
    from browser_use.llm import LLM as BrowserUseLLM
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    # Create stub base class if browser-use not available
    class BrowserUseLLM:
        """Stub base class when browser-use not available"""
        pass


class AzureOpenAIAdapter(BrowserUseLLM):
    """
    Adapter to use Azure OpenAI with browser-use library.
    
    Browser-use expects an LLM object with:
    - async achat() method for chat completions
    - Support for streaming responses
    """
    
    def __init__(self, azure_client=None):
        """
        Initialize adapter with Azure OpenAI client.
        
        Args:
            azure_client: Optional AzureClient instance (creates new if not provided)
        """
        if not BROWSER_USE_AVAILABLE:
            logger.warning("browser-use not available - adapter will not work")
        
        self.azure_client = azure_client or get_azure_client()
        
        if not self.azure_client or not self.azure_client.enabled:
            logger.warning("Azure OpenAI client not enabled - adapter will fail")
    
    async def achat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Async chat completion for browser-use.
        
        Browser-use calls this method with messages in format:
        [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            ...
        ]
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Assistant response as string
        """
        if not self.azure_client or not self.azure_client.enabled:
            raise ValueError("Azure OpenAI client not enabled")
        
        try:
            # Convert browser-use message format to Azure OpenAI format
            # Browser-use uses: [{"role": "system", "content": "..."}, ...]
            # Azure OpenAI expects same format, so we can use directly
            
            # Extract parameters from kwargs
            temperature = kwargs.get("temperature", 0.3)
            max_tokens = kwargs.get("max_tokens", 2000)
            
            # Call Azure OpenAI
            response = await self._call_azure_openai(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error in browser-use LLM adapter: {e}", exc_info=True)
            raise
    
    async def _call_azure_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        Call Azure OpenAI chat completion API (async wrapper).
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Max tokens in response
        
        Returns:
            Assistant response text
        """
        if not self.azure_client.client:
            raise ValueError("Azure OpenAI client not initialized")
        
        try:
            # Azure OpenAI SDK is synchronous, so we run it in a thread pool
            import asyncio
            
            def _sync_call():
                return self.azure_client.client.chat.completions.create(
                    model=self.azure_client.deployment,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            # Run synchronous call in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, _sync_call)
            
            # Extract response text
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                raise ValueError("No response from Azure OpenAI")
        
        except Exception as e:
            logger.error(f"Azure OpenAI API call failed: {e}", exc_info=True)
            raise
    
    async def astream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat completion for browser-use (optional, for real-time responses).
        
        Args:
            messages: List of message dicts
            **kwargs: Additional parameters
        
        Yields:
            Response chunks as strings
        """
        if not self.azure_client or not self.azure_client.enabled:
            raise ValueError("Azure OpenAI client not enabled")
        
        try:
            import asyncio
            
            temperature = kwargs.get("temperature", 0.3)
            max_tokens = kwargs.get("max_tokens", 2000)
            
            # Stream from Azure OpenAI (synchronous, so we need to wrap it)
            def _sync_stream():
                return self.azure_client.client.chat.completions.create(
                    model=self.azure_client.deployment,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
            
            # Run in thread pool and yield chunks
            loop = asyncio.get_event_loop()
            stream = await loop.run_in_executor(None, _sync_stream)
            
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield delta.content
        
        except Exception as e:
            logger.error(f"Error streaming from Azure OpenAI: {e}", exc_info=True)
            raise

