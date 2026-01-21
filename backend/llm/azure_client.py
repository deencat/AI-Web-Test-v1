"""
Azure OpenAI LLM Client - Enterprise-grade inference for web element analysis

Uses your company's Azure OpenAI deployment (ChatGPT-UAT with GPT-4o)
"""

import os
import logging
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

# Try to import Azure OpenAI SDK
try:
    from openai import AzureOpenAI
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning("Azure OpenAI SDK not installed. Using stub mode.")


class AzureClient:
    """
    Client for Azure OpenAI inference API.
    
    Usage:
        client = AzureClient()  # Loads from .env automatically
        result = await client.analyze_page_elements(
            html="<html>...</html>",
            basic_elements=[...],
            url="https://example.com/login"
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        """
        Initialize Azure OpenAI client.
        
        Args:
            api_key: Azure OpenAI API key (or set AZURE_OPENAI_API_KEY env var)
            endpoint: Azure OpenAI endpoint (or set AZURE_OPENAI_ENDPOINT env var)
            deployment: Deployment name (or set AZURE_OPENAI_MODEL env var)
            temperature: Sampling temperature (0.0-1.0, lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY", "")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_MODEL", "ChatGPT-UAT")
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if AZURE_AVAILABLE and self.api_key and self.endpoint:
            # Remove /openai/v1 suffix if present, SDK adds it automatically
            clean_endpoint = self.endpoint.replace("/openai/v1", "").replace("/openai", "")
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version="2024-02-15-preview",
                azure_endpoint=clean_endpoint
            )
            self.enabled = True
            logger.info(f"Azure OpenAI client initialized with deployment: {self.deployment}")
            logger.info(f"Using endpoint: {clean_endpoint}")
        else:
            self.client = None
            self.enabled = False
            if not AZURE_AVAILABLE:
                logger.warning("Azure OpenAI SDK not available - install with: pip install openai")
            elif not self.api_key:
                logger.warning("Azure OpenAI API key not provided - set AZURE_OPENAI_API_KEY")
            elif not self.endpoint:
                logger.warning("Azure OpenAI endpoint not provided - set AZURE_OPENAI_ENDPOINT")
    
    async def analyze_page_elements(
        self,
        html: str,
        basic_elements: List[Dict],
        url: str,
        page_title: str = "",
        learned_patterns: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Analyze page HTML to find interactive elements that Playwright might miss.
        
        Args:
            html: Page HTML content
            basic_elements: Elements already found by Playwright
            url: Page URL for context
            page_title: Page title
            learned_patterns: Previously learned patterns for similar pages
            
        Returns:
            Dict with enhanced_elements, suggested_selectors, page_patterns, missed_by_playwright
        """
        if not self.enabled:
            logger.warning("Azure OpenAI not enabled, using stub analysis")
            return self._stub_analysis(basic_elements)
        
        try:
            # Build analysis prompt
            prompt = self._build_analysis_prompt(
                html, basic_elements, url, page_title, learned_patterns
            )
            
            # Call Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert web element analyzer. Analyze HTML pages to find interactive elements for test automation. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Azure OpenAI found {len(result.get('enhanced_elements', []))} additional elements")
            return result
            
        except Exception as e:
            logger.error(f"Error in Azure OpenAI analysis: {e}")
            return self._stub_analysis(basic_elements)
    
    def _build_analysis_prompt(
        self,
        html: str,
        basic_elements: List[Dict],
        url: str,
        page_title: str,
        learned_patterns: Optional[List[Dict]]
    ) -> str:
        """Build detailed analysis prompt for Azure OpenAI."""
        
        # Truncate HTML to avoid token limits
        html_snippet = html[:15000] if len(html) > 15000 else html
        
        # Format basic elements
        elements_summary = "\n".join([
            f"- {elem.get('type', 'unknown')}: {elem.get('text', 'no text')[:50]}"
            for elem in basic_elements[:20]
        ])
        
        prompt = f"""Analyze this web page to find interactive elements for test automation.

**Page Information:**
- URL: {url}
- Title: {page_title}
- Playwright found {len(basic_elements)} elements

**Playwright Baseline Elements:**
{elements_summary}

**HTML Content (truncated):**
{html_snippet}

**Your Task:**
Find interactive elements that Playwright might have missed, such as:
1. Custom components with `role` attributes (e.g., `<div role="button">`)
2. Elements with `onclick` handlers
3. Shadow DOM elements
4. Dynamically loaded content
5. Hidden dropdowns/modals
6. Elements with `data-testid` or similar attributes

**Required JSON Response Format:**
```json
{{
  "enhanced_elements": [
    {{
      "type": "button|input|link|form|custom",
      "selector": "CSS or XPath selector",
      "text": "visible text content",
      "semantic_purpose": "login|search|navigation|submit|etc",
      "attributes": {{"role": "button", "data-testid": "..."}},
      "confidence": 0.0-1.0,
      "why_important": "explanation of why this element matters for testing"
    }}
  ],
  "suggested_selectors": {{
    "descriptive_name": "[data-testid='login'], button:has-text('Login')"
  }},
  "page_patterns": {{
    "page_type": "login|dashboard|form|e-commerce|pricing|etc",
    "framework": "react|vue|angular|jquery|custom",
    "complexity": "simple|medium|complex"
  }},
  "missed_by_playwright": [
    {{
      "element": "Element description",
      "reason": "Why Playwright missed it",
      "selector": "Recommended selector"
    }}
  ]
}}
```

Respond with valid JSON only."""
        
        return prompt
    
    def _stub_analysis(self, basic_elements: List[Dict]) -> Dict[str, Any]:
        """Fallback stub analysis when Azure OpenAI not available."""
        return {
            "enhanced_elements": [
                {
                    "type": "custom",
                    "selector": "[role='button']",
                    "text": "Custom button",
                    "semantic_purpose": "interaction",
                    "attributes": {"role": "button"},
                    "confidence": 0.7,
                    "why_important": "Custom interactive element"
                }
            ],
            "suggested_selectors": {
                "interactive_elements": "[role='button'], [onclick]"
            },
            "page_patterns": {
                "page_type": "form",
                "framework": "unknown",
                "complexity": "medium"
            },
            "missed_by_playwright": [
                {
                    "element": "Custom dropdown",
                    "reason": "Hidden in shadow DOM",
                    "selector": "[data-dropdown]"
                }
            ]
        }


# Singleton instance
_azure_client = None

def get_azure_client() -> AzureClient:
    """Get or create singleton Azure OpenAI client."""
    global _azure_client
    if _azure_client is None:
        _azure_client = AzureClient()
    return _azure_client
